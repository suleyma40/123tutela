import React from "react";

import { C } from "./theme";

export const Badge = ({ children, color = C.primary, style = {} }) => (
  <span
    style={{
      display: "inline-flex",
      alignItems: "center",
      padding: "4px 10px",
      borderRadius: 999,
      fontSize: 11,
      fontWeight: 700,
      letterSpacing: 0.4,
      background: `${color}15`,
      color,
      ...style,
    }}
  >
    {children}
  </span>
);

export const Button = ({
  children,
  variant = "primary",
  onClick,
  size = "md",
  disabled = false,
  icon: Icon,
  style = {},
  type = "button",
}) => {
  const variants = {
    primary: { background: C.primary, color: "#fff", border: "none" },
    secondary: { background: C.primaryLight, color: C.primary, border: "none" },
    outline: { background: "transparent", color: C.primary, border: `1px solid ${C.border}` },
    ghost: { background: "transparent", color: C.textMuted, border: "none" },
    dark: { background: C.bgDark, color: "#fff", border: "none" },
    danger: { background: "#FEE2E2", color: C.danger, border: "1px solid #FECACA" },
  };

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className="btn-transition"
      style={{
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        gap: 8,
        borderRadius: size === "lg" ? 14 : 12,
        padding: size === "lg" ? "15px 26px" : "11px 18px",
        fontSize: size === "lg" ? 15 : 14,
        fontWeight: 700,
        cursor: disabled ? "not-allowed" : "pointer",
        opacity: disabled ? 0.6 : 1,
        fontFamily: "'DM Sans', sans-serif",
        ...variants[variant],
        ...style,
      }}
    >
      {children}
      {Icon && <Icon size={size === "lg" ? 18 : 16} />}
    </button>
  );
};

export const Field = ({ label, children }) => (
  <label style={{ display: "block" }}>
    <span style={{ display: "block", fontSize: 13, fontWeight: 700, color: C.text, marginBottom: 8 }}>{label}</span>
    {children}
  </label>
);

export const TextInput = (props) => (
  <input
    {...props}
    style={{
      width: "100%",
      padding: "14px 16px",
      borderRadius: 12,
      border: `1px solid ${C.border}`,
      outline: "none",
      fontSize: 14,
      fontFamily: "'DM Sans', sans-serif",
      ...props.style,
    }}
  />
);

export const TextArea = (props) => (
  <textarea
    {...props}
    style={{
      width: "100%",
      minHeight: 160,
      padding: "16px",
      borderRadius: 16,
      border: `1px solid ${C.border}`,
      outline: "none",
      fontSize: 14,
      resize: "vertical",
      fontFamily: "'DM Sans', sans-serif",
      ...props.style,
    }}
  />
);

export const SessionCard = ({ title, subtitle, children }) => (
  <div className="glass-card" style={{ padding: 28 }}>
    <div style={{ marginBottom: 20 }}>
      <h3 style={{ fontSize: 24, fontWeight: 800, marginBottom: 8, color: C.text }}>{title}</h3>
      <p style={{ color: C.textMuted, lineHeight: 1.6 }}>{subtitle}</p>
    </div>
    {children}
  </div>
);
