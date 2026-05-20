import { InputHTMLAttributes, forwardRef } from "react";
import "./Input.css";

export type InputProps = Readonly<InputHTMLAttributes<HTMLInputElement> & {
  label?: string;
  error?: string;
  icon?: string;
  containerClassName?: string;
}>;

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className = "", label, error, icon, id, containerClassName = "", ...props }, ref) => {
    const inputId = id || (label ? label.toLowerCase().replace(/\s+/g, "-") : undefined);

    return (
      <div className={`input-wrapper ${containerClassName}`}>
        {label && (
          <label htmlFor={inputId} className="input-label">
            {label}
          </label>
        )}
        <div className="input-container">
          {icon && <i className={`bi ${icon} input-icon`} aria-hidden="true" />}
          <input
            ref={ref}
            id={inputId}
            className={`input-field ${icon ? "has-icon" : ""} ${error ? "has-error" : ""} ${className}`.trim()}
            {...props}
          />
        </div>
        {error && <span className="input-error-text">{error}</span>}
      </div>
    );
  }
);

Input.displayName = "Input";
