# ARCHITECTURE — Resume Screening System

This document describes how the system is built and why. It is the companion
to [`RUNBOOK.md`](RUNBOOK.md) (operation) and [`EVALUATION.md`](EVALUATION.md)
(testing/results). Decisions and rationale are tracked in the Open Decisions
Log (AGENTS.md §16).

## Pipeline overview

```
JD text + resume file(s)
  → [1] Extraction:  PDF/docx → plain text        (deterministic code, NOT an LLM call)
  → [2] Normalization: plain text → structured candidate profile (LLM call, structured output)
  → [3] Scoring: profile + JD + raw resume → rubric-based JSON (LLM call, structured output, forced schema)
  → [4] Validation: schema check, non-empty evidence, score range check, fit-band consistency
  → [5] Output: ranked table + flagged-for-review list (CLI JSON and/or Streamlit UI)
```

Stage [1] is deterministic code (`pdfplumber`/`python-docx`/`plain text`).
Stages [2] and [3] use structured output — a JSON schema in strict mode —
never free-text parsing or regex fallback. Stage [4] is pure functions
(`src/validate.py`) that reject invalid results; the pipeline retries once,
then flags for human review.

## Data flow & schemas

### Normalized candidate profile (intermediate, `src/normalize.py`)

```json
{
  "candidate_id": "string",
  "name": "string",
  "skills": ["string"],
  "titles": ["string"],
  "date_ranges": [{"start": "YYYY-MM", "end": "YYYY-MM or 'present'"}],
  "education": ["string"]
}
```

Pydantic v2 models mirror the Section 8 schemas exactly.

### Final output per candidate (`src/score.py`, ensembled)

```json
{
  "candidate_id": "string",
  "overall_fit": "Strong Fit | Possible Fit | Not a Fit",
  "confidence": "High | Medium | Low",
  "criteria_scores": [
    {"criterion": "Required skills match", "score": 0, "evidence": "string"},
    {"criterion": "Years of relevant experience", "score": 0, "evidence": "string"},
    {"criterion": "Title/seniority alignment", "score": 0, "evidence": "string"},
    {"criterion": "Career trajectory coherence", "score": 0, "evidence": "string"},
    {"criterion": "Red flags", "score": 0, "evidence": "string"}
  ],
  "flag_for_human_review": false,
  "flag_reason": "string or null"
}
```

- `score` is an integer **0–2** per criterion.
- `evidence` must be **non-empty and grounded** in the actual resume text.
  A missing or generic evidence string (e.g. "resume shows relevant
  experience") is a validation failure, not a pass. A generic phrase is only
  rejected when the evidence otherwise carries no digits (dates/numbers), so
  grounded evidence that echoes a criterion name passes
  (`evidence_valid()` in `src/validate.py`).
- Evidence strings are **paraphrase-only**: the rubric forbids literal
  double-quote, single-quote, or backslash characters in an evidence string
  (hardening added 2026-09-10 after a model began copying quote-spans
  verbatim and corrupting the strict-JSON output — see AGENTS.md §16).

## Scoring rubric

- Sum of `criteria_scores` → total (0–10).
- **8–10 → Strong Fit**, **5–7 → Possible Fit**, **0–4 → Not a Fit**.
- "Red flags" criterion: 2 = none found, 1 = minor (e.g. short unexplained
  gap), 0 = significant (e.g. pattern of very short tenures, major
  unexplained gap, JD/resume domain mismatch).

### Scoring ensemble

Each candidate is scored `pipeline.score_ensemble_n` times (default **3**).
The `overall_fit` label is **majority-voted** across the runs; the median
criteria-total breaks ties inside the winning label group. This stabilizes
run-to-run LLM variance (mitigates the case-13 instability seen at n=1).

### Grounding the evidence

The scoring call receives **candidate profile + JD + the raw resume text** so
(a) evidence strings are grounded in specific resume details and (b) any
embedded prompt-injection text is visible to the scorer as untrusted content
(case 13). This deviates from a literal "[3] profile + JD" reading of AGENTS.md
§7 and is required by the grounded-evidence rule (§8) and case 13 (§11).

## Auto-flag for human review (`src/validate.py:94`)

Flag when **ANY** of:

1. `confidence` is "Low".
2. total score is within 1 point of a band boundary — totals **4, 5, 7, 8**.
3. any single criterion scores 0 while `overall_fit` is "Strong Fit"
   (contradiction — always flagged, never silently resolved).
4. a validation retry already failed once.

`flag_reason` is populated with a semicolon-joined list of matching reasons.

## Validation & retry

`src/validate.py` checks, in order: criterion order (exactly 5, in rubric
order), score range (0–2 integers), evidence quality (non-empty +
non-generic), and fit-band consistency (`overall_fit` matches the total band).
Any failure raises `RuntimeError`; the pipeline (`src/pipeline.py`) retries
the failed normalize/score call once per AGENTS.md §7, and if it still fails,
the candidate is surfaced with `flag_for_human_review` set and the reason in
`flag_reason` — never silently dropped.

## Model & provider choices

### Why OpenAI `gpt-5.6-luna`

- Structured-output JSON in strict mode (`response_format` json_schema) —
  never regex-parsed free text.
- A lightweight reasoning model that rejects the `temperature` parameter
  server-side, so calls omit it entirely; the nullable `flag_reason` field
  uses a `["string", "null"]` type union (OpenAI rejects `oneOf`).
- History (see AGENTS.md §16): the system previously ran on Groq
  `openai/gpt-oss-120b` with a Groq→hosted-Ollama auto-failover. All
  Groq/Ollama provider code was removed 2026-09-13; the system is now
  OpenAI-only.

All LLM calls share one cached OpenAI client and log latency + token usage to
`data/results/call_metrics.log` (`log_metrics()` in `src/config.py`).

### Deterministic extraction

`src/extract.py` handles PDF/DOCX/TXT only (text-extractable). No OCR, no
scanned-image support — a documented non-goal (AGENTS.md §3, §6).

## Interfaces

- **CLI batch pipeline** (`src/pipeline.py`) — the primary entry point used
  by the evaluation suite; prints a ranked table and writes full JSON.
- **Streamlit web app** (`app.py`) — recruiter-facing wrapper over the same
  `pipeline.process_candidate()`; loads the same client from `src/config.py`.

## Data & test splitting

Two-tier test data, not one pool:

- **Dev/calibration set** — 13 generated cases designed to hit specific
  rubric categories, gold-labeled by the developer as proxy reviewer. The
  system is allowed to be tuned against this set.
- **Held-out set** — 4 generated on Day 4 *after* the pipeline was built and
  hardened, not designed to hit specific categories. Closest thing to a
  genuine blind test. Results reported as-is, even if worse than the dev set.

Full results: **EVALUATION.md**.

## Configuration

`src/config.py` loads secrets from `.env` and model settings from
`config.yaml` (falling back to `config.example.yaml`). It exposes
`get_model()`, `get_active_model()`, the cached OpenAI client
(`get_client()`), ensemble count, retries, pacing, and the metrics path as
getters, keeping normalize/score/pipeline modules provider-agnostic.

## Reproducibility caveat

Scoring is LLM-based; run-to-run variance exists (measured: identical
configs scored a single candidate 2, 5, 6, 7 — the motivation for the n=3
majority ensemble). This is a documented known, not a silent failure.