# RUNBOOK — Resume Screening System

For whoever operates or maintains the system. End users (recruiters) should
read [`README.md`](README.md) instead.

## Setup (one-time)

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# edit .env — add OPENAI_API_KEY (LLM provider is OpenAI).
```

Optional: copy `config.example.yaml` to `config.yaml` to override settings.
`config.yaml` is a local override — it is gitignored and never committed.

## Configuration reference

Secrets live in `.env` (never committed). Model and runtime settings live in
`config.yaml` (falls back to `config.example.yaml` if absent).

### `.env`

| Variable | Required? | Purpose |
|---|---|---|
| `OPENAI_API_KEY` | yes | OpenAI API key (api.openai.com) |

### `config.yaml` (`llm:`)

| Setting | Default | Purpose |
|---|---|---|
| `model` | `gpt-5.6-luna` | OpenAI model for normalize + score |
| `max_retries` | `2` | LLM-level retries on a failing call |
| `call_interval_s` | `0.0` | Fixed seconds waited before each first LLM attempt (rate-limit pacing) |

### `config.yaml` (`pipeline:`)

| Setting | Default | Purpose |
|---|---|---|
| `score_ensemble_n` | `3` | Number of scoring runs per candidate; `overall_fit` is majority-voted and the median total breaks ties |

### `config.yaml` (`logging:`)

| Setting | Default | Purpose |
|---|---|---|
| `metrics_file` | `data/results/call_metrics.log` | Where per-call latency/tokens are appended |

## Running

### Web app (recruiter-facing)

```bash
streamlit run app.py
```

Calls the pipeline in-process (no HTTP).

### CLI batch pipeline

```bash
python -m src.pipeline --jd data/sample_jds/jd_frontend.txt --resumes ./data/sample_resumes/ --output data/results/latest.json
```

The CLI prints the ranked table and writes full JSON (profiles + raw text +
results) to the output path.

### Evaluation suite (dev set)

```bash
python EvaluationPackage/tests/test_pipeline.py --output data/results/latest_test.json
```

## Modules

- `src/extract.py` — deterministic text extraction (PDF/docx/txt). Never an
  LLM call.
- `src/normalize.py` — LLM: resume text → candidate profile (structured
  output, strict schema).
- `src/score.py` — LLM: profile + JD + raw resume → rubric JSON (structured
  output, strict schema), ensembled `score_ensemble_n` times.
- `src/validate.py` — schema, evidence-quality, score-range and fit-band
  checks plus auto-flag rules.
- `src/pipeline.py` — orchestrates extract → normalize → score → validate;
  retries once on validation failure, then flags for human review.
- `src/config.py` — config loading, shared OpenAI client, metrics logging.
- `app.py` — Streamlit UI.
- `scripts/generate_synthetic_data.py` — dev-set resume/JD generator.
- `scripts/generate_held_out_data.py` — Day-4 held-out set generator.
- `scripts/run_held_out.py` — held-out evaluation runner.
- `scripts/diff_day34.py` — diff two result snapshots (baseline vs after).
- `EvaluationPackage/tests/test_pipeline.py` — dev-set evaluation suite.

## Known limitations

- No OCR / scanned resumes (text-extractable files only).
- English only.
- Bias/fairness not certified — review flags carefully for skew.
- Both the problem and the data are synthetic stand-ins for a real
  employer's applicant pool (5-day sprint scope trade-off). Gold labels are
  developer-as-proxy-reviewer assignments.
- Reproducibility: scoring is LLM-based and run-to-run variance exists
  (mitigated by the ensemble).

## Troubleshooting

- **`OPENAI_API_KEY not set`** at startup — create `.env` from `.env.example`
  with your key.
- **Rate limits / 429s** — OpenAI applies per-tier RPM/TPM limits. The
  `call_interval_s` setting paces the first attempts of a batch. Run big
  batches via the CLI, not the UI; expect large batches to take minutes at
  paced cadence.
- **A candidate has no row in the ranking** — check the "Failures" section
  in the UI / `failures` list in the JSON snapshot for the specific error,
  which includes the candidate id/file that caused it.
- **Evidence looks generic** — validation rejects these, retries once, then
  flags for human review; flag reasons are recorded in the result. Note a
  generic phrase is only rejected when the evidence has no digits (dates/
  numbers); grounded evidence that mentions a date/number passes even if it
  echoes the rubric criterion name.
- **Evidence strings contain quotes/backslashes** — the scoring rubric
  forbids literal quote/backslash characters in evidence (paraphrase-only).
  See EVALUATION.md — this was a hardening decision after a 20b-model
  regression.