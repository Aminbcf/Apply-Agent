import { useEffect, useState, FormEvent } from "react";
import { Header } from "../../components/Layout/Header";
import { Card } from "../../components/common/Card";
import { Input } from "../../components/common/Input";
import { Button } from "../../components/common/Button";
import { Badge } from "../../components/common/Badge";
import { getProfile, saveProfile, UserProfileData } from "../../services/api";
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
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

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

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setMessage(null);

    try {
      await saveProfile(profile);
      setMessage({ type: "success", text: "Profile saved successfully! Onboarding updated." });
    } catch (err) {
      console.error("Failed to save profile", err);
      setMessage({ type: "error", text: "Failed to save profile. Please try again." });
    } finally {
      setSaving(false);
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
  const step2Complete = true; // Placeholder for experience/skills
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
                <i className="bi bi-info-circle-fill text-primary" />
                <p>
                  <strong>CV Upload & CV Parsing coming soon!</strong>
                  <br />
                  Soon, you will be able to upload a PDF/Word CV and we will automatically parse your full experience, education, and skills.
                </p>
              </div>
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
      </div>
    </>
  );
}
