import React, { useState } from "react";

import { Button, Field, SessionCard, TextInput } from "../ui";
import { C } from "../theme";

export default function AuthView({
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

  return (
    <div style={{ minHeight: "100vh", background: C.bg, display: "grid", placeItems: "center", padding: 24 }}>
      <SessionCard title={title} subtitle={subtitle}>
        <div style={{ display: "grid", gap: 16 }}>
          {fields.map((field) => (
            <Field key={field.name} label={field.label}>
              <TextInput
                type={field.type}
                placeholder={field.placeholder}
                value={formData[field.name]}
                onChange={(event) => setFormData((current) => ({ ...current, [field.name]: event.target.value }))}
              />
            </Field>
          ))}
        </div>
        {error && <p style={{ marginTop: 16, color: C.danger, fontSize: 14 }}>{error}</p>}
        <div style={{ display: "grid", gap: 12, marginTop: 22 }}>
          <Button size="lg" onClick={() => onSubmit(formData)} disabled={loading} style={{ width: "100%" }}>
            {loading ? "Procesando..." : title}
          </Button>
          <Button variant="ghost" onClick={onBack}>
            Volver al inicio
          </Button>
        </div>
        <p style={{ marginTop: 18, color: C.textMuted, fontSize: 14 }}>
          {secondaryText}{" "}
          <span style={{ color: C.primary, fontWeight: 800, cursor: "pointer" }} onClick={secondaryAction}>
            {secondaryLabel}
          </span>
        </p>
      </SessionCard>
    </div>
  );
}
