import { useQuery } from "@tanstack/react-query";
import { Info } from "lucide-react";
import { getEvals } from "../api/evals";
import { Card } from "../components/ui/Card";
import { ErrorState, Spinner } from "../components/ui/States";

const MATCH_BADGE = (match: boolean | null, actual: string | null) => {
  if (actual === null || match === null) {
    return <span className="badge badge--flag">not run</span>;
  }
  return match ? (
    <span className="badge badge--strong">PASS</span>
  ) : (
    <span className="badge badge--not-fit">MISMATCH</span>
  );
};

export function EvaluationsPage() {
  const evals = useQuery({ queryKey: ["evals"], queryFn: getEvals });

  if (evals.isLoading) return <Spinner label="Loading evaluations…" />;
  if (evals.isError) {
    return <ErrorState message={evals.error.message} onRetry={() => evals.refetch()} />;
  }
  const data = evals.data;
  if (!data) {
    return <ErrorState message="No evaluation data available." />;
  }
  const { baseline, after, cases } = data;
  const matched = cases.filter((c) => c.baseline_match).length;

  return (
    <div className="stack">
      <div>
        <h1 className="page-title">Dev-Set Evaluations</h1>
        <p className="page-subtitle">
          Committed build snapshots of the 13-case dev suite — read-only, not
          live production data.
        </p>
      </div>

      <div className="alert-banner alert-banner--info" role="note">
        <Info size={18} aria-hidden="true" style={{ marginTop: 2, flexShrink: 0 }} />
        <p style={{ fontSize: "var(--fs-sm)" }}>
          These rows come directly from <span className="mono">data/results/day3_baseline.json</span>{" "}
          (before hardening) and <span className="mono">data/results/day4_narrowed_rule.json</span>{" "}
          (after). Agreement is {matched}/{cases.length} (Day&nbsp;3) vs{" "}
          {cases.filter((c) => c.after_match).length}/{cases.length} (Day&nbsp;4).
        </p>
      </div>

      <Card
        title="Case-by-case agreement"
        actions={
          <div className="row" style={{ gap: "var(--sp-2)", fontSize: "var(--fs-sm)" }}>
            <span className="badge badge--flag">
              gold: {cases.filter((c) => c.expected.includes("Strong")).length} Strong
            </span>
            <span className="badge badge--flag">
              after: {after.summary?.accuracy !== undefined ? `${Math.round((after.summary.accuracy as number) * 100)}%` : "—"}
            </span>
          </div>
        }
      >
        <div style={{ overflowX: "auto" }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Case</th>
                <th>Gold</th>
                <th>Day 3 (baseline)</th>
                <th>Day 4 (after)</th>
              </tr>
            </thead>
            <tbody>
              {cases.map((c) => (
                <tr key={c.name}>
                  <td className="mono faint">{c.case}</td>
                  <td>
                    <span className="mono">{c.name}</span>
                  </td>
                  <td>
                    <FitBadge label={c.expected} />
                  </td>
                  <td>
                    <div className="row" style={{ flexWrap: "nowrap" }}>
                      {MATCH_BADGE(c.baseline_match, c.baseline_actual)}
                      <span className="mono" style={{ fontSize: "var(--fs-xs)" }}>
                        {c.baseline_actual ?? "—"}
                        {c.baseline_total !== null && c.baseline_total !== undefined
                          ? ` (${c.baseline_total})`
                          : ""}
                      </span>
                    </div>
                  </td>
                  <td>
                    <div className="row" style={{ flexWrap: "nowrap" }}>
                      {MATCH_BADGE(c.after_match, c.after_actual)}
                      <span className="mono" style={{ fontSize: "var(--fs-xs)" }}>
                        {c.after_actual ?? "—"}
                        {c.after_total !== null && c.after_total !== undefined
                          ? ` (${c.after_total})`
                          : ""}
                      </span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      <div className="row">
        <Card title="Day 3 snapshot">
          <dl className="stack stack--sm">
            <div className="row" style={{ justifyContent: "space-between" }}>
              <dt className="muted">File</dt>
              <dd className="mono">{baseline.file}</dd>
            </div>
            <div className="row" style={{ justifyContent: "space-between" }}>
              <dt className="muted">Agreement</dt>
              <dd>
                {(baseline.summary?.accuracy as number | undefined) !== undefined
                  ? `${Math.round(((baseline.summary?.accuracy as number) ?? 0) * 100)}%`
                  : "—"}
              </dd>
            </div>
            <div className="row" style={{ justifyContent: "space-between" }}>
              <dt className="muted">Matched</dt>
              <dd className="mono">{baseline.summary?.matched ?? "—"}</dd>
            </div>
          </dl>
        </Card>
        <Card title="Day 4 snapshot">
          <dl className="stack stack--sm">
            <div className="row" style={{ justifyContent: "space-between" }}>
              <dt className="muted">File</dt>
              <dd className="mono">{after.file ?? "not generated"}</dd>
            </div>
            <div className="row" style={{ justifyContent: "space-between" }}>
              <dt className="muted">Agreement</dt>
              <dd>
                {after.file && (after.summary?.accuracy as number | undefined) !== undefined
                  ? `${Math.round(((after.summary?.accuracy as number) ?? 0) * 100)}%`
                  : "—"}
              </dd>
            </div>
            <div className="row" style={{ justifyContent: "space-between" }}>
              <dt className="muted">Matched</dt>
              <dd className="mono">{after.summary?.matched ?? "—"}</dd>
            </div>
          </dl>
        </Card>
      </div>
    </div>
  );
}

function FitBadge({ label }: { label: string }) {
  const variant =
    label === "Strong Fit"
      ? "badge--strong"
      : label === "Possible Fit"
        ? "badge--possible"
        : "badge--not-fit";
  return <span className={`badge ${variant}`}>{label}</span>;
}