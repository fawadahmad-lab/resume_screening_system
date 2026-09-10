"""Streamlit web UI for the Resume Screening System.

Run with:  streamlit run app.py
Target user: recruiter / hiring manager. No tech knowledge assumed.
"""

import os
import sys
import tempfile

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config import get_client
from src.extract import extract_text
from src.pipeline import process_candidate

st.set_page_config(
    page_title="Resume Screening",
    page_icon="📋",
    layout="wide",
)

FIT_COLORS = {
    "Strong Fit": "#00a36a",
    "Possible Fit": "#f5a623",
    "Not a Fit": "#d9534f",
}
CONF_ICONS = {"High": "🟢", "Medium": "🟡", "Low": "🔴"}

st.title("Resume Screening")
st.caption(
    "Paste a job description, upload resumes (PDF/DOCX/TXT), and get a ranked, "
    "evidence-backed fit assessment for every candidate."
)

@st.cache_resource
def _get_client():
    return get_client()


try:
    client = _get_client()
except RuntimeError as e:
    st.error(str(e))
    st.stop()


# ---------------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------------

st.sidebar.header("1. Job Description")
jd_source = st.sidebar.radio(
    "JD source", ["Paste text", "Upload file"], index=0
)
jd_text = ""
if jd_source == "Paste text":
    jd_text = st.sidebar.text_area(
        "Paste the job description",
        placeholder="Paste the full JD text here…",
        height=280,
    )
else:
    jd_file = st.sidebar.file_uploader(
        "Upload JD (.txt)", type=["txt", "pdf", "md"]
    )
    if jd_file is not None:
        suffix = os.path.splitext(jd_file.name)[1]
        with tempfile.NamedTemporaryFile(mode="wb", suffix=suffix, delete=False) as tmp:
            tmp.write(jd_file.getbuffer())
            tmp_path = tmp.name
        try:
            jd_text = extract_text(tmp_path)
        finally:
            os.unlink(tmp_path)

st.sidebar.markdown("---")
st.sidebar.header("2. Resumes")
resume_files = st.sidebar.file_uploader(
    "Upload resumes (multi-select)",
    type=["txt", "pdf", "docx"],
    accept_multiple_files=True,
)

run_enabled = bool(jd_text.strip()) and bool(resume_files)
run_button = st.sidebar.button(
    "Run screening",
    type="primary",
    disabled=not run_enabled,
    help="Needs a job description and at least one resume",
)

results_holder = st.empty()

if run_button:
    # Save uploads to temp files for deterministic extraction
    staged = []
    for f in resume_files:
        suffix = os.path.splitext(f.name)[1]
        with tempfile.NamedTemporaryFile(mode="wb", suffix=suffix, delete=False) as tmp:
            tmp.write(f.getbuffer())
            staged.append((f.name, tmp.name))

    ordered = []
    flagged = []
    failures = []

    with st.status("Screening candidates…", expanded=True) as status:
        st.write(f"Job description parsed ({len(jd_text)} chars). Processing {len(staged)} resumes.")
        progress = st.progress(0)
        for i, (fname, tmp_path) in enumerate(staged):
            st.write(f"→ {fname}")
            try:
                outcome = process_candidate(
                    file_path=tmp_path, jd_text=jd_text, client=client
                )
                result = outcome["result"]
                if result["flag_for_human_review"]:
                    flagged.append(outcome)
                ordered.append(outcome)
            except Exception as e:
                failures.append({"file": fname, "error": str(e)})
                st.warning(f"Failed: {fname} — {e}")
            finally:
                os.unlink(tmp_path)
                progress.progress((i + 1) / len(staged))
        status.update(label="Screening complete", state="complete")

    if failures:
        st.error(f"{len(failures)} resume(s) could not be processed")
        for fl in failures:
            st.text(f"{fl['file']}: {fl['error']}")

    if not ordered:
        st.warning("Nothing to show — all resumes failed to process.")
    else:
        ordered.sort(
            key=lambda o: sum(c["score"] for c in o["result"]["criteria_scores"]),
            reverse=True,
        )

        # ---- Flagged-for-review banner (auto-flag = human decides) ----
        if flagged:
            st.markdown(
                f"### ⚠️ {len(flagged)} candidate(s) flagged for human review"
            )
            for o in flagged:
                r = o["result"]
                st.error(
                    f"**{o['candidate_id']}** — {r['overall_fit']} · "
                    f"{r['flag_reason']}"
                )

        # ---- Candidate table ----
        rows = []
        for o in ordered:
            r = o["result"]
            total = sum(c["score"] for c in r["criteria_scores"])
            rows.append(
                {
                    "Candidate": o["candidate_id"],
                    "Fit": r["overall_fit"],
                    "Confidence": r["confidence"],
                    "Total": f"{total}/10",
                    "Flagged": "⚠️" if r["flag_for_human_review"] else "",
                    "Name": (o.get("profile") or {}).get("name", ""),
                }
            )

        st.markdown("## Ranking")
        st.dataframe(
            rows,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Fit": st.column_config.TextColumn(),
                "Total": st.column_config.TextColumn(width="small"),
            },
        )

        # ---- Per-candidate drill-down ----
        st.markdown("## Candidate details")
        for o in ordered:
            r = o["result"]
            total = sum(c["score"] for c in r["criteria_scores"])
            color = FIT_COLORS.get(r["overall_fit"], "#333")
            name = (o.get("profile") or {}).get("name", "")
            with st.expander(
                f"{name or o['candidate_id']} — "
                f"{r['overall_fit']} ({total}/10) · {r['confidence']}"
            ):
                st.markdown(
                    f"**Candidate ID:** `{o['candidate_id']}`  \n"
                    f"**Confidence:** {CONF_ICONS.get(r['confidence'], '')} {r['confidence']}  \n"
                    f"**Fit:** <span style='color:{color}'>{r['overall_fit']}</span>  \n"
                    f"**Flag for human review:** "
                    f"{'⚠️ Yes — ' + (r['flag_reason'] or '') if r['flag_for_human_review'] else 'No'}",
                    unsafe_allow_html=True,
                )
                for c in r["criteria_scores"]:
                    st.markdown(
                        f"**{c['criterion']}** — {c['score']}/2\n\n"
                        f"> {c['evidence']}"
                    )