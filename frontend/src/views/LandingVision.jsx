import React from "react";
import { ArrowRight, CheckCircle2, Heart, Landmark, Scale, Shield, ShoppingCart, Zap } from "lucide-react";

import { Badge, Button } from "../ui";
import { C } from "../theme";

const categories = [
  { title: "Salud / EPS", desc: "Tutelas, peticiones y desacatos por tratamientos, citas o medicamentos.", icon: Heart, color: "#F97316" },
  { title: "Laboral", desc: "Despido, salarios, acoso, estabilidad reforzada y minimo vital.", icon: Landmark, color: "#F59E0B" },
  { title: "Servicios", desc: "Cobros, cortes y reclamaciones por servicios publicos.", icon: Zap, color: "#14B8A6" },
  { title: "Consumidor", desc: "Garantias, devoluciones y publicidad enganosa.", icon: ShoppingCart, color: "#10B981" },
  { title: "Datos", desc: "Habeas data, correccion y eliminacion de informacion.", icon: Shield, color: "#EC4899" },
];

const steps = [
  {
    index: "01",
    title: "Describe tu problema",
    description: "Nos cuentas que paso y subes soportes si los tienes.",
  },
  {
    index: "02",
    title: "La IA analiza tu caso",
    description: "Identifica el derecho vulnerado y te entrega un informe inicial gratis.",
  },
  {
    index: "03",
    title: "Eliges que pagar",
    description: "Documento o documento mas radicacion. Todo queda visible en tu panel.",
  },
];

const priceHighlights = [
  "Analisis detallado del caso sin costo.",
  "Documento listo para pago individual por tipo de tramite.",
  "Radicacion automatizada cuando el cliente la elige.",
];

export default function LandingVision({ onStart, onLogin }) {
  return (
    <div style={{ minHeight: "100vh", background: "#F5F7FB", color: C.text }}>
      <nav
        style={{
          position: "sticky",
          top: 0,
          zIndex: 50,
          backdropFilter: "blur(18px)",
          background: "rgba(245,247,251,0.82)",
          borderBottom: `1px solid ${C.border}`,
        }}
      >
        <div
          style={{
            maxWidth: 1200,
            margin: "0 auto",
            padding: "22px 24px",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: 18,
            flexWrap: "wrap",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <div
              style={{
                width: 40,
                height: 40,
                borderRadius: 14,
                background: "linear-gradient(135deg, #0D68FF 0%, #19B7FF 100%)",
                display: "grid",
                placeItems: "center",
                color: "#fff",
              }}
            >
              <Scale size={20} />
            </div>
            <strong style={{ fontSize: 30 }}>
              123<span style={{ color: C.primary }}>tutela</span>
            </strong>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: 18, color: C.textMuted, fontWeight: 600 }}>
            <a href="#como-funciona" style={{ color: "inherit", textDecoration: "none" }}>
              Como funciona
            </a>
            <a href="#categorias" style={{ color: "inherit", textDecoration: "none" }}>
              Categorias
            </a>
            <a href="#precios" style={{ color: "inherit", textDecoration: "none" }}>
              Precios
            </a>
            <Button variant="outline" onClick={onLogin}>
              Iniciar sesion
            </Button>
            <Button onClick={onStart}>Empezar gratis</Button>
          </div>
        </div>
      </nav>

      <section style={{ maxWidth: 1200, margin: "0 auto", padding: "56px 24px 42px" }}>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1.05fr 0.95fr",
            gap: 28,
            alignItems: "stretch",
          }}
        >
          <div
            className="glass-card"
            style={{
              padding: "38px 34px",
              background: "radial-gradient(circle at top left, rgba(0,102,255,0.14), transparent 36%), #08172E",
              color: "#fff",
              border: "1px solid rgba(255,255,255,0.08)",
            }}
          >
            <Badge color="#36D399">Impulsado por IA juridica colombiana</Badge>
            <h1
              style={{
                marginTop: 22,
                fontFamily: "'Playfair Display', serif",
                fontSize: 64,
                lineHeight: 0.98,
                fontWeight: 700,
              }}
            >
              Tu justicia, sin
              <br />
              barreras.
            </h1>
            <p style={{ marginTop: 22, maxWidth: 560, color: "rgba(255,255,255,0.74)", fontSize: 18, lineHeight: 1.7 }}>
              Analisis gratis, identificacion del derecho vulnerado, informe claro y pago por evento. El cliente decide si compra solo el documento o documento mas radicacion.
            </p>
            <div style={{ display: "flex", gap: 14, flexWrap: "wrap", marginTop: 28 }}>
              <Button size="lg" onClick={onStart} icon={ArrowRight}>
                Empezar mi tramite
              </Button>
              <Button
                size="lg"
                variant="ghost"
                onClick={onLogin}
                style={{ background: "rgba(255,255,255,0.08)", color: "#fff", border: "1px solid rgba(255,255,255,0.1)" }}
              >
                Ya tengo cuenta
              </Button>
            </div>
            <div style={{ display: "flex", gap: 20, flexWrap: "wrap", marginTop: 24, color: "rgba(255,255,255,0.76)" }}>
              <span>Sin abogado</span>
              <span>Informe gratis</span>
              <span>Panel de seguimiento</span>
            </div>
          </div>

          <div className="glass-card" style={{ padding: 28, background: "#FCFDFF" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span style={{ color: C.textMuted, fontWeight: 700 }}>Caso analizado hace 2 min</span>
              <Badge color={C.accent}>En vivo</Badge>
            </div>
            <div style={{ display: "grid", gap: 16, marginTop: 18 }}>
              <div style={{ padding: 18, borderRadius: 18, background: "#F0FDF4", border: "1px solid #BBF7D0" }}>
                <div style={{ fontSize: 12, fontWeight: 800, color: "#15803D", marginBottom: 6 }}>DERECHO VULNERADO IDENTIFICADO</div>
                <div style={{ fontSize: 28, fontWeight: 800, color: C.text }}>Salud</div>
                <div style={{ color: C.textMuted }}>Acceso a tratamiento y continuidad del servicio.</div>
              </div>
              <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                <Badge color="#DC2626">EPS nego tratamiento</Badge>
                <Badge color="#2563EB">Ley 1751/2015</Badge>
                <Badge color="#7C3AED">T-760/2008</Badge>
              </div>
              <div style={{ padding: 20, borderRadius: 18, background: "#0F2C5F", color: "#fff" }}>
                <div style={{ fontSize: 12, fontWeight: 800, color: "#93C5FD", marginBottom: 6 }}>ACCION RECOMENDADA</div>
                <div style={{ fontSize: 30, fontWeight: 800 }}>Accion de tutela</div>
                <div style={{ marginTop: 8, color: "rgba(255,255,255,0.76)" }}>
                  Documento listo para pago y radicacion digital si el cliente la elige.
                </div>
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12 }}>
                {[
                  { label: "Analisis", value: "Gratis" },
                  { label: "Promesa", value: "< 5 min" },
                  { label: "Seguimiento", value: "Incluido" },
                ].map((item) => (
                  <div key={item.label} style={{ padding: 16, borderRadius: 16, background: "#F8FAFD", border: `1px solid ${C.border}` }}>
                    <div style={{ fontSize: 12, color: C.textMuted, fontWeight: 700 }}>{item.label}</div>
                    <div style={{ marginTop: 8, fontSize: 24, fontWeight: 800 }}>{item.value}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      <section id="categorias" style={{ maxWidth: 1200, margin: "0 auto", padding: "8px 24px 54px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", gap: 16, alignItems: "end", marginBottom: 24, flexWrap: "wrap" }}>
          <div>
            <Badge color={C.primary}>Categorias</Badge>
            <h2 style={{ marginTop: 12, fontSize: 44, lineHeight: 1.05, fontFamily: "'Playfair Display', serif" }}>
              Casos que la app ya puede
              <br />
              encaminar contigo.
            </h2>
          </div>
          <p style={{ maxWidth: 420, color: C.textMuted }}>
            El analisis no cobra. El cliente ve el informe y luego decide si paga el documento o el paquete con radicacion.
          </p>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: 16 }}>
          {categories.map((item) => (
            <div key={item.title} className="glass-card" style={{ padding: 20 }}>
              <div
                style={{
                  width: 50,
                  height: 50,
                  borderRadius: 16,
                  background: `${item.color}18`,
                  display: "grid",
                  placeItems: "center",
                  marginBottom: 16,
                }}
              >
                <item.icon size={22} style={{ color: item.color }} />
              </div>
              <h3 style={{ fontSize: 18, fontWeight: 800 }}>{item.title}</h3>
              <p style={{ marginTop: 8, color: C.textMuted, fontSize: 14, lineHeight: 1.65 }}>{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      <section id="como-funciona" style={{ background: "#08172E", color: "#fff", padding: "72px 24px" }}>
        <div style={{ maxWidth: 1200, margin: "0 auto" }}>
          <div style={{ textAlign: "center", marginBottom: 34 }}>
            <Badge color="#36D399">Como funciona</Badge>
            <h2 style={{ marginTop: 16, fontSize: 54, fontFamily: "'Playfair Display', serif" }}>Tres pasos. Sin complicaciones.</h2>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 18 }}>
            {steps.map((step) => (
              <div
                key={step.index}
                style={{
                  padding: 28,
                  borderRadius: 24,
                  background: "rgba(255,255,255,0.04)",
                  border: "1px solid rgba(255,255,255,0.08)",
                }}
              >
                <div style={{ fontSize: 52, color: "#1D4ED8", fontWeight: 800, fontFamily: "'Playfair Display', serif" }}>{step.index}</div>
                <h3 style={{ marginTop: 18, fontSize: 34, lineHeight: 1.1 }}>{step.title}</h3>
                <p style={{ marginTop: 14, color: "rgba(255,255,255,0.7)", lineHeight: 1.7 }}>{step.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section id="precios" style={{ maxWidth: 1200, margin: "0 auto", padding: "68px 24px 96px" }}>
        <div className="glass-card" style={{ padding: "34px 32px", display: "grid", gridTemplateColumns: "1fr 1fr", gap: 28 }}>
          <div>
            <Badge color={C.primary}>Precios</Badge>
            <h2 style={{ marginTop: 14, fontSize: 44, lineHeight: 1.05, fontFamily: "'Playfair Display', serif" }}>
              Pagas solo por lo que
              <br />
              decides activar.
            </h2>
            <p style={{ marginTop: 16, color: C.textMuted, lineHeight: 1.7, maxWidth: 520 }}>
              La promesa comercial es simple: diagnostico gratis, producto claro, radicacion opcional y seguimiento visible. Sin suscripciones ni paquetes confusos.
            </p>
            <div style={{ display: "grid", gap: 12, marginTop: 22 }}>
              {priceHighlights.map((item) => (
                <div key={item} style={{ display: "flex", alignItems: "center", gap: 12 }}>
                  <CheckCircle2 size={18} style={{ color: C.accent }} />
                  <span>{item}</span>
                </div>
              ))}
            </div>
          </div>

          <div
            style={{
              borderRadius: 26,
              padding: 24,
              background: "linear-gradient(180deg, #F8FBFF 0%, #EEF4FF 100%)",
              border: `1px solid ${C.border}`,
            }}
          >
            <div style={{ fontSize: 14, color: C.textMuted, fontWeight: 700 }}>Ejemplo visible para el cliente</div>
            <div style={{ marginTop: 12, fontSize: 42, fontWeight: 800 }}>Tutela desde $76.900</div>
            <div style={{ color: C.textMuted }}>Radicacion automatizada opcional desde $36.000 adicionales.</div>
            <div style={{ marginTop: 20, paddingTop: 20, borderTop: `1px solid ${C.border}` }}>
              <div style={{ display: "flex", justifyContent: "space-between", padding: "10px 0" }}>
                <span>Analisis juridico inicial</span>
                <strong>Gratis</strong>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", padding: "10px 0" }}>
                <span>Documento individual</span>
                <strong>Desde $32.900</strong>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", padding: "10px 0" }}>
                <span>Documento + radicacion</span>
                <strong>Desde $68.900</strong>
              </div>
            </div>
            <div style={{ marginTop: 24 }}>
              <Button size="lg" onClick={onStart} style={{ width: "100%" }}>
                Crear mi cuenta y empezar
              </Button>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
