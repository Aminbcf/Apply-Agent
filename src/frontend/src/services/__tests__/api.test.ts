import { describe, it, expect, vi, beforeEach } from "vitest";
import {
  getDashboardStats,
  getOnboardingStatus,
  getProfile,
  saveProfile,
  UserProfileData,
} from "../api";

describe("Frontend API Client", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ data: "test" }),
      })
    );
  });

  it("getDashboardStats performs GET request", async () => {
    await getDashboardStats();
    expect(globalThis.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/dashboard/stats"),
      expect.any(Object)
    );
  });

  it("getOnboardingStatus performs GET request", async () => {
    await getOnboardingStatus();
    expect(globalThis.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/onboarding/status"),
      expect.any(Object)
    );
  });

  it("getProfile performs GET request", async () => {
    await getProfile();
    expect(globalThis.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/profile/"),
      expect.any(Object)
    );
  });

  it("saveProfile performs POST request with body", async () => {
    const mockProfile: UserProfileData = {
      full_name: "John",
      email: null,
      phone: null,
      location: null,
      career_goals: null,
      experience: [],
      education: [],
      projects: [],
      skills: {},
      certifications: [],
      languages: [],
      achievements: [],
    };
    await saveProfile(mockProfile);
    expect(globalThis.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/profile/"),
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify(mockProfile),
      })
    );
  });
});
