# CASE STUDY — Resume Screening System (OUTLINE / DRAFT)

> **Status: OUTLINE.** This file is the skeleton the developer will expand
> into the final case study. Section headers + bullet-level content are
> provided as input material. The demo video and the adoption/iteration
> projections are **placeholders** — the developer writes those.

## 1. Problem & user

- Recruiter/hiring manager at a small-to-mid-size company without a
  sophisticated ATS, juggling multiple open reqs.
- JTBD: "When a batch of applications comes in, quickly identify who's worth
  an interview, with reasoning I can defend to the hiring manager — without
  reading every resume in full."
- Baseline to beat: (a) naive keyword-match ATS, (b) unstructured
  single-prompt LLM with no rubric/schema/evidence.

## 2. The workflow being replaced

- Applications arrive → resume + JD → human judges skills/experience/title/
  trajectory/red flags → shortlist → hiring manager review → interview list.
- Scope limits: text-extractable PDF/DOCX only, English only, no OCR, no
  auto-reject, no ATS integration, no bias certification.

## 3. Architecture & trade-offs

- 5-stage pipeline: deterministic extract → LLM normalize (structured JSON)
  → LLM score (forced schema) → pure-function validate (retry-once-then-flag)
  → ranked output + flags.
- Trade-off: schemas/agreement over recall; structured evidence over free-text
  prose; a rubric a human can defend vs a black-box score.
- Synthetic data trade-off: stand-ins for a real applicant pool, chosen for
  5-day scope — documented, not an oversight. Gold labels = developer as proxy
  reviewer.

## 4. Delegated vs retained (the AI collaboration)

- Summarize AI_COLLABORATION_NOTE.md §1–§2: AI scaffolded code, ran the 20b
  quota detour, traced failures, implemented narrow fixes; developer kept
  scope, schemas, gold labels, and every judgment call.
- Point to the decisions table (note §3) as the collaboration evidence.

## 5. Failures found & fixed (the compelling part)

- **20b strict-JSON corruption** → paraphrase-only evidence rule.
- **Case-13 prompt injection + bimodal output** → n=3 majority ensemble;
  residual gold-disagreement is a judgment call, documented.
- **FORMAT-rule over-suppression** → narrowed; fixed 6/9/10, partially
  resolved 11 (net gain).
- **Free-tier TPD exhaustion killing runs** → Groq→Ollama auto-failover.
- **TPM vs TPD** → rate-limit sleeper vs permanent failover.

## 6. Results

- 7/13 (53.8%) → 8/13 (61.5%) agreement with gold after hardening, zero
  errors in either run.
- Strongest: wrong-domain (5), adversarial keyword-stuffing (12), prompt
  injection (13) all correct in both runs — the security/domain checks.
- Weakest: career changer (2, unfixed), overqualified (4, no channel), vague
  claims (7) and sparse (8) judgment calls.
- Held-out blind set: preserved un-run (Checkpoint E) so it stays a true
  future test — when run, report as-is including any drop.

## 7. Limitations & honest context

- 53.8% is over judgment-call edge cases, never evidence fabrication (all
  evidence strings manually verified at Checkpoint C).
- No OCR/EN-only/no bias cert; overqualification and career-changer channels
  absent.
- Run-to-run LLM variance mitigated by the ensemble, not eliminated.
- Auto-failover can switch backends mid-batch (attributable per-call in
  `call_metrics.log`).

## 8. Next two weeks (iteration plan — developer drafts)

- [PLACEHOLDER: run Checkpoint E held-out + Checkpoint F final; record the
  demo; ship README/RUNBOOK to a real recruiter and capture Checkpoint D2
  proxy-user feedback.]
- [PLACEHOLDER: adoption projections — likely steps to trust the tool with
  a real applicant pool.]

## 9. Demo script (5 minutes — developer records)

- [PLACEHOLDER: narrated walkthrough of README → app → one batch → one flag
  → one evidence drill-down.]