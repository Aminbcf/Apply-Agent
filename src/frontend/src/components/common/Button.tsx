import { ButtonHTMLAttributes, forwardRef } from "react";
import "./Button.css";

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "outline" | "ghost" | "danger";
  size?: "sm" | "md" | "lg";
  icon?: string;
  loading?: boolean;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className = "",
      variant = "primary",
      size = "md",
      icon,
      loading,
      children,
      disabled,
      ...props
    },
    ref
  ) => {
    const classes = [
      "btn",
      `btn-${variant}`,
      `btn-${size}`,
      loading ? "btn-loading" : "",
      className,
    ]
      .filter(Boolean)
      .join(" ");

    return (
      <button
        ref={ref}
        className={classes}
        disabled={disabled || loading}
        {...props}
      >
        {loading && <i className="bi bi-arrow-repeat btn-spinner" aria-hidden="true" />}
        {!loading && icon && <i className={`bi ${icon}`} aria-hidden="true" />}
        {children && <span>{children}</span>}
      </button>
    );
  }
);

Button.displayName = "Button";
