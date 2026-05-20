import { NavLink } from "react-router-dom";
import { useThemeStore } from "../../stores/themeStore";
import "./Sidebar.css";

interface NavItem {
  label: string;
  to: string;
  icon: string;
}

const navItems: NavItem[] = [
  { label: "Dashboard", to: "/", icon: "bi-grid-1x2" },
  { label: "Onboarding", to: "/onboarding", icon: "bi-person-vcard" },
  { label: "Applications", to: "/applications", icon: "bi-folder2-open" },
  { label: "Interview prep", to: "/interview", icon: "bi-camera-video" },
  { label: "History", to: "/history", icon: "bi-clock-history" },
];

/**
 * Persistent sidebar navigation for Apply-Agent.
 * Renders the logo wordmark, primary nav links, and the theme toggle.
 */
export function Sidebar() {
  const theme = useThemeStore((s) => s.theme);
  const toggleTheme = useThemeStore((s) => s.toggleTheme);

  return (
    <aside className="sidebar" aria-label="Main navigation">
      {/* Wordmark */}
      <div className="sidebar-brand">
        <i className="bi bi-briefcase-fill sidebar-brand-icon" aria-hidden="true" />
        <span className="sidebar-brand-name">Apply-Agent</span>
      </div>

      {/* Primary nav */}
      <nav className="sidebar-nav">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === "/"}
            className={({ isActive }) =>
              ["sidebar-link", isActive ? "sidebar-link--active" : ""].join(" ").trim()
            }
          >
            <i className={`bi ${item.icon}`} aria-hidden="true" />
            {item.label}
          </NavLink>
        ))}
      </nav>

      {/* Theme toggle */}
      <button
        id="theme-toggle-btn"
        type="button"
        className="sidebar-theme-btn"
        onClick={toggleTheme}
        aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
      >
        <i
          className={`bi ${theme === "dark" ? "bi-sun" : "bi-moon-stars"}`}
          aria-hidden="true"
        />
        {theme === "dark" ? "Light mode" : "Dark mode"}
      </button>
    </aside>
  );
}
