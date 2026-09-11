import { Link } from "react-router-dom";
import { Flag } from "lucide-react";
import type { ScreeningRun } from "../../types";
import { totalScore } from "../../utils/score";
import { FitBadge } from "../ui/FitBadge";

export function ScreeningResults({ run }: { run: ScreeningRun }) {
  if (run.ordered.length === 0) {
    return (
      <p className="muted">No candidates were assessed in this run.</p>
    );
  }

  return (
    <div className="stack stack--sm">
      {run.flagged.length > 0 && (
        <div className="alert-banner alert-banner--flag" role="status">
          <Flag size={18} aria-hidden="true" style={{ marginTop: 2, flexShrink: 0 }} />
          <p>
            <strong>{run.flagged.length} candidate{run.flagged.length === 1 ? "" : "s"}</strong>{" "}
            flagged for human review (boundary scores, low confidence, or
            contradictions).
          </p>
        </div>
      )}

      <ul style={{ listStyle: "none", margin: 0, padding: 0 }}>
        {run.ordered.map((o) => (
          <li
            key={o.candidate_id}
            className="row"
            style={{
              justifyContent: "space-between",
              padding: "var(--sp-2) var(--sp-3)",
              borderBottom: "1px solid var(--color-border)",
            }}
          >
            <div>
              <Link
                to={`/candidates/${o.candidate_id}?run=${encodeURIComponent(run.id)}`}
              >
                <strong>{o.profile.name}</strong>
              </Link>
              <div className="mono faint">{o.input_file}</div>
            </div>
            <div className="row">
              <span className="mono">{totalScore(o)}/10</span>
              <FitBadge level={o.result.overall_fit} />
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}