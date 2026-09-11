import { Link } from "react-router-dom";
import type { ScreeningRun } from "../../types";
import { totalScore } from "../../utils/score";
import { FitBadge } from "../ui/FitBadge";

export function CandidatesTable({ run }: { run: ScreeningRun }) {
  const outcomes = run.ordered;
  if (outcomes.length === 0) {
    return (
      <p className="muted" style={{ padding: "var(--sp-4)" }}>
        No candidates were assessed in the latest run.
      </p>
    );
  }

  return (
    <div style={{ overflowX: "auto" }}>
      <table className="data-table">
        <thead>
          <tr>
            <th>Candidate</th>
            <th>Fit</th>
            <th>Confidence</th>
            <th>Total</th>
            <th>Review</th>
          </tr>
        </thead>
        <tbody>
          {outcomes.map((o) => (
            <tr key={o.candidate_id}>
              <td>
                <Link
                  to={`/candidates/${o.candidate_id}?run=${encodeURIComponent(run.id)}`}
                >
                  <strong>{o.profile.name}</strong>
                </Link>
                <div className="mono faint">{o.input_file}</div>
              </td>
              <td>
                <FitBadge level={o.result.overall_fit} />
              </td>
              <td>{o.result.confidence}</td>
              <td className="mono">{totalScore(o)}/10</td>
              <td>
                {o.result.flag_for_human_review ? (
                  <span className="badge badge--flag__danger">Flagged</span>
                ) : (
                  <span className="faint">—</span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}