import { Link } from "react-router-dom";
import type { ScreeningRun } from "../../types";

export function LatestScreening({ run }: { run: ScreeningRun }) {
  if (run.status === "queued" || run.status === "processing") {
    return (
      <div className="alert-banner alert-banner--info" role="status">
        <p className="muted">
          A screening is currently running —{" "}
          <Link to="/screening">view live progress</Link>.
        </p>
      </div>
    );
  }

  if (run.status === "failed") {
    return (
      <div className="alert-banner alert-banner--danger" role="alert">
        <p className="muted">
          The latest screening failed:{" "}
          <span className="mono">{run.error ?? "unknown error"}</span>
        </p>
      </div>
    );
  }

  if (run.ordered.length === 0 && run.failures.length === 0) {
    return null;
  }

  return (
    <div className="alert-banner alert-banner--info">
      <div className="stack stack--sm" style={{ flex: 1 }}>
        <div className="spread">
          <span style={{ fontWeight: 600 }}>Your Latest Screening</span>
          <span className="mono faint">{run.jd_name}</span>
        </div>
        <p className="muted" style={{ fontSize: "var(--fs-sm)" }}>
          <strong>{run.ordered.length}</strong> assessed ·{" "}
          <strong>{run.flagged.length}</strong> flagged{" "}
          {run.failures.length > 0 && (
            <>
              · <strong>{run.failures.length}</strong> failed to process
            </>
          )}
        </p>
      </div>
    </div>
  );
}