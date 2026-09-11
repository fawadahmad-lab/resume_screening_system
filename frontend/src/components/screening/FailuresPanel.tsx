import { AlertTriangle } from "lucide-react";

export function FailuresPanel({ failures }: { failures: { file: string; error: string }[] }) {
  if (failures.length === 0) return null;
  return (
    <div className="alert-banner alert-banner--danger" role="alert">
      <AlertTriangle size={18} aria-hidden="true" style={{ marginTop: 2, flexShrink: 0 }} />
      <div className="stack stack--sm" style={{ flex: 1 }}>
        <p style={{ fontWeight: 600 }}>
          {failures.length} candidate{failures.length === 1 ? "" : "s"} failed to process
        </p>
        <ul style={{ listStyle: "none", margin: 0, padding: 0 }}>
          {failures.map((f, i) => (
            <li key={`${f.file}-${i}`} className="stack stack--sm" style={{ marginBottom: "var(--sp-2)" }}>
              <span className="mono faint">{f.file}</span>
              <span style={{ fontSize: "var(--fs-sm)" }}>{f.error}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}