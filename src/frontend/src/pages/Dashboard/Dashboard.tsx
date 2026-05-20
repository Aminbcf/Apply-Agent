import { useEffect, useState } from "react";
import { Header } from "../../components/Layout/Header";
import { Card } from "../../components/common/Card";
import { Badge } from "../../components/common/Badge";
import {
  getDashboardStats,
  getOnboardingStatus,
  DashboardStats,
  OnboardingStatus,
} from "../../services/api";
import "./Dashboard.css";

export function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [onboarding, setOnboarding] = useState<OnboardingStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([getDashboardStats(), getOnboardingStatus()])
      .then(([statsData, onboardingData]) => {
        setStats(statsData);
        setOnboarding(onboardingData);
      })
      .catch((err) => console.error("Failed to load dashboard data", err))
      .finally(() => setLoading(false));
  }, []);

  const isOnboardingComplete = onboarding?.status === "completed";

  const dashboardCards = [
    {
      title: "Onboarding",
      value: loading ? "..." : `${onboarding?.steps_completed ?? 0}/3 steps complete`,
      detail: isOnboardingComplete
        ? "Your profile is saved and fully set up."
        : "Upload a CV or enter your profile manually.",
      icon: isOnboardingComplete ? "bi-person-check-fill" : "bi-person-check",
      badgeText: isOnboardingComplete ? "Complete" : "Pending",
      badgeVariant: isOnboardingComplete ? ("success" as const) : ("warning" as const),
    },
    {
      title: "Applications",
      value: loading ? "..." : `${stats?.active_applications ?? 0} active`,
      detail: "Track jobs, drafts, and generated documents in one place.",
      icon: "bi-briefcase",
      badgeText: "Active",
      badgeVariant: "primary" as const,
    },
    {
      title: "Interview prep",
      value: loading ? "..." : `${stats?.interview_sessions ?? 0} sessions`,
      detail: "Build contextual mock interviews from your career history.",
      icon: "bi-camera-video",
      badgeText: "Ready",
      badgeVariant: "success" as const,
    },
  ];

  return (
    <>
      <Header title="Dashboard" subtitle="Your career workspace overview." />
      <div className="dashboard-content">
        <section className="card-grid" aria-label="Workspace overview">
          {dashboardCards.map((card) => (
            <Card key={card.title} className="metric-card">
              <div className="metric-header">
                <div className="metric-icon" aria-hidden="true">
                  <i className={`bi ${card.icon}`} />
                </div>
                <Badge variant={card.badgeVariant}>{card.badgeText}</Badge>
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
              <h3>{isOnboardingComplete ? "Onboarding Complete!" : "Onboarding flow"}</h3>
            </div>
            <Badge variant={isOnboardingComplete ? "success" : "primary"}>
              {isOnboardingComplete ? "Ready" : "Planned"}
            </Badge>
          </div>
          <p className="panel-copy">
            {isOnboardingComplete
              ? "Your persistent user context is successfully saved. You can now start tracking job applications and generating custom CVs/cover letters!"
              : "Add CV upload, structured profile input, and generated CV review before saving persistent user context."}
          </p>
        </Card>
      </div>
    </>
  );
}
