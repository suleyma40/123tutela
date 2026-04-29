import React, { useEffect, useMemo, useState } from "react";
import { CheckCircle2, FileText, Landmark, Scale, Shield, Upload, Wallet } from "lucide-react";

import { api, extractError } from "./lib/api";

const ROUTES = {
  landing: "/",
  payment_result: "/pago/resultado",
  terminos: "/terminos",
  privacidad: "/privacidad",
  contacto: "/contacto",
};

const PRICE_LABEL = "$59.900";
const STORAGE_KEY = "hazlopormi-guest-case";
const widgetScriptUrl = "https://checkout.wompi.co/widget.js";

const C = {
  bg: "#F5F7FB",
  ink: "#10203A",
  muted: "#62718C",
  primary: "#0B63F3",
  primaryDark: "#0A1B39",
  accent: "#FF6B35",
  border: "#D8E0F0",
  card: "#FFFFFF",
  success: "#12A150",
  warning: "#D97706",
  danger: "#C62828",
};

const pathToView = (pathname) => {
  if (pathname === ROUTES.payment_result) return "payment_result";
  if (pathname === ROUTES.terminos) return "terminos";
  if (pathname === ROUTES.privacidad) return "privacidad";
  if (pathname === ROUTES.contacto) return "contacto";
  return "landing";
};

const persistGuestCase = (value) => {
  if (!value) {
    localStorage.removeItem(STORAGE_KEY);
    return;
  }
  localStorage.setItem(STORAGE_KEY, JSON.stringify(value));
};

const loadGuestCase = () => {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
};

const buttonStyle = (variant = "primary") => ({
  border: "none",
  borderRadius: 14,
  padding: "14px 22px",
  cursor: "pointer",
  fontWeight: 800,
  fontSize: 15,
  background: variant === "primary" ? C.primary : variant === "accent" ? C.accent : "transparent",
  color: variant === "ghost" ? C.ink : "#fff",
  borderWidth: variant === "ghost" ? 1 : 0,
  borderStyle: "solid",
  borderColor: C.border,
});

function Section({ id, title, subtitle, children, light = false }) {
  return (
    <section id={id} style={{ padding: "72px 20px", background: light ? C.card : "transparent" }}>
      <div style={{ maxWidth: 1100, margin: "0 auto" }}>
        {(title || subtitle) && (
          <div style={{ marginBottom: 28 }}>
            {title && <h2 style={{ margin: 0, fontSize: 38, lineHeight: 1.05, color: C.ink }}>{title}</h2>}
            {subtitle && <p style={{ margin: "12px 0 0", maxWidth: 760, color: C.muted, fontSize: 18, lineHeight: 1.65 }}>{subtitle}</p>}
          </div>
        )}
        {children}
      </div>
    </section>
  );
}

function StatusCard({ color, icon: Icon, title, children }) {
  return (
    <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 22, padding: 26 }}>
      <div style={{ width: 58, height: 58, borderRadius: 18, background: `${color}18`, display: "grid", placeItems: "center", color }}>
        <Icon size={28} />
      </div>
      <h3 style={{ margin: "18px 0 8px", color: C.ink }}>{title}</h3>
      <div style={{ color: C.muted, lineHeight: 1.7 }}>{children}</div>
    </div>
  );
}

function LegalView({ title, body }) {
  return (
    <div style={{ minHeight: "100vh", background: C.bg, padding: 24 }}>
      <div style={{ maxWidth: 860, margin: "0 auto", background: C.card, borderRadius: 24, border: `1px solid ${C.border}`, padding: 32 }}>
        <h1 style={{ marginTop: 0, color: C.ink }}>{title}</h1>
        <p style={{ whiteSpace: "pre-wrap", color: C.muted, lineHeight: 1.8 }}>{body}</p>
      </div>
    </div>
  );
}

function PaymentResult({ guestCase, onRefreshStatus, onBackHome }) {
  const params = useMemo(() => new URLSearchParams(window.location.search), []);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const status = (params.get("status") || "PENDING").toUpperCase();
  const reference = params.get("reference");
  const transactionId = params.get("id") || params.get("transaction_id") || params.get("transaction-id");

  useEffect(() => {
    const run = async () => {
      if (!guestCase?.publicToken || !guestCase?.caseId || !transactionId) return;
      setLoading(true);
      try {
        await onRefreshStatus({ transaction_id: transactionId, reference, public_token: guestCase.publicToken });
        setMessage("Pago sincronizado. Ya puedes continuar con el formulario completo.");
      } catch (error) {
        setMessage(extractError(error, "Todavia no fue posible sincronizar el pago."));
      } finally {
        setLoading(false);
      }
    };
    run();
  }, [guestCase?.caseId, guestCase?.publicToken, transactionId, reference, onRefreshStatus]);

  const label =
    status === "APPROVED" ? "Pago aprobado" :
    status === "DECLINED" ? "Pago rechazado" :
    status === "ERROR" ? "Pago con error" :
    status === "VOIDED" ? "Pago anulado" :
    "Pago en validacion";

  return (
    <div style={{ minHeight: "100vh", background: C.bg, padding: 24 }}>
      <div style={{ maxWidth: 920, margin: "0 auto", background: C.card, borderRadius: 28, border: `1px solid ${C.border}`, overflow: "hidden" }}>
        <div style={{ background: C.primaryDark, color: "#fff", padding: 28 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <Scale size={22} />
            <strong style={{ fontSize: 22 }}>HazloPorMi</strong>
          </div>
          <h1 style={{ margin: "22px 0 10px", fontSize: 42 }}>{label}</h1>
          <p style={{ margin: 0, color: "rgba(255,255,255,0.78)", lineHeight: 1.7 }}>
            Si el pago quedó aprobado, el siguiente paso es completar los datos y anexos para que el equipo entregue el documento en hasta 24 horas hábiles.
          </p>
        </div>
        <div style={{ padding: 28 }}>
          <div style={{ display: "grid", gap: 12, color: C.muted }}>
            <div><strong style={{ color: C.ink }}>Referencia:</strong> {reference || "Pendiente"}</div>
            <div><strong style={{ color: C.ink }}>Estado:</strong> {label}</div>
          </div>
          {message && <p style={{ color: C.primary, marginTop: 16 }}>{message}</p>}
          <div style={{ display: "flex", gap: 12, flexWrap: "wrap", marginTop: 24 }}>
            <button style={buttonStyle("primary")} onClick={onBackHome}>{loading ? "Verificando..." : "Continuar con mi caso"}</button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function MainAppV2() {
  const [view, setView] = useState(() => pathToView(window.location.pathname));
  const [guestCase, setGuestCase] = useState(loadGuestCase());
  const [caseStatus, setCaseStatus] = useState(null);
  const [step, setStep] = useState("diagnosis");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [intakeFiles, setIntakeFiles] = useState([]);
  const [diagnosisForm, setDiagnosisForm] = useState({
    name: "",
    email: "",
    phone: "",
    category: "Salud",
    department: "Bogotá D.C.",
    city: "Bogotá",
    entity_name: "",
    urgency_level: "",
    description: "",
  });
  const [intakeForm, setIntakeForm] = useState({
    name: "",
    email: "",
    phone: "",
    document_number: "",
    city: "Bogotá",
    department: "Bogotá D.C.",
    address: "",
    description: "",
    target_entity: "",
    problem_age: "",
    urgency: "",
    concrete_request: "",
    extra_details: "",
  });

  const navigate = (nextView, { replace = false } = {}) => {
    const target = ROUTES[nextView] || ROUTES.landing;
    if (window.location.pathname !== target) {
      const method = replace ? "replaceState" : "pushState";
      window.history[method]({}, "", target);
    }
    setView(nextView);
  };

  const hydrateFromStatus = (response) => {
    setCaseStatus(response);
    setIntakeForm((current) => ({
      ...current,
      name: response.case.user_name || current.name,
      email: response.case.user_email || current.email,
      phone: response.case.user_phone || current.phone,
      document_number: response.case.user_document || current.document_number,
      city: response.case.user_city || current.city,
      department: response.case.user_department || current.department,
      address: response.case.user_address || current.address,
      description: response.case.description || current.description,
      target_entity: response.case.facts?.intake_form?.target_entity || current.target_entity,
      urgency: response.case.facts?.intake_form?.urgency || current.urgency,
      concrete_request: response.case.facts?.intake_form?.concrete_request || current.concrete_request,
    }));
    if (response.case.payment_status !== "pagado") {
      setStep("result");
    } else if (["pagado_pendiente_intake", "checkout_pendiente"].includes(response.case.status)) {
      setStep("intake");
    } else {
      setStep("status");
    }
  };

  const refreshCaseStatus = async (reconcilePayload = null) => {
    if (!guestCase?.caseId || !guestCase?.publicToken) return null;
    if (reconcilePayload) {
      const reconciled = await api.post("/public/payments/wompi/reconcile", reconcilePayload);
      hydrateFromStatus(reconciled.data);
      return reconciled.data;
    }
    const response = await api.get(`/public/cases/${guestCase.caseId}`, { params: { public_token: guestCase.publicToken } });
    hydrateFromStatus(response.data);
    return response.data;
  };

  useEffect(() => {
    const onPopState = () => setView(pathToView(window.location.pathname));
    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
  }, []);

  useEffect(() => {
    if (!guestCase?.caseId || !guestCase?.publicToken || view !== "landing") return;
    refreshCaseStatus().catch(() => {});
  }, [guestCase?.caseId, guestCase?.publicToken, view]);

  const launchWidget = (checkout) =>
    new Promise((resolve, reject) => {
      const start = () => {
        if (!window.WidgetCheckout) {
          reject(new Error("Widget de Wompi no disponible."));
          return;
        }
        try {
          const widget = new window.WidgetCheckout({
            currency: checkout.currency,
            amountInCents: checkout.amount_in_cents,
            reference: checkout.reference,
            publicKey: checkout.public_key,
            redirectUrl: checkout["redirect-url"],
            customerData: { email: checkout["customer-data:email"] },
            signature: { integrity: checkout["signature:integrity"] },
          });
          widget.open((result) => resolve(result || {}));
        } catch (error) {
          reject(error);
        }
      };
      if (window.WidgetCheckout) {
        start();
        return;
      }
      const existing = document.querySelector('script[data-wompi-widget="true"]');
      if (existing) {
        existing.addEventListener("load", start, { once: true });
        existing.addEventListener("error", () => reject(new Error("No fue posible cargar el widget de Wompi.")), { once: true });
        return;
      }
      const script = document.createElement("script");
      script.src = widgetScriptUrl;
      script.async = true;
      script.dataset.wompiWidget = "true";
      script.onload = start;
      script.onerror = () => reject(new Error("No fue posible cargar el widget de Wompi."));
      document.body.appendChild(script);
    });

  const submitDiagnosis = async () => {
    setLoading(true);
    setError("");
    try {
      const response = await api.post("/public/leads/diagnosis", diagnosisForm);
      const nextGuest = { caseId: response.data.case.id, publicToken: response.data.public_token };
      setGuestCase(nextGuest);
      persistGuestCase(nextGuest);
      setCaseStatus({
        case: response.data.case,
        public_token: response.data.public_token,
        customer_summary: response.data.commercial_summary,
        customer_guide: {},
        delivery_package: {},
        latest_payment: {},
        files: [],
      });
      setIntakeForm((current) => ({
        ...current,
        name: diagnosisForm.name,
        email: diagnosisForm.email,
        phone: diagnosisForm.phone,
        city: diagnosisForm.city,
        department: diagnosisForm.department,
        description: diagnosisForm.description,
        target_entity: diagnosisForm.entity_name,
      }));
      setStep("result");
    } catch (err) {
      setError(extractError(err, "No fue posible analizar tu caso."));
    } finally {
      setLoading(false);
    }
  };

  const startPayment = async () => {
    if (!guestCase?.caseId || !guestCase?.publicToken) return;
    setLoading(true);
    setError("");
    try {
      const response = await api.post(`/public/cases/${guestCase.caseId}/payments/wompi/session`, { public_token: guestCase.publicToken });
      const updatedGuest = { ...guestCase, reference: response.data.order.reference };
      setGuestCase(updatedGuest);
      persistGuestCase(updatedGuest);
      await launchWidget(response.data.checkout);
    } catch (err) {
      setError(extractError(err, "No fue posible iniciar el pago."));
    } finally {
      setLoading(false);
    }
  };

  const submitIntake = async () => {
    if (!guestCase?.caseId || !guestCase?.publicToken) return;
    setLoading(true);
    setError("");
    try {
      for (const file of intakeFiles) {
        const formData = new FormData();
        formData.append("public_token", guestCase.publicToken);
        formData.append("file_kind", "supporting_evidence");
        formData.append("file", file);
        await api.post(`/public/cases/${guestCase.caseId}/uploads`, formData, { headers: { "Content-Type": "multipart/form-data" } });
      }
      const response = await api.patch(`/public/cases/${guestCase.caseId}/intake`, {
        public_token: guestCase.publicToken,
        ...intakeForm,
        form_data: {
          target_entity: intakeForm.target_entity,
          problem_age: intakeForm.problem_age,
          urgency: intakeForm.urgency,
          concrete_request: intakeForm.concrete_request,
          extra_details: intakeForm.extra_details,
        },
      });
      hydrateFromStatus(response.data);
      setIntakeFiles([]);
    } catch (err) {
      setError(extractError(err, "No fue posible completar la informacion del caso."));
    } finally {
      setLoading(false);
    }
  };

  const clearGuestSession = () => {
    setGuestCase(null);
    setCaseStatus(null);
    setStep("diagnosis");
    persistGuestCase(null);
  };

  if (view === "payment_result") {
    return (
      <PaymentResult
        guestCase={guestCase}
        onRefreshStatus={refreshCaseStatus}
        onBackHome={() => {
          navigate("landing", { replace: true });
          refreshCaseStatus().catch(() => {});
        }}
      />
    );
  }

  if (view === "terminos") {
    return <LegalView title="Terminos y condiciones" body={"HazloPorMi entrega diagnostico inicial, redaccion del documento por especialistas y guia detallada. No garantiza resultados judiciales o administrativos. El plazo comercial es hasta 24 horas habiles desde pago aprobado e informacion completa. Las promociones o incentivos, cuando existan, se sujetan a terminos publicados y normativa aplicable."} />;
  }
  if (view === "privacidad") {
    return <LegalView title="Politica de datos" body={"Tratamos los datos de contacto y los documentos adjuntos para analizar el caso, preparar el documento solicitado, operar pagos, hacer seguimiento y entregar el servicio por email o WhatsApp. El usuario debe suministrar informacion veraz y soportes pertinentes."} />;
  }
  if (view === "contacto") {
    return <LegalView title="Contacto" body={"Soporte comercial y operativo:\nEmail: soporte@hazlopormi.app\nWhatsApp: se informa en el mensaje de seguimiento cuando el canal este operativo.\nHorario de atencion: dias habiles."} />;
  }

  const summary = caseStatus?.customer_summary || {};
  const guide = caseStatus?.customer_guide || {};
  const deliveryPackage = caseStatus?.delivery_package || {};
  const invoice = summary.invoice || caseStatus?.latest_payment?.invoice || {};
  const raffle = summary.raffle || caseStatus?.latest_payment?.raffle || {};

  return (
    <div style={{ minHeight: "100vh", background: C.bg, color: C.ink }}>
      <header style={{ background: "linear-gradient(135deg, #08162F 0%, #11336D 100%)", color: "#fff" }}>
        <div style={{ maxWidth: 1100, margin: "0 auto", padding: "24px 20px 88px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 20 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
              <div style={{ width: 44, height: 44, borderRadius: 14, background: C.primary, display: "grid", placeItems: "center" }}>
                <Scale size={22} />
              </div>
              <strong style={{ fontSize: 24 }}>HazloPorMi</strong>
            </div>
            <nav style={{ display: "flex", gap: 18, flexWrap: "wrap" }}>
              <a href="#como-funciona" style={{ color: "rgba(255,255,255,0.78)", textDecoration: "none" }}>Cómo funciona</a>
              <a href="#servicios" style={{ color: "rgba(255,255,255,0.78)", textDecoration: "none" }}>Servicios</a>
              <a href="#precio" style={{ color: "rgba(255,255,255,0.78)", textDecoration: "none" }}>Precio</a>
            </nav>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1.2fr 0.8fr", gap: 28, marginTop: 56 }}>
            <div>
              <div style={{ display: "inline-flex", padding: "8px 12px", borderRadius: 999, background: "rgba(255,255,255,0.10)", fontWeight: 700, fontSize: 13 }}>
                Diagnóstico inicial + redacción por especialistas + guía detallada
              </div>
              <h1 style={{ margin: "18px 0 14px", fontSize: 66, lineHeight: 0.98 }}>
                ¿Tu EPS, tránsito o banco no responde?
              </h1>
              <p style={{ fontSize: 20, lineHeight: 1.7, color: "rgba(255,255,255,0.78)", maxWidth: 700 }}>
                Cuéntanos tu caso, te decimos qué camino tomar y, si pagas, especialistas preparan tu documento y tu paso a paso completo en hasta 24 horas hábiles.
              </p>
              <div style={{ display: "flex", gap: 14, flexWrap: "wrap", marginTop: 24 }}>
                <a href="#diagnostico"><button style={buttonStyle("accent")}>Empezar diagnóstico</button></a>
                {guestCase && <button style={buttonStyle("ghost")} onClick={() => refreshCaseStatus().catch(() => {})}>Retomar mi caso</button>}
              </div>
            </div>
            <div style={{ background: "rgba(255,255,255,0.08)", borderRadius: 28, padding: 28, border: "1px solid rgba(255,255,255,0.14)" }}>
              <div style={{ color: "rgba(255,255,255,0.7)", fontWeight: 700 }}>Precio de entrada</div>
              <div style={{ fontSize: 60, fontWeight: 900, marginTop: 8 }}>{PRICE_LABEL}</div>
              <p style={{ color: "rgba(255,255,255,0.78)", lineHeight: 1.7 }}>
                Incluye diagnóstico, revisión experta, documento final y checklist operativo con anexos, canal y siguiente paso si no responden o niegan.
              </p>
              <div style={{ display: "grid", gap: 10, marginTop: 18 }}>
                {["Sin registro obligatorio", "Pago seguro con Wompi", "Entrega por email y WhatsApp", "Hasta 24 horas hábiles"].map((item) => (
                  <div key={item} style={{ display: "flex", alignItems: "center", gap: 10 }}>
                    <CheckCircle2 size={18} color="#90F6B2" />
                    <span>{item}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </header>

      <Section id="servicios" title="Tres frentes para salir rápido con producto" subtitle="La V1 comercial se concentra en pocos documentos por vertical para mantener velocidad y calidad operativa.">
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 18 }}>
          <StatusCard color={C.danger} icon={Shield} title="Salud">
            Derecho de petición, queja y tutela para medicamentos negados, citas demoradas, procedimientos o urgencias.
          </StatusCard>
          <StatusCard color={C.warning} icon={Landmark} title="Tránsito">
            Derecho de petición, recurso y solicitudes de prescripción o desembargo cuando aplique.
          </StatusCard>
          <StatusCard color={C.primary} icon={Wallet} title="Bancos">
            Reclamos, habeas data y solicitudes de rectificación por cobros, bloqueos o reportes negativos.
          </StatusCard>
        </div>
      </Section>

      <Section id="como-funciona" title="Cómo funciona" subtitle="El proceso es simple: primero entiendes tu caso, luego pagas y completas la información necesaria para que nuestros especialistas elaboren tu documento.">
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 16 }}>
          {[
            ["1. Diagnóstico", "Nos dejas tu caso y te mostramos la acción sugerida."],
            ["2. Pago", `Pagas ${PRICE_LABEL} para activar la elaboración por especialistas.`],
            ["3. Formulario completo", "Cargas datos, anexos y detalles que faltan."],
            ["4. Entrega", "Recibes documento y guía detallada en hasta 24 horas hábiles."],
          ].map(([title, body]) => (
            <div key={title} style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 22, padding: 22 }}>
              <strong style={{ display: "block", fontSize: 22, marginBottom: 10 }}>{title}</strong>
              <span style={{ color: C.muted, lineHeight: 1.7 }}>{body}</span>
            </div>
          ))}
        </div>
      </Section>

      <Section id="diagnostico" title="Empieza tu diagnóstico" subtitle="No necesitas crear cuenta. Este resultado es orientativo y sirve para llevarte al pago correcto.">
        <div style={{ display: "grid", gridTemplateColumns: "1fr 0.95fr", gap: 22 }}>
          <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 28, padding: 28 }}>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 14 }}>
              {[
                ["name", "Nombre completo"],
                ["email", "Email"],
                ["phone", "Teléfono"],
                ["entity_name", "Entidad (EPS, banco, tránsito)"],
                ["city", "Ciudad"],
                ["department", "Departamento"],
              ].map(([key, label]) => (
                <label key={key} style={{ display: "grid", gap: 8 }}>
                  <span style={{ fontWeight: 700 }}>{label}</span>
                  <input value={diagnosisForm[key]} onChange={(event) => setDiagnosisForm({ ...diagnosisForm, [key]: event.target.value })} style={{ border: `1px solid ${C.border}`, borderRadius: 14, padding: 14, fontSize: 15 }} />
                </label>
              ))}
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14, marginTop: 14 }}>
              <label style={{ display: "grid", gap: 8 }}>
                <span style={{ fontWeight: 700 }}>Tipo de problema</span>
                <select value={diagnosisForm.category} onChange={(event) => setDiagnosisForm({ ...diagnosisForm, category: event.target.value })} style={{ border: `1px solid ${C.border}`, borderRadius: 14, padding: 14, fontSize: 15 }}>
                  <option>Salud</option>
                  <option>Tránsito</option>
                  <option>Bancos</option>
                </select>
              </label>
              <label style={{ display: "grid", gap: 8 }}>
                <span style={{ fontWeight: 700 }}>Urgencia</span>
                <input value={diagnosisForm.urgency_level} onChange={(event) => setDiagnosisForm({ ...diagnosisForm, urgency_level: event.target.value })} placeholder="Ej: embargo activo, medicamento urgente" style={{ border: `1px solid ${C.border}`, borderRadius: 14, padding: 14, fontSize: 15 }} />
              </label>
            </div>
            <label style={{ display: "grid", gap: 8, marginTop: 14 }}>
              <span style={{ fontWeight: 700 }}>Cuéntanos qué pasó</span>
              <textarea value={diagnosisForm.description} onChange={(event) => setDiagnosisForm({ ...diagnosisForm, description: event.target.value })} rows={8} placeholder="Describe el problema, la entidad, lo que pediste, qué respuesta recibiste y qué sigue pasando hoy." style={{ border: `1px solid ${C.border}`, borderRadius: 16, padding: 14, fontSize: 15, resize: "vertical" }} />
            </label>
            <div style={{ marginTop: 18, display: "flex", gap: 12, flexWrap: "wrap" }}>
              <button style={buttonStyle("primary")} onClick={submitDiagnosis}>{loading ? "Analizando..." : "Analizar mi caso"}</button>
              {guestCase && <button style={buttonStyle("ghost")} onClick={() => refreshCaseStatus().catch(() => {})}>Retomar</button>}
            </div>
            {error && <p style={{ color: C.danger, marginTop: 14 }}>{error}</p>}
          </div>

          <div style={{ background: C.primaryDark, borderRadius: 28, padding: 28, color: "#fff" }}>
            <h3 style={{ marginTop: 0, fontSize: 28 }}>Qué recibes si pagas</h3>
            <div style={{ display: "grid", gap: 14, marginTop: 16 }}>
              {[
                ["Documento final", "Redactado por especialistas con base en tu caso y soportes."],
                ["Checklist detallado", "Qué presentar, dónde, cómo, qué anexar y qué pedir exactamente."],
                ["Ruta siguiente", "Qué hacer si no responden o niegan la solicitud."],
                ["Entrega directa", "Lo recibes por email y WhatsApp, sin panel obligatorio."],
              ].map(([title, body]) => (
                <div key={title} style={{ padding: 16, borderRadius: 18, background: "rgba(255,255,255,0.06)" }}>
                  <strong>{title}</strong>
                  <div style={{ color: "rgba(255,255,255,0.72)", marginTop: 6, lineHeight: 1.7 }}>{body}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </Section>

      {step === "result" && caseStatus && (
        <Section title="Resultado preliminar" subtitle="Este diagnóstico orienta el pago. El documento final se prepara después del checkout y del formulario completo.">
          <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 28, padding: 28 }}>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 0.8fr", gap: 24 }}>
              <div>
                <div style={{ display: "inline-flex", padding: "8px 12px", borderRadius: 999, background: `${C.primary}14`, color: C.primary, fontWeight: 800 }}>
                  Acción sugerida: {caseStatus.case.recommended_action}
                </div>
                <h3 style={{ fontSize: 32, marginBottom: 8 }}>Qué detectó el sistema</h3>
                <p style={{ color: C.muted, lineHeight: 1.8 }}>{summary.headline || caseStatus.case.strategy_text}</p>
                <p style={{ color: C.muted, lineHeight: 1.8 }}>{summary.subheadline}</p>
                <div style={{ marginTop: 16 }}>
                  {(summary.included || []).map((item) => (
                    <div key={item} style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 10 }}>
                      <CheckCircle2 size={18} color={C.success} />
                      <span>{item}</span>
                    </div>
                  ))}
                </div>
              </div>
              <div style={{ background: "#F7F9FE", borderRadius: 24, padding: 24 }}>
                <div style={{ color: C.muted, fontWeight: 700 }}>Pago único</div>
                <div style={{ fontSize: 52, fontWeight: 900, color: C.accent, marginTop: 8 }}>{PRICE_LABEL}</div>
                <p style={{ color: C.muted, lineHeight: 1.7 }}>Nuestro equipo jurídico comienza a trabajar en cuanto el pago queda aprobado.</p>
                <button style={buttonStyle("accent")} onClick={startPayment}>{loading ? "Abriendo checkout..." : "Pagar con Wompi"}</button>
              </div>
            </div>
          </div>
        </Section>
      )}

      {step === "intake" && caseStatus && (
        <Section title="Completa tus datos" subtitle="El plazo de 24 horas hábiles corre desde que el pago está aprobado y la información queda completa.">
          <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 28, padding: 28 }}>
            {(invoice.number || raffle.code) && (
              <div style={{ marginBottom: 18, background: "#F7F9FE", border: `1px solid ${C.border}`, borderRadius: 18, padding: 18 }}>
                <div style={{ fontWeight: 800, color: C.ink, marginBottom: 8 }}>Pago confirmado</div>
                {invoice.number && <div style={{ color: C.muted, marginBottom: 6 }}><strong style={{ color: C.ink }}>Factura:</strong> {invoice.number}</div>}
                {raffle.code && <div style={{ color: C.muted }}><strong style={{ color: C.ink }}>Código único de participación:</strong> {raffle.code}</div>}
              </div>
            )}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 14 }}>
              {[
                ["name", "Nombre completo"],
                ["email", "Email"],
                ["phone", "Teléfono"],
                ["document_number", "Número de documento"],
                ["city", "Ciudad"],
                ["department", "Departamento"],
                ["address", "Dirección"],
                ["target_entity", "Entidad destinataria"],
                ["problem_age", "Tiempo del problema"],
                ["urgency", "Qué pasa hoy que lo hace urgente"],
                ["concrete_request", "Qué quieres que ordenen o corrijan"],
              ].map(([key, label]) => (
                <label key={key} style={{ display: "grid", gap: 8 }}>
                  <span style={{ fontWeight: 700 }}>{label}</span>
                  <input value={intakeForm[key] || ""} onChange={(event) => setIntakeForm({ ...intakeForm, [key]: event.target.value })} style={{ border: `1px solid ${C.border}`, borderRadius: 14, padding: 14, fontSize: 15 }} />
                </label>
              ))}
            </div>
            <label style={{ display: "grid", gap: 8, marginTop: 14 }}>
              <span style={{ fontWeight: 700 }}>Relato completo del caso</span>
              <textarea value={intakeForm.description} onChange={(event) => setIntakeForm({ ...intakeForm, description: event.target.value })} rows={7} style={{ border: `1px solid ${C.border}`, borderRadius: 16, padding: 14, fontSize: 15, resize: "vertical" }} />
            </label>
            <label style={{ display: "grid", gap: 8, marginTop: 14 }}>
              <span style={{ fontWeight: 700 }}>Detalles adicionales</span>
              <textarea value={intakeForm.extra_details} onChange={(event) => setIntakeForm({ ...intakeForm, extra_details: event.target.value })} rows={4} placeholder="Ej: recibo de pago, referencia de embargo, orden médica, respuesta previa, etc." style={{ border: `1px solid ${C.border}`, borderRadius: 16, padding: 14, fontSize: 15, resize: "vertical" }} />
            </label>
            <div style={{ marginTop: 16, padding: 18, borderRadius: 18, border: `1px dashed ${C.border}`, background: "#FBFCFF" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 10, fontWeight: 800 }}><Upload size={18} /> Adjunta soportes</div>
              <input type="file" multiple style={{ marginTop: 12 }} onChange={(event) => setIntakeFiles(Array.from(event.target.files || []))} />
              {!!intakeFiles.length && <p style={{ color: C.muted }}>{intakeFiles.length} archivo(s) listos para subir.</p>}
            </div>
            <div style={{ marginTop: 18 }}>
              <button style={buttonStyle("primary")} onClick={submitIntake}>{loading ? "Enviando..." : "Enviar al equipo jurídico"}</button>
            </div>
            {error && <p style={{ color: C.danger, marginTop: 14 }}>{error}</p>}
          </div>
        </Section>
      )}

      {step === "status" && caseStatus && (
        <Section title="Estado de tu caso" subtitle="Aquí ves el SLA, la guía generada para tu vertical y el estado operativo actual.">
          <div style={{ display: "grid", gridTemplateColumns: "1fr 0.95fr", gap: 18 }}>
            <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 28, padding: 28 }}>
              <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
                <span style={{ padding: "8px 12px", borderRadius: 999, background: `${C.primary}14`, color: C.primary, fontWeight: 800 }}>Estado: {caseStatus.case.status}</span>
                <span style={{ padding: "8px 12px", borderRadius: 999, background: `${C.success}14`, color: C.success, fontWeight: 800 }}>Pago: {caseStatus.case.payment_status}</span>
              </div>
              <h3 style={{ fontSize: 32, marginBottom: 8 }}>{caseStatus.case.recommended_action}</h3>
              <p style={{ color: C.muted, lineHeight: 1.8 }}>{summary.subheadline || "Tu caso ya está en cola operativa."}</p>
              <div style={{ marginTop: 20, display: "grid", gap: 12 }}>
                <div><strong>SLA objetivo:</strong> {caseStatus.case.submission_summary?.sla_deadline_at || "Se calcula al completar intake."}</div>
                <div><strong>Último pago:</strong> {caseStatus.latest_payment?.reference || "Pendiente"}</div>
                <div><strong>Entrega:</strong> {caseStatus.case.status === "entregado" ? "Documento enviado" : "En elaboración por especialistas"}</div>
                {invoice.number && <div><strong>Factura:</strong> {invoice.number}</div>}
                {raffle.code && <div><strong>Código de participación:</strong> {raffle.code}</div>}
              </div>
              {(invoice.relative_path || caseStatus.case.status === "entregado") && (
                <div style={{ marginTop: 22 }}>
                  {invoice.relative_path && (
                    <a href={`/public/files/${invoice.relative_path}`} target="_blank" rel="noreferrer" style={{ marginRight: 10 }}>
                      <button style={buttonStyle("ghost")}><FileText size={18} style={{ marginRight: 8 }} />Abrir factura</button>
                    </a>
                  )}
                </div>
              )}
              {caseStatus.case.status === "entregado" && deliveryPackage.document_pdf_url && (
                <div style={{ marginTop: 12 }}>
                  <a href={deliveryPackage.document_pdf_url} target="_blank" rel="noreferrer">
                    <button style={buttonStyle("accent")}><FileText size={18} style={{ marginRight: 8 }} />Abrir documento PDF</button>
                  </a>
                </div>
              )}
            </div>
            <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 28, padding: 28 }}>
              <h3 style={{ marginTop: 0 }}>Guía detallada</h3>
              <div style={{ color: C.muted, lineHeight: 1.8 }}>
                <p><strong style={{ color: C.ink }}>Qué vas a presentar:</strong><br />{guide.what_you_will_present}</p>
                <p><strong style={{ color: C.ink }}>Dónde presentarlo:</strong><br />{guide.where_to_submit}</p>
                <p><strong style={{ color: C.ink }}>Cómo presentarlo:</strong><br />{guide.how_to_submit}</p>
                <p><strong style={{ color: C.ink }}>Qué hacer si no responden:</strong><br />{guide.next_step_if_no_response}</p>
              </div>
            </div>
          </div>
          {!!guide.required_attachments?.length && (
            <div style={{ marginTop: 18, background: C.card, border: `1px solid ${C.border}`, borderRadius: 28, padding: 28 }}>
              <h3 style={{ marginTop: 0 }}>Documentos que debes llevar o adjuntar</h3>
              <div style={{ display: "grid", gap: 10 }}>
                {guide.required_attachments.map((item) => (
                  <div key={item} style={{ display: "flex", alignItems: "center", gap: 10 }}>
                    <CheckCircle2 size={18} color={C.success} />
                    <span>{item}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
          <div style={{ marginTop: 18, display: "flex", gap: 12, flexWrap: "wrap" }}>
            <button style={buttonStyle("ghost")} onClick={() => refreshCaseStatus().catch(() => {})}>Actualizar estado</button>
            <button style={buttonStyle("ghost")} onClick={clearGuestSession}>Cerrar este seguimiento</button>
          </div>
        </Section>
      )}

      <Section id="precio" title="Precio simple para salir rápido" subtitle="Un solo pago, sin planes complejos. Tu documento elaborado por especialistas.">
        <div style={{ background: C.primaryDark, color: "#fff", borderRadius: 28, padding: 32, display: "grid", gridTemplateColumns: "1fr auto", alignItems: "center", gap: 20 }}>
          <div>
            <div style={{ fontSize: 52, fontWeight: 900 }}>{PRICE_LABEL}</div>
            <p style={{ color: "rgba(255,255,255,0.78)", lineHeight: 1.8, maxWidth: 720 }}>
              Incluye diagnóstico preliminar, checkout, formulario completo, elaboración por especialistas, PDF final y checklist detallado con anexos, canal sugerido, tiempo de respuesta y siguiente paso si no responden o niegan.
            </p>
          </div>
          <a href="#diagnostico"><button style={buttonStyle("accent")}>Quiero empezar</button></a>
        </div>
      </Section>

      <footer style={{ padding: "36px 20px 60px", color: C.muted }}>
        <div style={{ maxWidth: 1100, margin: "0 auto", display: "flex", justifyContent: "space-between", gap: 20, flexWrap: "wrap" }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: 12, color: C.ink, fontWeight: 900 }}>
              <Scale size={20} />
              HazloPorMi
            </div>
            <p style={{ maxWidth: 480, lineHeight: 1.8 }}>
              No prometemos resultados judiciales o administrativos. El servicio consiste en diagnóstico, preparación documental y guía operativa.
            </p>
          </div>
          <div style={{ display: "grid", gap: 10 }}>
            <a href={ROUTES.terminos} onClick={(event) => { event.preventDefault(); navigate("terminos"); }} style={{ color: C.muted, textDecoration: "none" }}>Términos</a>
            <a href={ROUTES.privacidad} onClick={(event) => { event.preventDefault(); navigate("privacidad"); }} style={{ color: C.muted, textDecoration: "none" }}>Privacidad</a>
            <a href={ROUTES.contacto} onClick={(event) => { event.preventDefault(); navigate("contacto"); }} style={{ color: C.muted, textDecoration: "none" }}>Contacto</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
