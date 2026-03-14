import React from "react";

import { Button } from "../ui";
import { C } from "../theme";

export default function DocumentModal({ caseItem, onClose }) {
  if (!caseItem) {
    return null;
  }

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(11, 22, 40, 0.6)",
        display: "grid",
        placeItems: "center",
        zIndex: 100,
        padding: 24,
      }}
      onClick={onClose}
    >
      <div
        className="glass-card"
        style={{ width: "min(920px, 100%)", maxHeight: "82vh", overflowY: "auto", padding: 28 }}
        onClick={(event) => event.stopPropagation()}
      >
        <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "center", marginBottom: 18 }}>
          <div>
            <h3 style={{ fontSize: 26, fontWeight: 800, color: C.text }}>Borrador generado</h3>
            <p style={{ color: C.textMuted, marginTop: 4 }}>{caseItem.recommended_action}</p>
          </div>
          <Button variant="ghost" onClick={onClose}>Cerrar</Button>
        </div>
        <pre
          style={{
            whiteSpace: "pre-wrap",
            lineHeight: 1.8,
            color: C.text,
            background: "#F8FAFC",
            padding: 20,
            borderRadius: 18,
            border: `1px solid ${C.border}`,
            fontFamily: "'DM Sans', sans-serif",
            fontSize: 14,
          }}
        >
          {caseItem.generated_document}
        </pre>
      </div>
    </div>
  );
}
