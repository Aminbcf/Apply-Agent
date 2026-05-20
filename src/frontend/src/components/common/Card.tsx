import { ReactNode, CSSProperties, KeyboardEvent } from "react";
import "./Card.css";

export type CardProps = Readonly<{
  children: ReactNode;
  className?: string;
  padding?: "none" | "sm" | "md" | "lg";
  interactive?: boolean;
  onClick?: () => void;
  style?: CSSProperties;
}>;

export function Card({
  children,
  className = "",
  padding = "md",
  interactive = false,
  onClick,
  style,
}: CardProps) {
  const isInteractive = interactive || !!onClick;

  const classes = [
    "card",
    `card-p-${padding}`,
    isInteractive ? "card-interactive" : "",
    className,
  ]
    .filter(Boolean)
    .join(" ");

  const handleKeyDown = (e: KeyboardEvent<HTMLDivElement>) => {
    if (onClick && (e.key === "Enter" || e.key === " ")) {
      e.preventDefault();
      onClick();
    }
  };

  return (
    <div
      className={classes}
      onClick={onClick}
      onKeyDown={isInteractive ? handleKeyDown : undefined}
      role={isInteractive ? "button" : undefined}
      tabIndex={isInteractive ? 0 : undefined}
      style={style}
    >
      {children}
    </div>
  );
}
