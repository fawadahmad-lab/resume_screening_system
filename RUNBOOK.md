# RUNBOOK — Resume Screening System

For whoever operates or maintains the system.

## Setup (one-time)

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edit .env — add your GROQ_API_KEY
```

Model and runtime settings live in `config.example.yaml` (copied to
`config.yaml` if you want to override the defaults):

```yaml
llm:
  model: openai/gpt-oss-20b
  temperature: 0.0
  max_retries: 2
  timeout: 60
  call_interval_s: 40
```

## Running

### Web app (recruiter-facing)

```bash
streamlit run app.py
```

### CLI batch pipeline

```bash
python src/pipeline.py --jd data/sample_jds/jd_frontend.txt --resumes ./data/sample_resumes/ --output data/results/latest.json
```

The CLI prints the ranked table and writes full JSON (profiles + raw text +
results) to the output path.

### Evaluation suite (dev set)

```bash
python tests/test_pipeline.py --output data/results/latest_test.json
```

## Configuration reference

| Setting | Where | Purpose |
|---|---|---|
| `GROQ_API_KEY` | `.env` | LLM provider key (never committed) |
| `llm.model` | config | Groq model used for normalize + score |
| `llm.temperature` | config | Sampling temperature (keep low for structured tasks) |
| `llm.max_retries` | config | LLM-level retries on a failing call |
| `llm.call_interval_s` | config | Fixed seconds waited before each LLM call (free-tier TPM pacing) |
| `logging.metrics_file` | config | Where latency/token usage is appended |

## Modules

- `src/extract.py` — deterministic text extraction (PDF/docx/txt). Never an
  LLM call.
- `src/normalize.py` — LLM: resume text → candidate profile (structured
  output, strict schema).
- `src/score.py` — LLM: profile + JD + raw resume → rubric JSON (structured
  output, strict schema).
- `src/validate.py` — schema, evidence-quality, score-range and fit-band
  checks plus auto-flag rules.
- `src/pipeline.py` — orchestrates extract → normalize → score → validate;
  retries once on validation failure, then flags for human review.
- `app.py` — Streamlit UI.
- `tests/test_pipeline.py` — dev-set evaluation suite.

## Known limitations

- No OCR / scanned resumes (text-extractable files only).
- English only.
- Bias/fairness not certified — review flags carefully for skew.
- Both the problem and the data are synthetic stand-ins for a real
  employer's applicant pool (5-day sprint scope trade-off).

## Troubleshooting

- **`GROQ_API_KEY not set`** at startup — create `.env` from
  `.env.example` with your key.
- **Rate limits / 429s** — Groq retries automatically; large batches slow
  down naturally. Run big batches via the CLI, not the UI.
- **A candidate has no row in the ranking** — check the "Failures" section
  in the UI / `failures` list in the JSON snapshot for the specific error,
  which includes the candidate id/file that caused it.
- **Evidence looks generic** — validation rejects these and retries once
  before flagging for human review; flag reasons are recorded in the result.

## Data & results

- `data/sample_resumes/` — dev/calibration resumes (13 cases).
- `data/sample_jds/` — job descriptions.
- `data/held_out_resumes/` — Day-4 generated held-out set (blind test).
- `data/results/` — checkpoints and snapshots. **Commit these** — they are
  build deliverables, not scratch output. Never overwrite
  `day3_baseline.json`.
- `data/results/call_metrics.log` — per-call latency and token usage for
  cost/latency analysis.