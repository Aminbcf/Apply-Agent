import { useEffect, useState } from "react";
import { Header } from "../../components/Layout/Header";
import { Card } from "../../components/common/Card";
import { Badge } from "../../components/common/Badge";
import { getDashboardStats, DashboardStats } from "../../services/api";
import "./Dashboard.css";

export function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getDashboardStats()
      .then((data) => setStats(data))
      .catch((err) => console.error("Failed to load dashboard stats", err))
      .finally(() => setLoading(false));
  }, []);

  const dashboardCards = [
    {
      title: "Onboarding",
      value: "0 steps complete", // Will be linked later when onboarding is implemented
      detail: "Upload a CV or enter your profile manually.",
      icon: "bi-person-check",
    },
    {
      title: "Applications",
      value: loading ? "..." : `${stats?.active_applications ?? 0} active`,
      detail: "Track jobs, drafts, and generated documents in one place.",
      icon: "bi-briefcase",
    },
    {
      title: "Interview prep",
      value: loading ? "..." : `${stats?.interview_sessions ?? 0} sessions`,
      detail: "Build contextual mock interviews from your career history.",
      icon: "bi-chat-square-text",
    },
  ];

  return (
    <>
      <Header
        title="Dashboard"
        subtitle="Your career workspace overview."
      />
      <div className="dashboard-content">
        <section className="card-grid" aria-label="Workspace overview">
          {dashboardCards.map((card) => (
            <Card key={card.title} className="metric-card">
              <div className="metric-icon" aria-hidden="true">
                <i className={`bi ${card.icon}`} />
              </div>
              <p className="metric-title">{card.title}</p>
              <p className="metric-value">{card.value}</p>
              <p className="metric-detail">{card.detail}</p>
            </Card>
          ))}
        </section>

        <Card padding="lg" className="panel">
          <div className="panel-header">
            <div>
              <p className="eyebrow">Next step</p>
              <h3>Onboarding flow</h3>
            </div>
            <Badge variant="primary">Planned</Badge>
          </div>
          <p className="panel-copy">
            Add CV upload, structured profile input, and generated CV review before
            saving persistent user context.
          </p>
        </Card>
      </div>
    </>
  );
}
