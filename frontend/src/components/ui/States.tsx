export function Spinner({ label }: { label?: string }) {
  return (
    <span className="row" role="status">
      <span className="spinner" aria-hidden="true" />
      {label && <span>{label}</span>}
      <span className="sr-only">{label ?? "Loading"}</span>
    </span>
  );
}

export function ErrorState({ title, message, onRetry }: { title?: string; message: string; onRetry?: () => void }) {
  return (
    <div className="error-state" role="alert">
      <p className="error-state__title">{title ?? "Something went wrong"}</p>
      <p className="muted">{message}</p>
      {onRetry && (
        <button className="btn btn--secondary" style={{ marginTop: "var(--sp-3)" }} onClick={onRetry}>
          Retry
        </button>
      )}
    </div>
  );
}

export function EmptyState({ title, hint }: { title: string; hint?: string }) {
  return (
    <div className="empty-state">
      <p style={{ fontWeight: 600 }}>{title}</p>
      {hint && <p className="muted" style={{ marginTop: "var(--sp-1)" }}>{hint}</p>}
    </div>
  );
}