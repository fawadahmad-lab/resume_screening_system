"""FastAPI HTTP adapter for the React frontend (thin — calls src/pipeline.py).

No screening/scoring/evaluation logic lives here; this module only wires the
existing pipeline functions to HTTP, persists real screening runs to
data/screenings/<id>/ (gitignored, file-backed JSON, no database), and runs
long-running batches in a background thread so React can poll
GET /api/screenings/{id} instead of blocking an HTTP request.

Run (dev):
    uvicorn src.api:app --host 127.0.0.1 --port 8000

Endpoints:
    POST /api/screenings           multipart: jd_text (str) and/or jd_file
                                   (upload); resumes[] (uploads) and/or
                                   sample_resumes (filenames from
                                   data/sample_resumes/). Returns {screening_id}.
    GET  /api/screenings           list of persisted screening runs
    GET  /api/screenings/{id}      status, progress, results, failures
    GET  /api/jobs                 read-only catalog of data/sample_jds/
    GET  /api/jobs/{job_id}        text content of one sample JD
    GET  /api/sample-resumes       filenames in data/sample_resumes/
    GET  /api/evals                merged day3_baseline.json +
                                   day4_narrowed_rule.json (read-only)
    GET  /api/system               read-only live provider/model/config state

Production: frontend/dist is mounted at / so the built SPA is served from the
same origin (no CORS config). API routes take precedence over the mount.
"""

import json
import logging
import os
import re
import shutil
import threading
import time
import uuid
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src.config import (
    get_call_interval,
    get_client,
    get_max_retries,
    get_model,
    get_ollama_model,
    get_provider,
    get_score_ensemble_n,
    get_temperature,
    get_timeout,
)
from src.extract import extract_text
from src.pipeline import run_pipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("api")

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCREENINGS_DIR = os.path.join(ROOT_DIR, "data", "screenings")
SAMPLE_RESUMES_DIR = os.path.join(ROOT_DIR, "data", "sample_resumes")
SAMPLE_JDS_DIR = os.path.join(ROOT_DIR, "data", "sample_jds")
RESULTS_DIR = os.path.join(ROOT_DIR, "data", "results")
FRONTEND_DIST = os.path.join(ROOT_DIR, "frontend", "dist")

RESUME_EXTS = (".txt", ".pdf", ".docx")
JD_EXTS = (".txt", ".pdf", ".docx", ".md")

app = FastAPI(title="Resume Screening API", version="1.0.0")

# In-memory job registry: screening_id -> state dict. States are also
# persisted to disk after every candidate so runs survive a restart.
_JOBS: Dict[str, Dict[str, Any]] = {}
_JOBS_LOCK = threading.Lock()

VALID_STATUSES = {"queued", "processing", "done", "failed"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_name(name: str) -> str:
    """Sanitize a user-supplied filename to a safe basename."""
    base = os.path.basename(name or "").strip()
    base = re.sub(r"[^A-Za-z0-9._-]+", "_", base)
    if not base:
        raise HTTPException(status_code=400, detail="Invalid filename")
    return base


def _candidate_id_from_file(filename: str) -> str:
    return os.path.splitext(filename)[0]


def _job_path(screening_id: str) -> str:
    return os.path.join(SCREENINGS_DIR, screening_id, "screening.json")


def _list_sample_resumes() -> List[str]:
    if not os.path.isdir(SAMPLE_RESUMES_DIR):
        return []
    return sorted(
        f for f in os.listdir(SAMPLE_RESUMES_DIR)
        if f.lower().endswith(RESUME_EXTS)
    )


def _list_sample_jds() -> List[Dict[str, str]]:
    if not os.path.isdir(SAMPLE_JDS_DIR):
        return []
    out = []
    for f in sorted(os.listdir(SAMPLE_JDS_DIR)):
        if f.lower().endswith(".txt"):
            out.append({"id": f, "name": f})
    return out


def _read_job_state(screening_id: str) -> Dict[str, Any]:
    with _JOBS_LOCK:
        state = _JOBS.get(screening_id)
        if state is not None:
            return state
    path = _job_path(screening_id)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"Unknown screening {screening_id}")
    with open(path) as f:
        return json.load(f)


def _persist_state(state: Dict[str, Any]) -> None:
    try:
        dirpath = os.path.dirname(_job_path(state["id"]))
        os.makedirs(dirpath, exist_ok=True)
        tmp = _job_path(state["id"]) + ".tmp"
        with open(tmp, "w") as f:
            json.dump(state, f, indent=2, default=str)
        os.replace(tmp, _job_path(state["id"]))
    except Exception as e:
        logger.error("Failed to persist screening %s: %s", state.get("id"), e)


def _validate_resume_names(sample_names: List[str]) -> None:
    allowed = set(_list_sample_resumes())
    for name in sample_names:
        if name not in allowed:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown sample resume: {name}",
            )


def _build_resume_selections(
    uploaded: List[Any], sample_names: List[str], resumes_dir: str
) -> List[Dict[str, str]]:
    """Return normalized [{candidate_id, file, source, path}] with dedup."""
    selections: List[Dict[str, str]] = []
    used: set = set()

    for ug in uploaded:
        filename = _safe_name(ug.filename or "resume")
        if not filename.lower().endswith(RESUME_EXTS):
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported resume file type: {filename}",
            )
        base = _candidate_id_from_file(filename)
        dup = base
        n = 2
        while base in used:
            base = f"{dup}_{n}"
            n += 1
        used.add(base)
        path = os.path.join(resumes_dir, base + os.path.splitext(filename)[1])
        with open(path, "wb") as out:
            out.write(ug.file.read())  # type: ignore[attr-defined]
        selections.append(
            {"candidate_id": base, "file": base + os.path.splitext(filename)[1],
             "source": "upload", "path": path}
        )

    for name in sample_names:
        base = _candidate_id_from_file(name)
        dup = base
        n = 2
        while base in used:
            base = f"{dup}_{n}"
            n += 1
        used.add(base)
        path = os.path.join(SAMPLE_RESUMES_DIR, name)
        selections.append(
            {"candidate_id": base, "file": name, "source": "sample", "path": path}
        )
    return selections


# ---------------------------------------------------------------------------
# Background worker
# ---------------------------------------------------------------------------

def _run_screening_job(state: Dict[str, Any]) -> None:
    """Execute a screening batch in a background thread, updating state."""
    screening_id = state["id"]
    resumes_dir = os.path.join(SCREENINGS_DIR, screening_id, "resumes")
    try:
        with _JOBS_LOCK:
            for c in state["candidates"]:
                c["status"] = "queued"
            state["status"] = "processing"
            _persist_state(state)

        def on_progress(done: int, total: int) -> None:
            with _JOBS_LOCK:
                state["progress_done"] = done
                state["progress_total"] = total
                # mark the candidates finished so far as done (1-indexed)
                for idx, c in enumerate(state["candidates"], start=1):
                    if idx <= done and c["status"] == "queued":
                        c["status"] = "done"
                _persist_state(state)

        ordered, flagged, failures = run_pipeline(
            jd_text=state["jd_text"],
            resume_files=[c["path"] for c in state["candidates"]],
            client=get_client(),
            on_progress=on_progress,
        )

        with _JOBS_LOCK:
            by_file = {c["file"]: c for c in state["candidates"]}
            failed_files = {f.get("file") for f in failures}
            for outcome in ordered:
                c = by_file.get(outcome["input_file"])
                if c:
                    c["status"] = "done"
                    c["outcome"] = outcome
            # Candidates that started but never produced an outcome are failed
            for c in state["candidates"]:
                if c["file"] in failed_files:
                    c["status"] = "failed"
                elif c["status"] != "done":
                    c["status"] = "failed"
            state["ordered"] = ordered
            state["flagged"] = flagged
            state["failures"] = failures
            state["status"] = "completed"
            state["completed_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
            state["progress_done"] = len(ordered) + len(failures)
            state["progress_total"] = len(state["candidates"])
            _persist_state(state)
        logger.info("Screening %s completed: %d results, %d failures",
                    screening_id, len(ordered), len(failures))
    except Exception as e:
        logger.exception("Screening %s failed at the batch level", screening_id)
        with _JOBS_LOCK:
            state["status"] = "failed"
            state["error"] = str(e)
            state["completed_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
            _persist_state(state)


# ---------------------------------------------------------------------------
# Screening endpoints
# ---------------------------------------------------------------------------

@app.post("/api/screenings", status_code=202)
async def create_screening(
    resumes: Optional[List[UploadFile]] = File(default=None),
    sample_resumes: Optional[List[str]] = Form(default=None),
    jd_text: Optional[str] = Form(default=None),
    jd_file: Optional[UploadFile] = File(default=None),
    jd_name: Optional[str] = Form(default=None),
) -> Dict[str, str]:
    """Create a screening job. Returns before processing (job runs async)."""
    sample_names = [s for s in (sample_resumes or []) if s]
    uploaded = [r for r in (resumes or []) if r.filename]
    if not uploaded and not sample_names:
        raise HTTPException(
            status_code=400,
            detail="At least one resume is required (upload or sample resume)"
        )
    if sample_names:
        _validate_resume_names(sample_names)
    if not (jd_text and jd_text.strip()) and jd_file is None:
        raise HTTPException(
            status_code=400,
            detail="A job description is required (jd_text or jd_file)"
        )

    # Resolve JD text
    if jd_file is not None:
        jd_filename = _safe_name(jd_file.filename or "job.txt")
        if not jd_filename.lower().endswith(JD_EXTS):
            raise HTTPException(status_code=400, detail="Unsupported JD file type")
        tmp_path = os.path.join(SCREENINGS_DIR, "tmp", uuid.uuid4().hex + jd_filename)
        os.makedirs(os.path.dirname(tmp_path), exist_ok=True)
        with open(tmp_path, "wb") as out:
            out.write(jd_file.file.read())  # type: ignore[attr-defined]
        try:
            jd_text = extract_text(tmp_path)
        finally:
            shutil.rmtree(os.path.dirname(tmp_path), ignore_errors=True)
        if not jd_text.strip():
            raise HTTPException(status_code=400, detail="JD file produced no text")

    screening_id = uuid.uuid4().hex[:12]
    resumes_dir = os.path.join(SCREENINGS_DIR, screening_id, "resumes")
    os.makedirs(resumes_dir, exist_ok=True)

    selections = _build_resume_selections(
        uploaded, sample_names, resumes_dir
    )

    state: Dict[str, Any] = {
        "id": screening_id,
        "status": "queued",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "completed_at": None,
        "jd_text": (jd_text or "").strip(),
        "jd_name": jd_name or ("Uploaded job description" if jd_file is not None
                               else "Pasted job description"),
        "candidates": [
            {
                "candidate_id": s["candidate_id"],
                "file": s["file"],
                "source": s["source"],
                "path": s["path"],
                "status": "queued",
                "outcome": None,
                "error": None,
            }
            for s in selections
        ],
        "progress_done": 0,
        "progress_total": len(selections),
        "ordered": [],
        "flagged": [],
        "failures": [],
        "error": None,
    }

    with _JOBS_LOCK:
        _JOBS[screening_id] = state
    _persist_state(state)

    thread = threading.Thread(
        target=_run_screening_job, args=(state,), daemon=True
    )
    thread.start()
    return {"screening_id": screening_id}


@app.get("/api/screenings")
def list_screenings() -> Dict[str, Any]:
    """List persisted screening runs (newest first), without full results."""
    runs: List[Dict[str, Any]] = []
    if os.path.isdir(SCREENINGS_DIR):
        for entry in os.listdir(SCREENINGS_DIR):
            if not entry:  # skip tmp dir / non-dirs
                continue
            path = _job_path(entry)
            if not os.path.exists(path):
                continue
            try:
                with open(path) as f:
                    st = json.load(f)
                runs.append({
                    "id": st.get("id", entry),
                    "status": st.get("status"),
                    "created_at": st.get("created_at"),
                    "completed_at": st.get("completed_at"),
                    "candidate_count": st.get("progress_total", len(st.get("candidates", []))),
                    "result_count": len(st.get("ordered", [])),
                    "failure_count": len(st.get("failures", [])),
                    "flagged_count": len(st.get("flagged", [])),
                })
            except Exception as e:
                logger.warning("Could not read screening %s: %s", entry, e)
    runs.sort(key=lambda r: r.get("created_at") or "", reverse=True)
    return {"screenings": runs}


@app.get("/api/screenings/{screening_id}")
def get_screening(screening_id: str) -> Dict[str, Any]:
    """Return a screening's status, progress, results and failures."""
    state = _read_job_state(screening_id)
    return state


@app.get("/api/jobs")
def list_jobs() -> Dict[str, Any]:
    return {"jobs": _list_sample_jds()}


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str) -> Dict[str, str]:
    """Return the plain-text content of one sample JD (read-only catalog)."""
    safe = _safe_name(job_id)
    path = os.path.join(SAMPLE_JDS_DIR, safe)
    if not safe.endswith(".txt") or not os.path.isfile(path):
        raise HTTPException(status_code=404, detail=f"Unknown sample JD: {job_id}")
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return {"id": safe, "name": safe, "text": f.read()}


@app.get("/api/sample-resumes")
def list_sample_resumes() -> Dict[str, Any]:
    return {"resumes": _list_sample_resumes()}


@app.get("/api/evals")
def get_evals() -> Dict[str, Any]:
    """Merged read-only view of the committed dev-set snapshots."""
    baseline_path = os.path.join(RESULTS_DIR, "day3_baseline.json")
    after_path = os.path.join(RESULTS_DIR, "day4_narrowed_rule.json")
    if not os.path.exists(baseline_path):
        raise HTTPException(status_code=404, detail="day3_baseline.json not found")
    with open(baseline_path) as f:
        baseline = json.load(f)
    after = None
    if os.path.exists(after_path):
        with open(after_path) as f:
            after = json.load(f)

    merged = []
    if after is not None:
        after_by_name = {r["name"]: r for r in after["results"]}
        for comp in baseline.get("comparison", []):
            name = comp["name"]
            ar = after_by_name.get(name)
            merged.append({
                "case": comp["case"],
                "name": name,
                "expected": comp["expected"],
                "baseline_actual": comp["actual"],
                "baseline_match": comp["match"],
                "after_actual": ar.get("predicted") if ar else None,
                "after_match": (ar.get("predicted") == comp["expected"]) if ar else None,
                "after_total": ar.get("total") if ar else None,
                "baseline_total": next(
                    (r.get("total") for r in baseline["results"] if r.get("name") == name),
                    None,
                ),
            })
    else:
        for comp in baseline.get("comparison", []):
            merged.append({
                "case": comp["case"],
                "name": comp["name"],
                "expected": comp["expected"],
                "baseline_actual": comp["actual"],
                "baseline_match": comp["match"],
                "after_actual": None,
                "after_match": None,
                "after_total": None,
                "baseline_total": next(
                    (r.get("total") for r in baseline["results"] if r.get("name") == name),
                    None,
                ),
            })

    return {
        "baseline": {
            "file": "day3_baseline.json",
            "summary": baseline.get("summary"),
        },
        "after": {
            "file": "day4_narrowed_rule.json" if after else None,
            "summary": after.get("summary") if after else None,
        },
        "cases": merged,
    }


@app.get("/api/system")
def get_system() -> Dict[str, Any]:
    """Read-only live system/configuration state."""
    return {
        "provider": get_provider(),
        "model": get_model(),
        "ollama_model": get_ollama_model(),
        "temperature": get_temperature(),
        "max_retries": get_max_retries(),
        "call_interval_s": get_call_interval(),
        "timeout_s": get_timeout(),
        "score_ensemble_n": get_score_ensemble_n(),
        "data_dir": "data/screenings",
    }


# ---------------------------------------------------------------------------
# Static SPA (production build) + SPA fallback
# ---------------------------------------------------------------------------

if os.path.isdir(FRONTEND_DIST):
    assets_dir = os.path.join(FRONTEND_DIST, "assets")
    if os.path.isdir(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}")
    def spa_fallback(full_path: str):
        """Serve index.html for client-side routes; real files when they exist."""
        candidate = os.path.join(FRONTEND_DIST, full_path)
        if full_path and os.path.isfile(candidate):
            return FileResponse(candidate)
        index = os.path.join(FRONTEND_DIST, "index.html")
        if os.path.exists(index):
            return FileResponse(index)
        raise HTTPException(status_code=404, detail="Frontend build not found")


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)