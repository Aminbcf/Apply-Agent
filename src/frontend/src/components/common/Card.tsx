import { ReactNode } from "react";
import "./Card.css";

interface CardProps {
  children: ReactNode;
  className?: string;
  padding?: "none" | "sm" | "md" | "lg";
  interactive?: boolean;
  onClick?: () => void;
}

export function Card({
  children,
  className = "",
  padding = "md",
  interactive = false,
  onClick,
}: CardProps) {
  const classes = [
    "card",
    `card-p-${padding}`,
    interactive ? "card-interactive" : "",
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div
      className={classes}
      onClick={onClick}
      role={interactive || onClick ? "button" : undefined}
      tabIndex={interactive || onClick ? 0 : undefined}
    >
      {children}
    </div>
  );
}
