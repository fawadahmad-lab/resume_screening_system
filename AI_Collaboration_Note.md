# AI Collaboration Note

## 1. What I delegated to the AI

I used an agentic coding tool (OpenCode) for most of the actual
implementation:

- Project scaffolding - directory structure, `src/` modules, `tests/`,
  `scripts/`, the Streamlit app, config loading, `requirements.txt`, and the
  README/RUNBOOK family of docs.
- Deterministic extraction (`src/extract.py`) - PDF/DOCX/TXT text extraction,
  written entirely by the agent, verified at Checkpoint A against zero
  exceptions and zero empty outputs.
- The LLM call modules (`src/normalize.py`, `src/score.py`) - structured
  JSON output against Groq's `openai/gpt-oss-120b`, with Pydantic v2 schema
  validation mirroring the contracts I'd defined upfront.
- Validation and auto-flag logic (`src/validate.py`).
- Pipeline orchestration (`src/pipeline.py`).
- The evaluation harness, diff scripts, and synthetic data generators.
- Debugging the Day 4 failures - tracing the model-specific JSON corruption
  bug, running the variance probe on the prompt-injection test case,
  implementing the narrowed format-handling rule, building the 3-run
  ensemble, and implementing the failover between model providers when
  quota ran out.
- Triaging the quota/rate-limit issues that came up mid-build.

## 2. What I kept for myself

- The scope, schemas, and rubric - every criterion, score band, and flag
  rule this system runs on came from decisions I made before any code was
  written, not from the agent.
- The gold labels for all 13 test cases, and the call to treat mismatches as
  judgment-call edge cases to investigate, not just failures to patch over.
- The demo, this note, and the case study - written by me.
- **The proxy-user test.** I ran this myself in two passes: first testing my
  own resume against a JD (which I recognized afterward wasn't a valid test
  - I already knew what the answer should look like, so I couldn't be
  surprised by it), then a real test with someone else running a batch of
  resumes against one JD, cold, playing the recruiter's role. They
  understood the ranking table and the flagged-candidate logic without any
  explanation from me. That's a real, positive result, not a gap.
- Every "stop and decide" moment below - the agent surfaced options and
  built what I approved, but the calls themselves were mine.

## 3. Key decisions and who actually made them

| Decision | Made by | Result / rationale |
|---|---|---|
| Groq `openai/gpt-oss-120b` as primary model | Me | Structured JSON output support, free tier adequate for the sprint's scope. |
| Mid-build switch to a smaller model, then back | Agent, quota-driven | Purely a response to daily quota exhaustion; reverted once the primary model's window refilled. |
| Evidence strings must be paraphrased, not quoted verbatim | Me, on the agent's finding | The smaller model was copying resume text verbatim into evidence, including quote/backslash characters that broke strict JSON output deterministically. I rejected a narrower fix (escaping problem characters after generation) because repairing model output after the fact would mask real model misbehavior rather than catch it. |
| Pass raw resume text into the scoring call, not just the normalized profile | Me | Grounds evidence in specific resume language and, as a side effect, is what let the system correctly recognize a prompt-injection attempt in one of my test cases instead of being fooled by it. |
| Broad rule to stop garbled/unclear text from being penalized as a red flag | Agent, then narrowed by me | The original version also suppressed a legitimate red flag on a different resume - a title/work-history mismatch. Narrowing it fixed two cases that were wrong at baseline; the title-discrepancy check on the other case still doesn't reliably fire. Net improvement, not a full fix, and I'm documenting it as such. |
| 3-run majority-vote ensemble for scoring | Agent proposed, I approved | A single test case swung across three fit bands (scores of 2, 5, 6, 7) on identical inputs due to run-to-run model variance. The ensemble stabilizes the output label - though the stabilized answer still disagrees with my gold label on that case, which I'm treating as an open finding rather than a solved problem (see §6). |
| Automatic failover between model providers on quota exhaustion | Me, after the agent implemented it without flagging the change up front | Free-tier daily limits were genuinely blocking evaluation runs mid-batch; the failover makes the sprint viable on a limited budget. I asked the agent to document this plainly in the architecture and runbook docs, since it means two batches run at different times could come from different backends without an operator noticing unless they check the logs. |
| Career-changer rubric gap (a candidate with strong but non-domain experience scoring too low) | Me | Scoped and understood, but deliberately left unfixed to keep Day 4 stable rather than risk a rushed rubric change late in the build. |
| No fabricated evidence, ever | Me | Every mismatch in the evaluation set was manually checked against source resume text. All were genuine judgment-call disagreements, never invented or ungrounded evidence. |

A pattern worth naming honestly: a few of these changes (the format rule,
the provider failover) were made by the agent mid-session without being
surfaced up front - I found them by asking direct questions when a status
update didn't add up, not because they were proactively flagged. That's
part of why the decision log above exists - every one of these needed me to
stop, understand what actually changed, and decide whether to keep it,
narrow it, or reject it.

## 4. What the AI was not allowed to do

- Extract resume text via an LLM call - extraction is deterministic code,
  no exceptions.
- Parse model output as free text - everything goes through structured,
  schema-validated JSON.
- Add fields, pipeline stages, or dependencies without updating the shared
  spec first.
- Auto-reject a candidate, silently treat an unreviewed flag as a decision,
  or drop a failure without surfacing it.
- Generate or weight gold labels, or touch the held-out test set.
- Overwrite a prior evaluation snapshot.

## 5. Where each piece of this came from

- **Code**: agent-generated, checked by me at multiple points - most
  concretely, every evidence string in the evaluation set was manually
  read against its source resume, not just trusted because the JSON
  validated.
- **Data**: synthetic resumes and job descriptions generated by the agent
  from my specification; content is invented (a documented trade-off, not
  an oversight); gold labels are mine.
- **Evaluation snapshots**: the baseline run and the post-fix run are both
  real, committed results.
- **Failure-investigation runs** (the variance probes, the isolated test
  reruns): logged outside the main results directory, available on request.

