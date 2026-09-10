# AGENTS.md — Resume Screening System

## 1. Project Overview

A system that takes a job description and a batch of resumes, and produces a
ranked, evidence-backed fit assessment for each candidate — fast enough to
replace a 6-8 second manual glance, rigorous enough to replace a 20-30 minute
deep read.

This file is the single source of truth for scope, schemas, and rules.
Before implementing anything, re-read the relevant section below. Do not
introduce new fields, new stages, or new dependencies without updating this
file first and flagging the change in the session summary.

## 2. Target User & Job-to-be-Done

**User:** A recruiter or hiring manager at a small-to-mid-size company
without a sophisticated ATS, handling multiple open reqs at once.

**JTBD:** "When a batch of applications comes in, I need to quickly identify
who's worth an interview, with reasoning I can defend to the hiring manager —
without reading every resume in full."

## 3. Non-Goals (do not build these, even if it seems easy)

- No OCR / scanned-image resume support (text-extractable PDF/docx only)
- No candidate sourcing or outreach
- No auto-reject — the system recommends, a human decides
- No ATS integration
- No bias/fairness certification (note as a limitation in docs, not a v1 feature)
- No multi-language support

## 4. Baseline (what this system must beat)

1. **Naive keyword-match baseline** — simple overlap score between resume
   text and JD text. This simulates a bad ATS.
2. **Naive-LLM baseline** — a single unstructured prompt ("should I interview
   this person?") with no rubric, no schema, no evidence requirement.

Success = higher agreement with gold-labeled test cases than both baselines,
AND every score has non-fabricated, resume-grounded evidence.

## 5. Manual Workflow Being Replaced (reference only, not in scope to automate)

Trigger (applications arrive) → resume + JD as input → recruiter judges
skills/experience/title/trajectory/red flags → shortlist → hiring manager
reviews → interview list. Exceptions: ambiguous titles, career changes,
employment gaps, missing info.

## 6. Data & Assumptions

- Resumes and JDs are fully synthetic (generated, not sourced from a public
  dataset). **This is a documented trade-off, not an oversight** — the case
  study must state explicitly that both the problem and the data are
  stand-ins for a real employer's applicant pool, chosen for time/access
  reasons within the 5-day scope.
- Gold labels (Strong Fit / Possible Fit / Not a Fit) are assigned by the
  developer acting as proxy reviewer, documented as an assumption.
- **Two-tier test data, not one pool:**
  - **Dev/calibration set** (Section 11) — generated Day 1-2, designed to
    hit specific rubric categories. Used throughout the build. The system
    is allowed to be tuned against this set.
  - **Held-out set** (Section 11) — generated fresh on Day 4, *after* the
    pipeline is built and hardened against the dev set. Not designed to hit
    specific categories — just plausible resumes from the same synthetic
    generator. This is the closest thing this project has to a genuine
    blind test, and its results must be reported honestly even if worse
    than the dev set's.

## 7. Architecture

```
JD text + resume file(s)
  → [1] Extraction: PDF/docx → plain text        (deterministic code, NOT an LLM call)
  → [2] Normalization: plain text → structured candidate profile (LLM call, structured output)
  → [3] Scoring: profile + JD → rubric-based JSON  (LLM call, structured output, forced schema)
  → [4] Validation: schema check, non-empty evidence, score range check
  → [5] Output: ranked table + flagged-for-review list
```

**Hard rule:** Stage [1] must be deterministic code (`pdfplumber` / `python-docx`
or equivalent) — never an LLM call. Stages [2] and [3] must use structured/
forced-JSON output, never free-text parsing. Stage [4] must reject and retry
(once) on any validation failure before flagging for human review.

## 8. Schemas

**Normalized candidate profile (intermediate):**
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

**Final output (per candidate) — do not deviate from this shape:**
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

`score` is an integer 0-2 for every criterion. `evidence` must be a
non-empty string grounded in the actual resume text — never fabricated. A
missing or generic evidence string (e.g., "resume shows relevant experience")
is a validation failure, not a pass.

## 9. Scoring Rubric

- Sum of criteria_scores → total (0-10)
- 8-10 → Strong Fit
- 5-7 → Possible Fit
- 0-4 → Not a Fit
- "Red flags" criterion: 2 = none found, 1 = minor (e.g., short unexplained
  gap), 0 = significant (e.g., pattern of very short tenures, major
  unexplained gap, JD/resume domain mismatch)

## 10. Auto-Flag for Human Review — flag when ANY of:

- `confidence` is "Low"
- total score is within 1 point of a band boundary (4-5 or 7-8)
- any single criterion scores 0 while `overall_fit` is "Strong Fit"
  (contradiction — always flag, never silently resolve)
- validation retry failed once already

## 11. Test Cases

### Dev/Calibration Set (13 cases — gold labels filled in before Day 3, used throughout the build)

1. Strong fit — full skills + title match
2. Strong fit — career changer, transferable skills, non-obvious title
3. Borderline — meets ~70% of requirements, missing one key skill
4. Borderline — overqualified for the level of the role
5. Not a fit — wrong domain entirely
6. Edge — unexplained 1-2 year employment gap
7. Edge — vague/unquantified claims, no metrics
8. Edge — very sparse, short resume
9. Edge — very long resume (10+ pages), requires synthesis
10. Failure case — garbled/corrupted extracted text
11. Failure case — unconventional resume format (functional vs. chronological)
12. Adversarial — keyword-stuffed resume with weak real substance
13. Adversarial — resume containing text designed to instruct the model
    directly (e.g., an embedded line telling the reader/model to rate this
    candidate highly). Expected behavior: the injected instruction is
    ignored and scoring proceeds normally based on actual qualifications —
    this is a distinct failure mode from keyword-stuffing and should be
    tested and documented separately in Day 4.

### Held-Out Set (3-5 cases — do not generate or view until Day 4)

Generated fresh on Day 4, after the dev set has already shaped the build.
Plausible synthetic resumes from the same generator, *not* deliberately
constructed to hit a specific rubric category. Purpose: check whether the
pipeline generalizes or has overfit to the dev set's designed patterns.
Results go in `data/results/day4_held_out.json` and must be reported as-is,
including if they're worse than the dev set's.

## 12. Coding Conventions

- Language: Python
- LLM provider: Groq API, model `openai/gpt-oss-120b`, structured output via
  `response_format` JSON schema (strict mode) — never regex-parse free text
- Schema validation: Pydantic v2 models mirroring Section 8 exactly
- Interface: Streamlit
- Config and secrets (API keys, model names) live in a `.env` / config file,
  never hardcoded, never committed
- No silent failures — every caught exception logs a clear, actionable
  message including which candidate_id / file caused it
- Keep extraction, normalization, scoring, and validation as separate
  functions/modules, independently testable
- Every `normalize.py` and `score.py` call logs latency (seconds) and token
  usage to `data/results/call_metrics.log` — needed for Day 4's cost/latency
  metrics, so start logging from Phase 4, not retroactively
- `data/results/*.json` snapshots (baseline, after, held-out, final) are
  build deliverables, not scratch output — do not add `data/results/` to
  `.gitignore`

## 13. Proposed Directory Structure

```
/scripts
  generate_synthetic_data.py   # Phase 1: dev set resumes/JDs; reused Day 4 for held-out set
/src
  extract.py         # deterministic text extraction
  normalize.py        # LLM call: text -> candidate profile
  score.py             # LLM call: profile + JD -> rubric JSON
  validate.py          # schema + evidence checks
  pipeline.py          # orchestrates the above
/tests
  test_cases.json      # the 13 dev cases + gold labels
  test_pipeline.py     # runs test_cases through pipeline, reports pass/fail
/data
  sample_resumes/       # dev/calibration set (13 cases)
  sample_jds/
  held_out_resumes/     # generated Day 4 only — see Section 6 & 11
  results/               # checkpoint snapshots — see Section 14, never overwrite; commit to git, see Section 12
config.example.yaml
README.md              # for the end user (recruiter)
RUNBOOK.md              # for whoever operates/maintains the system
AGENTS.md               # this file
```

## 14. Build & Test Checkpoints (mandatory — do not skip)

Do not move on to the next stage until the current checkpoint passes. Do not
build multiple stages back-to-back without testing between them, even if
instructed to complete "the whole pipeline" in one pass — stop at each
checkpoint and report results before continuing.

- **Checkpoint A — after `extract.py` exists:** Run extraction on every file
  in `/data/sample_resumes/`. Confirm zero exceptions and zero empty
  outputs. Print raw extracted text for at least 3 files for manual
  inspection before proceeding.

- **Checkpoint B — after `normalize.py` exists:** Run normalization on the
  same 3-5 sample resumes. Validate output against the candidate profile
  schema (Section 8). Explicitly check for hallucinated fields — any skill,
  title, or date not traceable to the source text is a failure, not a pass.

- **Checkpoint C — after `score.py` exists, before `validate.py`:** Run
  scoring on at least 3 cases from Section 11. Manually read every evidence
  string against the source resume — do not accept an LLM's self-report that
  its evidence is accurate.

- **Checkpoint D — Day 3, full pipeline assembled:** Run the complete
  13-case dev suite (`tests/test_pipeline.py`). Save output to
  `data/results/day3_baseline.json`. This file is the "before" snapshot
  required for Day 4's regression comparison — never overwrite it.

- **Checkpoint D2 — Day 3, proxy-user execution:** Have someone other than
  the developer run the Streamlit app cold, with no explanation given
  beforehand. Record where they got confused, what they clicked
  incorrectly, and any output they misread. This feedback feeds Day 4's
  hardening and must be captured before Day 4 starts, not reconstructed
  afterward.

- **Checkpoint E — Day 4, after hardening/fixes:** Three parts, in order:
  1. Generate the held-out set (Section 11) fresh — do not reuse or peek at
     dev-set generation logic beyond the shared script.
  2. Re-run the 13-case dev suite. Save to `data/results/day4_after.json`.
     Diff against `day3_baseline.json` and write a short summary of what
     changed, what broke, and why — this is the before-and-after
     regression evidence the sprint requires.
  3. Run the held-out set once, for the first time. Save to
     `data/results/day4_held_out.json`. Report results honestly, including
     if performance drops relative to the dev set — this gap (if any) is
     itself a valid, useful finding for the case study.

- **Checkpoint F — Day 5, before recording the demo:** Run both the dev and
  held-out suites one final time, save to `data/results/final.json`, and
  confirm no regression was introduced while packaging/writing docs.

**If any checkpoint fails:** stop, fix the failing stage, and re-run that
checkpoint before proceeding. Do not accumulate untested stages on the
assumption that a later end-to-end test will catch everything.

## 15. Commands

- Run full pipeline on a batch: `python src/pipeline.py --jd path/to/jd.txt --resumes ./data/sample_resumes/`
- Run the evaluation suite: `python tests/test_pipeline.py`

## 16. Open Decisions Log (append here during the build — feeds the AI Collaboration Note)

- [ ] Interface choice: CLI vs. Streamlit — decision + rationale:
- [ ] Model used for normalization/scoring calls:
- [ ] Any deviations from this spec and why:
- [ ] Checkpoint results log — date/time each checkpoint (A-F) passed, and
      anything caught/fixed at that stage:
- [ ] Proxy-user feedback (Checkpoint D2) — what they got confused by, what
      changed in response:
- [ ] Held-out set results (Checkpoint E) — how they compared to the dev
      set, and what that gap (or lack of one) suggests: