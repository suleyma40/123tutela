import React, { useEffect, useMemo, useState } from "react";
import { Briefcase, CreditCard, FileText, HelpCircle, Layout, LogOut, Plus, Scale, Search, Shield, Upload } from "lucide-react";

import { Badge, Button, Field, SessionCard, TextArea, TextInput } from "../ui";
import { C, CATEGORIES } from "../theme";

const priorActionMap = {
  Salud: [
    { id: "eps_pqrs", label: "Ya radiqué PQRS o derecho de petición ante la EPS" },
    { id: "supersalud", label: "Ya escalé o intenté escalar ante Supersalud" },
  ],
  Laboral: [{ id: "reclamo_empleador", label: "Ya pedí respuesta formal al empleador" }],
  Bancos: [{ id: "reclamo_banco", label: "Ya reclamé ante el banco o entidad financiera" }],
  Servicios: [{ id: "reclamo_empresa", label: "Ya reclamé ante la empresa de servicios" }],
  Consumidor: [{ id: "reclamo_comercio", label: "Ya reclamé ante el comercio o proveedor" }],
  Datos: [{ id: "reclamo_fuente", label: "Ya reclamé ante la fuente o central de riesgo" }],
};

const statusLabels = {
  borrador: "Borrador",
  pendiente_pago: "Pendiente de pago",
  listo_para_envio: "Listo para envío",
  enviado: "Enviado",
  radicado: "Radicado",
  seguimiento: "Seguimiento",
  resuelto: "Resuelto",
  requiere_accion_manual: "Requiere acción manual",
};

const statusColors = {
  borrador: C.textMuted,
  pendiente_pago: C.warning,
  listo_para_envio: C.primary,
  enviado: C.accent,
  radicado: C.success,
  seguimiento: "#7C3AED",
  resuelto: C.success,
  requiere_accion_manual: C.danger,
};

const shortDate = (value) => new Date(value).toLocaleString("es-CO", { dateStyle: "medium", timeStyle: "short" });
const apiBase = import.meta.env.VITE_API_URL || "http://localhost:8000";
const widgetScriptUrl = "https://checkout.wompi.co/widget.js";

const normalizeAction = (value) =>
  String(value || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .trim();

function PaymentCard({ title, caseItem, catalog, onCreateWompiSession, onGetPayment, onRefreshCase, loading }) {
  const [includeFiling, setIncludeFiling] = useState(false);
  const [paymentMessage, setPaymentMessage] = useState("");
  const [selectedCode, setSelectedCode] = useState("");

  const suggestedCode = useMemo(() => {
    const action = normalizeAction(caseItem?.recommended_action);
    const exact = {
      "accion de tutela": "accion_tutela",
      "derecho de peticion": "derecho_peticion",
      "incidente de desacato": "incidente_desacato",
      "impugnacion de tutela": "impugnacion_tutela",
      "accion popular": "accion_popular",
      "accion de cumplimiento": "accion_cumplimiento",
      "habeas data": "habeas_data",
      "recurso de reposicion o apelacion": "recurso_reposicion_apelacion",
      "queja disciplinaria": "queja_disciplinaria",
      "queja formal": "queja_formal",
      "reclamo administrativo": "reclamo_administrativo",
      "carta formal a entidad": "carta_formal",
    };
    return exact[action] || "";
  }, [caseItem?.recommended_action]);

  useEffect(() => {
    setSelectedCode(suggestedCode || catalog[0]?.code || "");
  }, [suggestedCode, catalog]);

  const selectedProduct = useMemo(
    () => catalog.find((item) => item.code === selectedCode) || null,
    [catalog, selectedCode]
  );

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

  const pollPayment = async (reference) => {
    for (let attempt = 0; attempt < 8; attempt += 1) {
      const order = await onGetPayment(reference);
      if (order.status === "approved") {
        await onRefreshCase(caseItem.id);
        setPaymentMessage("Pago aprobado. Ya puedes generar el documento final.");
        return;
      }
      if (["declined", "error", "voided"].includes(order.status)) {
        await onRefreshCase(caseItem.id);
        setPaymentMessage(`Pago ${order.status}. Puedes volver a intentarlo si hace falta.`);
        return;
      }
      await new Promise((resolve) => setTimeout(resolve, 2000));
    }
    await onRefreshCase(caseItem.id);
    setPaymentMessage("El pago quedó en validación. Refresca en unos segundos para ver el estado final.");
  };

  const startPayment = async () => {
    if (!selectedProduct) {
      setPaymentMessage("No hay producto seleccionado para cobrar.");
      return;
    }
    setPaymentMessage("");
    const session = await onCreateWompiSession(caseItem.id, {
      product_code: selectedProduct.code,
      include_filing: includeFiling,
    });
    await launchWidget(session.checkout);
    setPaymentMessage("Pago iniciado. Esperando confirmación segura de Wompi.");
    await pollPayment(session.order.reference);
  };

  if (!caseItem) {
    return null;
  }

  const finalPrice = includeFiling ? selectedProduct?.price_with_filing_cop : selectedProduct?.price_cop;
  const filingPrice = selectedProduct ? selectedProduct.price_with_filing_cop - selectedProduct.price_cop : 0;

  return (
    <SessionCard title={title} subtitle="El análisis es gratis. Pagas solo cuando decides generar el documento o el documento con radicación.">
      <div style={{ display: "grid", gap: 14 }}>
        <div style={{ padding: 16, borderRadius: 16, background: C.primaryLight }}>
          <div style={{ fontWeight: 800, color: C.text }}>{caseItem.recommended_action || "Producto sugerido"}</div>
          <div style={{ color: C.textMuted, marginTop: 8 }}>
            {caseItem.strategy_text || "La plataforma analiza tu caso gratis y luego te ofrece el documento correspondiente."}
          </div>
        </div>
        <Field label="Producto a pagar">
          <select
            value={selectedCode}
            onChange={(event) => setSelectedCode(event.target.value)}
            style={{ width: "100%", padding: "14px 16px", borderRadius: 14, border: `1px solid ${C.border}`, background: "#fff", color: C.text }}
          >
            {catalog.map((item) => (
              <option key={item.code} value={item.code}>
                {item.name}
              </option>
            ))}
          </select>
        </Field>
        {selectedProduct && (
          <div className="glass-card" style={{ padding: 18 }}>
            <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "center" }}>
              <strong style={{ color: C.text }}>{selectedProduct.name}</strong>
              <Badge color={C.primary}>
                {(finalPrice || 0).toLocaleString("es-CO", { style: "currency", currency: "COP", maximumFractionDigits: 0 })}
              </Badge>
            </div>
            <div style={{ color: C.textMuted, marginTop: 10 }}>{selectedProduct.short_description}</div>
            <div style={{ color: C.textMuted, marginTop: 10 }}>{selectedProduct.detailed_description}</div>
            <div style={{ marginTop: 12, color: C.text, fontSize: 14 }}>
              Incluye análisis gratis, informe del derecho vulnerado y documento completo después del pago.
            </div>
            <label style={{ display: "flex", gap: 10, alignItems: "center", marginTop: 16, color: C.text }}>
              <input type="checkbox" checked={includeFiling} onChange={(event) => setIncludeFiling(event.target.checked)} />
              Agregar radicación por nosotros
              <strong>+{filingPrice.toLocaleString("es-CO")} COP</strong>
            </label>
            <div style={{ color: C.textMuted, fontSize: 13, marginTop: 10 }}>
              Si compras radicación, usamos la base operativa de juzgados y entidades en Colombia y te enviamos el comprobante al correo cuando aplique.
            </div>
            <div style={{ color: C.textMuted, fontSize: 13, marginTop: 8 }}>
              Siguiente paso sugerido: {selectedProduct.next_step_hint}
            </div>
          </div>
        )}
        <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
          <Button onClick={startPayment} disabled={loading || caseItem.payment_status === "pagado"} icon={CreditCard}>
            {caseItem.payment_status === "pagado" ? "Pago confirmado" : "Pagar con Wompi"}
          </Button>
        </div>
        {paymentMessage && <div style={{ color: C.textMuted }}>{paymentMessage}</div>}
      </div>
    </SessionCard>
  );
}

function DetailPanel({ detail, onViewDocument }) {
  if (!detail) {
    return <div className="glass-card" style={{ padding: 24, color: C.textMuted }}>Abre un expediente para ver timeline, archivos y trazabilidad.</div>;
  }

  const { case: item, files, submission_attempts: attempts, timeline } = detail;
  return (
    <div style={{ display: "grid", gap: 18 }}>
      <SessionCard title="Expediente activo" subtitle={`${item.category} · ${item.workflow_type.replaceAll("_", " ")}`}>
        <div style={{ display: "grid", gap: 12 }}>
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
            <Badge color={statusColors[item.status] || C.primary}>{statusLabels[item.status] || item.status}</Badge>
            <Badge color={item.payment_status === "pagado" ? C.success : C.warning}>Pago: {item.payment_status}</Badge>
            <Badge color={item.routing?.automatable ? C.primary : C.danger}>{item.routing?.automatable ? "Canal automático" : "Fallback manual"}</Badge>
          </div>
          <div style={{ color: C.text }}>{item.description}</div>
          <div style={{ padding: 16, borderRadius: 16, background: C.primaryLight }}>
            <div style={{ fontWeight: 800, color: C.text }}>{item.routing?.primary_target?.name || "Sin destino"}</div>
            <div style={{ color: C.textMuted, marginTop: 6 }}>{item.routing?.subject || "Sin asunto sugerido"}</div>
          </div>
          {item.generated_document && <Button variant="outline" onClick={() => onViewDocument(item)} style={{ width: "fit-content" }}>Abrir borrador</Button>}
        </div>
      </SessionCard>

      <SessionCard title="Archivos" subtitle="Anexos iniciales y evidencias del expediente.">
        {files.length ? files.map((file) => (
          <div key={file.id} style={{ display: "flex", justifyContent: "space-between", gap: 12, padding: 14, borderRadius: 14, border: `1px solid ${C.border}`, marginBottom: 10 }}>
            <div>
              <div style={{ fontWeight: 700, color: C.text }}>{file.original_name}</div>
              <div style={{ color: C.textMuted, fontSize: 13 }}>{file.file_kind} · {Math.round(file.file_size / 1024)} KB</div>
            </div>
            <a href={`${apiBase}/files/${file.id}`} target="_blank" rel="noreferrer" style={{ color: C.primary, textDecoration: "none", fontWeight: 700 }}>Abrir</a>
          </div>
        )) : <div style={{ color: C.textMuted }}>Sin archivos asociados.</div>}
      </SessionCard>

      <SessionCard title="Intentos de envío" subtitle="Trazabilidad de canal, contacto y radicado.">
        {attempts.length ? attempts.map((attempt) => (
          <div key={attempt.id} style={{ padding: 14, borderRadius: 14, border: `1px solid ${C.border}`, marginBottom: 10 }}>
            <div style={{ display: "flex", justifyContent: "space-between", gap: 12 }}>
              <strong style={{ color: C.text }}>{attempt.channel}</strong>
              <Badge color={attempt.radicado ? C.success : C.primary}>{attempt.status}</Badge>
            </div>
            <div style={{ color: C.textMuted, marginTop: 8 }}>{attempt.destination_name || "Destino manual"}</div>
            <div style={{ color: C.textMuted }}>{attempt.destination_contact || "Sin contacto"}</div>
            {attempt.radicado && <div style={{ marginTop: 8, color: C.success, fontWeight: 700 }}>Radicado: {attempt.radicado}</div>}
          </div>
        )) : <div style={{ color: C.textMuted }}>No hay envíos registrados.</div>}
      </SessionCard>

      <SessionCard title="Timeline" subtitle="Eventos del expediente.">
        {timeline.length ? timeline.map((event) => (
          <div key={event.id} style={{ padding: 14, borderRadius: 14, border: `1px solid ${C.border}`, marginBottom: 10 }}>
            <div style={{ display: "flex", justifyContent: "space-between", gap: 12 }}>
              <strong style={{ color: C.text }}>{event.event_type}</strong>
              <span style={{ color: C.textMuted, fontSize: 13 }}>{shortDate(event.created_at)}</span>
            </div>
            <pre style={{ margin: "8px 0 0", whiteSpace: "pre-wrap", color: C.textMuted, fontFamily: "'DM Sans', sans-serif" }}>{JSON.stringify(event.payload || {}, null, 2)}</pre>
          </div>
        )) : <div style={{ color: C.textMuted }}>Sin eventos todavía.</div>}
      </SessionCard>
    </div>
  );
}

export default function DashboardV2(props) {
  const {
    session,
    cases,
    internalCases,
    catalog,
    activeTab,
    setActiveTab,
    activeCaseDetail,
    setDocumentCase,
    onLogout,
    onSaveProfile,
    onPreview,
    onTempUpload,
    onCreateCase,
    onOpenCase,
    onConfirmPayment,
    onCreateWompiSession,
    onGetPayment,
    onRefreshCase,
    onGenerateDocument,
    onSubmitCase,
    onManualRadicado,
    onUploadEvidence,
    onInternalStatus,
    loading,
    actionError,
  } = props;

  const isInternal = session.user.role === "internal";
  const [profile, setProfile] = useState({
    name: session.user.name || "",
    document_number: session.user.document_number || "",
    phone: session.user.phone || "",
    city: session.user.city || "",
    department: session.user.department || "",
    address: session.user.address || "",
  });
  const [form, setForm] = useState({
    category: "",
    city: session.user.city || "Bogotá",
    department: session.user.department || "Cundinamarca",
    description: "",
    prior_actions: [],
  });
  const [tempFiles, setTempFiles] = useState([]);
  const [preview, setPreview] = useState(null);
  const [draftDetail, setDraftDetail] = useState(null);
  const [manualContact, setManualContact] = useState("");
  const [submissionNote, setSubmissionNote] = useState("");
  const [radicadoManual, setRadicadoManual] = useState("");
  const [radicadoNote, setRadicadoNote] = useState("");
  const [evidenceNote, setEvidenceNote] = useState("");
  const [internalStatus, setInternalStatus] = useState("seguimiento");
  const [internalNote, setInternalNote] = useState("");

  const profileReady = useMemo(
    () => [profile.name, profile.document_number, profile.phone, profile.city, profile.department, profile.address].every((value) => value?.trim()),
    [profile]
  );

  const stats = useMemo(
    () => [
      { label: "Expedientes", value: String(cases.length) },
      { label: "Pagados", value: String(cases.filter((item) => item.payment_status === "pagado").length) },
      { label: "Radicados", value: String(cases.filter((item) => item.status === "radicado").length) },
    ],
    [cases]
  );

  const sideItems = [
    { id: "inicio", label: "Inicio", icon: Layout },
    { id: "nuevo", label: "Nuevo trámite", icon: Plus },
    { id: "tramites", label: "Expedientes", icon: Briefcase },
    { id: "detalle", label: "Detalle activo", icon: FileText },
    { id: "ayuda", label: "Ayuda", icon: HelpCircle },
  ];
  if (isInternal) sideItems.push({ id: "interno", label: "Backoffice", icon: Shield });

  const selectedPriorActions = priorActionMap[form.category] || [];
  const canOperateActiveCase = !!activeCaseDetail?.case && activeCaseDetail.case.user_id === session.user.id;

  const resetWizard = () => {
    setForm({ category: "", city: session.user.city || "Bogotá", department: session.user.department || "Cundinamarca", description: "", prior_actions: [] });
    setTempFiles([]);
    setPreview(null);
    setDraftDetail(null);
  };

  const uploadTemp = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    const uploaded = await onTempUpload(file);
    setTempFiles((current) => [...current, uploaded]);
  };

  const uploadEvidence = async (event) => {
    const file = event.target.files?.[0];
    if (!file || !activeCaseDetail?.case?.id) return;
    await onUploadEvidence(activeCaseDetail.case.id, file, evidenceNote);
    setEvidenceNote("");
  };

  const content = {
    inicio: (
      <div style={{ display: "grid", gap: 24 }}>
        <div style={{ background: "linear-gradient(135deg, #0B1628 0%, #111D32 100%)", borderRadius: 24, padding: "40px 34px", color: "#fff" }}>
          <Badge color={C.accent}>123tutela MVP operativo</Badge>
          <h2 style={{ fontSize: 38, margin: "18px 0 10px", fontWeight: 800, fontFamily: "'Playfair Display', serif" }}>Expediente jurídico con pago y trazabilidad</h2>
          <p style={{ maxWidth: 620, color: "rgba(255,255,255,0.72)", lineHeight: 1.7 }}>
            El flujo cubre preview gratis, perfil obligatorio, pago antes del documento final, radicación automática cuando hay canal confiable y fallback manual cuando no lo hay.
          </p>
          <div style={{ display: "flex", gap: 12, marginTop: 24 }}>
            <Button onClick={() => setActiveTab("nuevo")}>Crear nuevo trámite</Button>
            <Button variant="ghost" style={{ color: "#fff", background: "rgba(255,255,255,0.08)", border: "1px solid rgba(255,255,255,0.1)" }} onClick={() => setActiveTab("tramites")}>
              Ver expedientes
            </Button>
          </div>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 18 }}>
          {stats.map((item) => (
            <div key={item.label} className="glass-card" style={{ padding: 22 }}>
              <div style={{ color: C.textMuted, fontSize: 13, fontWeight: 700 }}>{item.label}</div>
              <div style={{ marginTop: 10, fontSize: 24, fontWeight: 800, color: C.text }}>{item.value}</div>
            </div>
          ))}
        </div>
        <DetailPanel detail={activeCaseDetail} onViewDocument={setDocumentCase} />
      </div>
    ),
    nuevo: (
      <div style={{ display: "grid", gap: 18 }}>
        <SessionCard title="1. Perfil jurídico obligatorio" subtitle="Se usa en el documento, el asunto del correo y la radicación.">
          <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 16 }}>
            {[
              ["Nombre completo", "name"],
              ["Cédula", "document_number"],
              ["Celular", "phone"],
              ["Ciudad", "city"],
              ["Departamento", "department"],
              ["Dirección", "address"],
            ].map(([label, key]) => (
              <Field key={key} label={label}>
                <TextInput value={profile[key]} onChange={(event) => setProfile((current) => ({ ...current, [key]: event.target.value }))} />
              </Field>
            ))}
          </div>
          <div style={{ marginTop: 16, display: "flex", gap: 12 }}>
            <Button onClick={() => onSaveProfile(profile)}>Guardar perfil</Button>
            <Badge color={profileReady ? C.success : C.warning}>{profileReady ? "Perfil completo" : "Faltan datos"}</Badge>
          </div>
        </SessionCard>

        <SessionCard title="2. Análisis del caso" subtitle="Combina IA jurídica con reglas operativas y destino sugerido.">
          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12, marginBottom: 18 }}>
            {CATEGORIES.map((item) => (
              <button
                key={item.label}
                onClick={() => setForm((current) => ({ ...current, category: item.label, prior_actions: [] }))}
                style={{ textAlign: "left", padding: 16, borderRadius: 18, border: form.category === item.label ? `2px solid ${item.color}` : `1px solid ${C.border}`, background: form.category === item.label ? `${item.color}15` : C.card }}
              >
                <div style={{ fontWeight: 800, color: C.text }}>{item.title}</div>
                <div style={{ color: C.textMuted, marginTop: 6, fontSize: 14 }}>{item.desc}</div>
              </button>
            ))}
          </div>
          <TextArea value={form.description} onChange={(event) => setForm((current) => ({ ...current, description: event.target.value }))} placeholder="Describe hechos, fechas, respuestas previas y urgencia." />
          <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 16, marginTop: 16 }}>
            <Field label="Ciudad"><TextInput value={form.city} onChange={(event) => setForm((current) => ({ ...current, city: event.target.value }))} /></Field>
            <Field label="Departamento"><TextInput value={form.department} onChange={(event) => setForm((current) => ({ ...current, department: event.target.value }))} /></Field>
          </div>
          {!!selectedPriorActions.length && (
            <div style={{ display: "grid", gap: 8, marginTop: 16 }}>
              {selectedPriorActions.map((item) => (
                <label key={item.id} style={{ display: "flex", gap: 10, alignItems: "center", color: C.text }}>
                  <input
                    type="checkbox"
                    checked={form.prior_actions.includes(item.id)}
                    onChange={(event) =>
                      setForm((current) => ({
                        ...current,
                        prior_actions: event.target.checked ? [...current.prior_actions, item.id] : current.prior_actions.filter((value) => value !== item.id),
                      }))
                    }
                  />
                  {item.label}
                </label>
              ))}
            </div>
          )}
          <div style={{ marginTop: 16, display: "flex", gap: 12, flexWrap: "wrap" }}>
            <input id="wizard-upload" type="file" style={{ display: "none" }} onChange={uploadTemp} />
            <Button variant="secondary" onClick={() => document.getElementById("wizard-upload").click()} icon={Upload}>Subir anexo</Button>
            {tempFiles.map((item) => <Badge key={item.id} color={C.accent}>{item.original_name}</Badge>)}
            <Button onClick={async () => setPreview(await onPreview(form))} disabled={!form.category || form.description.trim().length < 20 || loading} icon={Search}>
              {loading ? "Analizando..." : "Generar preview"}
            </Button>
          </div>
        </SessionCard>

        {preview && (
          <SessionCard title="3. Preview gratis y expediente" subtitle="Se guarda antes del pago para que quede trazabilidad.">
            <div style={{ display: "grid", gap: 14 }}>
              <div style={{ padding: 16, borderRadius: 16, background: C.primaryLight }}>
                <div style={{ fontWeight: 800, color: C.text }}>{preview.recommended_action}</div>
                <div style={{ color: C.textMuted, marginTop: 8 }}>{preview.strategy}</div>
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 16 }}>
                <div className="glass-card" style={{ padding: 18 }}>
                  <strong style={{ color: C.text }}>Prerequisitos</strong>
                  <div style={{ display: "grid", gap: 8, marginTop: 12 }}>
                    {preview.prerequisites.length ? preview.prerequisites.map((item) => (
                      <Badge key={item.id} color={item.completed ? C.success : C.warning}>{item.completed ? "Cumplido" : "Pendiente"} · {item.label}</Badge>
                    )) : <span style={{ color: C.textMuted }}>Sin vía previa obligatoria detectada.</span>}
                  </div>
                </div>
                <div className="glass-card" style={{ padding: 18 }}>
                  <strong style={{ color: C.text }}>Destino sugerido</strong>
                  <div style={{ color: C.textMuted, marginTop: 12 }}>{preview.routing?.primary_target?.name || "Sin destino automático"}</div>
                  <div style={{ color: C.textMuted, marginTop: 6 }}>{preview.routing?.subject || "Sin asunto sugerido"}</div>
                </div>
              </div>
              {preview.warnings?.map((warning) => <div key={warning} style={{ color: "#92400E", background: "#FFFBEB", border: "1px solid #FDE68A", padding: 14, borderRadius: 14 }}>{warning}</div>)}
              <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
                <Button onClick={async () => { const detail = await onCreateCase({ ...form, attachment_ids: tempFiles.map((item) => item.id) }); setDraftDetail(detail); setActiveTab("detalle"); }} disabled={!profileReady}>Guardar expediente</Button>
                <Button variant="outline" onClick={resetWizard}>Reiniciar</Button>
              </div>
            </div>
          </SessionCard>
        )}

        {draftDetail && (
          <PaymentCard
            title="4. Pago real y documento"
            caseItem={draftDetail.case}
            catalog={catalog}
            onCreateWompiSession={onCreateWompiSession}
            onGetPayment={onGetPayment}
            onRefreshCase={onRefreshCase}
            loading={loading}
          />
        )}
      </div>
    ),
    tramites: cases.length ? (
      <div style={{ display: "grid", gap: 16 }}>
        {cases.map((item) => (
          <div key={item.id} className="glass-card" style={{ padding: 22, display: "grid", gap: 12 }}>
            <div style={{ display: "flex", justifyContent: "space-between", gap: 12 }}>
              <div>
                <div style={{ fontWeight: 800, color: C.text }}>{item.recommended_action || item.workflow_type}</div>
                <div style={{ color: C.textMuted, marginTop: 4 }}>{item.category} · {item.user_city}, {item.user_department}</div>
              </div>
              <Badge color={statusColors[item.status] || C.primary}>{statusLabels[item.status] || item.status}</Badge>
            </div>
            <div style={{ color: C.textMuted }}>{item.description}</div>
            <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
              <Badge color={item.payment_status === "pagado" ? C.success : C.warning}>Pago: {item.payment_status}</Badge>
              <Badge color={item.routing?.automatable ? C.primary : C.danger}>{item.routing?.automatable ? "Canal automático" : "Fallback manual"}</Badge>
            </div>
            <div style={{ display: "flex", gap: 10 }}>
              <Button variant="secondary" onClick={() => onOpenCase(item.id)}>Abrir expediente</Button>
              {item.generated_document && <Button variant="outline" onClick={() => setDocumentCase(item)}>Ver documento</Button>}
            </div>
          </div>
        ))}
      </div>
    ) : <div className="glass-card" style={{ padding: 24, color: C.textMuted }}>Todavía no tienes expedientes guardados.</div>,
    detalle: (
      <div style={{ display: "grid", gap: 18 }}>
        <DetailPanel detail={activeCaseDetail} onViewDocument={setDocumentCase} />
        {activeCaseDetail && canOperateActiveCase && (
          <>
            <PaymentCard
              title="Pago y activación del documento"
              caseItem={activeCaseDetail.case}
              catalog={catalog}
              onCreateWompiSession={onCreateWompiSession}
              onGetPayment={onGetPayment}
              onRefreshCase={onRefreshCase}
              loading={loading}
            />
            <SessionCard title="Acciones operativas" subtitle="Documento, envío, radicado manual y evidencia del caso activo.">
              <div style={{ display: "grid", gap: 14 }}>
                <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
                  <Button variant="secondary" onClick={() => onGenerateDocument(activeCaseDetail.case.id)} disabled={activeCaseDetail.case.payment_status !== "pagado"} icon={FileText}>Generar documento</Button>
                </div>
                <TextInput value={manualContact} onChange={(event) => setManualContact(event.target.value)} placeholder="Correo o contacto manual" />
                <TextArea value={submissionNote} onChange={(event) => setSubmissionNote(event.target.value)} placeholder="Notas del envío o fallback" style={{ minHeight: 90 }} />
                <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
                  <Button onClick={() => onSubmitCase(activeCaseDetail.case.id, { mode: "auto", notes: submissionNote })} disabled={!activeCaseDetail.case.generated_document}>Ejecutar envío automático</Button>
                  <Button variant="outline" onClick={() => onSubmitCase(activeCaseDetail.case.id, { mode: "manual_contact", manual_contact: manualContact, notes: submissionNote })}>Usar contacto manual</Button>
                  <Button variant="ghost" onClick={() => onSubmitCase(activeCaseDetail.case.id, { mode: "presencial", notes: submissionNote })}>Activar modo presencial</Button>
                </div>
                <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
                  <TextInput value={radicadoManual} onChange={(event) => setRadicadoManual(event.target.value)} placeholder="Número de radicado manual" />
                  <Button variant="secondary" onClick={() => onManualRadicado(activeCaseDetail.case.id, { radicado: radicadoManual, notes: radicadoNote })}>Registrar radicado manual</Button>
                </div>
                <TextArea value={radicadoNote} onChange={(event) => setRadicadoNote(event.target.value)} placeholder="Notas del radicado manual" style={{ minHeight: 80 }} />
                <input id="evidence-upload" type="file" style={{ display: "none" }} onChange={uploadEvidence} />
                <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
                  <TextInput value={evidenceNote} onChange={(event) => setEvidenceNote(event.target.value)} placeholder="Nota sobre la evidencia" />
                  <Button variant="outline" onClick={() => document.getElementById("evidence-upload").click()} icon={Upload}>Subir evidencia</Button>
                </div>
              </div>
            </SessionCard>
          </>
        )}
      </div>
    ),
    ayuda: (
      <div style={{ display: "grid", gap: 12 }}>
        {[
          "Preview gratis antes del pago.",
          "Pago obligatorio antes del documento final y la radicación.",
          "Canal automático solo cuando existe contacto confiable en la base operativa.",
          "Fallback manual o presencial cuando no hay canal digital verificado.",
        ].map((item) => <div key={item} className="glass-card" style={{ padding: 18, color: C.text }}>{item}</div>)}
      </div>
    ),
    interno: (
      <div style={{ display: "grid", gap: 16 }}>
        {internalCases.map((item) => (
          <div key={item.id} className="glass-card" style={{ padding: 18, display: "flex", justifyContent: "space-between", gap: 12, alignItems: "center" }}>
            <div>
              <div style={{ fontWeight: 800, color: C.text }}>{item.user_name} · {item.recommended_action || item.workflow_type}</div>
              <div style={{ color: C.textMuted, marginTop: 4 }}>{item.category} · {item.user_city}, {item.user_department}</div>
            </div>
            <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
              <Badge color={statusColors[item.status] || C.primary}>{statusLabels[item.status] || item.status}</Badge>
              <Button variant="secondary" onClick={() => onOpenCase(item.id, "internal")}>Abrir</Button>
            </div>
          </div>
        ))}
        {activeCaseDetail && (
          <SessionCard title="Actualizar estado interno" subtitle="Úsalo para marcar seguimiento, resolución o intervención manual.">
            <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
              <TextInput value={internalStatus} onChange={(event) => setInternalStatus(event.target.value)} />
              <TextInput value={internalNote} onChange={(event) => setInternalNote(event.target.value)} placeholder="Nota interna" />
              <Button onClick={() => onInternalStatus(activeCaseDetail.case.id, { status: internalStatus, note: internalNote })}>Guardar estado</Button>
            </div>
          </SessionCard>
        )}
      </div>
    ),
  };

  return (
    <div style={{ minHeight: "100vh", background: "#111827", display: "flex", color: "#fff" }}>
      <aside style={{ width: 270, background: "#0F172A", borderRight: "1px solid rgba(255,255,255,0.08)", padding: 24, display: "flex", flexDirection: "column" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 34 }}>
          <div style={{ width: 38, height: 38, borderRadius: 10, background: C.primary, display: "grid", placeItems: "center" }}><Scale size={20} /></div>
          <strong style={{ fontSize: 22 }}>123<span style={{ color: C.primary }}>tutela</span></strong>
        </div>
        <div style={{ display: "grid", gap: 8, flex: 1 }}>
          {sideItems.map((item) => (
            <button key={item.id} onClick={() => setActiveTab(item.id)} style={{ border: "none", background: activeTab === item.id ? "#fff" : "transparent", color: activeTab === item.id ? C.primary : "rgba(255,255,255,0.65)", display: "flex", alignItems: "center", gap: 12, padding: "12px 14px", borderRadius: 14, fontSize: 14, fontWeight: 700, cursor: "pointer" }}>
              <item.icon size={18} />{item.label}
            </button>
          ))}
        </div>
        <div style={{ padding: 14, borderRadius: 16, background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <div style={{ width: 42, height: 42, borderRadius: 12, background: C.primary, display: "grid", placeItems: "center", fontWeight: 800 }}>{session.user.name.slice(0, 2).toUpperCase()}</div>
            <div style={{ flex: 1, overflow: "hidden" }}>
              <div style={{ fontWeight: 800, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{session.user.name}</div>
              <div style={{ fontSize: 12, color: "rgba(255,255,255,0.55)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{session.user.email}</div>
            </div>
            <button onClick={onLogout} style={{ background: "transparent", border: "none", color: "rgba(255,255,255,0.5)", cursor: "pointer" }}><LogOut size={16} /></button>
          </div>
        </div>
      </aside>

      <main style={{ flex: 1, padding: 34, background: C.bg, overflowY: "auto" }}>
        {content[activeTab]}
        {actionError && <div style={{ marginTop: 16, color: C.danger }}>{actionError}</div>}
      </main>
    </div>
  );
}
