import type { ReactNode } from "react";

export function Card({
  title,
  actions,
  children,
  header,
}: {
  title?: ReactNode;
  actions?: ReactNode;
  children: ReactNode;
  header?: ReactNode;
}) {
  return (
    <section className="card">
      {(title || actions || header) && (
        <div className="card__header">
          <div>
            {title && <h2 className="card__title">{title}</h2>}
            {header}
          </div>
          {actions}
        </div>
      )}
      <div className="card__body">{children}</div>
    </section>
  );
}