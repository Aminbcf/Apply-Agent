import { useEffect } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { useThemeStore } from "./stores/themeStore";
import { AppShell } from "./components/Layout/AppShell";
import { Dashboard } from "./pages/Dashboard/Dashboard";
import { Onboarding } from "./pages/Onboarding/Onboarding";
import { Applications } from "./pages/Applications/Applications";
import { DocumentEditor } from "./pages/Applications/DocumentEditor";
import { Interviews } from "./pages/Interviews/Interviews";
import { Settings } from "./pages/Settings/Settings";

// Temporary stub for pages not yet implemented
const Stub = ({ title }: { title: string }) => (
  <div style={{ padding: "2rem 2.5rem" }}>
    <h2>{title}</h2>
    <p>This page is coming soon.</p>
  </div>
);

function App() {
  const theme = useThemeStore((state) => state.theme);

  useEffect(() => {
    const root = document.documentElement;
    root.dataset.theme = theme;
    root.style.colorScheme = theme;
  }, [theme]);

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<AppShell />}>
          <Route index element={<Dashboard />} />
          <Route path="onboarding" element={<Onboarding />} />
          <Route path="applications" element={<Applications />} />
          <Route path="applications/:jobId/edit" element={<DocumentEditor />} />
          <Route path="interview" element={<Interviews />} />
          <Route path="history" element={<Stub title="History" />} />
          <Route path="settings" element={<Settings />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
