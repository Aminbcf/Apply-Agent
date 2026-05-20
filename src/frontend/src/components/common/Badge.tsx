import { ReactNode } from "react";
import "./Badge.css";

export type BadgeProps = Readonly<{
  children: ReactNode;
  variant?: "neutral" | "primary" | "secondary" | "success" | "warning" | "danger";
  className?: string;
}>;

export function Badge({ children, variant = "neutral", className = "" }: BadgeProps) {
  return <span className={`badge badge-${variant} ${className}`}>{children}</span>;
}
