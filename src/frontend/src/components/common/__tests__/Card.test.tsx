import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { Card } from "../Card";

describe("Card Component", () => {
  it("renders content", () => {
    render(<Card>Card content</Card>);
    expect(screen.getByText("Card content")).toBeDefined();
  });

  it("applies padding class", () => {
    render(<Card padding="lg">Padded</Card>);
    const card = screen.getByText("Padded");
    expect(card.className).toContain("card-p-lg");
  });

  it("applies custom classes", () => {
    render(<Card className="my-card">Custom</Card>);
    const card = screen.getByText("Custom");
    expect(card.className).toContain("my-card");
  });

  it("handles click if provided and applies interactive class", () => {
    const handleClick = vi.fn();
    render(<Card onClick={handleClick} interactive>Clickable</Card>);
    const card = screen.getByText("Clickable");
    expect(card.className).toContain("card-interactive");
    fireEvent.click(card);
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it("triggers onClick when Enter or Space is pressed when interactive", () => {
    const handleClick = vi.fn();
    render(<Card onClick={handleClick}>Keyboard Interactive</Card>);
    const card = screen.getByText("Keyboard Interactive");
    
    // Pressing a random key should not trigger onClick
    fireEvent.keyDown(card, { key: "Tab" });
    expect(handleClick).not.toHaveBeenCalled();

    // Pressing Enter should trigger onClick
    fireEvent.keyDown(card, { key: "Enter" });
    expect(handleClick).toHaveBeenCalledTimes(1);

    // Pressing Space should trigger onClick
    fireEvent.keyDown(card, { key: " " });
    expect(handleClick).toHaveBeenCalledTimes(2);
  });
});

