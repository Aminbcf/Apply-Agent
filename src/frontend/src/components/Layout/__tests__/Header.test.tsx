import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { Header } from "../Header";

describe("Header Component", () => {
  it("renders title correctly", () => {
    render(<Header title="Dashboard" />);
    expect(screen.getByText("Dashboard")).toBeDefined();
  });

  it("renders subtitle if provided", () => {
    render(<Header title="Dashboard" subtitle="Overview" />);
    expect(screen.getByText("Overview")).toBeDefined();
  });

  it("renders actions if provided", () => {
    render(
      <Header
        title="Dashboard"
        actions={<button>Action</button>}
      />
    );
    expect(screen.getByText("Action")).toBeDefined();
  });
});
