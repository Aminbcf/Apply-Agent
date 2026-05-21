import { useEffect, useState, FormEvent } from "react";
import { Header } from "../../components/Layout/Header";
import { Card } from "../../components/common/Card";
import { Input } from "../../components/common/Input";
import { Button } from "../../components/common/Button";
import { Badge } from "../../components/common/Badge";
import { getProfile, saveProfile, uploadOnboardingCv, getOnboardingDebug, UserProfileData, OnboardingDebugData } from "../../services/api";
import "./Onboarding.css";

const defaultProfile: UserProfileData = {
  full_name: "",
  email: "",
  phone: "",
  location: "",
  career_goals: "",
  experience: [],
  education: [],
  projects: [],
  skills: {},
  certifications: [],
  languages: [],
  achievements: [],
};

export function Onboarding() {
  const [profile, setProfile] = useState<UserProfileData>(defaultProfile);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [cvUploading, setCvUploading] = useState(false);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  // Debugging States
  const [debugEnabled, setDebugEnabled] = useState(false);
  const [debugData, setDebugData] = useState<OnboardingDebugData | null>(null);
  const [debugLoading, setDebugLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<"raw" | "parsed" | "context">("raw");

  useEffect(() => {
    getProfile()
      .then((data) => {
        // Fallback null fields to empty string for controlled inputs
        setProfile({
          ...defaultProfile,
          ...data,
          full_name: data.full_name ?? "",
          email: data.email ?? "",
          phone: data.phone ?? "",
          location: data.location ?? "",
          career_goals: data.career_goals ?? "",
        });
      })
      .catch((err) => console.error("Failed to load profile", err))
      .finally(() => setLoading(false));
  }, []);

  const handleInputChange = (field: keyof UserProfileData, value: string) => {
    setProfile((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const refreshDebug = async () => {
    try {
      const data = await getOnboardingDebug();
      setDebugData(data);
    } catch (err) {
      console.error("Failed to refresh debugging details", err);
    }
  };

  const handleToggleDebug = async () => {
    if (debugEnabled) {
      setDebugEnabled(false);
      return;
    }

    setDebugLoading(true);
    try {
      const data = await getOnboardingDebug();
      setDebugData(data);
      setDebugEnabled(true);
    } catch (err) {
      console.error("Failed to load debugging details", err);
      setMessage({ type: "error", text: "Failed to load debugging details from server." });
    } finally {
      setDebugLoading(false);
    }
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setMessage(null);

    try {
      await saveProfile(profile);
      setMessage({ type: "success", text: "Profile saved successfully! Onboarding updated." });
      if (debugEnabled) {
        await refreshDebug();
      }
    } catch (err) {
      console.error("Failed to save profile", err);
      setMessage({ type: "error", text: "Failed to save profile. Please try again." });
    } finally {
      setSaving(false);
    }
  };

  const handleCvUpload = async (file: File | null) => {
    if (!file) return;

    setCvUploading(true);
    setMessage(null);

    try {
      const updated = await uploadOnboardingCv(file);
      setProfile({
        ...defaultProfile,
        ...updated,
        full_name: updated.full_name ?? "",
        email: updated.email ?? "",
        phone: updated.phone ?? "",
        location: updated.location ?? "",
        career_goals: updated.career_goals ?? "",
      });
      setMessage({ type: "success", text: "CV uploaded and parsed. Profile updated." });
    } catch (err) {
      console.error("Failed to upload CV", err);
      setMessage({ type: "error", text: "Failed to upload CV. Please try again." });
      return;
    } finally {
      setCvUploading(false);
    }

    if (debugEnabled) {
      await refreshDebug();
    }
  };

  if (loading) {
    return (
      <>
        <Header title="Onboarding" subtitle="Set up your profile and upload your CV." />
        <div style={{ padding: "2rem 2.5rem" }}>
          <p>Loading your profile...</p>
        </div>
      </>
    );
  }

  // Count step completeness
  const step1Complete = !!profile.full_name && !!profile.email;
  const step2Complete = profile.experience.length > 0 || Object.keys(profile.skills).length > 0;
  const step3Complete = !!profile.career_goals;
  
  let stepsCount = 0;
  if (step1Complete) stepsCount++;
  if (step2Complete) stepsCount++; // Default complete for empty list for simplicity
  if (step3Complete) stepsCount++;

  return (
    <>
      <Header title="Onboarding" subtitle="Set up your profile and upload your CV." />
      <div className="onboarding-container" style={{ padding: "2rem 2.5rem", maxWidth: "800px" }}>
        
        <div className="onboarding-progress-banner">
          <div className="progress-text">
            <span>Profile Completeness</span>
            <strong>{stepsCount}/3 steps complete</strong>
          </div>
          <Badge variant={stepsCount === 3 ? "success" : "warning"}>
            {stepsCount === 3 ? "Complete" : "Pending"}
          </Badge>
        </div>

        {message && (
          <div className={`onboarding-alert alert-${message.type}`}>
            <i className={`bi ${message.type === "success" ? "bi-check-circle" : "bi-exclamation-triangle"}`} />
            <span>{message.text}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="onboarding-form">
          <Card padding="lg" className="form-card">
            <h3>Step 1: Contact Information</h3>
            <p className="card-sub">Please enter your basic information to get started.</p>
            <hr className="divider" />
            
            <div className="form-grid">
              <Input
                label="Full Name"
                value={profile.full_name || ""}
                onChange={(e) => handleInputChange("full_name", e.target.value)}
                placeholder="e.g. Jane Doe"
                icon="bi-person"
                required
              />
              <Input
                label="Email Address"
                type="email"
                value={profile.email || ""}
                onChange={(e) => handleInputChange("email", e.target.value)}
                placeholder="e.g. jane.doe@example.com"
                icon="bi-envelope"
                required
              />
              <Input
                label="Phone Number"
                value={profile.phone || ""}
                onChange={(e) => handleInputChange("phone", e.target.value)}
                placeholder="e.g. +1 (555) 019-2834"
                icon="bi-telephone"
              />
              <Input
                label="Location"
                value={profile.location || ""}
                onChange={(e) => handleInputChange("location", e.target.value)}
                placeholder="e.g. London, UK"
                icon="bi-geo-alt"
              />
            </div>
          </Card>

          <Card padding="lg" className="form-card" style={{ marginTop: "1.5rem" }}>
            <h3>Step 2: Experience & Skills</h3>
            <p className="card-sub">Let's build your professional background profile.</p>
            <hr className="divider" />
            
            <div className="placeholder-section">
              <div className="info-box">
                <i className="bi bi-upload text-primary" />
                <p>
                  Upload a CV (PDF/DOCX/TXT) and we'll auto-fill experience, education, and skills.
                </p>
              </div>

              <Input
                label="Upload CV"
                type="file"
                accept=".pdf,.docx,.txt"
                icon="bi-file-earmark-arrow-up"
                disabled={cvUploading}
                onChange={(e) => handleCvUpload(e.currentTarget.files?.item(0) ?? null)}
              />

              {cvUploading && <p style={{ marginTop: "0.75rem" }}>Parsing your CV...</p>}
            </div>
          </Card>

          <Card padding="lg" className="form-card" style={{ marginTop: "1.5rem" }}>
            <h3>Step 3: Career Goals</h3>
            <p className="card-sub">Explain what you are looking for in your next role.</p>
            <hr className="divider" />
            
            <div className="input-wrapper">
              <label htmlFor="career-goals-input" className="input-label">Career Goals & Preferences</label>
              <div className="input-container">
                <textarea
                  id="career-goals-input"
                  className="input-field textarea-field"
                  rows={4}
                  value={profile.career_goals || ""}
                  onChange={(e) => handleInputChange("career_goals", e.target.value)}
                  placeholder="e.g. Looking for a Senior Full Stack Engineer role specializing in React, TypeScript, and FastAPI. Passionate about AI integrations and Developer Tooling."
                />
              </div>
            </div>
          </Card>

          <div className="form-actions" style={{ marginTop: "2rem", display: "flex", justifyContent: "flex-end" }}>
            <Button
              type="submit"
              variant="primary"
              size="lg"
              loading={saving}
              icon="bi-send-check"
            >
              Save Profile & Complete Onboarding
            </Button>
          </div>
        </form>

        {/* Developer Debugging Panel */}
        {(stepsCount === 3 || profile.experience.length > 0 || (profile.skills && Object.keys(profile.skills).length > 0)) && (
          <div className="debug-toggle-wrapper">
            <div className="debug-toggle-container">
              <span className="debug-toggle-label">
                <i className="bi bi-braces-asterisk text-primary" style={{ marginRight: "0.5rem" }} />
                <strong>Developer Tools:</strong> Inspect parser and LLM prompt telemetry.
              </span>
              <Button
                type="button"
                variant={debugEnabled ? "danger" : "secondary"}
                onClick={handleToggleDebug}
                loading={debugLoading}
                icon={debugEnabled ? "bi-bug-fill" : "bi-bug"}
              >
                {debugEnabled ? "Disable Debug Mode" : "Enable Debug Mode"}
              </Button>
            </div>

            {debugEnabled && debugData && (
              <Card padding="lg" className="debug-dashboard-card" style={{ marginTop: "1.5rem" }}>
                <div className="debug-header">
                  <div className="debug-title-group">
                    <h3>CV Parser & LLM Context Telemetry</h3>
                    <p className="card-sub">Inspect how the parser structured your CV and formatted the LLM system prompt.</p>
                  </div>
                  <Button
                    type="button"
                    variant="secondary"
                    size="sm"
                    onClick={refreshDebug}
                    icon="bi-arrow-clockwise"
                  >
                    Refresh
                  </Button>
                </div>
                
                <hr className="divider" />
                
                <div className="debug-tabs">
                  <button
                    type="button"
                    className={`debug-tab ${activeTab === "raw" ? "active" : ""}`}
                    onClick={() => setActiveTab("raw")}
                    aria-pressed={activeTab === "raw"}
                  >
                    <i className="bi bi-file-earmark-text" /> Raw CV Text
                  </button>
                  <button
                    type="button"
                    className={`debug-tab ${activeTab === "parsed" ? "active" : ""}`}
                    onClick={() => setActiveTab("parsed")}
                    aria-pressed={activeTab === "parsed"}
                  >
                    <i className="bi bi-diagram-3" /> Parser Interpretation
                  </button>
                  <button
                    type="button"
                    className={`debug-tab ${activeTab === "context" ? "active" : ""}`}
                    onClick={() => setActiveTab("context")}
                    aria-pressed={activeTab === "context"}
                  >
                    <i className="bi bi-cpu" /> LLM Prompt Context
                  </button>
                </div>

                <div className="debug-tab-content">
                  {activeTab === "raw" && (
                    <div className="debug-code-container">
                      <div className="debug-code-header">
                        <span>raw_cv_text.txt</span>
                        <button
                          type="button"
                          className="copy-btn"
                          onClick={() => navigator.clipboard.writeText(debugData.raw_cv_text || "")}
                        >
                          <i className="bi bi-clipboard" /> Copy
                        </button>
                      </div>
                      <pre className="debug-pre">
                        {debugData.raw_cv_text ? debugData.raw_cv_text : "No raw CV text parsed. Please upload a CV first in Step 2."}
                      </pre>
                    </div>
                  )}

                  {activeTab === "parsed" && (
                    <div className="debug-code-container">
                      <div className="debug-code-header">
                        <span>parsed_cv_json.json</span>
                        <button
                          type="button"
                          className="copy-btn"
                          onClick={() => navigator.clipboard.writeText(JSON.stringify(debugData.parsed_cv_json, null, 2))}
                        >
                          <i className="bi bi-clipboard" /> Copy
                        </button>
                      </div>
                      <pre className="debug-pre">
                        {debugData.parsed_cv_json ? JSON.stringify(debugData.parsed_cv_json, null, 2) : "No parsed CV telemetry. Please upload a CV first in Step 2."}
                      </pre>
                    </div>
                  )}

                  {activeTab === "context" && (
                    <div className="debug-code-container">
                      <div className="debug-code-header">
                        <span>llm_context_payload.json</span>
                        <button
                          type="button"
                          className="copy-btn"
                          onClick={() => navigator.clipboard.writeText(JSON.stringify(debugData.llm_context, null, 2))}
                        >
                          <i className="bi bi-clipboard" /> Copy
                        </button>
                      </div>
                      <pre className="debug-pre">
                        {debugData.llm_context ? JSON.stringify(debugData.llm_context, null, 2) : "No LLM context structured. Complete onboarding first."}
                      </pre>
                    </div>
                  )}
                </div>
              </Card>
            )}
          </div>
        )}
      </div>
    </>
  );
}
