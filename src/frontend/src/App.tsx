import { useEffect } from "react";
import "./App.css";
import { useThemeStore } from "./stores/themeStore";

const dashboardCards = [
  {
    title: "Onboarding",
    value: "0 steps complete",
    detail: "Upload a CV or enter your profile manually.",
    icon: "bi-person-check",
  },
  {
    title: "Applications",
    value: "0 active",
    detail: "Track jobs, drafts, and generated documents in one place.",
    icon: "bi-briefcase",
  },
  {
    title: "Interview prep",
    value: "0 sessions",
    detail: "Build contextual mock interviews from your career history.",
    icon: "bi-chat-square-text",
  },
];

function App() {
  const theme = useThemeStore((state) => state.theme);
  const toggleTheme = useThemeStore((state) => state.toggleTheme);

  useEffect(() => {
    const root = document.documentElement;
    root.dataset.theme = theme;
    root.style.colorScheme = theme;
  }, [theme]);

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div>
          <p className="eyebrow">Apply-Agent</p>
          <h1 className="app-title">Career workspace</h1>
          <p className="app-copy">
            A local-first desktop assistant for CVs, cover letters, job matching,
            and interview prep.
          </p>
        </div>

        <nav className="sidebar-nav" aria-label="Primary">
          <a className="nav-item active" href="#dashboard">
            <i className="bi bi-grid-1x2-fill" aria-hidden="true" />
            Dashboard
          </a>
          <a className="nav-item" href="#onboarding">
            <i className="bi bi-person-vcard" aria-hidden="true" />
            Onboarding
          </a>
          <a className="nav-item" href="#applications">
            <i className="bi bi-folder2-open" aria-hidden="true" />
            Applications
          </a>
          <a className="nav-item" href="#interviews">
            <i className="bi bi-camera-video" aria-hidden="true" />
            Interview prep
          </a>
        </nav>

        <button className="theme-toggle" type="button" onClick={toggleTheme}>
          <i className={`bi ${theme === "dark" ? "bi-sun" : "bi-moon-stars"}`} aria-hidden="true" />
          {theme === "dark" ? "Light mode" : "Dark mode"}
        </button>
      </aside>

      <main className="content" id="dashboard">
        <header className="hero">
          <div>
            <p className="eyebrow">Phase 1 scaffold</p>
            <h2>Build the desktop career assistant shell first.</h2>
            <p className="hero-copy">
              The current pass focuses on the foundation: stable navigation, theme
              persistence, backend connectivity, and a clean place to grow the app.
            </p>
          </div>
          <div className="hero-status">
            <span className="status-label">Backend</span>
            <strong>FastAPI prototype</strong>
            <span className="status-muted">Listening on localhost:8000</span>
          </div>
        </header>

        <section className="card-grid" aria-label="Workspace overview">
          {dashboardCards.map((card) => (
            <article className="metric-card" key={card.title}>
              <div className="metric-icon" aria-hidden="true">
                <i className={`bi ${card.icon}`} />
              </div>
              <p className="metric-title">{card.title}</p>
              <p className="metric-value">{card.value}</p>
              <p className="metric-detail">{card.detail}</p>
            </article>
          ))}
        </section>

        <section className="panel" id="onboarding">
          <div className="panel-header">
            <div>
              <p className="eyebrow">Next step</p>
              <h3>Onboarding flow</h3>
            </div>
            <span className="panel-badge">Planned</span>
          </div>
          <p className="panel-copy">
            Add CV upload, structured profile input, and generated CV review before
            saving persistent user context.
          </p>
        </section>

        <section className="panel" id="applications">
          <div className="panel-header">
            <div>
              <p className="eyebrow">Workflow</p>
              <h3>Job applications</h3>
            </div>
            <span className="panel-badge">Planned</span>
          </div>
          <p className="panel-copy">
            The eventual workflow will analyze the role, score fit, generate a CV,
            and create a tailored cover letter in parallel.
          </p>
        </section>

        <section className="panel" id="interviews">
          <div className="panel-header">
            <div>
              <p className="eyebrow">Preparation</p>
              <h3>Interview module</h3>
            </div>
            <span className="panel-badge">Planned</span>
          </div>
          <p className="panel-copy">
            Interview context, mock Q&A, and coaching feedback will use the same
            local memory and retrieval layer.
          </p>
        </section>
      </main>
    </div>
  );
}

export default App;
