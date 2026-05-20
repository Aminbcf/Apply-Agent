import { ReactNode } from "react";
import "./Header.css";

export type HeaderProps = Readonly<{
  title: string;
  subtitle?: string;
  actions?: ReactNode;
}>;

export function Header({ title, subtitle, actions }: HeaderProps) {
  return (
    <header className="page-header">
      <div className="page-header-title">
        <h1 className="page-title">{title}</h1>
        {subtitle && <p className="page-subtitle">{subtitle}</p>}
      </div>
      {actions && <div className="page-header-actions">{actions}</div>}
    </header>
  );
}
