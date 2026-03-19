import React from "react";
import { ArrowLeft, Mail, Scale, ShieldCheck } from "lucide-react";

import { Badge, Button } from "../ui";
import { C } from "../theme";

const PAGE_COPY = {
  terminos: {
    badge: "Términos",
    title: "Términos del servicio",
    subtitle: "Condiciones base para el uso de 123tutela y la compra de documentos o radicaciones.",
    sections: [
      {
        title: "Qué hace la plataforma",
        body:
          "123tutela analiza la información entregada por el usuario, recomienda la ruta jurídica disponible y permite pagar por la generación del documento y, cuando aplica, por la radicación del trámite.",
      },
      {
        title: "Qué no promete",
        body:
          "La plataforma no garantiza resultados judiciales o administrativos. La recomendación y los documentos dependen de la información suministrada por el usuario y de la respuesta de las entidades o juzgados.",
      },
      {
        title: "Pago y activación",
        body:
          "El análisis inicial puede ser gratuito. El documento final y la radicación solo se activan cuando el pago correspondiente haya sido confirmado de forma segura por el sistema.",
      },
      {
        title: "Continuidad del caso",
        body:
          "Pasos posteriores como seguimiento, impugnación o desacato pueden requerir validación adicional y nuevos cobros por evento cuando aplique.",
      },
    ],
  },
  privacidad: {
    badge: "Privacidad",
    title: "Política de privacidad",
    subtitle: "Cómo usamos la información personal y documental dentro del servicio.",
    sections: [
      {
        title: "Datos que tratamos",
        body:
          "Tratamos datos de identificación, contacto, ubicación, información del caso, documentos aportados y registros operativos del expediente para poder analizar, generar y radicar trámites cuando el usuario lo solicite.",
      },
      {
        title: "Finalidad del tratamiento",
        body:
          "La información se usa para operar la cuenta, analizar el caso, generar documentos, ejecutar pagos, soportar la radicación, mantener trazabilidad y comunicar al usuario los estados y siguientes pasos del trámite.",
      },
      {
        title: "Compartición limitada",
        body:
          "Solo se comparte la información necesaria con proveedores tecnológicos y canales de pago, y con entidades o despachos cuando la radicación del trámite así lo requiera.",
      },
      {
        title: "Derechos del titular",
        body:
          "El usuario puede solicitar actualización, corrección o supresión de datos cuando proceda, usando los canales de contacto publicados por la plataforma.",
      },
    ],
  },
  contacto: {
    badge: "Contacto",
    title: "Soporte y contacto",
    subtitle: "Canales para resolver dudas de acceso, pagos o estado del trámite.",
    sections: [
      {
        title: "Soporte general",
        body:
          "Para consultas sobre acceso, pagos, expedientes o estado del proceso, el usuario puede escribir al correo oficial de soporte y detallar su referencia o número de caso.",
      },
      {
        title: "Pagos y conciliación",
        body:
          "Si un pago fue aprobado pero no se refleja de inmediato en la interfaz, el usuario debe reportar la referencia de la transacción para validar el estado en el panel y en los registros internos.",
      },
      {
        title: "Casos sensibles",
        body:
          "Cuando el trámite requiera continuidad como impugnación, desacato o seguimiento, el usuario debe revisar primero el estado del expediente y luego contactar soporte si necesita orientación adicional.",
      },
    ],
  },
};

export default function LegalPageView({ page = "terminos", onBackHome }) {
  const content = PAGE_COPY[page] || PAGE_COPY.terminos;

  return (
    <div style={{ minHeight: "100vh", background: "#F5F7FB", color: C.text }}>
      <div style={{ maxWidth: 1080, margin: "0 auto", padding: "32px 24px 80px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", gap: 16, alignItems: "center", flexWrap: "wrap", marginBottom: 28 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <div
              style={{
                width: 42,
                height: 42,
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
          <Button variant="outline" onClick={onBackHome} icon={ArrowLeft}>
            Volver al inicio
          </Button>
        </div>

        <div className="glass-card" style={{ padding: "34px 32px", display: "grid", gap: 28 }}>
          <div>
            <Badge color={page === "contacto" ? C.accent : C.primary}>{content.badge}</Badge>
            <h1 style={{ marginTop: 14, fontSize: 50, lineHeight: 1, fontFamily: "'Playfair Display', serif" }}>{content.title}</h1>
            <p style={{ marginTop: 14, color: C.textMuted, maxWidth: 760, lineHeight: 1.75 }}>{content.subtitle}</p>
          </div>

          {content.sections.map((section) => (
            <section key={section.title} style={{ paddingTop: 22, borderTop: `1px solid ${C.border}` }}>
              <h2 style={{ fontSize: 26, lineHeight: 1.1, marginBottom: 10 }}>{section.title}</h2>
              <p style={{ color: C.textMuted, lineHeight: 1.75 }}>{section.body}</p>
            </section>
          ))}

          {page === "contacto" && (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 16 }}>
              <div className="glass-card" style={{ padding: 20, background: "#FCFDFF" }}>
                <div style={{ display: "flex", alignItems: "center", gap: 10, color: C.primary, fontWeight: 800 }}>
                  <Mail size={18} />
                  soporte@123tutelaapp.com
                </div>
                <p style={{ marginTop: 10, color: C.textMuted, lineHeight: 1.65 }}>
                  Canal principal para soporte, conciliación de pagos y seguimiento del expediente.
                </p>
              </div>
              <div className="glass-card" style={{ padding: 20, background: "#FCFDFF" }}>
                <div style={{ display: "flex", alignItems: "center", gap: 10, color: C.accent, fontWeight: 800 }}>
                  <ShieldCheck size={18} />
                  Respuesta con referencia
                </div>
                <p style={{ marginTop: 10, color: C.textMuted, lineHeight: 1.65 }}>
                  Cuando escribas, incluye el correo de la cuenta y la referencia del pago o el identificador del expediente.
                </p>
              </div>
              <div className="glass-card" style={{ padding: 20, background: "#FCFDFF" }}>
                <div style={{ display: "flex", alignItems: "center", gap: 10, color: C.accent, fontWeight: 800 }}>
                  <Mail size={18} />
                  radicaciones@123tutelaapp.com
                </div>
                <p style={{ marginTop: 10, color: C.textMuted, lineHeight: 1.65 }}>
                  Buzon operativo para envios judiciales y recepcion inicial de acuses o radicados cuando el despacho responde al canal de salida.
                </p>
              </div>
              <div className="glass-card" style={{ padding: 20, background: "#FCFDFF" }}>
                <div style={{ display: "flex", alignItems: "center", gap: 10, color: C.primary, fontWeight: 800 }}>
                  <Mail size={18} />
                  notificaciones@123tutelaapp.com
                </div>
                <p style={{ marginTop: 10, color: C.textMuted, lineHeight: 1.65 }}>
                  Remitente operativo para copias al cliente, avisos del expediente y comprobantes que luego tambien quedan visibles en el panel.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
