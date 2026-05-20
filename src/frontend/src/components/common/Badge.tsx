import { ReactNode } from "react";
import "./Badge.css";

interface BadgeProps {
  children: ReactNode;
  variant?: "neutral" | "primary" | "success" | "warning" | "danger";
  className?: string;
}

export function Badge({ children, variant = "neutral", className = "" }: BadgeProps) {
  return <span className={`badge badge-${variant} ${className}`}>{children}</span>;
}
