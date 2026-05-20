import { useEffect } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { useThemeStore } from "./stores/themeStore";
import { AppShell } from "./components/Layout/AppShell";
import { Dashboard } from "./pages/Dashboard/Dashboard";
import { Onboarding } from "./pages/Onboarding/Onboarding";

// Temporary stubs for other pages
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
          <Route path="applications" element={<Stub title="Applications" />} />
          <Route path="interview" element={<Stub title="Interview Prep" />} />
          <Route path="history" element={<Stub title="History" />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;

