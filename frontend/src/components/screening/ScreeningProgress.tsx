import type { ScreeningRun } from "../../types";

const STATUS_LABEL: Record<string, string> = {
  queued: "Queued",
  processing: "Processing",
  done: "Done",
  failed: "Failed",
};

const STATUS_CLASS: Record<string, string> = {
  queued: "badge badge--flag",
  processing: "badge badge--flag",
  done: "badge badge--strong",
  failed: "badge badge--not-fit",
};

export function ScreeningProgress({ run }: { run: ScreeningRun }) {
  const total = run.progress_total || run.candidates.length;
  const done = Math.min(run.progress_done, total);
  const percent = total > 0 ? Math.round((done / total) * 100) : 0;

  const active = run.candidates.filter(
    (c) => c.status === "queued" || c.status === "processing",
  ).length;

  return (
    <div className="stack stack--sm" role="status" aria-live="polite">
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: "var(--fs-sm)" }}>
        <span>
          <strong>{done}</strong> of <strong>{total}</strong> candidates
          {active > 0 && ` (${active} in progress)`}
        </span>
        <span className="mono">{percent}%</span>
      </div>
      <div
        className="progress-track"
        role="progressbar"
        aria-valuenow={done}
        aria-valuemin={0}
        aria-valuemax={total}
      >
        <div
          className="progress-fill"
          style={{ width: `${Math.max(percent, 3)}%` }}
        />
      </div>
      <ul style={{ listStyle: "none", margin: 0, padding: 0 }}>
        {run.candidates.map((c) => (
          <li
            key={c.candidate_id}
            className="row"
            style={{ justifyContent: "space-between", padding: "var(--sp-1) 0" }}
          >
            <span className="mono">{c.file}</span>
            <span className={STATUS_CLASS[c.status]}>
              {STATUS_LABEL[c.status]}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}