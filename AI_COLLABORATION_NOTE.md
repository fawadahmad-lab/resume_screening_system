# AI Collaboration Note — DRAFT (developer to rewrite in own words)

> **Status: DRAFT INPUT.** This is a point-form log of how the code in this
> repo was produced with AI assistance, for the developer to rewrite as the
> final collaboration note. It is deliberately factual and terse — the
> developer owns the final narrative, and the grading rubric credits their
> explanation of the decisions below, not this file's.

## 1. What was delegated to the AI (OpenCode agent)

- **Greenfield scaffolding:** project structure, `src/` modules, `tests/`,
  `scripts/`, `app.py`, config loading, `requirements.txt`, this README/RUNBOOK
  family of docs.
- **Deterministic extraction** (`src/extract.py`): PDF/DOCX/TXT text
  extraction via pdfplumber/python-docx — written entirely by the AI, then
  verified at Checkpoint A (zero exceptions/empty outputs).
- **LLM call modules** (`src/normalize.py`, `src/score.py`): structured-output
  JSON calls against Groq's `openai/gpt-oss-120b` in strict `response_format`
  mode; Pydantic v2 schema validation mirroring AGENTS.md §8.
- **Validation & auto-flag logic** (`src/validate.py`): pure functions for
  schema/evidence/range/band checks and the Section 10 flag rules.
- **Pipeline orchestration** (`src/pipeline.py`): extract → normalize → score
  → validate, retry-once-then-flag.
- **Evaluation harness** (`tests/test_pipeline.py`, `scripts/diff_day34.py`,
  `scripts/run_held_out.py`, synthetic data generators).
- **Debugging day-4 failures:** the AI traced the 20b-model strict-JSON
  corruption (verbatim quote-span copy), ran the case-13 variance probe (4
  identical runs scoring 2, 5, 6, 7), implemented the narrowed FORMAT RULE 1,
  built the n=3 majority ensemble, and implemented the Groq→Ollama
  auto-failover.
- **Issue triage on quota/429s:** TPM vs TPD distinction; `rate_limit_sleep()`
  rider for per-minute waits, TPD failover for daily exhaustion.

## 2. What was kept human (developer-owned)

- **Scope, schemas, and rules**: AGENTS.md §1–§14 (the developer defined
  every contract this system follows — criteria order, score bands, flag
  rules, two-tier data split).
- **The demo, final case study, and this note**: written by the developer.
- **Gold labels** for the 13 dev cases (proxy reviewer), and the *decision to
  treat them as judgment calls* rather than automatically "right".
- **The proxy-user test (Checkpoint D2)** — not run; recorded as a gap.
- **Held-out set (Checkpoint E)** — not run; the developer chose to hold it
  to preserve a true future blind test and prioritize documentation.
- **Every "explain and decide" moment** (below).

## 3. Key decisions and who made them

| Decision | Made by | Result / rationale |
|---|---|---|
| Groq `openai/gpt-oss-120b` as primary model | Developer | Structured strict-JSON output; free tier adequate for the 5-day sprint. |
| Switch to `openai/gpt-oss-20b` mid-Day-4 | AI (quota-attributed) | Purely TPD-driven; **reverted** to 120b when the window refilled. The 20b detour is documented in AGENTS.md §16 as history. |
| Evidence strings must be **paraphrase-only** (no literal quotes/backslashes) | Developer, on AI's finding | The 20b model copied quote-spans verbatim, corrupting strict-JSON output. Retained post-switch as hardening. |
| Pass **raw resume text** into the scoring call | Developer | Grounds evidence in specific resume text; surfaces prompt-injection attempts to the scorer (case 13). Deliberate deviation from the literal "profile + JD" architecture note. |
| FORMAT RULES for header lines / 'unknown' dates | AI, then **narrowed by developer** | Full version over-suppressed the case-11 red flag; narrowed version (header title = applied-for role only, may still flag discrepancy) fixed cases 6/9/10 — partially resolved, net gain. |
| `score_ensemble_n` = 3, **majority vote** on `overall_fit` | AI proposed, developer approved | Stabilizes run-to-run variance (case-13 probe: 2/5/6/7 across identical runs). Label now stable but gold-disagrees — judgment call, documented. |
| Groq → Ollama **auto-failover** (`provider: auto`) | Developer | Free-tier TPD exhaustion killed runs mid-batch; auto-failover makes the sprint viable. Detected as an undisclosed arch change → documented in ARCHITECTURE/RUNBOOK. |
| Case 2 (career changer) **analysis only, no fix** | Developer | Rubric gap (no transferable-skills credit) scoped but deliberately not changed to keep Day 4 stable. |
| Baseline 7/13 "no manufacture" rule | Developer | All mismatches manually read as judgment-call edge cases, never evidence fabrication. |

## 4. What the AI was *not* allowed to do

- Extract text via any LLM call (deterministic code only — hard rule).
- Free-text/unsafe parsing (structured JSON in strict mode only).
- Add fields/stages/dependencies without AGENTS.md §16 updates first.
- Auto-reject candidates, tag unreviewed flags as decisions, or silently
  drop failures.
- Generate or weight gold labels, held-out results, or final snapshots.
- Overwrite `data/results/day3_baseline.json` or any prior snapshot.

## 5. Provenance of every artifact

- **Code:** AI-generated, verified at checkpoints A–C by the developer
  (evidence strings manually read against source resumes).
- **Data:** `scripts/generate_synthetic_data.py` and
  `scripts/generate_held_out_data.py` — AI-generated, content invented
  (documented synthetic-data trade-off), gold labels developer-assigned.
- **Snapshots:** `data/results/day3_baseline.json` (real run), 
  `data/results/day4_narrowed_rule.json` (real run, n=1, narrowed FORMAT
  RULES). All committed.
- **Failure investigation artifacts** (case-13 reruns, ensemble probes,
  narrowed-suite runs): stored in `/tmp/opencode/` (outside the repo) —
  available on request.

## 6. Remaining work the developer owns

1. Record the 5-minute demo.
2. Write the final case study + this note in their own words.
3. Run Checkpoint E (held-out set) and Checkpoint F (final run) when ready —
   both kept un-run to preserve a genuine blind test.
4. Record Checkpoint D2 (proxy-user) feedback if time allows.