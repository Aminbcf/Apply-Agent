import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { Badge } from "../Badge";

describe("Badge Component", () => {
  it("renders children correctly", () => {
    render(<Badge>New Item</Badge>);
    expect(screen.getByText("New Item")).toBeDefined();
  });

  it("applies the correct variant class", () => {
    render(<Badge variant="success">Success</Badge>);
    const badge = screen.getByText("Success");
    expect(badge.className).toContain("badge-success");
  });

  it("applies custom className", () => {
    render(<Badge className="custom-class">Custom</Badge>);
    const badge = screen.getByText("Custom");
    expect(badge.className).toContain("custom-class");
  });

  it("defaults to neutral variant", () => {
    render(<Badge>Default</Badge>);
    const badge = screen.getByText("Default");
    expect(badge.className).toContain("badge-neutral");
  });
});
