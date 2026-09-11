import { Link, useParams, useSearchParams } from "react-router-dom";
import { useScreeningPolling } from "../hooks/useScreeningPolling";
import { Card } from "../components/ui/Card";
import { FitBadge } from "../components/ui/FitBadge";
import { ScoreBar } from "../components/ui/ScoreBar";
import { ErrorState, Spinner } from "../components/ui/States";
import { totalScore } from "../utils/score";

export function CandidateDetailPage() {
  const { candidateId } = useParams<{ candidateId: string }>();
  const [searchParams] = useSearchParams();
  const runId = searchParams.get("run");

  const run = useScreeningPolling(runId);

  if (
    run.data &&
    run.data.status !== "processing" &&
    run.data.status !== "queued" &&
    !run.data.ordered.some((o) => o.candidate_id === candidateId)
  ) {
    return (
      <ErrorState
        message={`Candidate "${candidateId}" was not found in this screening run.`}
      />
    );
  }
  if (run.isLoading) {
    return <Spinner label="Loading candidate…" />;
  }
  if (run.isError) {
    return <ErrorState message={run.error.message} onRetry={() => run.refetch()} />;
  }
  if (!run.data) {
    return <ErrorState message="No screening run found." />;
  }

  const outcome = run.data.ordered.find((o) => o.candidate_id === candidateId);
  if (!outcome) {
    return (
      <ErrorState message={`Candidate "${candidateId}" was not found in the latest screening.`} />
    );
  }

  const { profile, result, raw_text: rawText, input_file: inputFile } = outcome;
  const total = totalScore(outcome);
  const concerned = result.criteria_scores.filter((c) => c.score === 0);
  const medium = result.criteria_scores.filter((c) => c.score === 1);

  return (
    <div className="stack">
      <div>
        <Link to="/" className="btn btn--ghost" style={{ paddingLeft: 0 }}>
          ← Back to candidates
        </Link>
        <h1 className="page-title" style={{ marginTop: "var(--sp-2)" }}>
          {profile.name}
        </h1>
        <p className="mono faint">{inputFile} · run {run.data.id}</p>
      </div>

      <div className="row">
        <FitBadge level={result.overall_fit} />
        <span className="badge badge--flag">Confidence: {result.confidence}</span>
        <span className="badge badge--flag">Total: {total}/10</span>
        {result.flag_for_human_review && (
          <span className="badge badge--flag__danger">Flagged for review</span>
        )}
      </div>

      {result.flag_for_human_review && result.flag_reason && (
        <div className="alert-banner alert-banner--flag" role="status">
          {result.flag_reason}
        </div>
      )}

      <Card title="Criteria scores">
        <div className="stack stack--sm">
          {result.criteria_scores.map((c) => (
            <div key={c.criterion} className="stack stack--sm">
              <div
                className="row"
                style={{ justifyContent: "space-between" }}
              >
                <span style={{ fontWeight: 600 }}>{c.criterion}</span>
                <ScoreBar score={c.score} />
              </div>
              <p
                className="muted"
                style={{
                  fontSize: "var(--fs-sm)",
                  borderLeft: "3px solid var(--color-border)",
                  paddingLeft: "var(--sp-3)",
                }}
              >
                {c.evidence}
              </p>
            </div>
          ))}
        </div>
      </Card>

      <div className="row">
        {concerned.length > 0 && (
          <Card
            title={`Concerns (${concerned.length})`}
            actions={<span className="badge badge--not-fit">0-scored</span>}
          >
            <ul className="stack stack--sm" style={{ listStyle: "none", margin: 0, padding: 0 }}>
              {concerned.map((c) => (
                <li key={c.criterion}>
                  <strong>{c.criterion}</strong> — {c.evidence}
                </li>
              ))}
            </ul>
          </Card>
        )}
        {medium.length > 0 && (
          <Card title="Partial matches">
            <ul style={{ listStyle: "none", margin: 0, padding: 0 }}>
              {medium.map((c) => (
                <li key={c.criterion} className="muted">
                  {c.criterion}
                </li>
              ))}
            </ul>
          </Card>
        )}
      </div>

      <Card title="Normalized profile">
        <div className="stack stack--sm">
          <div>
            <span className="field__label">Skills</span>
            <div className="row" style={{ marginTop: "var(--sp-1)" }}>
              {profile.skills.map((s) => (
                <span key={s} className="badge badge--flag">
                  {s}
                </span>
              ))}
            </div>
          </div>
          <div>
            <span className="field__label">Titles</span>
            <ul style={{ marginLeft: "var(--sp-4)" }}>
              {profile.titles.map((t) => (
                <li key={t}>{t}</li>
              ))}
            </ul>
          </div>
          <div>
            <span className="field__label">Date ranges</span>
            <ul className="mono" style={{ marginLeft: "var(--sp-4)", listStyle: "none" }}>
              {profile.date_ranges.map((d, i) => (
                <li key={i}>
                  {d.start} → {d.end}
                </li>
              ))}
            </ul>
          </div>
          <div>
            <span className="field__label">Education</span>
            <ul style={{ marginLeft: "var(--sp-4)" }}>
              {profile.education.map((e) => (
                <li key={e}>{e}</li>
              ))}
            </ul>
          </div>
        </div>
      </Card>

      <Card title="Extracted resume text">
        <pre
          className="mono"
          style={{
            whiteSpace: "pre-wrap",
            fontSize: "var(--fs-sm)",
            lineHeight: 1.6,
            background: "var(--color-surface-muted)",
            padding: "var(--sp-4)",
            borderRadius: "var(--radius-md)",
            maxHeight: "420px",
            overflowY: "auto",
          }}
        >
          {rawText}
        </pre>
      </Card>
    </div>
  );
}