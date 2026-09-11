import { NavLink, Outlet } from "react-router-dom";
import { FileSearch } from "lucide-react";

const NAV_ITEMS = [
  { to: "/", label: "Candidates", end: true },
  { to: "/screening", label: "New Screening" },
  { to: "/evaluations", label: "Evaluations" },
  { to: "/system", label: "System" },
];

export function AppLayout() {
  return (
    <div className="layout-shell">
      <a href="#main" className="skip-link">
        Skip to main content
      </a>
      <header className="app-header">
        <div className="app-header__inner">
          <NavLink to="/" className="app-header__brand">
            <FileSearch size={18} aria-hidden="true" />
            Resume Screening
          </NavLink>
          <nav className="app-header__nav" aria-label="Primary">
            {NAV_ITEMS.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={({ isActive }) => (isActive ? "active" : undefined)}
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
        </div>
      </header>
      <main id="main" className="layout-main">
        <Outlet />
      </main>
      <footer className="app-footer">
        <div className="app-footer__inner">
          <span>Resume Screening System — ranked, evidence-backed assessments.</span>
          <span className="mono">dev-set snapshots &amp; sample data are clearly labeled</span>
        </div>
      </footer>
    </div>
  );
}