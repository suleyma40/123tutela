import React, { useState } from "react";
import { ArrowLeft, CheckCircle2, Scale, ShieldCheck, Zap } from "lucide-react";

import { Button, Field, TextInput } from "../ui";
import { C } from "../theme";

const sellingPoints = [
  "Analisis inicial sin costo para definir la ruta correcta.",
  "Documento listo para revisar y pagar en el mismo flujo.",
  "Panel del cliente con estado, soporte y trazabilidad.",
];

const statCards = [
  { label: "Promesa", value: "Documento en minutos", icon: Zap },
  { label: "Cobertura", value: "Colombia", icon: Scale },
  { label: "Seguimiento", value: "Siempre visible", icon: ShieldCheck },
];

export default function AuthViewVision({
  title,
  subtitle,
  fields,
  onSubmit,
  secondaryAction,
  secondaryLabel,
  secondaryText,
  onBack,
  loading,
  error,
}) {
  const [formData, setFormData] = useState(fields.reduce((acc, field) => ({ ...acc, [field.name]: "" }), {}));

  const handleChange = (name, value) => {
    setFormData((current) => ({ ...current, [name]: value }));
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "linear-gradient(180deg, #F6F8FC 0%, #EEF3FB 100%)",
        padding: "28px 20px",
        display: "grid",
        placeItems: "center",
      }}
    >
      <div
        className="glass-card"
        style={{
          width: "min(1120px, 100%)",
          overflow: "hidden",
          display: "grid",
          gridTemplateColumns: "1fr 460px",
          background: "#fff",
        }}
      >
        <section
          style={{
            padding: "42px 40px",
            background: "radial-gradient(circle at top left, rgba(0,102,255,0.18), transparent 34%), #08172E",
            color: "#fff",
            display: "grid",
            gap: 28,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <div
              style={{
                width: 44,
                height: 44,
                borderRadius: 14,
                background: "linear-gradient(135deg, #0D68FF 0%, #19B7FF 100%)",
                display: "grid",
                placeItems: "center",
              }}
            >
              <Scale size={22} />
            </div>
            <strong style={{ fontSize: 28 }}>
              123<span style={{ color: "#2E90FA" }}>tutela</span>
            </strong>
          </div>

          <div style={{ maxWidth: 520 }}>
            <div
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: 8,
                padding: "8px 14px",
                borderRadius: 999,
                background: "rgba(255,255,255,0.08)",
                color: "#A8F4D6",
                fontSize: 12,
                fontWeight: 700,
                letterSpacing: 0.3,
              }}
            >
              <CheckCircle2 size={15} />
              Analisis, documento y radicacion con trazabilidad
            </div>
            <h1
              style={{
                marginTop: 20,
                fontSize: 56,
                lineHeight: 1,
                fontFamily: "'Playfair Display', serif",
                fontWeight: 700,
              }}
            >
              Tu defensa legal,
              <br />
              clara desde el primer paso.
            </h1>
            <p style={{ marginTop: 18, color: "rgba(255,255,255,0.74)", fontSize: 18, lineHeight: 1.7 }}>
              El cliente entra, analiza su caso, decide que pagar y sigue todo desde su panel. Sin saltos raros y sin perder contexto.
            </p>
          </div>

          <div style={{ display: "grid", gap: 12 }}>
            {sellingPoints.map((point) => (
              <div
                key={point}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 12,
                  padding: "14px 16px",
                  borderRadius: 16,
                  background: "rgba(255,255,255,0.06)",
                  border: "1px solid rgba(255,255,255,0.08)",
                }}
              >
                <CheckCircle2 size={18} style={{ color: "#36D399", flexShrink: 0 }} />
                <span style={{ color: "rgba(255,255,255,0.88)" }}>{point}</span>
              </div>
            ))}
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 14 }}>
            {statCards.map((item) => (
              <div
                key={item.label}
                style={{
                  padding: 18,
                  borderRadius: 18,
                  background: "rgba(255,255,255,0.06)",
                  border: "1px solid rgba(255,255,255,0.08)",
                }}
              >
                <item.icon size={18} style={{ color: "#66B6FF" }} />
                <div style={{ marginTop: 18, fontSize: 28, fontWeight: 800 }}>{item.value}</div>
                <div style={{ color: "rgba(255,255,255,0.6)", fontSize: 13 }}>{item.label}</div>
              </div>
            ))}
          </div>
        </section>

        <section style={{ padding: "42px 36px", display: "grid", alignContent: "center" }}>
          <div style={{ marginBottom: 26 }}>
            <button
              type="button"
              onClick={onBack}
              style={{
                border: "none",
                background: "transparent",
                color: C.textMuted,
                display: "inline-flex",
                alignItems: "center",
                gap: 8,
                cursor: "pointer",
                fontWeight: 700,
                marginBottom: 18,
              }}
            >
              <ArrowLeft size={16} />
              Volver al inicio
            </button>
            <h2 style={{ fontSize: 38, lineHeight: 1.05, color: C.text, fontWeight: 800 }}>{title}</h2>
            <p style={{ marginTop: 12, color: C.textMuted, lineHeight: 1.7 }}>{subtitle}</p>
          </div>

          <div style={{ display: "grid", gap: 16 }}>
            {fields.map((field) => (
              <Field key={field.name} label={field.label}>
                <TextInput
                  type={field.type}
                  placeholder={field.placeholder}
                  value={formData[field.name]}
                  onChange={(event) => handleChange(field.name, event.target.value)}
                  style={{ padding: "16px 18px", borderRadius: 16, background: "#F8FAFD" }}
                />
              </Field>
            ))}
          </div>

          {error && (
            <p
              style={{
                marginTop: 18,
                color: C.danger,
                background: "#FEF2F2",
                border: "1px solid #FECACA",
                padding: "12px 14px",
                borderRadius: 14,
                fontSize: 14,
              }}
            >
              {error}
            </p>
          )}

          <div style={{ display: "grid", gap: 14, marginTop: 22 }}>
            <Button size="lg" onClick={() => onSubmit(formData)} disabled={loading} style={{ width: "100%" }}>
              {loading ? "Procesando..." : title}
            </Button>
            <p style={{ color: C.textMuted, fontSize: 14, textAlign: "center" }}>
              {secondaryText}{" "}
              <span style={{ color: C.primary, fontWeight: 800, cursor: "pointer" }} onClick={secondaryAction}>
                {secondaryLabel}
              </span>
            </p>
          </div>
        </section>
      </div>
    </div>
  );
}
