import { useEffect, useState, FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { Header } from "../../components/Layout/Header";
import { Card } from "../../components/common/Card";
import { Button } from "../../components/common/Button";
import { Input } from "../../components/common/Input";
import {
  getJobs,
  evaluateJob,
  updateJobStatus,
  deleteJob,
  JobApplicationListOut,
  JobOfferIn,
  WorkflowStatus,
} from "../../services/api";
import "./Applications.css";

const STATUS_CONFIG: Record<
  string,
  { label: string; icon: string; className: string }
> = {
  pending: { label: "Pending", icon: "bi-clock", className: "status-pending" },
  interview: { label: "Interview", icon: "bi-camera-video", className: "status-interview" },
  accepted: { label: "Accepted", icon: "bi-check-circle", className: "status-accepted" },
  rejected: { label: "Rejected", icon: "bi-x-circle", className: "status-rejected" },
  ghosted: { label: "Ghosted", icon: "bi-eye-slash", className: "status-ghosted" },
};

const STATUS_OPTIONS: WorkflowStatus[] = ["pending", "interview", "accepted", "rejected", "ghosted"];

export function Applications() {
  const navigate = useNavigate();
  const [jobs, setJobs] = useState<JobApplicationListOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // Form State
  const [title, setTitle] = useState("");
  const [company, setCompany] = useState("");
  const [description, setDescription] = useState("");

  const fetchJobs = async () => {
    try {
      const data = await getJobs();
      setJobs(data);
    } catch (err) {
      console.error("Failed to load jobs", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJobs();
  }, []);

  // Poll for status if any job is processing
  useEffect(() => {
    const hasProcessing = jobs.some((j) => j.processing);
    if (!hasProcessing) return;

    const interval = setInterval(() => {
      fetchJobs();
    }, 5000);

    return () => clearInterval(interval);
  }, [jobs]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setSubmitting(true);

    const sessionId = crypto.randomUUID();

    const payload: JobOfferIn = {
      title,
      company,
      description,
      session_id: sessionId,
    };

    setIsModalOpen(false);

    // Reset form
    setTitle("");
    setCompany("");
    setDescription("");

    try {
      const result = await evaluateJob(payload);
      // Navigate to the document editor for streaming generation
      navigate(`/applications/${result.job_id}/edit`);
    } catch (err) {
      console.error("Failed to evaluate job", err);
      alert("Failed to add job application. Please check your inputs.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleStatusChange = async (jobId: string, newStatus: WorkflowStatus) => {
    try {
      await updateJobStatus(jobId, newStatus);
      setJobs((prev) =>
        prev.map((j) => (j.job_id === jobId ? { ...j, workflow_status: newStatus } : j))
      );
    } catch (err) {
      console.error("Failed to update status", err);
    }
  };

  const handleDeleteJob = async (jobId: string) => {
    if (!globalThis.confirm("Are you sure you want to delete this job application? This action cannot be undone.")) return;
    
    try {
      await deleteJob(jobId);
      setJobs((prev) => prev.filter((j) => j.job_id !== jobId));
    } catch (err) {
      console.error("Failed to delete job", err);
      alert("Failed to delete job application.");
    }
  };

  const getScoreColorClass = (score: number | null) => {
    if (score === null) return "";
    if (score >= 80) return "high";
    if (score >= 50) return "medium";
    return "low";
  };

  const downloadFile = (jobId: string, type: "cv" | "cover") => {
    window.open(`http://127.0.0.1:8000/jobs/${jobId}/download?file_type=${type}`, "_blank");
  };

  const renderContent = () => {
    if (loading) {
      return (
        <div className="loading-state">
          <output className="spinner-border" />
          <span>Loading applications…</span>
        </div>
      );
    }
    if (jobs.length === 0) {
      return (
        <Card padding="lg" style={{ textAlign: "center", marginTop: "2rem" }}>
          <div className="empty-state">
            <i className="bi bi-briefcase" />
            <h3>No applications yet</h3>
            <p>Add your first job description to get a tailored CV and cover letter.</p>
            <Button variant="primary" onClick={() => setIsModalOpen(true)}>
              Add First Job
            </Button>
          </div>
        </Card>
      );
    }
    return (
      <div className="applications-grid">
        {jobs.map((job) => {
          const statusConf = STATUS_CONFIG[job.workflow_status] ?? STATUS_CONFIG.pending;

          return (
            <Card key={job.job_id} padding="lg" className="job-card">
              <div className="job-header">
                <div className="job-info" style={{ width: '100%' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', width: '100%' }}>
                    <h3 className="job-title">{job.job_title}</h3>
                    <button
                      className="delete-job-btn"
                      onClick={() => handleDeleteJob(job.job_id)}
                      title="Delete Application"
                      style={{ background: 'none', border: 'none', cursor: 'pointer', padding: '0.2rem' }}
                    >
                      <i className="bi bi-trash" style={{ color: '#dc2626', fontSize: '1.1rem' }}></i>
                    </button>
                  </div>
                  <p className="company-name">
                    <i className="bi bi-building" />
                    {job.company_name}
                  </p>
                </div>
                {job.match_score !== null && (
                  <div className={`score-badge ${getScoreColorClass(job.match_score)}`}>
                    {Math.round(job.match_score)}%
                  </div>
                )}
              </div>

              {/* Status Section */}
              <div className="job-status-section">
                <div className={`status-badge ${statusConf.className}`}>
                  <i className={`bi ${statusConf.icon}`} />
                  <span>{statusConf.label}</span>
                </div>

                {job.processing && (
                  <div className="processing-indicator">
                    <output className="spinner-border spinner-border-sm" />
                    <span>Processing…</span>
                  </div>
                )}
              </div>

              {/* Status Dropdown */}
              <div className="status-dropdown-wrapper">
                <label htmlFor={`status-select-${job.job_id}`} className="status-label">Change Status</label>
                <select
                  id={`status-select-${job.job_id}`}
                  className="status-select"
                  value={job.workflow_status}
                  onChange={(e) =>
                    handleStatusChange(job.job_id, e.target.value as WorkflowStatus)
                  }
                >
                  {STATUS_OPTIONS.map((s) => (
                    <option key={s} value={s}>
                      {STATUS_CONFIG[s].label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Actions */}
              <div className="job-actions">
                {job.confirmed ? (
                  <>
                    <Button
                      variant="secondary"
                      size="sm"
                      icon="bi-file-earmark-pdf"
                      onClick={() => downloadFile(job.job_id, "cv")}
                      style={{ flex: 1 }}
                    >
                      CV PDF
                    </Button>
                    <Button
                      variant="secondary"
                      size="sm"
                      icon="bi-envelope-paper"
                      onClick={() => downloadFile(job.job_id, "cover")}
                      style={{ flex: 1 }}
                    >
                      Cover Letter
                    </Button>
                  </>
                ) : (
                  <Button
                    variant="primary"
                    size="sm"
                    icon="bi-pencil-square"
                    onClick={() => navigate(`/applications/${job.job_id}/edit`)}
                    disabled={job.processing}
                    style={{ flex: 1 }}
                  >
                    {job.cv_text ? "Edit & Confirm" : "Generate Documents"}
                  </Button>
                )}
              </div>

              <div className="job-meta">
                <span className="job-date">
                  <i className="bi bi-calendar3" />
                  {new Date(job.created_at).toLocaleDateString()}
                </span>
              </div>
            </Card>
          );
        })}
      </div>
    );
  };

  return (
    <>
      <Header title="Applications" subtitle="Track and manage your job applications." />

      <div className="applications-container">
        <div className="applications-header">
          <h2>Your Tracked Jobs</h2>
          <Button variant="primary" icon="bi-plus-lg" onClick={() => setIsModalOpen(true)}>
            New Application
          </Button>
        </div>

        {renderContent()}
      </div>

      {/* New Application Modal */}
      {isModalOpen && (
        <div 
          className="modal-overlay" 
          role="presentation"
          onClick={() => setIsModalOpen(false)}
          onKeyDown={(e) => { if (e.key === 'Escape') setIsModalOpen(false); }}
        >
          <div 
            role="dialog"
            aria-modal="true"
            aria-labelledby="modal-title"
            onClick={(e) => e.stopPropagation()} 
            onKeyDown={(e) => e.stopPropagation()}
          >
          <Card
            padding="lg"
            className="modal-content"
          >
            <div className="modal-header">
              <h3 id="modal-title">New Job Application</h3>
              <button className="close-btn" onClick={() => setIsModalOpen(false)}>
                <i className="bi bi-x-lg" />
              </button>
            </div>

            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <Input
                  label="Job Title"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g. Senior Frontend Engineer"
                  required
                />
              </div>
              <div className="form-group">
                <Input
                  label="Company Name"
                  value={company}
                  onChange={(e) => setCompany(e.target.value)}
                  placeholder="e.g. Acme Corp"
                  required
                />
              </div>
              <div className="form-group input-wrapper" style={{ marginTop: "1rem" }}>
                <label htmlFor="job-description" className="input-label">Job Description</label>
                <div className="input-container">
                  <textarea
                    id="job-description"
                    className="input-field textarea-field"
                    rows={8}
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="Paste the full job description here…"
                    required
                  />
                </div>
              </div>

              <div className="modal-footer">
                <Button type="button" variant="secondary" onClick={() => setIsModalOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit" variant="primary" loading={submitting}>
                  Evaluate & Generate
                </Button>
              </div>
            </form>
          </Card>
          </div>
        </div>
      )}
    </>
  );
}
