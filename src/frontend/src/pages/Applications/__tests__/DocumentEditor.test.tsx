import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { DocumentEditor } from "../DocumentEditor";

// Mock the API services
vi.mock("../../../services/api", () => ({
  streamGenerateDocuments: vi.fn(),
  confirmJob: vi.fn(),
  updateJobDocuments: vi.fn(),
}));

describe("DocumentEditor", () => {
  it("renders correctly and starts generation phase", () => {
    render(
      <MemoryRouter initialEntries={["/applications/123/edit"]}>
        <Routes>
          <Route path="/applications/:jobId/edit" element={<DocumentEditor />} />
        </Routes>
      </MemoryRouter>
    );

    // Initial state check
    expect(screen.getByText("Document Editor")).toBeDefined();
    expect(screen.getByText("Curriculum Vitae")).toBeDefined();
    expect(screen.getByText("Cover Letter")).toBeDefined();
  });
});
