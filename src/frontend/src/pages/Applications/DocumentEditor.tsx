import { useEffect, useState, useRef, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Header } from "../../components/Layout/Header";
import { Button } from "../../components/common/Button";
import {
  streamGenerateDocuments,
  confirmJob,
  updateJobDocuments,
} from "../../services/api";
import "./DocumentEditor.css";

type GenerationPhase = "idle" | "generating_cv" | "generating_cover" | "editing" | "confirming" | "done";

export function DocumentEditor() {
  const { jobId } = useParams<{ jobId: string }>();
  const navigate = useNavigate();

  const [phase, setPhase] = useState<GenerationPhase>("idle");
  const [cvText, setCvText] = useState("");
  const [coverText, setCoverText] = useState("");
  const [error, setError] = useState<string | null>(null);

  // For streaming animation
  const [streamingCv, setStreamingCv] = useState("");
  const [streamingCover, setStreamingCover] = useState("");
  const [cvSectionsStatus, setCvSectionsStatus] = useState<Record<string, "generating" | "done" | "error">>({});

  // Auto-save debounce
  const saveTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Start streaming when component mounts
  useEffect(() => {
    if (!jobId) return;

    setPhase("generating_cv");

    streamGenerateDocuments(jobId, {
      onCvSectionStart: (section) => {
        setCvSectionsStatus((prev) => ({ ...prev, [section]: "generating" }));
      },
      onCvSectionDone: (section, ok) => {
        setCvSectionsStatus((prev) => ({ ...prev, [section]: ok ? "done" : "error" }));
      },
      onCvToken: (token) => {
        setStreamingCv((prev) => prev + token);
      },
      onCvComplete: (text) => {
        setCvText(text);
        setStreamingCv(text);
        setPhase("generating_cover");
      },
      onCoverToken: (token) => {
        setStreamingCover((prev) => prev + token);
      },
      onCoverComplete: (text) => {
        setCoverText(text);
        setStreamingCover(text);
        setPhase("editing");
      },
      onError: (message) => {
        setError(message);
        setPhase("editing");
      },
      onDone: () => {
        if (phase !== "editing") {
          setPhase("editing");
        }
      },
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [jobId]);

  // Auto-save debounced
  const autoSave = useCallback(() => {
    if (!jobId || phase !== "editing") return;

    if (saveTimerRef.current) clearTimeout(saveTimerRef.current);
    saveTimerRef.current = setTimeout(() => {
      updateJobDocuments(jobId, cvText, coverText).catch(console.error);
    }, 2000);
  }, [jobId, cvText, coverText, phase]);

  useEffect(() => {
    autoSave();
    return () => {
      if (saveTimerRef.current) clearTimeout(saveTimerRef.current);
    };
  }, [autoSave]);

  const handleConfirm = async () => {
    if (!jobId) return;
    setPhase("confirming");

    try {
      await confirmJob(jobId, cvText, coverText);
      setPhase("done");
      navigate("/applications", { replace: true });
    } catch (err) {
      console.error("Confirm failed", err);
      setError("Failed to generate PDFs. Please try again.");
      setPhase("editing");
    }
  };

  const handleCancel = () => {
    navigate("/applications", { replace: true });
  };

  const isGenerating = phase === "generating_cv" || phase === "generating_cover";
  const isEditable = phase === "editing";

  return (
    <>
      <Header
        title="Document Editor"
        subtitle="Review and edit your generated CV and cover letter before creating PDFs."
      />

      <div className="doc-editor-container">
        {error && (
          <div className="doc-editor-error">
            <i className="bi bi-exclamation-triangle" />
            <span>{error}</span>
            <button onClick={() => setError(null)}>
              <i className="bi bi-x" />
            </button>
          </div>
        )}

        <div className="doc-editor-panels">
          {/* CV Panel */}
          <div className="doc-editor-panel">
            <div className="panel-header">
              <div className="panel-title">
                <i className="bi bi-file-earmark-text" />
                <span>Curriculum Vitae</span>
              </div>
              {phase === "generating_cv" && (
                <span className="panel-status generating">
                  <span className="pulse-dot" />
                  Generating…
                </span>
              )}
              {phase === "generating_cover" && (
                <span className="panel-status complete">
                  <i className="bi bi-check-circle-fill" />
                  Complete
                </span>
              )}
              {isEditable && (
                <span className="panel-status editable">
                  <i className="bi bi-pencil" />
                  Editable
                </span>
              )}
            </div>

            <div className="panel-body">
              {isEditable || phase === "confirming" ? (
                <textarea
                  className="doc-textarea"
                  value={cvText}
                  onChange={(e) => setCvText(e.target.value)}
                  disabled={phase === "confirming"}
                  placeholder="CV content will appear here…"
                />
              ) : (
                <div className="doc-stream-display">
                  <div className="cv-sections-checklist">
                    {Object.entries(cvSectionsStatus).map(([section, status]) => (
                      <div key={section} className={`checklist-item ${status}`}>
                        {status === "generating" && <div className="spinner-border spinner-border-sm text-primary me-2" role="status" />}
                        {status === "done" && <i className="bi bi-check-circle-fill text-success me-2" />}
                        {status === "error" && <i className="bi bi-x-circle-fill text-danger me-2" />}
                        <span className="section-name">Generating {section.charAt(0).toUpperCase() + section.slice(1)}...</span>
                      </div>
                    ))}
                    {Object.keys(cvSectionsStatus).length === 0 && (
                      <div className="checklist-item generating">
                        <div className="spinner-border spinner-border-sm text-primary me-2" role="status" />
                        <span className="section-name">Initializing parallel extraction...</span>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Cover Letter Panel */}
          <div className="doc-editor-panel">
            <div className="panel-header">
              <div className="panel-title">
                <i className="bi bi-envelope-paper" />
                <span>Cover Letter</span>
              </div>
              {phase === "generating_cover" && (
                <span className="panel-status generating">
                  <span className="pulse-dot" />
                  Generating…
                </span>
              )}
              {(phase === "generating_cv") && (
                <span className="panel-status waiting">
                  <i className="bi bi-hourglass-split" />
                  Waiting…
                </span>
              )}
              {isEditable && (
                <span className="panel-status editable">
                  <i className="bi bi-pencil" />
                  Editable
                </span>
              )}
            </div>

            <div className="panel-body">
              {isEditable || phase === "confirming" ? (
                <textarea
                  className="doc-textarea"
                  value={coverText}
                  onChange={(e) => setCoverText(e.target.value)}
                  disabled={phase === "confirming"}
                  placeholder="Cover letter content will appear here…"
                />
              ) : (
                <div className="doc-stream-display">
                  <pre className="stream-text">
                    {streamingCover}
                    {phase === "generating_cover" && <span className="typing-cursor">▊</span>}
                  </pre>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Action Bar */}
        <div className="doc-editor-actions">
          <Button
            type="button"
            variant="secondary"
            onClick={handleCancel}
            disabled={phase === "confirming"}
          >
            Cancel
          </Button>

          {isGenerating && (
            <div className="generation-progress">
              <div className="spinner-border spinner-border-sm" role="status" />
              <span>
                {phase === "generating_cv" ? "Generating CV…" : "Generating Cover Letter…"}
              </span>
            </div>
          )}

          <Button
            type="button"
            variant="primary"
            icon="bi-check-lg"
            onClick={handleConfirm}
            loading={phase === "confirming"}
            disabled={!isEditable || !cvText.trim() || !coverText.trim()}
          >
            Confirm & Generate PDF
          </Button>
        </div>
      </div>
    </>
  );
}
