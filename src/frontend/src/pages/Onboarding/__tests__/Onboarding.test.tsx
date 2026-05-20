import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { Onboarding } from "../Onboarding";
import * as api from "../../../services/api";

vi.mock("../../../services/api", () => ({
  getProfile: vi.fn(),
  saveProfile: vi.fn(),
  uploadOnboardingCv: vi.fn(),
}));

describe("Onboarding Component", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders loading state initially", () => {
    vi.mocked(api.getProfile).mockReturnValue(new Promise(() => {})); // Never resolves
    render(<Onboarding />);
    expect(screen.getByText("Loading your profile...")).toBeDefined();
  });

  it("renders form after profile loads", async () => {
    vi.mocked(api.getProfile).mockResolvedValue({
      full_name: "Jane Doe",
      email: "jane@example.com",
      phone: "123456789",
      location: "Paris",
      career_goals: "Build neat apps",
      experience: [],
      education: [],
      projects: [],
      skills: {},
      certifications: [],
      languages: [],
      achievements: [],
    });

    render(<Onboarding />);

    await waitFor(() => {
      expect(screen.queryByText("Loading your profile...")).toBeNull();
    });

    expect(screen.getByLabelText("Full Name")).toBeDefined();
    expect((screen.getByLabelText("Full Name") as HTMLInputElement).value).toBe("Jane Doe");
    expect((screen.getByLabelText("Email Address") as HTMLInputElement).value).toBe("jane@example.com");
  });

  it("handles input changes and submission", async () => {
    vi.mocked(api.getProfile).mockResolvedValue({
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
    });

    vi.mocked(api.saveProfile).mockResolvedValue({} as any);

    render(<Onboarding />);

    await waitFor(() => {
      expect(screen.queryByText("Loading your profile...")).toBeNull();
    });

    const nameInput = screen.getByLabelText("Full Name") as HTMLInputElement;
    const emailInput = screen.getByLabelText("Email Address") as HTMLInputElement;
    const saveButton = screen.getByText("Save Profile & Complete Onboarding");

    fireEvent.change(nameInput, { target: { value: "John Smith" } });
    fireEvent.change(emailInput, { target: { value: "john@example.com" } });
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(api.saveProfile).toHaveBeenCalledWith(
        expect.objectContaining({
          full_name: "John Smith",
          email: "john@example.com",
        })
      );
      expect(screen.getByText("Profile saved successfully! Onboarding updated.")).toBeDefined();
    });
  });
});
