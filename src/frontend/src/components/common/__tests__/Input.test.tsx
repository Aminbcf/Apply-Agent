import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { Input } from "../Input";

describe("Input Component", () => {
  it("renders correctly", () => {
    render(<Input placeholder="Enter text" />);
    expect(screen.getByPlaceholderText("Enter text")).toBeDefined();
  });

  it("renders with a label", () => {
    render(<Input label="Username" />);
    expect(screen.getByLabelText("Username")).toBeDefined();
  });

  it("shows an error message and applies error class", () => {
    render(<Input label="Email" error="Invalid email" />);
    const errorMsg = screen.getByText("Invalid email");
    expect(errorMsg).toBeDefined();
    
    const input = screen.getByLabelText("Email");
    expect(input.className).toContain("has-error");
  });

  it("renders with an icon", () => {
    render(<Input icon="bi-search" />);
    const icon = document.querySelector(".bi-search");
    expect(icon).toBeDefined();
  });

  it("handles typing", () => {
    render(<Input label="Test" />);
    const input = screen.getByLabelText("Test") as HTMLInputElement;
    fireEvent.change(input, { target: { value: "hello" } });
    expect(input.value).toBe("hello");
  });
});
