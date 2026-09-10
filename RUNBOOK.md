# RUNBOOK — Resume Screening System

For whoever operates or maintains the system. End users (recruiters) should
read [`README.md`](README.md) instead.

## Setup (one-time)

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# edit .env — add GROQ_API_KEY (required), and OLLAMA_API_KEY if you plan to
# use provider: ollama, or rely on the auto-failover (see below).
```

Optional: copy `config.example.yaml` to `config.yaml` to override settings.
`config.yaml` is a local override — it is gitignored and never committed.

## Configuration reference

Secrets live in `.env` (never committed). Model and runtime settings live in
`config.yaml` (falls back to `config.example.yaml` if absent).

### `.env`

| Variable | Required? | Purpose |
|---|---|---|
| `GROQ_API_KEY` | yes | Groq API key (primary provider) |
| `OLLAMA_API_KEY` | only for `ollama` provider | Hosted Ollama (https://ollama.com) API key |

### `config.yaml` (`llm:`)

| Setting | Default | Purpose |
|---|---|---|
| `provider` | `groq` | `groq` = always Groq (raise if TPD exhausted); `auto` = Groq first, fail over to Ollama permanently on daily-token exhaustion; `ollama` = always Ollama |
| `model` | `openai/gpt-oss-120b` | Groq model for normalize + score |
| `ollama_model` | `gpt-oss:120b` | Ollama model (its namespace differs from Groq's) |
| `ollama_host` | `https://ollama.com` | Hosted Ollama endpoint |
| `temperature` | `0.0` | Sampling temperature (keep low for structured tasks) |
| `max_retries` | `2` | LLM-level retries on a failing call |
| `timeout` | `60` | HTTP timeout in seconds |
| `call_interval_s` | `0.0` | Fixed seconds waited before each first LLM attempt (free-tier TPM pacing) |
| `verbose` | `false` | Extra logging |

### `config.yaml` (`pipeline:`)

| Setting | Default | Purpose |
|---|---|---|
| `score_ensemble_n` | `3` | Number of scoring runs per candidate; `overall_fit` is majority-voted and the median total breaks ties |

### `config.yaml` (`logging:`)

| Setting | Default | Purpose |
|---|---|---|
| `metrics_file` | `data/results/call_metrics.log` | Where per-call latency/tokens are appended |

## Groq → Ollama auto-failover

When `provider: auto`, the system starts every LLM call on Groq. If a call
fails because the **Groq daily-token (TPD) window is exhausted** (free tier is
200k tokens/day), the provider fails over to the hosted Ollama endpoint
**permanently for the remainder of the process**.

Important details:

- **Trigger is TPD only.** Transient per-minute (TPM) 429s — "Please try
  again in Xs" — are ridden out by `rate_limit_sleep()` in
  `src/config.py:97`; they do **not** trigger failover. Only wording that
  means the daily window is used up ("daily", "per day", "TPD", "for the
  day") triggers it. See `_is_tpd_exhaustion()` at `src/config.py:203`.
- **It persists for the session.** `_FALLBACK_TRIGGERED` is module-level and
  caches the decision; a single process will keep using Ollama once it has
  switched. Start a new process to try Groq again.
- **A loud one-time log line** marks the transition
  (`src/config.py:259`): `Groq daily token (TPD) window exhausted ... Failing
  over to Ollama provider for the remainder of this process.`
- **How to tell which backend produced a result:** the `model=` field in
  `data/results/call_metrics.log` — `openai/gpt-oss-120b` means Groq was
  active for that call, `gpt-oss:120b` means Ollama. `get_active_model()`
  (`src/config.py:238`) reports the truly-active model. The architecture
  consequence: a batch can be half Groq, half Ollama, and that is by design.

With `provider: groq`, a TPD exhaustion raises an error (no automatic
fallback). With `provider: ollama`, everything runs on Ollama from the start.

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

### Held-out set (blind test — no gold labels)

```bash
python scripts/run_held_out.py --output data/results/day4_held_out.json
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
- `src/config.py` — config loading, shared client (Groq/Ollama adapters),
  TPD detection, TPM rate-limit sleep, metrics logging.
- `app.py` — Streamlit UI.
- `scripts/generate_synthetic_data.py` — dev-set resume/JD generator.
- `scripts/generate_held_out_data.py` — Day-4 held-out set generator.
- `scripts/run_held_out.py` — held-out evaluation runner.
- `scripts/diff_day34.py` — diff two result snapshots (baseline vs after).
- `tests/test_pipeline.py` — dev-set evaluation suite.

## Known limitations

- No OCR / scanned resumes (text-extractable files only).
- English only.
- Bias/fairness not certified — review flags carefully for skew.
- Both the problem and the data are synthetic stand-ins for a real
  employer's applicant pool (5-day sprint scope trade-off). Gold labels are
  developer-as-proxy-reviewer assignments.
- Reproducibility: scoring is LLM-based and run-to-run variance exists
  (mitigated by the ensemble); under `provider: auto` the active backend can
  change mid-batch.

## Troubleshooting

- **`GROQ_API_KEY not set`** at startup — create `.env` from `.env.example`
  with your key.
- **`OLLAMA_API_KEY not set`** — needed only when `provider: ollama`, or
  when `provider: auto` needs to fail over and no key was provided.
- **Rate limits / 429s (TPM)** — tight 8k tokens/min free-tier window;
  `rate_limit_sleep()` parses Groq's "Please try again in Xs" and waits it
  out between retries. `call_interval_s` paces the first attempts of a batch.
  Run big batches via the CLI, not the UI; expect large batches to take
  minutes-hours at free-tier pacing.
- **Daily-token exhaustion (TPD)** — under `auto`, failover to Ollama
  handles it (see above). Under `groq`, the run fails with the provider
  error.
- **A candidate has no row in the ranking** — check the "Failures" section
  in the UI / `failures` list in the JSON snapshot for the specific error,
  which includes the candidate id/file that caused it.
- **Evidence looks generic** — validation rejects these, retries once, then
  flags for human review; flag reasons are recorded in the result.
- **Evidence strings contain quotes/backslashes** — the scoring rubric
  forbids literal quote/backslash characters in evidence (paraphrase-only).
  See EVALUATION.md — this was a hardening decision after a 20b-model
  regression.

## Data & results

- `data/sample_resumes/` — dev/calibration resumes (13 cases).
- `data/sample_jds/` — job descriptions.
- `data/held_out_resumes/` — Day-4 generated held-out set (blind test).
- `data/results/day3_baseline.json` — the Day-3 "before" snapshot. **Never
  overwrite.** Required for regression comparison.
- `data/results/day4_narrowed_rule.json` — the Day-4 narrowed-rule suite
  run (see EVALUATION.md).
- `data/results/call_metrics.log` — per-call latency and token usage for
  cost/latency analysis.
- `data/results/` — checkpoints and snapshots are **build deliverables, not
  scratch output. Commit them.**