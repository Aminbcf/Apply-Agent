import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { Button } from "../Button";

describe("Button Component", () => {
  it("renders children correctly", () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText("Click me")).toBeDefined();
  });

  it("handles click events", () => {
    const handleClick = vi.fn();
    render(<Button onClick={handleClick}>Click me</Button>);
    fireEvent.click(screen.getByText("Click me"));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it("applies variant and size classes", () => {
    render(<Button variant="danger" size="lg">Delete</Button>);
    const button = screen.getByRole("button");
    expect(button.className).toContain("btn-danger");
    expect(button.className).toContain("btn-lg");
  });

  it("shows loading state", () => {
    render(<Button loading>Submit</Button>);
    const button = screen.getByRole("button");
    expect(button.className).toContain("btn-loading");
    expect(button.querySelector(".btn-spinner")).toBeDefined();
  });

  it("disables button when loading", () => {
    render(<Button loading>Submit</Button>);
    const button = screen.getByRole("button");
    expect((button as HTMLButtonElement).disabled).toBe(true);
  });
});
