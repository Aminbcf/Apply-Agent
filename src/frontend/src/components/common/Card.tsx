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

  const handleKeyDown = (e: KeyboardEvent<HTMLButtonElement>) => {
    if (onClick && (e.key === "Enter" || e.key === " ")) {
      e.preventDefault();
      onClick();
    }
  };

  if (isInteractive) {
    return (
      <button
        type="button"
        className={classes}
        onClick={onClick}
        onKeyDown={handleKeyDown}
        style={style}
      >
        {children}
      </button>
    );
  }

  return (
    <div className={classes} style={style}>
      {children}
    </div>
  );
}
