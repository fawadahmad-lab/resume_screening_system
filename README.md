# Resume Screening System

A tool that takes a job description and a batch of resumes, and returns a
ranked, **evidence-backed** fit assessment for every candidate — which ones
are worth an interview, and why, without reading every resume cover to cover.

## What it does

1. Extracts plain text from each resume (PDF / DOCX / TXT).
2. Builds a structured candidate profile (skills, titles, dates, education).
3. Scores each candidate against the job description on a 0–10 rubric:
   - Required skills match
   - Years of relevant experience
   - Title / seniority alignment
   - Career trajectory coherence
   - Red flags
4. Produces a ranking: **Strong Fit** (8–10), **Possible Fit** (5–7),
   **Not a Fit** (0–4).
5. **Flags** any candidate whose result needs a human decision (low
   confidence, near a score boundary, or contradictory scores). The system
   recommends — a human always decides.

Every score is backed by a quoted, non-generic evidence string taken from
the candidate's actual resume. The system never auto-rejects anyone.

## How to use it (recruiter)

Start the app:

```bash
streamlit run app.py
```

Your browser opens the app. Then:

1. **Paste the job description** (or upload a `.txt`/`.pdf` file).
2. **Upload resumes** — select as many PDF/DOCX/TXT files as you like.
3. Click **Run screening**.
4. Read the **Ranking** table, open any candidate for their evidence-backed
   breakdown, and pay attention to anything under **flagged for human
   review** — those need a human's eyes before deciding.

That's it. No settings, no APIs, no command line required.

## Notes & limitations

- Text-extractable PDF/DOCX only. Scanned/image resumes are not supported.
- English only. Resumes in other languages won't be assessed reliably.
- This is a screening aid, not a hiring decision. A human reviews every
  flagged case.

## For developers / operators

See [`RUNBOOK.md`](RUNBOOK.md) for setup, configuration, and running the
evaluation suite.