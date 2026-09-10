# Resume Screening System

A tool that takes a **job description** and a **batch of resumes**, and returns
a ranked, evidence-backed fit assessment for every candidate — which ones are
worth an interview, and **why**, without reading every resume cover to cover.

It replaces a 6–8 second manual glance, rigorous enough to stand in for a
20–30 minute deep read.

> **This is a screening aid, not a hiring decision.** The system recommends;
> a person always decides. It never rejects anyone by itself.

---

## What it does for you

1. Reads each resume (PDF, DOCX, or TXT) and pulls out the essentials —
   skills, job titles, dates, education.
2. Scores every candidate against the job description on 5 criteria.
3. Ranks them: **Strong Fit**, **Possible Fit**, or **Not a Fit**.
4. **Flags** anything that needs a human's eyes before you decide.

Each score comes with a **short, quoted piece of that candidate's actual
resume** showing *why* it got that mark. No mystery scores, no thumbs-up from
a black box.

## The 5 criteria (each marked 0–2)

| Criterion | What it asks |
|---|---|
| **Required skills match** | Do they actually list the skills the job needs? |
| **Years of relevant experience** | Years in the kind of work this job is about. |
| **Title / seniority alignment** | Is their track-record level right for the role? |
| **Career trajectory coherence** | Does their work history tell a sensible story? |
| **Red flags** | Unexplained gaps, run of very short jobs, or a domain mismatch? |

## The fit bands

| Overall fit | Total score |
|---|---|
| Strong Fit | 8–10 |
| Possible Fit | 5–7 |
| Not a Fit | 0–4 |

## What "flagged for human review" means

Sometimes the system isn't sure, and those cases are **flagged** in the output.
That flag means: *look at this one yourself before deciding.* Examples:

- Low confidence in the result,
- A score sitting right on the edge of a band,
- Scores that seem to contradict each other.

**A flag is not a rejection.** It is exactly the opposite — the tool saying
*"this one deserves your actual judgement."* You always have the final say.

## What you need to prepare

- The **job description** — as text, or a `.txt` / `.pdf` file.
- The **resumes** — PDF, DOCX, or TXT.
- The resumes must be **digital text files** (not scanned images), and in
  **English**.

## How to use it (once your IT has started the app)

1. **Paste the job description** into the box on the left (or upload a file).
2. **Upload the resumes** — select as many files as you like.
3. Click **Run screening.**
4. Read the **Ranking** table, open any candidate to see their evidence-backed
   breakdown, and **pay special attention to anything flagged for human
   review.**

That's it. No settings, no command line, no technical knowledge required.

## What it does NOT do

- **Scanned / image-only resumes** — not supported (text-extractable files only).
- **Other languages** — English only.
- **Bias/fairness certification** — not certified. Review flagged and boundary
  cases carefully.
- **Outreach, sourcing, or scheduling** — screening helps you sort, it won't
  chase candidates.

---

## For developers and operators

Setup, configuration, the Groq→Ollama auto-failover, and troubleshooting live
in **[`RUNBOOK.md`](RUNBOOK.md)**, and the system design in
**[`ARCHITECTURE.md`](ARCHITECTURE.md)**. How it was tested, and what it gets
wrong, is in **[`EVALUATION.md`](EVALUATION.md)**.