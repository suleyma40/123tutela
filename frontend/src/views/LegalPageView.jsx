import React from "react";
import { ArrowLeft, Mail, Scale, ShieldCheck } from "lucide-react";

import { Badge, Button } from "../ui";
import { C } from "../theme";
import { NOTIFICATIONS_EMAIL, RADICATIONS_EMAIL, SUPPORT_EMAIL } from "../lib/launchConfig";

const PAGE_COPY = {
  terminos: {
    badge: "Terminos",
    title: "Terminos del servicio",
    subtitle: "Condiciones de uso para el bloque de salud y para la compra de documentos o radicacion operativa.",
    sections: [
      {
        title: "Que hace la plataforma",
        body:
          "123tutela recibe la informacion del caso, revisa los soportes cargados, recomienda la via juridica disponible y permite pagar por la preparacion del documento. Cuando el producto lo incluye, tambien permite activar una radicacion operativa del tramite.",
      },
      {
        title: "Alcance de salida",
        body:
          "En esta etapa la plataforma opera solo para derecho de peticion en salud, tutela en salud, impugnacion y desacato. Impugnacion y desacato solo se habilitan cuando el usuario aporta el fallo previo en copia legible para lectura de la IA.",
      },
      {
        title: "Que no prometemos",
        body:
          "La plataforma no garantiza resultados judiciales, administrativos ni medicos. Tampoco garantiza que una EPS, IPS, juzgado o entidad responda en un plazo especifico ni que el despacho admita o falle a favor del usuario.",
      },
      {
        title: "Pago y activacion",
        body:
          "El documento final y la radicacion operativa solo se activan cuando el pago haya sido confirmado de forma segura por el sistema. Si el pago no se confirma, el producto pago no se habilita aunque el usuario haya completado el formulario.",
      },
      {
        title: "Tiempo de respuesta",
        body:
          "La referencia comercial de menos de 5 minutos aplica a la generacion del documento y al inicio del envio digital cuando el caso ya esta completo, el pago fue aprobado y el canal permite tramite inmediato. No significa respuesta de la entidad ni radicado definitivo dentro de ese mismo tiempo.",
      },
      {
        title: "Continuidad del caso",
        body:
          "Impugnacion, desacato y otros pasos posteriores pueden requerir nueva validacion documental, verificacion de terminos y cobro independiente. Si falta un soporte esencial, la plataforma puede impedir la compra o pedir informacion adicional antes de seguir.",
      },
      {
        title: "Reembolsos",
        body:
          "Si el usuario paga y el sistema no presta el servicio contratado por una falla operativa imputable a la plataforma, puede solicitar revision para reverso o reembolso. No aplica reembolso cuando el documento ya fue generado con base en la informacion entregada, cuando la radicacion no procede por datos incompletos, o cuando el resultado desfavorable depende de la entidad o del juzgado.",
      },
    ],
  },
  privacidad: {
    badge: "Privacidad",
    title: "Politica de privacidad",
    subtitle: "Como usamos la informacion personal, clinica y documental dentro del servicio.",
    sections: [
      {
        title: "Datos que tratamos",
        body:
          "Tratamos datos de identificacion, contacto, ciudad, informacion del caso, datos de salud que el usuario cargue, documentos de soporte, fallos judiciales previos y registros tecnicos del expediente para poder operar el servicio.",
      },
      {
        title: "Finalidad del tratamiento",
        body:
          "La informacion se usa para analizar el caso, generar documentos, validar requisitos, ejecutar pagos, soportar radicacion operativa, mantener trazabilidad y comunicar estados, incidencias y siguientes pasos al usuario.",
      },
      {
        title: "Autorizacion de tratamiento y comunicaciones",
        body:
          "Al usar la plataforma y enviar formularios o soportes, el usuario autoriza el tratamiento de sus datos personales y sensibles estrictamente para la prestacion del servicio, asi como el envio de comunicaciones transaccionales y operativas por correo electronico o WhatsApp relacionadas con pago, expediente, entrega documental, soporte e incidencias.",
      },
      {
        title: "Comparticion limitada",
        body:
          "Solo compartimos la informacion necesaria con proveedores tecnologicos, canales de pago y, cuando el usuario activa la radicacion, con las entidades o despachos ante los que deba presentarse el tramite.",
      },
      {
        title: "Conservacion y seguridad",
        body:
          "Aplicamos medidas tecnicas y operativas razonables para proteger la informacion. Aun asi, ningun sistema digital es completamente inmune a incidentes, por lo que el usuario debe cargar informacion veraz y mantener control sobre sus credenciales.",
      },
      {
        title: "Consulta, actualizacion y supresion",
        body:
          "Como titular de datos puedes solicitar consulta, actualizacion, correccion o supresion cuando proceda legalmente, y tambien revocar autorizaciones no esenciales, usando los canales oficiales publicados en esta pagina.",
      },
      {
        title: "Derechos del titular",
        body:
          "El usuario puede solicitar acceso, actualizacion, correccion o supresion de datos cuando proceda legalmente, usando los canales oficiales de contacto publicados por la plataforma.",
      },
    ],
  },
  contacto: {
    badge: "Contacto",
    title: "Soporte y contacto",
    subtitle: "Canales para resolver dudas sobre acceso, pagos, radicacion y estado del expediente.",
    sections: [
      {
        title: "Soporte general",
        body:
          "Para consultas sobre acceso, pagos, expediente o estado del proceso, escribe al canal principal de soporte con el correo de tu cuenta y una descripcion corta del problema.",
      },
      {
        title: "Pagos y conciliacion",
        body:
          "Si un pago fue aprobado pero no se refleja en la interfaz, reporta la referencia de la transaccion para revisar el estado en el panel y en los registros internos del sistema.",
      },
      {
        title: "Tratamiento de datos",
        body:
          "Las solicitudes sobre habeas data, actualizacion, correccion, supresion y revocatoria de autorizaciones deben enviarse por los canales de soporte indicando nombre, correo usado en la plataforma y motivo de la solicitud.",
      },
      {
        title: "Impugnacion y desacato",
        body:
          "Si tu caso requiere impugnacion o desacato, adjunta el fallo previo en formato legible. Sin ese documento no se puede validar ni preparar correctamente el siguiente escrito.",
      },
    ],
  },
};

export default function LegalPageView({ page = "terminos", onBackHome }) {
  const content = PAGE_COPY[page] || PAGE_COPY.terminos;

  return (
    <div style={{ minHeight: "100vh", background: "#F5F7FB", color: C.text }}>
      <div style={{ maxWidth: 1080, margin: "0 auto", padding: "32px 24px 80px" }}>
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            gap: 16,
            alignItems: "center",
            flexWrap: "wrap",
            marginBottom: 28,
          }}
        >
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
            <h1
              style={{
                marginTop: 14,
                fontSize: 50,
                lineHeight: 1,
                fontFamily: "'Playfair Display', serif",
              }}
            >
              {content.title}
            </h1>
            <p style={{ marginTop: 14, color: C.textMuted, maxWidth: 760, lineHeight: 1.75 }}>
              {content.subtitle}
            </p>
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
                  {SUPPORT_EMAIL}
                </div>
                <p style={{ marginTop: 10, color: C.textMuted, lineHeight: 1.65 }}>
                  Canal principal para soporte, conciliacion de pagos y validacion del expediente.
                </p>
              </div>
              <div className="glass-card" style={{ padding: 20, background: "#FCFDFF" }}>
                <div style={{ display: "flex", alignItems: "center", gap: 10, color: C.accent, fontWeight: 800 }}>
                  <ShieldCheck size={18} />
                  Escribe con referencia
                </div>
                <p style={{ marginTop: 10, color: C.textMuted, lineHeight: 1.65 }}>
                  Incluye el correo de la cuenta, la referencia del pago o el identificador del expediente para acelerar la revision.
                </p>
              </div>
              <div className="glass-card" style={{ padding: 20, background: "#FCFDFF" }}>
                <div style={{ display: "flex", alignItems: "center", gap: 10, color: C.accent, fontWeight: 800 }}>
                  <Mail size={18} />
                  {RADICATIONS_EMAIL}
                </div>
                <p style={{ marginTop: 10, color: C.textMuted, lineHeight: 1.65 }}>
                  Buzon operativo para tramites enviados, acuses, radicados y novedades del canal de presentacion.
                </p>
              </div>
              <div className="glass-card" style={{ padding: 20, background: "#FCFDFF" }}>
                <div style={{ display: "flex", alignItems: "center", gap: 10, color: C.primary, fontWeight: 800 }}>
                  <Mail size={18} />
                  {NOTIFICATIONS_EMAIL}
                </div>
                <p style={{ marginTop: 10, color: C.textMuted, lineHeight: 1.65 }}>
                  Remitente operativo para copias al cliente, avisos del expediente y comprobantes visibles en el panel.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
