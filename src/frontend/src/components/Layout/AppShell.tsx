import { Outlet } from "react-router-dom";
import { Sidebar } from "./Sidebar";
import "./AppShell.css";

/**
 * Root layout shell: fixed sidebar + scrollable main content area.
 * Uses React Router's <Outlet /> so child pages render in <main>.
 */
export function AppShell() {
  return (
    <div className="app-shell">
      <Sidebar />
      <main className="app-main" id="main-content">
        <Outlet />
      </main>
    </div>
  );
}
