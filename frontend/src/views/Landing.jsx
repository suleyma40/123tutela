import React from "react";
import { ArrowRight, Heart, Landmark, Scale, Shield, ShoppingCart, Zap } from "lucide-react";

import { Badge, Button } from "../ui";
import { C } from "../theme";

const categories = [
  { title: "Salud / EPS", desc: "Tratamientos, citas y barreras de acceso.", icon: Heart, color: "#EF4444" },
  { title: "Laboral", desc: "Despido, salarios y estabilidad reforzada.", icon: Landmark, color: "#F59E0B" },
  { title: "Servicios Públicos", desc: "Cortes, cobros excesivos y reclamaciones.", icon: Zap, color: "#06B6D4" },
  { title: "Consumidor", desc: "Garantías, devoluciones y fallas de servicio.", icon: ShoppingCart, color: "#10B981" },
  { title: "Datos Personales", desc: "Habeas data y corrección de información.", icon: Shield, color: "#EC4899" },
];

export default function Landing({ onStart, onLogin }) {
  return (
    <div style={{ minHeight: "100vh", background: C.bgDark, color: "#fff" }}>
      <nav
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          padding: "28px 40px",
          position: "sticky",
          top: 0,
          backdropFilter: "blur(12px)",
          background: "rgba(11, 22, 40, 0.86)",
          borderBottom: `1px solid ${C.borderDark}`,
          zIndex: 20,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div style={{ width: 38, height: 38, borderRadius: 10, background: C.primary, display: "grid", placeItems: "center" }}>
            <Scale size={20} />
          </div>
          <strong style={{ fontSize: 24 }}>123<span style={{ color: C.primary }}>tutela</span></strong>
        </div>
        <div style={{ display: "flex", gap: 12 }}>
          <Button variant="outline" onClick={onLogin} style={{ borderColor: "rgba(255,255,255,0.18)", color: "#fff" }}>
            Iniciar sesión
          </Button>
          <Button onClick={onStart}>Crear cuenta</Button>
        </div>
      </nav>

      <section style={{ maxWidth: 1180, margin: "0 auto", padding: "90px 40px 70px" }}>
        <div style={{ display: "grid", gridTemplateColumns: "1.1fr 0.9fr", gap: 48, alignItems: "center" }}>
          <div>
            <Badge color={C.accent}>Motor jurídico colombiano + automatización operativa</Badge>
            <h1 style={{ fontSize: 58, lineHeight: 1.05, margin: "24px 0", fontWeight: 800, fontFamily: "'Playfair Display', serif" }}>
              Trámites legales claros,
              <br />
              rápidos y con destino sugerido.
            </h1>
            <p style={{ color: "rgba(255,255,255,0.72)", fontSize: 18, lineHeight: 1.7, maxWidth: 560 }}>
              123tutela analiza el caso, identifica normas aplicables, recomienda la acción más fuerte y deja listo el borrador para radicación.
            </p>
            <div style={{ display: "flex", gap: 14, marginTop: 34 }}>
              <Button size="lg" onClick={onStart} icon={ArrowRight}>
                Empezar ahora
              </Button>
              <Button
                variant="ghost"
                size="lg"
                style={{ background: "rgba(255,255,255,0.06)", color: "#fff", border: "1px solid rgba(255,255,255,0.1)" }}
                onClick={onLogin}
              >
                Ya tengo cuenta
              </Button>
            </div>
          </div>

          <div className="glass-card" style={{ padding: 28, background: "rgba(255,255,255,0.96)" }}>
            <Badge color={C.success}>Vista del resultado</Badge>
            <div style={{ marginTop: 18, display: "grid", gap: 16 }}>
              <div style={{ padding: 18, borderRadius: 16, background: "#F0FDF4", border: "1px solid #BBF7D0" }}>
                <div style={{ fontSize: 12, fontWeight: 800, color: C.success, marginBottom: 6 }}>ACCIÓN SUGERIDA</div>
                <div style={{ fontSize: 20, fontWeight: 800, color: C.text }}>Acción de tutela</div>
              </div>
              <div style={{ padding: 18, borderRadius: 16, background: C.primaryLight, border: `1px solid ${C.primary}22` }}>
                <div style={{ fontSize: 12, fontWeight: 800, color: C.primary, marginBottom: 6 }}>FUNDAMENTO PRINCIPAL</div>
                <div style={{ color: C.text, lineHeight: 1.6 }}>Derecho fundamental a la salud, Art. 49 de la Constitución y Ley 1751 de 2015.</div>
              </div>
              <div style={{ padding: 18, borderRadius: 16, background: "#FFF7ED", border: "1px solid #FED7AA" }}>
                <div style={{ fontSize: 12, fontWeight: 800, color: "#C2410C", marginBottom: 6 }}>DESTINO OPERATIVO</div>
                <div style={{ color: C.text, lineHeight: 1.6 }}>Portal Tutela en Línea o juzgado de reparto sugerido según ciudad y departamento.</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section style={{ maxWidth: 1180, margin: "0 auto", padding: "0 40px 90px" }}>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: 18 }}>
          {categories.map((item) => (
            <div key={item.title} className="glass-card" style={{ padding: 20, background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)" }}>
              <div style={{ width: 48, height: 48, borderRadius: 14, background: `${item.color}1f`, display: "grid", placeItems: "center", marginBottom: 16 }}>
                <item.icon size={22} style={{ color: item.color }} />
              </div>
              <h3 style={{ fontSize: 18, fontWeight: 800, marginBottom: 8 }}>{item.title}</h3>
              <p style={{ color: "rgba(255,255,255,0.64)", lineHeight: 1.6, fontSize: 14 }}>{item.desc}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
