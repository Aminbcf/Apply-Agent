import { useEffect, useState } from "react";
import { Header } from "../../components/Layout/Header";
import { Card } from "../../components/common/Card";
import { Button } from "../../components/common/Button";
import { getInterviews, JobApplicationListOut } from "../../services/api";
import "./Interviews.css";

export function Interviews() {
  const [interviews, setInterviews] = useState<JobApplicationListOut[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchInterviews = async () => {
      try {
        const data = await getInterviews();
        setInterviews(data);
      } catch (err) {
        console.error("Failed to load interviews", err);
      } finally {
        setLoading(false);
      }
    };
    fetchInterviews();
  }, []);

  const downloadFile = (jobId: string, type: "cv" | "cover") => {
    window.open(`http://127.0.0.1:8000/jobs/${jobId}/download?file_type=${type}`, "_blank");
  };

  return (
    <>
      <Header
        title="Interview Prep"
        subtitle="Prepare for your upcoming interviews with your generated documents."
      />

      <div className="interviews-container">
        {loading ? (
          <div className="interviews-loading">
            <div className="spinner-border" role="status" />
            <span>Loading interviews…</span>
          </div>
        ) : interviews.length === 0 ? (
          <Card padding="lg" className="interviews-empty">
            <div className="empty-content">
              <div className="empty-icon">
                <i className="bi bi-camera-video" />
              </div>
              <h3>No interviews scheduled yet</h3>
              <p>
                When you change a job application's status to "Interview", it
                will appear here with your prepared documents.
              </p>
            </div>
          </Card>
        ) : (
          <div className="interviews-grid">
            {interviews.map((interview) => (
              <Card key={interview.job_id} padding="lg" className="interview-card">
                <div className="interview-header">
                  <div className="interview-info">
                    <h3 className="interview-title">{interview.job_title}</h3>
                    <p className="interview-company">
                      <i className="bi bi-building" />
                      {interview.company_name}
                    </p>
                  </div>

                  {interview.match_score !== null && (
                    <div className="interview-score">
                      <span className="score-value">{Math.round(interview.match_score)}%</span>
                      <span className="score-label">Match</span>
                    </div>
                  )}
                </div>

                <div className="interview-badge">
                  <i className="bi bi-camera-video-fill" />
                  <span>Interview Scheduled</span>
                </div>

                <div className="interview-date">
                  <i className="bi bi-calendar3" />
                  <span>Added {new Date(interview.created_at).toLocaleDateString()}</span>
                </div>

                {interview.confirmed && (
                  <div className="interview-docs">
                    <span className="docs-label">Documents Ready</span>
                    <div className="docs-actions">
                      <Button
                        variant="secondary"
                        size="sm"
                        icon="bi-file-earmark-pdf"
                        onClick={() => downloadFile(interview.job_id, "cv")}
                      >
                        CV
                      </Button>
                      <Button
                        variant="secondary"
                        size="sm"
                        icon="bi-envelope-paper"
                        onClick={() => downloadFile(interview.job_id, "cover")}
                      >
                        Cover Letter
                      </Button>
                    </div>
                  </div>
                )}
              </Card>
            ))}
          </div>
        )}
      </div>
    </>
  );
}
