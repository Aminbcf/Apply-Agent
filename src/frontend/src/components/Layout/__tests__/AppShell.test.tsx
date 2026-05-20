import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { MemoryRouter } from "react-router-dom";
import { AppShell } from "../AppShell";

describe("AppShell Component", () => {
  it("renders the sidebar and a main container", () => {
    render(
      <MemoryRouter>
        <AppShell />
      </MemoryRouter>
    );
    
    // Sidebar should be present
    expect(screen.getByRole("navigation")).toBeDefined();
    
    // Main container should be present
    expect(document.getElementById("main-content")).toBeDefined();
  });
});
