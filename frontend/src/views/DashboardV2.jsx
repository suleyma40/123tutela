import React, { useEffect, useMemo, useState } from "react";
import { ArrowLeft, ArrowRight, Briefcase, CreditCard, FileText, HelpCircle, Layout, LogOut, Plus, Scale, Shield, Upload } from "lucide-react";

import { api } from "../lib/api";
import { Badge, Button, Field, SessionCard, TextArea, TextInput } from "../ui";
import { ACTIVE_CASE_CATEGORIES, C } from "../theme";

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

const defaultIntakeFields = {
  target_entity: "",
  event_date: "",
  event_period_detail: "",
  concrete_request: "",
  current_harm: "",
  prior_response_status: "sin_respuesta",
  previous_response: "",
  response_channel: "",
  case_reference: "",
  request_type: "interes_particular",
  numbered_requests: "",
  authority_act_type: "",
  authority_act_date: "",
  evidence_summary: "",
  supporting_documents: "",
  eps_name: "",
  ips_name: "",
  diagnosis: "",
  treatment_needed: "",
  urgency_detail: "",
  medical_order_date: "",
  treating_doctor_name: "",
  treating_ips_name: "",
  eps_request_date: "",
  eps_request_channel: "",
  eps_request_reference: "",
  eps_response_detail: "",
  disputed_data: "",
  requested_data_action: "corregir",
  labor_relation_type: "",
  labor_employer_name: "",
  labor_measure_date: "",
  labor_salary_detail: "",
  dismissal_or_measure: "",
  minimum_vital_impact: "",
  reinforced_stability: "",
  bank_product_type: "",
  bank_amount_involved: "",
  bank_claim_goal: "",
  bank_event_date: "",
  disputed_charge: "",
  report_or_block_reason: "",
  service_company_name: "",
  service_type: "",
  subscriber_reference: "",
  invoice_period: "",
  service_impact: "",
  cutoff_or_billing_detail: "",
  provider_name: "",
  purchase_date: "",
  order_reference: "",
  seller_response_detail: "",
  product_or_service_issue: "",
  guarantee_or_refund_request: "",
  complaint_reason: "",
  complaint_expected_response: "",
  administrative_error_detail: "",
  administrative_requested_fix: "",
  disciplinary_subject_name: "",
  disciplinary_subject_role: "",
  disciplinary_conduct: "",
  disciplinary_event_date: "",
  compliance_norm_or_act: "",
  compliance_authority: "",
  compliance_prior_requirement: "",
  compliance_breach_detail: "",
  tutela_court_name: "",
  tutela_ruling_date: "",
  tutela_decision_result: "",
  tutela_appeal_reason: "",
  tutela_order_summary: "",
  tutela_noncompliance_detail: "",
  tutela_previous_action_detail: "",
  tutela_oath_statement: "",
  tutela_no_temperity_detail: "",
  tutela_other_means_detail: "",
  tutela_immediacy_detail: "",
  tutela_special_protection_detail: "",
  tutela_private_party_ground: "",
  acting_capacity: "nombre_propio",
  represented_person_name: "",
  represented_person_document: "",
  represented_person_birth_date: "",
  represented_person_age: "",
  represented_person_identity: "",
  represented_person_condition: "",
  petition_target_nature: "publica",
  petition_private_ground: "",
  petition_previous_submission_date: "",
  petition_sector_rule: "",
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

const specialProtectionOptions = ["Menor de edad", "Adulto mayor", "Embarazada", "Discapacidad", "Otro", "No aplica"];
const autofillFieldLabels = {
  key_dates: "Fechas detectadas",
  target_entity: "Entidad detectada",
  evidence_summary: "Pruebas detectadas",
  bank_product_type: "Producto financiero",
  disputed_charge: "Cobro discutido",
  bank_amount_involved: "Monto detectado",
  bank_event_date: "Fecha del primer hecho",
  diagnosis: "Diagnostico detectado",
  treatment_needed: "Tratamiento o servicio",
  disputed_data: "Dato cuestionado",
  prior_claim: "Gestion previa detectada",
  prior_claim_result: "Respuesta o barrera detectada",
  urgency_detail: "Riesgo o afectacion actual",
  tutela_other_means_detail: "Gestion previa resumida",
  special_protection: "Proteccion especial",
  tutela_special_protection_detail: "Detalle de proteccion especial",
  prior_tutela: "Tutela previa",
};
const evidenceTypeHints = {
  Bancos: ["Extractos bancarios PDF", "Capturas del cobro o movimiento", "Chat o correo con el banco", "Contrato o reglamento del producto", "Radicado o respuesta previa"],
  Salud: ["Orden medica o formula", "Historia clinica PDF", "Capturas de autorizaciones", "Respuesta de EPS", "Facturas o soportes de pago"],
  Datos: ["Reporte de central de riesgo", "Pantallazo del dato cuestionado", "Derecho de peticion o reclamo previo", "Respuesta de la fuente", "Correo o PDF con evidencia"],
  default: ["PDF", "Fotos o capturas", "Chats exportados", "Correos", "Word o documentos escaneados"],
};

const summarizeUploadedEvidence = (files = []) =>
  files
    .map((item) => item?.original_name || item?.name || "")
    .filter(Boolean)
    .join(", ");

const hasEvidenceAvailable = (form, files = []) =>
  Boolean(form.evidence_summary.trim() || (files || []).length);

const formatAutofillEntry = ([key, value]) => `${autofillFieldLabels[key] || key}: ${String(value)}`;

const parseRepresentedPersonIdentity = (value = "") => {
  const text = String(value || "").trim();
  if (!text) return {};
  const next = {};
  const birthDateMatch = text.match(/\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b/);
  if (birthDateMatch) next.represented_person_birth_date = birthDateMatch[1];
  const ageMatch = text.match(/\b(\d{1,2}\s*(?:anos|años))\b/i);
  if (ageMatch) next.represented_person_age = ageMatch[1];
  const documentMatch = text.match(/\b(?:ti|nuip|rc|registro civil|documento)?\s*#?\s*([0-9.\-]{6,20})\b/i);
  if (documentMatch) next.represented_person_document = documentMatch[1];
  const nameCandidate = text
    .replace(/\b(?:ti|nuip|rc|registro civil|documento)\b/gi, " ")
    .replace(/\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b/g, " ")
    .replace(/\b\d{1,2}\s*(?:anos|años)\b/gi, " ")
    .replace(/[0-9.\-#]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
  if (nameCandidate.split(" ").filter(Boolean).length >= 2) {
    next.represented_person_name = nameCandidate;
  }
  return next;
};

const mergeDetectedFormValues = (currentForm = {}, detectedForm = {}) => {
  const next = { ...currentForm };
  Object.entries(detectedForm || {}).forEach(([key, value]) => {
    if (key.startsWith("_")) return;
    const currentValue = currentForm?.[key];
    const normalizedCurrent = typeof currentValue === "string" ? currentValue.trim() : currentValue;
    const normalizedValue = typeof value === "string" ? value.trim() : value;
    const shouldFillString = !normalizedCurrent || normalizedCurrent === "no" || normalizedCurrent === "No aplica";
    const shouldFillOther = currentValue == null || currentValue === "";
    if ((typeof normalizedValue === "string" && normalizedValue && shouldFillString) || (typeof normalizedValue !== "string" && normalizedValue && shouldFillOther)) {
      next[key] = value;
    }
  });
  return next;
};

const routingChannelLabels = {
  email: "Correo",
  portal: "Portal",
  portal_pqrs: "Portal PQRS",
  email_alterno: "Correo alterno",
  telefono: "Telefono",
  manual: "Manual",
};

const getRoutingChannelLabel = (channel) => routingChannelLabels[String(channel || "").toLowerCase()] || (channel || "Manual");
const hasRefundDestinationHint = (form = {}) => {
  const text = [
    form.refund_destination,
    form.concrete_request,
    form.case_story,
    form.bank_claim_goal,
  ]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();
  return [
    "misma tarjeta",
    "misma cuenta",
    "mismo producto",
    "a la misma tarjeta",
    "a la misma cuenta",
    "a mi tarjeta",
    "a mi cuenta",
    "a la tarjeta",
    "reintegrar",
    "devolver a",
  ].some((marker) => text.includes(marker));
};

const getFieldFixLocation = (field = "", recommendedAction = "") => {
  const normalized = String(field || "").toLowerCase();
  const action = String(recommendedAction || "").toLowerCase();

  if (["full_name", "document_number", "address", "phone", "copy_email"].includes(normalized)) return "Datos personales y de contacto";
  if (["target_entity", "target_pqrs_email", "target_phone", "target_website", "target_identifier"].includes(normalized)) return "Entidad y canal de radicacion";
  if (["key_dates", "bank_event_date", "prior_claim_date", "petition_previous_submission_date"].includes(normalized)) return "Fechas importantes del caso";
  if (["case_story", "concrete_request", "numbered_requests", "request_type", "requested_data_action"].includes(normalized)) return "Solucion concreta que necesitas";
  if (["available_evidence", "evidence_summary", "supporting_documents"].includes(normalized)) return "Pruebas y anexos";
  if (normalized.startsWith("bank_") || ["disputed_charge", "refund_destination"].includes(normalized)) return "Detalle del caso financiero";
  if (["diagnosis", "treatment_needed", "urgency_detail", "eps_name"].includes(normalized)) return "Detalle del caso de salud";
  if (["disputed_data", "requested_data_action"].includes(normalized)) return "Detalle del dato o reporte cuestionado";
  if (normalized.startsWith("tutela_") || ["acting_capacity", "represented_person_name", "represented_person_age", "represented_person_document", "special_protection", "prior_tutela", "prior_tutela_reason", "ongoing_harm", "subsidiarity_support"].includes(normalized)) {
    return "Preguntas finas para tutela";
  }
  if (action.includes("tutela")) return "Paso de tutela y urgencia actual";
  if (action.includes("peticion")) return "Paso de derecho de peticion";
  return "Completa datos del caso";
};

const buildActionableGaps = (caseItem = {}, pendingQuestions = []) => {
  const recommendedAction = caseItem?.recommended_action || caseItem?.workflow_type || "";
  const finalValidation = caseItem?.final_validation || caseItem?.submission_summary?.final_validation || {};
  const existing = finalValidation?.actionable_gaps || [];
  if (existing.length) {
    return existing.map((item) => ({
      label: item.label || item.prompt || "Dato critico faltante",
      prompt: item.prompt || item.label || "Completa este dato antes de entregar.",
      where_to_fix: item.where_to_fix || getFieldFixLocation(item.field, recommendedAction),
    }));
  }
  return (pendingQuestions || [])
    .filter((item) => item?.priority === "alta")
    .map((item) => ({
      label: item.reason || item.question || "Dato critico faltante",
      prompt: item.question || item.reason || "Completa este dato antes de entregar.",
      where_to_fix: getFieldFixLocation(item.field, recommendedAction),
    }));
};

const buildSubmissionSignatureNote = (signatureForm = {}, baseNote = "") => {
  const signatureLine = [
    "Firma electronica simple:",
    signatureForm.full_name || "sin nombre",
    signatureForm.document_number || "sin cc",
    signatureForm.city || "sin ciudad",
    signatureForm.date || "sin fecha",
  ].join(" | ");
  return [baseNote || "", signatureLine].filter(Boolean).join(" || ").slice(0, 500);
};

const SIMPLE_SIGNATURE_CONSENT_VERSION = "ses_v1";
const SIMPLE_SIGNATURE_CONSENT_TEXT =
  "Autorizo a 123tutela para usar mi firma electronica simple en la radicacion o envio del documento generado para este caso. Confirmo que revise el contenido final antes de aceptarlo, que los datos de identificacion y ciudad que suministro son correctos, y que esta aceptacion expresa representa mi voluntad de presentar este documento por medios electronicos en el canal aplicable. Entiendo que la plataforma conservara evidencia basica de esta aceptacion, incluida la fecha y hora, la version del consentimiento y metadatos tecnicos del envio disponibles en el sistema.";

const timelineEventLabelMap = {
  case_created: "Expediente creado",
  evidence_uploaded: "Prueba agregada",
  document_generated: "Documento generado",
  document_regenerated: "Documento actualizado",
  signed_submission_ready: "Documento firmado",
  submission_requested: "Radicacion solicitada",
  submission_sent: "Documento enviado",
  filing_completed: "Radicacion registrada",
  manual_filing_reported: "Radicacion reportada",
  judicial_update_reported: "Novedad reportada",
};

const hiddenTimelineEventTypes = new Set([
  "payment_order_created",
  "payment_link_created",
  "payment_reference_created",
  "payment_status_checked",
  "case_viewed",
]);

const isMeaningfulTimelineEvent = (event = {}) => {
  const type = String(event.event_type || "").toLowerCase();
  return !!type && !hiddenTimelineEventTypes.has(type);
};

const formatTimelineEventLabel = (event = {}) => {
  const type = String(event.event_type || "").toLowerCase();
  return timelineEventLabelMap[type] || String(type || "evento").replaceAll("_", " ");
};

const formatTimelineEventDetail = (event = {}) => {
  if (event.payload?.radicado) return `Comprobante o radicado: ${event.payload.radicado}.`;
  if (event.payload?.destination_name) return `Destino: ${event.payload.destination_name}.`;
  if (event.payload?.channel) return `Canal usado: ${getRoutingChannelLabel(event.payload.channel)}.`;
  if (event.payload?.status) return `Estado: ${String(event.payload.status).replaceAll("_", " ")}.`;
  return "Novedad registrada en tu expediente.";
};

const formatDeliveryStatusLabel = (status = "") => {
  const normalized = String(status || "").toLowerCase();
  if (["sent", "success", "delivered"].includes(normalized)) return "Enviado";
  if (["pending", "queued", "processing"].includes(normalized)) return "En proceso";
  if (["error", "failed"].includes(normalized)) return "Requiere revision";
  return normalized ? normalized.replaceAll("_", " ") : "Pendiente";
};

const buildPostPayDescription = (form, caseItem) => {
  const parts = [
    caseItem?.recommended_action ? `Documento esperado: ${caseItem.recommended_action}.` : "",
    form.target_entity ? `Entidad reclamada: ${form.target_entity}.` : "",
    form.target_identifier ? `Identificacion de la entidad: ${form.target_identifier}.` : "",
    form.target_address ? `Direccion de la entidad: ${form.target_address}.` : "",
    form.legal_representative ? `Representante legal conocido: ${form.legal_representative}.` : "",
    form.target_pqrs_email ? `Correo PQRS sugerido: ${form.target_pqrs_email}.` : "",
    form.target_phone ? `Telefono de contacto de la entidad: ${form.target_phone}.` : "",
    form.target_superintendence ? `Entidad de control relacionada: ${form.target_superintendence}.` : "",
    form.case_story ? `Relato detallado: ${form.case_story}` : "",
    form.concrete_request ? `Resultado o solucion esperada por la persona usuaria: ${form.concrete_request}.` : "",
    form.key_dates ? `Fechas importantes: ${form.key_dates}.` : "",
    form.bank_product_type ? `Producto financiero: ${form.bank_product_type}.` : "",
    form.disputed_charge ? `Cobro o concepto discutido: ${form.disputed_charge}.` : "",
    form.bank_amount_involved ? `Valor o monto discutido: ${form.bank_amount_involved}.` : "",
    form.bank_event_date ? `Fecha del primer cobro o hecho relevante: ${form.bank_event_date}.` : "",
    form.bank_account_reference ? `Referencia del producto financiero: ${form.bank_account_reference}.` : "",
    form.refund_destination
      ? `Destino solicitado para la devolucion: ${form.refund_destination}.`
      : hasRefundDestinationHint(form)
        ? "Destino solicitado para la devolucion: al mismo producto o medio ya indicado por la persona usuaria."
        : "",
    form.tutela_previous_action_detail ? `Otra tutela o medida previa sobre el mismo caso: ${form.tutela_previous_action_detail}.` : "",
    form.tutela_oath_statement ? `Declaracion bajo juramento sobre no temeridad: ${form.tutela_oath_statement}.` : "",
    form.tutela_no_temperity_detail ? `No temeridad o tutela previa: ${form.tutela_no_temperity_detail}.` : "",
    form.tutela_other_means_detail ? `Gestiones previas y estado actual del problema: ${form.tutela_other_means_detail}.` : "",
    form.tutela_immediacy_detail ? `Inmediatez o justificacion temporal: ${form.tutela_immediacy_detail}.` : "",
    form.tutela_special_protection_detail ? `Condicion de especial proteccion: ${form.tutela_special_protection_detail}.` : "",
    form.tutela_private_party_ground ? `Fundamento contra particular: ${form.tutela_private_party_ground}.` : "",
    form.prior_claim === "si"
      ? `Gestion previa: ${form.prior_claim_result || "Si reclamo antes."}`
      : form.prior_claim === "no"
        ? "Gestion previa: No ha reclamado directamente ante la entidad."
        : "",
    form.prior_claim_date ? `Fecha del reclamo previo: ${form.prior_claim_date}.` : "",
    form.entity_response ? `Respuesta recibida: ${form.entity_response}` : "",
    form.evidence_summary ? `Pruebas o soportes disponibles: ${form.evidence_summary}.` : "",
    form.special_protection && form.special_protection !== "No aplica" ? `Sujeto de especial proteccion: ${form.special_protection}.` : "",
    form.prior_tutela === "si" ? `Ya hubo tutela previa. Diferencia relevante: ${form.prior_tutela_reason || "Sin detalle adicional."}` : "",
    form.copy_email ? `Enviar copia adicional a: ${form.copy_email}.` : "",
  ].filter(Boolean);

  return parts.join("\n");
};

const getPostPayMissingFields = (form, caseItem) => {
  const missing = [];
  if (!form.full_name.trim()) missing.push("Nombre completo");
  if (!form.document_number.trim()) missing.push("Cedula");
  if (!form.address.trim()) missing.push("Direccion");
  if (!form.phone.trim()) missing.push("WhatsApp / celular");
  if (!form.target_entity.trim()) missing.push("Entidad contra la que reclamas");
  if (!form.case_story.trim()) missing.push("Cuenta con detalle que paso");
  if (!form.concrete_request.trim()) missing.push("Que solucion concreta necesitas");
  if (!form.key_dates.trim()) missing.push("Fechas importantes");
  if (!form.evidence_summary?.trim()) missing.push("Pruebas o soportes disponibles");
  if (!form.special_protection.trim()) missing.push("Proteccion especial");
  if (!form.prior_tutela.trim()) missing.push("Tutela previa");
  if ((caseItem?.category || "").toLowerCase() === "bancos") {
    if (!form.bank_product_type?.trim()) missing.push("Producto financiero");
    if (!form.disputed_charge?.trim()) missing.push("Cobro o concepto discutido");
    if (!form.bank_amount_involved?.trim()) missing.push("Valor o monto cobrado");
    if (!form.bank_event_date?.trim()) missing.push("Fecha del primer cobro o hecho");
    if (form.prior_claim === "si" && !form.prior_claim_date?.trim()) missing.push("Fecha del reclamo previo");
  }
  if ((caseItem?.recommended_action || "").toLowerCase().includes("tutela") && form.prior_tutela === "si" && !form.prior_tutela_reason.trim()) {
    missing.push("Que paso con la solicitud o tutela anterior");
  }
  return missing;
};

const getPostPayQuestionPrompts = (form, caseItem) => {
  const prompts = [];
  const category = (caseItem?.category || "").toLowerCase();
  const action = normalizeAction(caseItem?.recommended_action || caseItem?.workflow_type || "");
  if (!form.key_dates.trim()) prompts.push("Que fecha exacta o aproximada tuvo el primer hecho relevante?");
  if (!form.concrete_request.trim()) prompts.push("Que solucion concreta necesitas para que el problema quede resuelto?");
  if (!form.evidence_summary?.trim()) prompts.push("Que pruebas tienes hoy: extracto, chat, correo, captura, PDF, audio o contrato?");
  if (category === "bancos") {
    if (!form.bank_product_type?.trim()) prompts.push("Que producto financiero esta involucrado: tarjeta de credito, cuenta, prestamo, Nequi u otro?");
    if (!form.disputed_charge?.trim()) prompts.push("Cual es exactamente el cobro discutido: seguro, cuota de manejo, interes, reporte o bloqueo?");
    if (!form.bank_amount_involved?.trim()) prompts.push("Por que valor o monto te estan cobrando ese concepto?");
    if (!form.bank_event_date?.trim()) prompts.push("Desde que fecha comenzaron los cobros o desde cuando viste el cargo por primera vez?");
    if (form.prior_claim === "si" && !form.prior_claim_date?.trim()) prompts.push("En que fecha reclamaste al banco y por que canal lo hiciste?");
    if (form.prior_claim === "si" && !form.prior_claim_result?.trim()) prompts.push("Que respondio el banco o que paso despues de tu reclamo?");
    if (!form.refund_destination?.trim() && !hasRefundDestinationHint(form)) prompts.push("Si pides devolucion del dinero, a que cuenta, tarjeta o producto debe hacerse el reintegro?");
  }
  if (category === "datos" && !form.requested_data_action?.trim()) prompts.push("Como deberia quedar corregido ese dato o reporte?");
  if (action.includes("derecho de peticion") && !form.numbered_requests?.trim()) prompts.push("Si la entidad te respondiera hoy, cuales serian las 2 o 3 soluciones concretas que necesitas recibir?");
  if (action === "accion de tutela" && !form.tutela_other_means_detail?.trim()) prompts.push("Que hiciste antes para resolverlo y que hizo despues la EPS o la entidad?");
  if (action === "accion de tutela" && !form.tutela_immediacy_detail?.trim()) prompts.push("Que sigue pasando hoy al paciente o al afectado desde que no entregan el servicio?");
  if (action === "accion de tutela" && category === "salud") {
    if (!form.medical_order_date?.trim()) prompts.push("En que fecha te ordenaron el examen, medicamento o procedimiento?");
    if (!form.treating_doctor_name?.trim()) prompts.push("Como se llama el medico tratante que ordeno el servicio?");
    if (!form.eps_request_date?.trim()) prompts.push("En que fecha solicitaste a la EPS la autorizacion o prestacion?");
    if (!form.eps_response_detail?.trim()) prompts.push("Que hizo la EPS despues: nego, guardo silencio, demoro o no agendo?");
  }
  return prompts;
};

const buildPostPayInterviewStepsClean = (form, caseItem) => {
  const category = (caseItem?.category || "").toLowerCase();
  const action = normalizeAction(caseItem?.recommended_action || caseItem?.workflow_type || "");
  const steps = [
    {
      id: "case_story",
      question: "Cuentame brevemente que paso, en que orden y como te afecta hoy.",
      placeholder: "Ej: saque la tarjeta en octubre, luego empezaron a cobrar un seguro que nunca autorice y el banco no resolvio.",
      multiline: true,
      show: !form.case_story.trim(),
    },
    {
      id: "key_dates",
      question: "Que fechas exactas o aproximadas recuerdas de los hechos?",
      placeholder: "Ej: octubre de 2025 apertura, noviembre de 2025 primer cobro, enero de 2026 reclamo",
      multiline: false,
      show: !form.key_dates.trim(),
    },
    {
      id: "concrete_request",
      question: "Que necesitas que pase para que el problema quede resuelto?",
      placeholder: "Ej: eliminar el seguro, devolver los cobros, entregar el medicamento o corregir el reporte",
      multiline: true,
      show: !form.concrete_request.trim(),
    },
    {
      id: "evidence_summary",
      question: "Que pruebas tienes hoy disponibles?",
      placeholder: "Ej: extractos PDF, capturas, chat, correo, contrato, audio o radicado",
      multiline: true,
      show: !form.evidence_summary?.trim(),
    },
  ];

  if (category === "bancos") {
    steps.push(
      {
        id: "bank_product_type",
        question: "Que producto financiero esta involucrado?",
        placeholder: "Ej: tarjeta de credito, cuenta de ahorros, prestamo o Nequi",
        multiline: false,
        show: !form.bank_product_type?.trim(),
      },
      {
        id: "disputed_charge",
        question: "Cual es exactamente el cobro o concepto discutido?",
        placeholder: "Ej: seguro de desempleo, cuota de manejo, interes o cargo no reconocido",
        multiline: false,
        show: !form.disputed_charge?.trim(),
      },
      {
        id: "bank_amount_involved",
        question: "Por que valor te estan cobrando ese concepto o cuanto te han cobrado en total?",
        placeholder: "Ej: $38.500 mensuales o $154.000 acumulados",
        multiline: false,
        show: !form.bank_amount_involved?.trim(),
      },
      {
        id: "bank_event_date",
        question: "Desde que fecha viste el primer cobro o el primer hecho relevante?",
        placeholder: "Ej: 12 de octubre de 2025",
        multiline: false,
        show: !form.bank_event_date?.trim(),
      },
      {
        id: "bank_account_reference",
        question: "Que referencia del producto puedes compartir sin exponer todo el dato?",
        placeholder: "Ej: tarjeta terminada en 4821 o cuenta de ahorros terminada en 9912",
        multiline: false,
        show: !form.bank_account_reference?.trim(),
      },
      {
        id: "refund_destination",
        question: "Si pides devolucion, a que cuenta, tarjeta o medio deben abonarte los valores?",
        placeholder: "Ej: a la misma tarjeta terminada en 4821 o a la cuenta de ahorros Bancolombia",
        multiline: false,
        show: !form.refund_destination?.trim() && !hasRefundDestinationHint(form),
      }
    );
    if (form.prior_claim === "si") {
      steps.push(
        {
          id: "prior_claim_date",
          question: "En que fecha reclamaste al banco y por que canal lo hiciste?",
          placeholder: "Ej: 14 de enero de 2026 por PQRS web y llamada",
          multiline: false,
          show: !form.prior_claim_date?.trim(),
        },
        {
          id: "prior_claim_result",
          question: "Que te respondio el banco o que ocurrio despues del reclamo?",
          placeholder: "Ej: dijeron que el seguro estaba activo, pero no enviaron autorizacion ni soporte",
          multiline: true,
          show: !form.prior_claim_result?.trim(),
        }
      );
    }
  }

  if (category === "salud") {
    steps.push(
      {
        id: "diagnosis",
        question: "Cual es el diagnostico o la condicion medica principal?",
        placeholder: "Ej: artritis reumatoide, embarazo de alto riesgo o trastorno de ansiedad",
        multiline: false,
        show: !form.diagnosis.trim(),
      },
      {
        id: "treatment_needed",
        question: "Que medicamento, procedimiento, cita o tratamiento hace falta?",
        placeholder: "Ej: medicamento biologico, resonancia, cirugia o cita con especialista",
        multiline: false,
        show: !form.treatment_needed.trim(),
      },
      {
        id: "urgency_detail",
        question: "Por que esto es urgente hoy?",
        placeholder: "Ej: el dolor empeora, suspendieron tratamiento o existe riesgo vital",
        multiline: true,
        show: !form.urgency_detail.trim(),
      },
      {
        id: "medical_order_date",
        question: "En que fecha te ordenaron el examen, procedimiento o tratamiento?",
        placeholder: "Ej: 12 de marzo de 2026",
        multiline: false,
        show: !form.medical_order_date?.trim(),
      },
      {
        id: "treating_doctor_name",
        question: "Como se llama el medico tratante que ordeno ese servicio?",
        placeholder: "Ej: Dra. Ana Gomez",
        multiline: false,
        show: !form.treating_doctor_name?.trim(),
      },
      {
        id: "eps_request_date",
        question: "En que fecha pediste a la EPS la autorizacion o prestacion del servicio?",
        placeholder: "Ej: 14 de marzo de 2026",
        multiline: false,
        show: action === "accion de tutela" && !form.eps_request_date?.trim(),
      },
      {
        id: "eps_response_detail",
        question: "Que hizo la EPS despues: nego, guardo silencio, demoro, no agendo o puso otra barrera?",
        placeholder: "Ej: no respondio, nego por fuera de PBS, no genero agenda o dejo el caso pendiente",
        multiline: true,
        show: action === "accion de tutela" && !form.eps_response_detail?.trim(),
      }
    );
  }

  if (category === "datos") {
    steps.push(
      {
        id: "disputed_data",
        question: "Que dato o reporte esta mal o te esta afectando?",
        placeholder: "Ej: reporte negativo en Datacredito por obligacion ya pagada",
        multiline: true,
        show: !form.disputed_data.trim(),
      },
      {
        id: "requested_data_action",
        question: "Como deberia quedar corregido ese dato o reporte?",
        placeholder: "Ej: actualizar el estado, eliminar el reporte o corregir la fecha",
        multiline: false,
        show: !form.requested_data_action.trim(),
      }
    );
  }

  if (action === "accion de tutela") {
    steps.push(
      {
        id: "tutela_previous_action_detail",
        question: "Antes de esta tutela, cuentame si ya presentaste otra solicitud, peticion o tutela por este mismo problema.",
        placeholder: "Ej: no habia presentado otra / ya habia presentado una peticion previa y esto fue lo que paso",
        multiline: true,
        show: !form.tutela_previous_action_detail?.trim(),
      },
      {
        id: "tutela_oath_statement",
        question: "Confirma si ya habias presentado otra tutela por este mismo problema o si esta es la primera vez.",
        placeholder: "Ej: no habia presentado otra tutela por estos mismos hechos",
        multiline: true,
        show: !form.tutela_oath_statement?.trim() && !form.tutela_no_temperity_detail?.trim(),
      },
      {
        id: "tutela_other_means_detail",
        question: "Que hiciste antes para resolverlo y que esta pasando ahora que sigue siendo urgente?",
        placeholder: "Ej: reclame antes, no solucionaron y el dano sigue ocurriendo hoy",
        multiline: true,
        show: !form.tutela_other_means_detail?.trim(),
      },
      {
        id: "tutela_immediacy_detail",
        question: "Que esta pasando hoy que hace urgente presentar esto ahora?",
        placeholder: "Ej: el hecho es reciente, la vulneracion sigue ocurriendo o el riesgo es actual",
        multiline: true,
        show: !form.tutela_immediacy_detail?.trim(),
      },
      {
        id: "tutela_special_protection_detail",
        question: "Existe alguna condicion de especial proteccion que deba resaltarse?",
        placeholder: "Ej: menor de edad, adulto mayor, embarazo, discapacidad o enfermedad grave",
        multiline: false,
        show: !form.tutela_special_protection_detail?.trim(),
      }
    );
  }

  if (action.includes("derecho de peticion")) {
    steps.push(
      {
        id: "request_type",
        question: "Que necesitas de la entidad: informacion, documentos, una respuesta sobre tu caso o una correccion?",
        placeholder: "Ej: informacion, documentos o respuesta de fondo",
        multiline: false,
        show: !form.request_type.trim(),
      },
      {
        id: "numbered_requests",
        question: "Si la entidad te respondiera hoy, cuales serian las 2 o 3 soluciones concretas que necesitas recibir?",
        placeholder: "Ej: entregar copia del contrato, corregir el cobro y certificar el estado del caso",
        multiline: true,
        show: !form.numbered_requests.trim(),
      }
    );
  }

  return steps.filter((step) => step.show);
};

const buildPostPayInterviewSteps = (form, caseItem) => {
  return buildPostPayInterviewStepsClean(form, caseItem);
  const category = (caseItem?.category || "").toLowerCase();
  const action = normalizeAction(caseItem?.recommended_action || caseItem?.workflow_type || "");
  const steps = [
    {
      id: "case_story",
      question: "Cuéntame brevemente qué pasó, en qué orden y cómo te afecta hoy.",
      placeholder: "Ej: saqué la tarjeta en octubre, luego empezaron a cobrar un seguro que nunca autoricé...",
      multiline: true,
      show: !form.case_story.trim(),
    },
    {
      id: "key_dates",
      question: "¿Qué fechas exactas o aproximadas recuerdas de los hechos?",
      placeholder: "Ej: octubre de 2025 apertura, noviembre de 2025 primer cobro, enero de 2026 reclamo",
      multiline: false,
      show: !form.key_dates.trim(),
    },
    {
      id: "concrete_request",
      question: "¿Qué quieres exactamente que ordene, corrija o responda la entidad?",
      placeholder: "Ej: eliminar el seguro, devolver los cobros y responder de fondo",
      multiline: true,
      show: !form.concrete_request.trim(),
    },
    {
      id: "evidence_summary",
      question: "¿Qué pruebas tienes hoy disponibles?",
      placeholder: "Ej: extractos PDF, capturas, chat, correo, contrato, audio, radicado",
      multiline: true,
      show: !form.evidence_summary?.trim(),
    },
  ];

  if (category === "bancos") {
    steps.push(
      {
        id: "bank_product_type",
        question: "¿Qué producto financiero está involucrado?",
        placeholder: "Ej: tarjeta de crédito Visa, cuenta de ahorros, préstamo",
        multiline: false,
        show: !form.bank_product_type?.trim(),
      },
      {
        id: "disputed_charge",
        question: "¿Cuál es exactamente el cobro o concepto discutido?",
        placeholder: "Ej: seguro de desempleo, cuota de manejo, interés o cargo no reconocido",
        multiline: false,
        show: !form.disputed_charge?.trim(),
      },
      {
        id: "bank_amount_involved",
        question: "¿Por qué valor te están cobrando ese concepto o cuánto te han cobrado en total?",
        placeholder: "Ej: $38.500 mensuales o $154.000 acumulados",
        multiline: false,
        show: !form.bank_amount_involved?.trim(),
      },
      {
        id: "bank_event_date",
        question: "¿Desde qué fecha viste el primer cobro o el primer hecho relevante?",
        placeholder: "Ej: 12 de octubre de 2025",
        multiline: false,
        show: !form.bank_event_date?.trim(),
      },
      {
        id: "bank_account_reference",
        question: "¿Qué referencia del producto puedes compartir sin exponer todo el dato?",
        placeholder: "Ej: tarjeta terminada en 4821 o cuenta de ahorros terminada en 9912",
        multiline: false,
        show: !form.bank_account_reference?.trim(),
      },
      {
        id: "refund_destination",
        question: "Si pides devolución, ¿a qué cuenta, tarjeta o medio deben abonarte los valores?",
        placeholder: "Ej: a la misma tarjeta terminada en 4821 o a la cuenta de ahorros Bancolombia",
        multiline: false,
        show: !form.refund_destination?.trim(),
      }
    );
    if (form.prior_claim === "si") {
      steps.push(
        {
          id: "prior_claim_date",
          question: "¿En qué fecha reclamaste al banco y por qué canal lo hiciste?",
          placeholder: "Ej: 14 de enero de 2026 por PQRS web y llamada",
          multiline: false,
          show: !form.prior_claim_date?.trim(),
        },
        {
          id: "prior_claim_result",
          question: "¿Qué te respondió el banco o qué ocurrió después del reclamo?",
          placeholder: "Ej: dijeron que el seguro estaba activo, pero no enviaron autorización ni soporte",
          multiline: true,
          show: !form.prior_claim_result?.trim(),
        }
      );
    }
  }

  if (action === "accion de tutela") {
    steps.push(
      {
        id: "tutela_previous_action_detail",
        question: "Antes de la tutela, necesito saber si ya presentaste otra tutela, incidente, peticion o medida por estos mismos hechos.",
        placeholder: "Ej: no he presentado otra tutela ni otra medida / ya hubo una tutela o una peticion previa y esto fue lo que paso...",
        multiline: true,
        show: !form.tutela_previous_action_detail?.trim(),
      },
      {
        id: "tutela_oath_statement",
        question: "Ahora deja la declaracion bajo juramento sobre no temeridad.",
        placeholder: "Ej: bajo juramento manifiesto que no he presentado otra tutela por los mismos hechos, derechos y pretensiones.",
        multiline: true,
        show: !form.tutela_oath_statement?.trim() && !form.tutela_no_temperity_detail?.trim(),
      },
      {
        id: "tutela_other_means_detail",
        question: "¿Por qué la tutela sí procede en este caso y no basta con otro trámite?",
        placeholder: "Ej: no existe otro medio eficaz o el daño sigue ocurriendo y necesito protección urgente",
        multiline: true,
        show: !form.tutela_other_means_detail?.trim(),
      },
      {
        id: "tutela_immediacy_detail",
        question: "¿Por qué presentas la tutela ahora? Necesito la explicación de inmediatez.",
        placeholder: "Ej: el hecho es reciente / la vulneración sigue ocurriendo / el riesgo es actual",
        multiline: true,
        show: !form.tutela_immediacy_detail?.trim(),
      },
      {
        id: "tutela_special_protection_detail",
        question: "¿Existe alguna condición de especial protección que deba resaltarse?",
        placeholder: "Ej: menor de edad, adulto mayor, embarazo, discapacidad, enfermedad grave",
        multiline: false,
        show: !form.tutela_special_protection_detail?.trim(),
      }
    );
    if (String(form.target_entity || "").trim()) {
      steps.push({
        id: "tutela_private_party_ground",
        question: "Si la tutela va contra un particular o empresa privada, ¿por qué jurídicamente procede?",
        placeholder: "Ej: presta servicio público, existe indefensión, subordinación o habeas data",
        multiline: true,
        show: !form.tutela_private_party_ground?.trim(),
      });
    }
  }

  return steps.filter((step) => step.show);
};

const buildDocumentChecklist = (item, review, files) => {
  const explicit = review?.strengths?.slice(0, 4) || [];
  const rights = item.legal_analysis?.derechos_vulnerados || [];
  const rules = item.legal_analysis?.normas_relevantes || [];
  const base = [
    rights.length ? `${rights.length} derechos identificados` : "",
    rules.length ? `${rules.length} normas base usadas` : "",
    files.length ? `${files.length} pruebas adjuntas revisadas` : "Puedes seguir agregando pruebas si luego las necesitas",
    review?.passed ? "Paso control automatico de calidad" : "",
  ].filter(Boolean);
  return [...explicit, ...base].slice(0, 6);
};

const getActiveFlowStep = (item) => {
  if (!item) return 1;
  if (item.status === "radicado") return 4;
  if (item.generated_document) return 3;
  if (item.payment_status === "pagado") return 2;
  return 1;
};

const buildWritingGuide = (category) => {
  const base = {
    title: "Que debes contar para que el documento salga bien",
    bullets: [
      "Que paso exactamente y desde cuando.",
      "A que entidad, empresa o persona le reclamas.",
      "Que pediste antes y que te respondieron, si hubo respuesta.",
      "Que necesitas que quede ordenado o resuelto.",
    ],
  };
  if (category === "Salud") {
    return {
      title: "Para salud o tutela por salud, cuenta esto",
      bullets: [
        "Diagnostico, medicamento, examen o procedimiento pendiente.",
        "Desde cuando la EPS o IPS no responde, niega o interrumpe el servicio.",
        "Orden medica, formula o incapacidad si existe.",
        "Si el tratamiento se interrumpio, explica que pasa hoy por esa suspension.",
        "Si el paciente es menor, embarazada, tiene discapacidad o enfermedad grave, dilo expresamente.",
        "Como te afecta hoy: dolor, riesgo, suspension del tratamiento, empeoramiento o minimo vital.",
      ],
    };
  }
  if (category === "Bancos") {
    return {
      title: "Para bancos o habeas data, cuenta esto",
      bullets: [
        "Cobro, reporte o bloqueo que consideras injusto.",
        "Fecha aproximada del problema y monto comprometido.",
        "Si ya reclamaste al banco o a la central de riesgo.",
        "Que quieres lograr: corregir, devolver, eliminar reporte o responder peticion.",
      ],
    };
  }
  if (category === "Laboral") {
    return {
      title: "Para un caso laboral, cuenta esto",
      bullets: [
        "Que relacion tenias con el empleador y que paso.",
        "Fecha de despido, suspension, no pago o negativa.",
        "Cuanto te deben o como se afecto tu minimo vital.",
        "Si ya pediste respuesta formal al empleador.",
      ],
    };
  }
  if (category === "Servicios") {
    return {
      title: "Para servicios publicos o privados, cuenta esto",
      bullets: [
        "Empresa involucrada y numero de factura o suscriptor si lo tienes.",
        "Corte, cobro, suspension o negativa concreta.",
        "Desde cuando ocurre el problema.",
        "Que solucion concreta estas pidiendo.",
      ],
    };
  }
  if (category === "Consumidor") {
    return {
      title: "Para consumidor, queja o reclamo, cuenta esto",
      bullets: [
        "Que compraste o contrataste y cuando.",
        "Que fallo presento el producto o servicio.",
        "Si pediste garantia, cambio, devolucion o respuesta previa.",
        "Que esperas que hagan: devolver, cambiar, corregir o responder.",
      ],
    };
  }
  return base;
};

const shortDate = (value) => new Date(value).toLocaleString("es-CO", { dateStyle: "medium", timeStyle: "short" });
const apiBase =
  import.meta.env.VITE_API_URL ||
  (import.meta.env.PROD ? "https://api.123tutelaapp.com" : "http://localhost:8000");
const widgetScriptUrl = "https://checkout.wompi.co/widget.js";

const normalizeMentionedDates = (value) => {
  if (Array.isArray(value)) return value.join(", ");
  if (typeof value === "string") return value;
  return "";
};

class DashboardErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error) {
    console.error("Dashboard render error", error);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="glass-card" style={{ padding: 28, color: C.text }}>
          <div style={{ fontSize: 14, fontWeight: 800, color: C.danger }}>No pudimos cargar este panel.</div>
          <div style={{ marginTop: 8, color: C.textMuted }}>
            Recarga la pagina. Si un bloque falla, ya no debe tumbar todo el dashboard.
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

const normalizeAction = (value) =>
  String(value || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .trim();

const extractArticleLabel = (value) => {
  const text = String(value || "");
  const match = text.match(/Art(?:í|i)culo\s+(\d+)/i);
  return match ? `Articulo ${match[1]} — Constitucion Politica` : text;
};

const buildPreviewRights = (preview) => {
  const rights = (preview?.legal_analysis?.derechos_vulnerados || []).slice(0, 2);
  const constitutionNorms = (preview?.legal_analysis?.normas_relevantes || []).filter((item) =>
    normalizeAction(item).includes("constitucion"),
  );

  return rights.map((right, index) => ({
    title: right,
    article: extractArticleLabel(constitutionNorms[index] || constitutionNorms[0] || ""),
  }));
};

const getViabilityConfig = (dxResult) => {
  const viability = normalizeAction(dxResult?.viability_preliminary);
  if (viability === "alta") {
    return {
      label: "Alta",
      note: "Tu caso tiene buen fundamento preliminar.",
      color: "#16A34A",
      segments: [true, true, true, false],
    };
  }
  if (viability === "media") {
    return {
      label: "Media",
      note: "Hay base, pero conviene afinar algunos hechos antes del documento.",
      color: "#D97706",
      segments: [true, true, false, false],
    };
  }
  return {
    label: "Baja",
    note: "La IA ve riesgo en la ruta y podria requerir otra via o mas soporte.",
    color: "#DC2626",
    segments: [true, false, false, false],
  };
};

const shortenRouteLabel = (label, fallback = "") => {
  const normalized = normalizeAction(label);
  if (normalized.includes("pqrs") || normalized.includes("derecho de peticion")) return "PQRS / Reclamo";
  if (normalized.includes("supersalud")) return "Supersalud";
  if (normalized.includes("banco")) return "Reclamo";
  if (normalized.includes("queja")) return "Queja";
  if (normalized.includes("habeas data")) return "Habeas data";
  if (normalized.includes("accion de tutela")) return "Tutela";
  if (normalized.includes("tutela")) return "Tutela";
  if (fallback) return fallback;
  return String(label || "").slice(0, 32);
};

const buildCommercialDiagnosisCopy = (action = "", category = "") => {
  const normalizedAction = normalizeAction(action);
  const normalizedCategory = normalizeAction(category);
  if (normalizedAction === "accion de tutela" || normalizedCategory === "salud") {
    return "La plataforma detecto una posible vulneracion de derechos fundamentales y una ruta judicial viable. La argumentacion completa, el escrito final y la radicacion se habilitan al activar el documento.";
  }
  if (normalizedAction.includes("derecho de peticion")) {
    return "La plataforma confirmo que tu caso amerita un derecho de peticion formal. Al activar el documento se libera la redaccion completa, la estructura juridica y la opcion de radicacion.";
  }
  if (normalizedCategory === "bancos") {
    return "La plataforma detecto un reclamo financiero con sustento inicial y posibilidad de exigir respuesta de fondo. El escrito final y la ruta de envio se activan despues del pago.";
  }
  return "La plataforma confirmo una ruta legal viable para tu caso. La estrategia completa, el documento final y la radicacion se habilitan al activar el servicio.";
};

const buildPaymentOfferCopy = (action = "", category = "") => {
  const normalizedAction = normalizeAction(action);
  const normalizedCategory = normalizeAction(category);
  if (normalizedAction === "accion de tutela" || normalizedCategory === "salud") {
    return {
      headline: "Activa tu tutela lista para presentar",
      body: "Al pagar se desbloquea la accion de tutela completa, con hechos depurados, fundamentos juridicos, pretensiones y control final de calidad.",
      unlocks: [
        "Tutela final lista para revisar, firmar y presentar.",
        "Redaccion juridica completa con estructura judicial.",
        "Acceso al expediente activo y trazabilidad del caso.",
      ],
    };
  }
  if (normalizedAction.includes("derecho de peticion")) {
    return {
      headline: "Activa tu derecho de peticion final",
      body: "Al pagar se libera el documento completo, con fundamento legal, solicitudes numeradas y control de calidad antes del envio.",
      unlocks: [
        "Derecho de peticion final listo para revisar y usar.",
        "Argumentacion juridica completa y solicitudes claras.",
        "Acceso al expediente activo y trazabilidad del caso.",
      ],
    };
  }
  if (normalizedCategory === "bancos") {
    return {
      headline: "Activa tu reclamo financiero final",
      body: "Al pagar se desbloquea el escrito formal para la entidad, con calculo de pretensiones, soporte juridico y control final antes de radicar.",
      unlocks: [
        "Reclamo financiero final listo para revisar y firmar.",
        "Calculo y redaccion completa del documento.",
        "Acceso al expediente activo y trazabilidad del caso.",
      ],
    };
  }
  return {
    headline: "Activa tu documento legal final",
    body: "Al pagar se libera la version completa del documento, con estructura juridica, revision final y acceso al flujo de firma y radicacion.",
    unlocks: [
      "Documento final listo para revisar y usar.",
      "Redaccion juridica completa y control final de calidad.",
      "Acceso al expediente activo y trazabilidad del caso.",
    ],
  };
};

const buildRouteSteps = (preview) => {
  const steps = [];
  (preview?.prerequisites || []).slice(0, 2).forEach((item) => {
    steps.push(shortenRouteLabel(item?.label));
  });
  steps.push(shortenRouteLabel(preview?.recommended_action, "Documento"));
  return steps.filter(Boolean).slice(0, 3);
};

const summarizeCaseCard = (item) => {
  const details = [];
  const routingName = item?.routing?.primary_target?.name;
  if (routingName) details.push(`Entidad: ${routingName}`);
  if (item?.recommended_action) details.push(`Ruta: ${item.recommended_action}`);
  if (item?.payment_status === "pagado") details.push("Pago confirmado");
  return details.slice(0, 3).join(" · ");
};

const summarizePreviewFixes = ({
  intakeReview,
  documentRuleReview,
  actionSpecificMissing,
  actionSpecificIssues,
  previewWarnings,
  pendingQuestions,
}) => {
  const items = [
    ...((pendingQuestions || []).map((item) => item?.question).filter(Boolean)),
    ...(actionSpecificMissing || []).map((item) => `Completa: ${item}`),
    ...(actionSpecificIssues || []),
    ...((intakeReview?.blocking_issues || []).filter((item) => !isAiOwnedReviewIssue(item))),
    ...((intakeReview?.warnings || []).filter((item) => !isAiOwnedReviewIssue(item))),
    ...((documentRuleReview?.blocking_issues || []).filter((item) => !isAiOwnedReviewIssue(item))),
    ...((documentRuleReview?.warnings || []).filter((item) => !isAiOwnedReviewIssue(item))),
    ...(previewWarnings || []).filter((item) => !isAiOwnedReviewIssue(item)),
  ];

  return [...new Set(items)].slice(0, 4);
};

const buildContinuationOptions = (item) => {
  const action = normalizeAction(item?.recommended_action);
  if (item?.status === "radicado") {
    return [
      "Seguimiento del caso para revisar respuesta, admisión o requerimientos.",
      action === "accion de tutela" ? "Impugnación si el fallo no protege completamente el derecho." : null,
      action === "accion de tutela" ? "Incidente de desacato si existe orden judicial incumplida." : null,
    ].filter(Boolean);
  }

  if (item?.payment_status === "pagado" && !item?.generated_document) {
    return ["Generar el documento final y revisar el contenido antes de radicar."];
  }

  if (item?.generated_document && item?.status !== "radicado") {
    return [
      item?.routing?.automatable
        ? "Radicación automática con el canal sugerido y envío de comprobante."
        : "Radicación manual o presencial con registro del comprobante en el panel.",
    ];
  }

  return ["Completar el paso actual para habilitar la siguiente etapa del caso."];
};

const buildStructuredDescription = (form) => {
  const sections = [
    `Categoria: ${form.category || "Sin categoria definida"}`,
    form.target_entity ? `Entidad o destinatario: ${form.target_entity}` : "",
    form.event_date ? `Fecha o periodo relevante: ${form.event_date}` : "",
    form.event_period_detail ? `Detalle adicional de la cronologia: ${form.event_period_detail}` : "",
    form.case_reference ? `Numero o referencia relacionada: ${form.case_reference}` : "",
    form.request_type ? `Tipo de peticion o enfoque principal: ${form.request_type}` : "",
    form.concrete_request ? `Solicitud principal del usuario: ${form.concrete_request}` : "",
    form.numbered_requests ? `Solicitudes numeradas esperadas: ${form.numbered_requests}` : "",
    form.current_harm ? `Afectacion actual o riesgo: ${form.current_harm}` : "",
    form.prior_response_status ? `Estado de respuesta previa: ${form.prior_response_status}` : "",
    form.previous_response ? `Respuesta previa o antecedente: ${form.previous_response}` : "",
    form.response_channel ? `Canal de respuesta deseado: ${form.response_channel}` : "",
    form.authority_act_type ? `Acto, decision o barrera relevante: ${form.authority_act_type}` : "",
    form.authority_act_date ? `Fecha del acto o decision: ${form.authority_act_date}` : "",
    form.evidence_summary ? `Pruebas o soportes disponibles: ${form.evidence_summary}` : "",
    form.supporting_documents ? `Documentos o anexos esperados: ${form.supporting_documents}` : "",
    form.category === "Salud" && form.eps_name ? `EPS involucrada: ${form.eps_name}` : "",
    form.category === "Salud" && form.ips_name ? `IPS o clinica: ${form.ips_name}` : "",
    form.category === "Salud" && form.diagnosis ? `Diagnostico o condicion medica: ${form.diagnosis}` : "",
    form.category === "Salud" && form.treatment_needed ? `Tratamiento, orden o servicio requerido: ${form.treatment_needed}` : "",
    form.category === "Salud" && form.medical_order_date ? `Fecha de la orden medica: ${form.medical_order_date}` : "",
    form.category === "Salud" && form.treating_doctor_name ? `Medico tratante: ${form.treating_doctor_name}` : "",
    form.category === "Salud" && form.treating_ips_name ? `IPS o clinica tratante: ${form.treating_ips_name}` : "",
    form.category === "Salud" && form.eps_request_date ? `Fecha de solicitud a la EPS: ${form.eps_request_date}` : "",
    form.category === "Salud" && form.eps_request_channel ? `Canal de solicitud a la EPS: ${form.eps_request_channel}` : "",
    form.category === "Salud" && form.eps_request_reference ? `Radicado o referencia de la EPS: ${form.eps_request_reference}` : "",
    form.category === "Salud" && form.eps_response_detail ? `Respuesta o barrera de la EPS: ${form.eps_response_detail}` : "",
    form.category === "Salud" && form.urgency_detail ? `Urgencia o riesgo clinico: ${form.urgency_detail}` : "",
    form.category === "Datos" && form.disputed_data ? `Dato o reporte cuestionado: ${form.disputed_data}` : "",
    form.category === "Datos" && form.requested_data_action ? `Accion solicitada sobre el dato: ${form.requested_data_action}` : "",
    form.category === "Laboral" && form.labor_relation_type ? `Tipo de relacion laboral: ${form.labor_relation_type}` : "",
    form.category === "Laboral" && form.labor_employer_name ? `Empleador o contratante: ${form.labor_employer_name}` : "",
    form.category === "Laboral" && form.labor_measure_date ? `Fecha de la medida o despido: ${form.labor_measure_date}` : "",
    form.category === "Laboral" && form.labor_salary_detail ? `Salario, honorarios o pagos pendientes: ${form.labor_salary_detail}` : "",
    form.category === "Laboral" && form.dismissal_or_measure ? `Despido, sancion o medida cuestionada: ${form.dismissal_or_measure}` : "",
    form.category === "Laboral" && form.minimum_vital_impact ? `Impacto en minimo vital: ${form.minimum_vital_impact}` : "",
    form.category === "Laboral" && form.reinforced_stability ? `Estabilidad reforzada o condicion especial: ${form.reinforced_stability}` : "",
    form.category === "Bancos" && form.bank_product_type ? `Producto financiero involucrado: ${form.bank_product_type}` : "",
    form.category === "Bancos" && form.bank_amount_involved ? `Monto o valor discutido: ${form.bank_amount_involved}` : "",
    form.category === "Bancos" && form.bank_claim_goal ? `Resultado esperado frente al banco: ${form.bank_claim_goal}` : "",
    form.category === "Bancos" && form.bank_event_date ? `Fecha del cargo, bloqueo o reporte: ${form.bank_event_date}` : "",
    form.category === "Bancos" && form.disputed_charge ? `Cobro, mora o valor discutido: ${form.disputed_charge}` : "",
    form.category === "Bancos" && form.report_or_block_reason ? `Reporte, bloqueo o causa principal: ${form.report_or_block_reason}` : "",
    form.category === "Servicios" && form.service_company_name ? `Empresa de servicios: ${form.service_company_name}` : "",
    form.category === "Servicios" && form.service_type ? `Tipo de servicio afectado: ${form.service_type}` : "",
    form.category === "Servicios" && form.subscriber_reference ? `Numero de suscriptor o referencia: ${form.subscriber_reference}` : "",
    form.category === "Servicios" && form.invoice_period ? `Factura o periodo discutido: ${form.invoice_period}` : "",
    form.category === "Servicios" && form.service_impact ? `Impacto del servicio o corte: ${form.service_impact}` : "",
    form.category === "Servicios" && form.cutoff_or_billing_detail ? `Detalle de corte o facturacion discutida: ${form.cutoff_or_billing_detail}` : "",
    form.category === "Consumidor" && form.provider_name ? `Proveedor o comercio: ${form.provider_name}` : "",
    form.category === "Consumidor" && form.purchase_date ? `Fecha de compra o contratacion: ${form.purchase_date}` : "",
    form.category === "Consumidor" && form.order_reference ? `Pedido, factura o referencia: ${form.order_reference}` : "",
    form.category === "Consumidor" && form.seller_response_detail ? `Respuesta del proveedor: ${form.seller_response_detail}` : "",
    form.category === "Consumidor" && form.product_or_service_issue ? `Falla del producto o servicio: ${form.product_or_service_issue}` : "",
    form.category === "Consumidor" && form.guarantee_or_refund_request ? `Garantia, cambio o devolucion solicitada: ${form.guarantee_or_refund_request}` : "",
    form.complaint_reason ? `Motivo principal de la queja: ${form.complaint_reason}` : "",
    form.complaint_expected_response ? `Respuesta o intervencion esperada: ${form.complaint_expected_response}` : "",
    form.administrative_error_detail ? `Error, cobro o actuacion administrativa cuestionada: ${form.administrative_error_detail}` : "",
    form.administrative_requested_fix ? `Correccion administrativa solicitada: ${form.administrative_requested_fix}` : "",
    form.disciplinary_subject_name ? `Funcionario o sujeto disciplinable: ${form.disciplinary_subject_name}` : "",
    form.disciplinary_subject_role ? `Cargo o rol del sujeto disciplinable: ${form.disciplinary_subject_role}` : "",
    form.disciplinary_conduct ? `Conducta disciplinaria denunciada: ${form.disciplinary_conduct}` : "",
    form.disciplinary_event_date ? `Fecha de la conducta o hecho disciplinario: ${form.disciplinary_event_date}` : "",
    form.compliance_norm_or_act ? `Norma o acto incumplido: ${form.compliance_norm_or_act}` : "",
    form.compliance_authority ? `Autoridad obligada a cumplir: ${form.compliance_authority}` : "",
    form.compliance_prior_requirement ? `Requerimiento previo realizado: ${form.compliance_prior_requirement}` : "",
    form.compliance_breach_detail ? `Forma concreta del incumplimiento: ${form.compliance_breach_detail}` : "",
    form.tutela_court_name ? `Juzgado o despacho de tutela: ${form.tutela_court_name}` : "",
    form.tutela_ruling_date ? `Fecha del fallo o decision de tutela: ${form.tutela_ruling_date}` : "",
    form.tutela_decision_result ? `Resultado de la decision de tutela: ${form.tutela_decision_result}` : "",
    form.tutela_appeal_reason ? `Motivos de impugnacion: ${form.tutela_appeal_reason}` : "",
    form.tutela_order_summary ? `Orden judicial incumplida: ${form.tutela_order_summary}` : "",
    form.tutela_noncompliance_detail ? `Detalle del incumplimiento: ${form.tutela_noncompliance_detail}` : "",
    form.tutela_previous_action_detail ? `Otra tutela o medida previa sobre el mismo caso: ${form.tutela_previous_action_detail}` : "",
    form.tutela_oath_statement ? `Declaracion bajo juramento sobre no temeridad: ${form.tutela_oath_statement}` : "",
    form.tutela_no_temperity_detail ? `No temeridad o tutela previa: ${form.tutela_no_temperity_detail}` : "",
    form.tutela_other_means_detail ? `Subsidiariedad o ausencia de otro medio eficaz: ${form.tutela_other_means_detail}` : "",
    form.tutela_immediacy_detail ? `Inmediatez o justificacion temporal: ${form.tutela_immediacy_detail}` : "",
    form.tutela_special_protection_detail ? `Sujeto de especial proteccion: ${form.tutela_special_protection_detail}` : "",
    form.tutela_private_party_ground ? `Fundamento contra particular: ${form.tutela_private_party_ground}` : "",
    form.acting_capacity ? `Calidad en que actua quien presenta el caso: ${form.acting_capacity}` : "",
    form.represented_person_name ? `Persona representada o afectada principal: ${form.represented_person_name}` : "",
    form.represented_person_document ? `Documento de la persona representada: ${form.represented_person_document}` : "",
    form.represented_person_age ? `Edad o fecha de nacimiento de la persona representada: ${form.represented_person_age}` : "",
    form.represented_person_condition ? `Condicion relevante de la persona representada: ${form.represented_person_condition}` : "",
    form.petition_target_nature ? `Naturaleza del destinatario de la peticion: ${form.petition_target_nature}` : "",
    form.petition_private_ground ? `Fundamento para peticion a particular: ${form.petition_private_ground}` : "",
    form.petition_previous_submission_date ? `Fecha de radicacion o gestion previa: ${form.petition_previous_submission_date}` : "",
    form.petition_sector_rule ? `Norma sectorial o contexto especial: ${form.petition_sector_rule}` : "",
    form.description ? `Relato del usuario: ${form.description}` : "",
  ].filter(Boolean);

  return sections.join("\n");
};

const getGuidedIntakeMissing = (form, files = []) => {
  const missing = [];

  if (form.category === "Salud") {
    if (!form.target_entity.trim() && !form.eps_name.trim()) missing.push("EPS, IPS o entidad de salud");
    if (!form.diagnosis.trim()) missing.push("Diagnostico o condicion medica");
    if (!form.treatment_needed.trim()) missing.push("Tratamiento, orden o servicio requerido");
    if (!form.urgency_detail.trim() && !form.current_harm.trim()) missing.push("Que sigue pasando hoy al paciente");
    if (form.acting_capacity !== "nombre_propio") {
      if (!form.represented_person_name.trim()) missing.push("Nombre del menor o paciente representado");
    }
    return missing;
  }

  if (!form.target_entity.trim()) missing.push("Entidad o destinatario");
  if (!form.event_date.trim()) missing.push("Fecha o periodo");
  if (!form.concrete_request.trim()) missing.push("Solicitud concreta");

  if (form.category === "Datos") {
    if (!form.disputed_data.trim()) missing.push("Dato o reporte cuestionado");
  }

  if (["Laboral", "Bancos", "Servicios", "Consumidor"].includes(form.category)) {
    if (!form.current_harm.trim()) missing.push("Afectacion actual o riesgo");
  }

  if (form.category === "Laboral") {
    if (!form.dismissal_or_measure.trim()) missing.push("Despido, sancion o medida cuestionada");
  }

  if (form.category === "Bancos") {
    if (!form.report_or_block_reason.trim()) missing.push("Reporte, bloqueo o causa principal");
  }

  if (form.category === "Servicios") {
    if (!form.cutoff_or_billing_detail.trim()) missing.push("Detalle de corte o facturacion");
  }

  if (form.category === "Consumidor") {
    if (!form.product_or_service_issue.trim()) missing.push("Falla del producto o servicio");
  }

  return missing;
};

const getPreviewGateIssues = (form, files = []) => {
  const issues = [];
  const descriptionLength = form.description.trim().length;
  const harmLength = form.current_harm.trim().length;
  const urgencyLength = form.urgency_detail.trim().length;
  if (descriptionLength < 60) {
    issues.push("El relato libre todavia es muy corto. Describe mejor que paso, en que orden y con que fechas.");
  }

  if (form.category !== "Salud" && harmLength < 25) {
    issues.push("Debes explicar mejor la afectacion actual o el riesgo concreto que justifica el documento.");
  }

  if (form.prior_response_status === "sin_gestion_previa" && ["Laboral", "Bancos", "Servicios", "Consumidor", "Datos"].includes(form.category)) {
    issues.push("Todavia no reportas una gestion previa. Revisa si primero conviene un derecho de peticion o una reclamacion formal.");
  }

  if (form.category === "Salud" && urgencyLength < 20 && harmLength < 25) {
    issues.push("En salud falta contar mejor que sigue pasando hoy al paciente y que afectacion continua sin el servicio.");
  }

  if (form.category === "Laboral" && form.minimum_vital_impact.trim().length < 20) {
    issues.push("En laboral debes explicar mejor como afecta el minimo vital o la estabilidad del usuario.");
  }

  if (form.category === "Laboral" && form.labor_salary_detail.trim().length < 10) {
    issues.push("En laboral conviene precisar salarios, honorarios o pagos pendientes para reforzar la gravedad del caso.");
  }

  if (form.category === "Bancos" && form.disputed_charge.trim().length < 10) {
    issues.push("En bancos debes precisar mejor el cobro, mora, bloqueo o reporte discutido.");
  }

  if (form.category === "Bancos" && form.bank_claim_goal.trim().length < 15) {
    issues.push("En bancos debes decir con claridad si pides reverso, desbloqueo, correccion del reporte o respuesta de fondo.");
  }

  if (form.category === "Datos" && form.disputed_data.trim().length < 15) {
    issues.push("En habeas data debes identificar mejor el dato, reporte o registro que quieres corregir o suprimir.");
  }

  if (form.category === "Servicios" && form.service_impact.trim().length < 20) {
    issues.push("En servicios debes explicar con mas detalle el impacto del corte, cobro o incumplimiento.");
  }

  if (form.category === "Consumidor" && form.guarantee_or_refund_request.trim().length < 15) {
    issues.push("En consumidor debes explicar con mas claridad la garantia, cambio o devolucion que solicitas.");
  }

  return issues;
};

const getWritingAid = (category) => {
  if (category === "Salud") {
    return "Cuenta los hechos en orden: que te ordenaron, que negaron o demoraron, desde cuando pasa y por que hoy existe urgencia o riesgo.";
  }
  if (category === "Bancos") {
    return "Indica producto financiero, fecha del primer cobro o bloqueo, valor discutido, reclamo previo, respuesta del banco y exactamente que quieres que corrijan o devuelvan.";
  }
  if (category === "Datos") {
    return "Explica que dato esta mal, donde aparece, desde cuando lo conoces, si ya reclamaste y que accion exacta quieres: corregir, actualizar o suprimir.";
  }
  if (["Laboral", "Servicios", "Consumidor"].includes(category)) {
    return "Escribe como una peticion o reclamacion seria: identifica a quien va dirigida, que paso, que soporte tienes, que exiges exactamente y por que eso te afecta hoy.";
  }
  return "Describe hechos concretos, fechas, entidad involucrada y una solicitud clara. Evita opiniones generales y enfocate en lo verificable.";
};

const buildGuidedIntakeInterviewSteps = (form) => {
  const action = normalizeAction(form.recommended_action);
  if (form.category === "Salud") {
    const loweredHealthText = [
      form.description,
      form.case_story,
      form.urgency_detail,
      form.current_harm,
      form.ongoing_harm,
      form.prior_claim_result,
      form.eps_response_detail,
      form.tutela_other_means_detail,
      form.tutela_immediacy_detail,
      form.tutela_special_protection_detail,
    ]
      .filter(Boolean)
      .join(" ")
      .toLowerCase();

    const contradictionSteps = [];
    if (form.target_entity.trim() && form.eps_name.trim() && normalizeAction(form.target_entity) !== normalizeAction(form.eps_name)) {
      contradictionSteps.push({
        id: "target_entity",
        question: `Veo dos entidades distintas en tu caso: "${form.target_entity}" y "${form.eps_name}". Cual es la EPS o IPS correcta contra la que va el documento?`,
        placeholder: "Escribe un solo nombre oficial de la EPS o IPS correcta",
        multiline: false,
        show: true,
      });
    }
    if (form.prior_claim === "no" && (form.prior_claim_result.trim() || form.eps_response_detail.trim() || form.tutela_other_means_detail.trim())) {
      contradictionSteps.push({
        id: "prior_claim_result",
        question: "Marcaste que no hubo gestion previa, pero ya aparece una solicitud o respuesta de la EPS. Aclara que paso realmente.",
        placeholder: "Ej: si hubo PQRS el 3 de marzo y respondieron..., o no hubo ninguna gestion previa",
        multiline: true,
        show: true,
      });
    }
    if (form.acting_capacity === "nombre_propio" && (form.represented_person_name.trim() || form.represented_person_age.trim() || form.represented_person_document.trim())) {
      contradictionSteps.push({
        id: "acting_capacity",
        question: "El caso trae datos de otra persona, pero sigue marcado en nombre propio. Confirma si presentas este caso por ti o por alguien mas.",
        placeholder: "Ej: nombre propio, madre del menor, acudiente, agente oficioso",
        multiline: false,
        show: true,
      });
    }
    if (["no aplica", "ninguno"].includes(normalizeAction(form.special_protection)) && form.tutela_special_protection_detail.trim()) {
      contradictionSteps.push({
        id: "special_protection",
        question: "Marcaste que no aplica proteccion especial, pero el relato si menciona una condicion reforzada. Que opcion describe mejor al paciente?",
        placeholder: "Ej: Menor de edad, Adulto mayor, Embarazada, Discapacidad, No aplica",
        multiline: false,
        show: true,
      });
    }
    if (
      (loweredHealthText.includes("ya autorizaron") || loweredHealthText.includes("ya entregaron") || loweredHealthText.includes("ya resolvieron") || loweredHealthText.includes("solucionado")) &&
      (form.urgency_detail.trim() || form.current_harm.trim())
    ) {
      contradictionSteps.push({
        id: "urgency_detail",
        question: "Tu relato mezcla una posible solucion ya cumplida con una urgencia actual. Aclara exactamente que parte sigue incumplida hoy.",
        placeholder: "Ej: autorizaron una parte, pero aun no entregan el medicamento / ya resolvieron todo",
        multiline: true,
        show: true,
      });
    }

    const healthSteps = [];
    if (form.acting_capacity !== "nombre_propio") {
      healthSteps.push(
        {
          id: "represented_person_name",
          question: "Como se llama el menor o la persona afectada por quien presentas el caso?",
          placeholder: "Ej: Jeronimo Perez Lopez",
          multiline: false,
          show: !form.represented_person_name.trim(),
        },
        {
          id: "represented_person_age",
          question: "Que edad tiene o cual es la fecha de nacimiento del menor o representado?",
          placeholder: "Ej: 7 anos / 12 de abril de 2018",
          multiline: false,
          show: !form.represented_person_age.trim(),
        },
        {
          id: "represented_person_document",
          question: "Si la tienes a la mano, cual es la TI, NUIP o documento del menor o representado?",
          placeholder: "Ej: TI 1022334455",
          multiline: false,
          show: !form.represented_person_document.trim(),
        }
      );
    }

    healthSteps.push(
      {
        id: "target_entity",
        question: "Cual EPS, IPS o entidad de salud esta causando hoy el problema?",
        placeholder: "Ej: Nueva EPS, Sura EPS, Sanitas, Hospital X",
        multiline: false,
        show: !form.target_entity.trim() && !form.eps_name.trim(),
      },
      {
        id: "diagnosis",
        question: "Cual es el diagnostico o la condicion medica principal del paciente?",
        placeholder: "Ej: cancer de seno, anemia falciforme, insuficiencia renal, embarazo de alto riesgo",
        multiline: false,
        show: !form.diagnosis.trim(),
      },
      {
        id: "treatment_needed",
        question: "Que medicamento, examen, cita, terapia, cirugia o tratamiento necesitas exactamente?",
        placeholder: "Ej: autorizacion de resonancia, entrega de medicamento, quimioterapia, terapia integral",
        multiline: true,
        show: !form.treatment_needed.trim(),
      },
      {
        id: "urgency_detail",
        question: "Que sigue pasando hoy al paciente y por que no se puede esperar mas, especialmente si el tratamiento se interrumpio?",
        placeholder: "Ej: dolor intenso, empeoramiento, crisis frecuentes, suspension del tratamiento, riesgo para embarazo o para un menor",
        multiline: true,
        show: !form.urgency_detail.trim() && !form.current_harm.trim(),
      },
      {
        id: "evidence_summary",
        question: "Que soporte medico tienes hoy o puedes describir ya: orden medica, formula, historia clinica, autorizacion, negacion o radicado?",
        placeholder: "Ej: orden del 4 de marzo, formula medica, historia clinica PDF, respuesta de la EPS",
        multiline: true,
        show: !form.evidence_summary.trim() && !form.supporting_documents.trim(),
      },
      {
        id: "prior_claim_result",
        question: "Cuando pidieron el servicio, que hizo la EPS o la entidad: nego, guardo silencio, demoro, no agendo o puso otra barrera?",
        placeholder: "Ej: negaron por no PBS, no respondieron al radicado, no asignaron cita, dejaron vencer la autorizacion",
        multiline: true,
        show: !form.prior_claim_result.trim() && !form.eps_response_detail.trim(),
      },
      {
        id: "concrete_request",
        question: "Que necesitas que ordenen o entreguen exactamente para resolver el caso?",
        placeholder: "Ej: autorizar el examen, entregar medicamento continuo, programar cirugia, responder de fondo",
        multiline: true,
        show: !form.concrete_request.trim(),
      }
    );

    if (action === "accion de tutela") {
      healthSteps.push(
        {
          id: "tutela_special_protection_detail",
          question: "Si el paciente es menor, esta embarazada, tiene discapacidad o una condicion grave, explica por que eso vuelve mas urgente el caso.",
          placeholder: "Ej: es un menor de edad con tratamiento continuo / embarazo de alto riesgo / discapacidad con dependencia funcional",
          multiline: true,
          show:
            (!form.tutela_special_protection_detail.trim() && normalizeAction(form.special_protection) !== "no aplica")
            || (!form.tutela_special_protection_detail.trim() && !!form.represented_person_name.trim()),
        },
        {
          id: "tutela_other_means_detail",
          question: "Que hiciste antes para resolverlo y por que eso no alcanzo a proteger al paciente?",
          placeholder: "Ej: radique PQRS, llame varias veces y la EPS siguio sin autorizar ni agendar",
          multiline: true,
          show: !form.tutela_other_means_detail.trim(),
        },
        {
          id: "tutela_immediacy_detail",
          question: "Por que la tutela se presenta ahora y que riesgo actual sigue vigente?",
          placeholder: "Ej: la negativa es reciente y el dano sigue ocurriendo hoy",
          multiline: true,
          show: !form.tutela_immediacy_detail.trim(),
        },
        {
          id: "tutela_no_temperity_detail",
          question: "Ya hubo otra tutela por este mismo problema o esta es la primera?",
          placeholder: "Ej: no he presentado otra tutela por estos mismos hechos y derechos",
          multiline: true,
          show: !form.tutela_no_temperity_detail.trim() && !form.prior_tutela.trim(),
        }
      );
    }

    return [...contradictionSteps, ...healthSteps.filter((step) => step.show)].filter((step, index, array) =>
      array.findIndex((candidate) => candidate.id === step.id) === index,
    );
  }

  const steps = [
    {
      id: "target_entity",
      question: "¿Contra qué entidad, empresa o autoridad va dirigido este documento?",
      placeholder: "Ej: Nueva EPS, Bancolombia, Alcaldia de Medellin, Datacredito",
      multiline: false,
      show: !form.target_entity.trim(),
    },
    {
      id: "event_date",
      question: "¿Desde cuándo ocurre el problema o cuál fue la fecha clave del primer hecho?",
      placeholder: "Ej: desde enero de 2026 / el 12 de marzo de 2026",
      multiline: false,
      show: !form.event_date.trim(),
    },
    {
      id: "concrete_request",
      question: "¿Qué quieres que ordenen, corrijan, entreguen o respondan exactamente?",
      placeholder: "Ej: entregar medicamento, corregir reporte, reversar cobro, responder de fondo",
      multiline: true,
      show: !form.concrete_request.trim(),
    },
    {
      id: "current_harm",
      question: "¿Cómo te afecta hoy este problema o qué riesgo existe si no responden?",
      placeholder: "Ej: afectacion en salud, minimo vital, suspension del servicio, reporte negativo",
      multiline: true,
      show: !form.current_harm.trim(),
    },
    {
      id: "evidence_summary",
      question: "¿Qué pruebas tienes ya disponibles para respaldar el caso?",
      placeholder: "Ej: PDF, fotos, capturas, chats, correos, orden medica, contrato, extractos",
      multiline: true,
      show: !form.evidence_summary.trim(),
    },
  ];

  if (form.category === "Salud") {
    steps.push(
      {
        id: "eps_name",
        question: "¿Qué EPS, IPS o entidad de salud está involucrada?",
        placeholder: "Ej: Nueva EPS, Sura, San Vicente Fundacion",
        multiline: false,
        show: !form.eps_name.trim(),
      },
      {
        id: "diagnosis",
        question: "¿Cuál es el diagnóstico o condición médica relevante?",
        placeholder: "Ej: anemia falciforme, cáncer, insuficiencia renal, embarazo de alto riesgo",
        multiline: false,
        show: !form.diagnosis.trim(),
      },
      {
        id: "treatment_needed",
        question: "¿Qué medicamento, examen, cirugía o tratamiento necesitas exactamente?",
        placeholder: "Ej: entrega de hidroxiurea 500 mg cada 8 horas por 6 meses",
        multiline: true,
        show: !form.treatment_needed.trim(),
      },
      {
        id: "urgency_detail",
        question: "¿Por qué este caso de salud es urgente hoy o qué riesgo existe si no actúan ya?",
        placeholder: "Ej: empeora la enfermedad, dolor intenso, suspension del tratamiento, riesgo de recaida o complicacion",
        multiline: true,
        show: !form.urgency_detail.trim(),
      }
    );
  }

  if (form.category === "Salud" || action === "accion de tutela") {
    steps.push(
      {
        id: "represented_person_name",
        question: "¿Cuál es el nombre del menor o de la persona afectada principal?",
        placeholder: "Ej: Jeronimo Perez Lopez",
        multiline: false,
        show:
          form.acting_capacity !== "nombre_propio" &&
          !form.represented_person_name?.trim(),
      },
      {
        id: "represented_person_age",
        question: "¿Qué edad tiene o cuál es la fecha de nacimiento de la persona representada?",
        placeholder: "Ej: 7 años / 12 de abril de 2018",
        multiline: false,
        show:
          form.acting_capacity !== "nombre_propio" &&
          !form.represented_person_age?.trim(),
      },
      {
        id: "represented_person_document",
        question: "¿Cuál es el documento del menor o de la persona representada?",
        placeholder: "Ej: Registro civil 12345678 / TI 1022334455 / NUIP 1234567890",
        multiline: false,
        show:
          form.acting_capacity !== "nombre_propio" &&
          !form.represented_person_document?.trim(),
      }
    );
  }

  if (form.category === "Bancos") {
    steps.push(
      {
        id: "bank_product_type",
        question: "¿Qué producto financiero está involucrado?",
        placeholder: "Ej: tarjeta de credito, cuenta de ahorros, prestamo",
        multiline: false,
        show: !form.bank_product_type.trim(),
      },
      {
        id: "bank_amount_involved",
        question: "¿Qué valor, monto o cobro está en discusión?",
        placeholder: "Ej: $38.500 mensuales / $154.000 acumulados",
        multiline: false,
        show: !form.bank_amount_involved.trim(),
      },
      {
        id: "bank_claim_goal",
        question: "¿Qué resultado esperas frente al banco: reverso, devolución, corrección del reporte, desbloqueo o respuesta?",
        placeholder: "Ej: eliminar el seguro, devolver cobros, corregir reporte y responder de fondo",
        multiline: true,
        show: !form.bank_claim_goal.trim(),
      },
      {
        id: "report_or_block_reason",
        question: "¿Cuál es el hecho bancario principal: cobro, seguro, reporte, mora, fraude o bloqueo?",
        placeholder: "Ej: seguro no autorizado y cuota de manejo cobrada sin consentimiento",
        multiline: true,
        show: !form.report_or_block_reason.trim(),
      }
    );
  }

  if (form.category === "Datos") {
    steps.push(
      {
        id: "disputed_data",
        question: "¿Qué dato, reporte o registro personal está mal o debe corregirse?",
        placeholder: "Ej: reporte negativo en Datacredito por obligación ya pagada",
        multiline: true,
        show: !form.disputed_data.trim(),
      },
      {
        id: "requested_data_action",
        question: "¿Qué quieres que haga la entidad con ese dato?",
        placeholder: "Ej: corregir, actualizar, eliminar o probar autorizacion",
        multiline: false,
        show: !form.requested_data_action.trim(),
      },
      {
        id: "previous_response",
        question: "¿Ya reclamaste antes ante la fuente o central de riesgo? Si sí, ¿qué te respondieron?",
        placeholder: "Ej: reclamé por derecho de peticion el 3 de marzo y respondieron que el reporte seguía vigente",
        multiline: true,
        show: !form.previous_response.trim(),
      }
    );
  }

  if (form.category === "Laboral") {
    steps.push(
      {
        id: "labor_employer_name",
        question: "¿Quién es el empleador o contratante involucrado?",
        placeholder: "Ej: Empresa X SAS, Alcaldia, persona natural",
        multiline: false,
        show: !form.labor_employer_name.trim(),
      },
      {
        id: "dismissal_or_measure",
        question: "¿Qué medida o incumplimiento laboral ocurrió exactamente?",
        placeholder: "Ej: despido, no pago de salarios, suspension, negativa de reintegro",
        multiline: true,
        show: !form.dismissal_or_measure.trim(),
      }
    );
  }

  if (normalizeAction(form.recommended_action) === "accion de tutela") {
    steps.push(
      {
        id: "tutela_other_means_detail",
        question: "Para esta tutela, ¿por qué no basta otro trámite o por qué hay urgencia?",
        placeholder: "Ej: la vulneracion sigue ocurriendo y no existe otro medio eficaz",
        multiline: true,
        show: !form.tutela_other_means_detail.trim(),
      },
      {
        id: "tutela_immediacy_detail",
        question: "¿Por qué se presenta la tutela ahora y no después?",
        placeholder: "Ej: el daño es actual, el riesgo sigue vigente, la negativa es reciente",
        multiline: true,
        show: !form.tutela_immediacy_detail.trim(),
      },
      {
        id: "tutela_no_temperity_detail",
        question: "¿Ya presentaste otra tutela por los mismos hechos y derechos? Si no, déjalo claro aquí.",
        placeholder: "Ej: no he presentado otra tutela por estos mismos hechos y derechos",
        multiline: true,
        show: !form.tutela_no_temperity_detail.trim(),
      }
    );
  }

  if (normalizeAction(form.recommended_action).includes("derecho de peticion")) {
    steps.push(
      {
        id: "request_type",
        question: "¿Tu derecho de petición es de información, documentos, consulta o interés particular?",
        placeholder: "Ej: informacion o interes particular",
        multiline: false,
        show: !form.request_type.trim(),
      },
      {
        id: "numbered_requests",
        question: "Separa en dos o tres solicitudes numeradas exactamente lo que esperas que te respondan.",
        placeholder: "Ej: 1) Entregar copia de la respuesta 2) Corregir el cobro 3) Certificar el estado del caso",
        multiline: true,
        show: !form.numbered_requests.trim(),
      }
    );
  }

  for (const step of steps) {
    if (step.id === "urgency_detail") {
      step.question = "Que esta pasando hoy al paciente desde que falta el servicio o medicamento?";
      step.placeholder = "Ej: sigue sin medicamento, empeora, tiene dolor, crisis, recaidas o no puede iniciar el tratamiento";
    }
    if (step.id === "tutela_other_means_detail") {
      step.question = "Antes de llegar aqui, que hiciste para resolverlo y que paso despues?";
      step.placeholder = "Ej: pedi autorizacion, no respondieron o no agendaron, y el problema sigue igual";
    }
    if (step.id === "tutela_immediacy_detail") {
      step.question = "Que sigue pasando hoy al paciente o al afectado desde que no entregan el servicio?";
      step.placeholder = "Ej: sigue sin medicamento, no hacen el examen, empeora, tiene dolor o no puede empezar el tratamiento";
    }
  }

  return steps.filter((step) => step.show);
};

const getActionSpecificMissing = (recommendedAction, form) => {
  const action = normalizeAction(recommendedAction);
  const missing = [];

  if (action === "queja formal") {
    if (!form.complaint_reason.trim()) missing.push("Motivo principal de la queja");
    if (!form.complaint_expected_response.trim()) missing.push("Respuesta o intervencion esperada");
  }

  if (action === "accion de tutela") {
    if (!form.tutela_no_temperity_detail.trim()) missing.push("Si ya hubo otra tutela o solicitud previa");
    if (!form.tutela_other_means_detail.trim()) missing.push("Que hiciste antes y que sigue pasando hoy");
    if (!form.tutela_immediacy_detail.trim()) missing.push("Por que esto es urgente ahora");
  }

  if (action === "derecho de peticion" || action === "derecho de peticion a eps" || action === "derecho de peticion laboral" || action === "derecho de peticion financiero" || action === "derecho de peticion a empresa de servicios" || action === "derecho de peticion al proveedor") {
    if (!form.petition_target_nature.trim()) missing.push("Naturaleza del destinatario");
    if (!form.petition_previous_submission_date.trim()) missing.push("Fecha de radicacion o gestion previa");
    if (form.petition_target_nature === "privada" && !form.petition_private_ground.trim()) missing.push("Fundamento para peticion a particular");
  }

  if (action === "reclamo administrativo" || action === "reclamacion financiera" || action === "reclamacion por servicios publicos" || action === "reclamo de consumo") {
    if (!form.administrative_error_detail.trim()) missing.push("Actuacion, cobro o error administrativo cuestionado");
    if (!form.administrative_requested_fix.trim()) missing.push("Correccion administrativa solicitada");
  }

  if (action === "queja disciplinaria") {
    if (!form.disciplinary_subject_name.trim()) missing.push("Funcionario o sujeto disciplinable");
    if (!form.disciplinary_subject_role.trim()) missing.push("Cargo o rol del sujeto disciplinable");
    if (!form.disciplinary_conduct.trim()) missing.push("Conducta disciplinaria denunciada");
    if (!form.disciplinary_event_date.trim()) missing.push("Fecha de la conducta o hecho disciplinario");
  }

  if (action === "accion de cumplimiento" || action === "acción de cumplimiento") {
    if (!form.compliance_norm_or_act.trim()) missing.push("Norma o acto incumplido");
    if (!form.compliance_authority.trim()) missing.push("Autoridad obligada a cumplir");
    if (!form.compliance_prior_requirement.trim()) missing.push("Requerimiento previo realizado");
    if (!form.compliance_breach_detail.trim()) missing.push("Forma concreta del incumplimiento");
  }

  if (action === "impugnacion de tutela" || action === "impugnación de tutela") {
    if (!form.tutela_court_name.trim()) missing.push("Juzgado o despacho que decidio la tutela");
    if (!form.tutela_ruling_date.trim()) missing.push("Fecha del fallo o decision");
    if (!form.tutela_decision_result.trim()) missing.push("Resultado de la decision de tutela");
    if (!form.tutela_appeal_reason.trim()) missing.push("Motivos concretos de impugnacion");
  }

  if (action === "incidente de desacato") {
    if (!form.tutela_court_name.trim()) missing.push("Juzgado o despacho de tutela");
    if (!form.tutela_ruling_date.trim()) missing.push("Fecha del fallo de tutela");
    if (!form.tutela_order_summary.trim()) missing.push("Orden judicial incumplida");
    if (!form.tutela_noncompliance_detail.trim()) missing.push("Detalle del incumplimiento");
  }

  return missing;
};

const getActionSpecificIssues = (recommendedAction, form) => {
  const action = normalizeAction(recommendedAction);
  const issues = [];

  if (action === "queja formal") {
    if (form.complaint_reason.trim().length < 20) issues.push("La queja formal necesita una descripcion mas clara de la irregularidad o mala atencion.");
    if (form.complaint_expected_response.trim().length < 15) issues.push("Debes decir que esperas: investigacion, respuesta formal, correccion o traslado.");
  }

  if (action === "accion de tutela") {
    if (form.tutela_previous_action_detail.trim().length < 15) issues.push("La tutela debe diferenciar si ya hubo otra tutela, peticion, incidente o medida previa por los mismos hechos.");
    if (!form.tutela_oath_statement.trim() && form.tutela_no_temperity_detail.trim().length < 20) issues.push("La tutela debe incluir una declaracion expresa bajo juramento sobre no temeridad.");
    if (form.tutela_other_means_detail.trim().length < 25) issues.push("Cuenta con mas detalle que hiciste antes y que sigue pasando hoy para mostrar por que el problema sigue abierto.");
    if (form.tutela_immediacy_detail.trim().length < 20) issues.push("Cuenta mejor que sigue pasando hoy al paciente para que la IA construya internamente la urgencia del caso.");
  }

  if (action === "derecho de peticion" || action === "derecho de peticion a eps" || action === "derecho de peticion laboral" || action === "derecho de peticion financiero" || action === "derecho de peticion a empresa de servicios" || action === "derecho de peticion al proveedor") {
    if (form.petition_previous_submission_date.trim().length < 8) issues.push("Conviene precisar la fecha de radicacion o el momento exacto de la solicitud para controlar el termino legal.");
    if (form.request_type.trim().length < 5) issues.push("Debes precisar mejor la modalidad del derecho de peticion.");
    if (form.petition_target_nature === "privada" && form.petition_private_ground.trim().length < 15) {
      issues.push("Si la peticion va contra un privado, debes explicar por que ese particular esta obligado a responder.");
    }
  }

  if (action === "reclamo administrativo" || action === "reclamacion financiera" || action === "reclamacion por servicios publicos" || action === "reclamo de consumo") {
    if (form.administrative_error_detail.trim().length < 20) issues.push("El reclamo debe explicar mejor el error, cobro o decision administrativa controvertida.");
    if (form.administrative_requested_fix.trim().length < 15) issues.push("Debes concretar la correccion administrativa que solicitas.");
  }

  if (action === "queja disciplinaria") {
    if (form.disciplinary_conduct.trim().length < 20) issues.push("La queja disciplinaria debe narrar mejor la conducta irregular denunciada.");
  }

  if (action === "accion de cumplimiento" || action === "acción de cumplimiento") {
    if (form.compliance_norm_or_act.trim().length < 12) issues.push("Debes identificar con mayor precision la ley, norma o acto administrativo incumplido.");
    if (form.compliance_breach_detail.trim().length < 20) issues.push("Falta explicar con mas claridad como se esta incumpliendo la obligacion.");
  }

  if (action === "impugnacion de tutela" || action === "impugnación de tutela") {
    if (form.tutela_appeal_reason.trim().length < 25) issues.push("La impugnacion necesita motivos concretos de desacuerdo con la decision de tutela.");
  }

  if (action === "incidente de desacato") {
    if (form.tutela_noncompliance_detail.trim().length < 25) issues.push("El desacato necesita explicar con hechos concretos como se incumplio la orden del juez.");
  }

  return issues;
};

function ActionSpecificQuestions({ recommendedAction, form, setForm, missingFields, issues }) {
  const action = normalizeAction(recommendedAction);
  const setField = (key, value) => setForm((current) => ({ ...current, [key]: value }));

  if (!action) return null;

  let title = "";
  let fields = null;

  if (action === "queja formal") {
    title = "Preguntas finas para queja formal";
    fields = (
      <>
        <Field label="Motivo principal de la queja">
          <TextArea value={form.complaint_reason} onChange={(event) => setField("complaint_reason", event.target.value)} placeholder="Explica la irregularidad, mala atencion, omision o incumplimiento que quieres denunciar." style={{ minHeight: 90 }} />
        </Field>
        <Field label="Respuesta o intervencion esperada">
          <TextInput value={form.complaint_expected_response} onChange={(event) => setField("complaint_expected_response", event.target.value)} placeholder="Ej: investigacion, respuesta formal, correccion, traslado al area competente" />
        </Field>
      </>
    );
  } else if (action === "accion de tutela") {
    title = "Preguntas finas para accion de tutela";
    fields = (
      <>
        <Field label="Calidad en que actuas">
          <select
            value={form.acting_capacity}
            onChange={(event) => setField("acting_capacity", event.target.value)}
            style={{ width: "100%", padding: "14px 16px", borderRadius: 12, border: `1px solid ${C.border}`, background: "#fff", color: C.text }}
          >
            <option value="nombre_propio">En nombre propio</option>
            <option value="madre_padre_menor">Madre o padre de menor de edad</option>
            <option value="acudiente">Acudiente o cuidador</option>
            <option value="agente_oficioso">Agente oficioso</option>
            <option value="representante_legal">Representante legal</option>
          </select>
        </Field>
        {form.acting_capacity !== "nombre_propio" && (
          <>
            <Field label="Nombre del menor o persona representada">
              <TextInput value={form.represented_person_name} onChange={(event) => setField("represented_person_name", event.target.value)} placeholder="Ej: Jeronimo Perez Lopez" />
            </Field>
            <Field label="Documento del menor o persona representada">
              <TextInput value={form.represented_person_document} onChange={(event) => setField("represented_person_document", event.target.value)} placeholder="Ej: registro civil, TI, NUIP o sin documento aun" />
            </Field>
            <Field label="Edad o fecha de nacimiento">
              <TextInput value={form.represented_person_age} onChange={(event) => setField("represented_person_age", event.target.value)} placeholder="Ej: 7 años / 12 de abril de 2018" />
            </Field>
            <Field label="Condicion relevante de la persona representada">
              <TextInput value={form.represented_person_condition} onChange={(event) => setField("represented_person_condition", event.target.value)} placeholder="Ej: menor con anemia falciforme, paciente de alto riesgo, discapacidad" />
            </Field>
          </>
        )}
        <Field label="Otra tutela, medida o actuacion previa sobre estos mismos hechos">
          <TextArea value={form.tutela_previous_action_detail} onChange={(event) => setField("tutela_previous_action_detail", event.target.value)} placeholder="Indica si ya presentaste otra tutela, peticion, incidente o medida por este mismo caso. Si no, dilo con claridad." style={{ minHeight: 90 }} />
        </Field>
        <Field label="Confirma si esta es la primera tutela por este problema">
          <TextArea value={form.tutela_oath_statement} onChange={(event) => setField("tutela_oath_statement", event.target.value)} placeholder="Ej: no he presentado otra tutela por estos mismos hechos." style={{ minHeight: 90 }} />
        </Field>
        <Field label="Que hiciste antes para resolverlo y que sigue pasando hoy">
          <TextArea value={form.tutela_other_means_detail} onChange={(event) => setField("tutela_other_means_detail", event.target.value)} placeholder="Ej: fui a la EPS, a la farmacia y a atencion al usuario, pero no solucionaron; mi hijo sigue sin medicamento y el riesgo continua." style={{ minHeight: 90 }} />
        </Field>
        <Field label="Que sigue pasando hoy al paciente">
          <TextInput value={form.tutela_immediacy_detail} onChange={(event) => setField("tutela_immediacy_detail", event.target.value)} placeholder="Ej: el medicamento sigue sin entregarse, no hacen el examen y el paciente sigue empeorando" />
        </Field>
        <Field label="Sujeto de especial proteccion, si aplica">
          <TextInput value={form.tutela_special_protection_detail} onChange={(event) => setField("tutela_special_protection_detail", event.target.value)} placeholder="Ej: menor, embarazada, adulto mayor, discapacidad, paciente de alto riesgo" />
        </Field>
      </>
    );
  } else if (action === "derecho de peticion" || action === "derecho de peticion a eps" || action === "derecho de peticion laboral" || action === "derecho de peticion financiero" || action === "derecho de peticion a empresa de servicios" || action === "derecho de peticion al proveedor") {
    title = "Preguntas finas para derecho de peticion";
    fields = (
      <>
        <Field label="Naturaleza del destinatario">
          <select
            value={form.petition_target_nature}
            onChange={(event) => setField("petition_target_nature", event.target.value)}
            style={{ width: "100%", padding: "14px 16px", borderRadius: 12, border: `1px solid ${C.border}`, background: "#fff", color: C.text }}
          >
            <option value="publica">Entidad publica</option>
            <option value="privada">Particular obligado</option>
          </select>
        </Field>
        <Field label="Fecha de radicacion o gestion previa">
          <TextInput value={form.petition_previous_submission_date} onChange={(event) => setField("petition_previous_submission_date", event.target.value)} placeholder="Ej: 4 de marzo de 2026 / hoy se radica por primera vez" />
        </Field>
        <Field label="Norma sectorial o contexto especial">
          <TextInput value={form.petition_sector_rule} onChange={(event) => setField("petition_sector_rule", event.target.value)} placeholder="Ej: salud, consumidor, servicios, financiero, datos personales" />
        </Field>
        {form.petition_target_nature === "privada" && (
          <Field label="Fundamento para peticion a particular">
            <TextArea value={form.petition_private_ground} onChange={(event) => setField("petition_private_ground", event.target.value)} placeholder="Explica por que ese particular esta obligado a responder: servicio publico, interes colectivo, posicion dominante, etc." style={{ minHeight: 90 }} />
          </Field>
        )}
      </>
    );
  } else if (action === "reclamo administrativo" || action === "reclamacion financiera" || action === "reclamacion por servicios publicos" || action === "reclamo de consumo") {
    title = "Preguntas finas para reclamo administrativo";
    fields = (
      <>
        <Field label="Actuacion, cobro o error cuestionado">
          <TextArea value={form.administrative_error_detail} onChange={(event) => setField("administrative_error_detail", event.target.value)} placeholder="Describe el cobro, respuesta, factura, decision o actuacion que debe corregirse." style={{ minHeight: 90 }} />
        </Field>
        <Field label="Correccion administrativa solicitada">
          <TextInput value={form.administrative_requested_fix} onChange={(event) => setField("administrative_requested_fix", event.target.value)} placeholder="Ej: anular cobro, corregir factura, responder de fondo, levantar reporte, devolver dinero" />
        </Field>
      </>
    );
  } else if (action === "queja disciplinaria") {
    title = "Preguntas finas para queja disciplinaria";
    fields = (
      <>
        <Field label="Funcionario o sujeto disciplinable">
          <TextInput value={form.disciplinary_subject_name} onChange={(event) => setField("disciplinary_subject_name", event.target.value)} placeholder="Nombre de la persona denunciada" />
        </Field>
        <Field label="Cargo o rol del sujeto disciplinable">
          <TextInput value={form.disciplinary_subject_role} onChange={(event) => setField("disciplinary_subject_role", event.target.value)} placeholder="Ej: inspector, secretario, directivo, servidor publico" />
        </Field>
        <Field label="Fecha del hecho disciplinario">
          <TextInput value={form.disciplinary_event_date} onChange={(event) => setField("disciplinary_event_date", event.target.value)} placeholder="Ej: 14 de marzo de 2026" />
        </Field>
        <Field label="Conducta disciplinaria denunciada">
          <TextArea value={form.disciplinary_conduct} onChange={(event) => setField("disciplinary_conduct", event.target.value)} placeholder="Explica la conducta, omision o abuso que debe investigarse." style={{ minHeight: 90 }} />
        </Field>
      </>
    );
  } else if (action === "accion de cumplimiento" || action === "acción de cumplimiento") {
    title = "Preguntas finas para accion de cumplimiento";
    fields = (
      <>
        <Field label="Norma o acto incumplido">
          <TextInput value={form.compliance_norm_or_act} onChange={(event) => setField("compliance_norm_or_act", event.target.value)} placeholder="Ley, decreto, resolucion o acto administrativo concreto" />
        </Field>
        <Field label="Autoridad obligada a cumplir">
          <TextInput value={form.compliance_authority} onChange={(event) => setField("compliance_authority", event.target.value)} placeholder="Entidad o autoridad responsable" />
        </Field>
        <Field label="Requerimiento previo realizado">
          <TextInput value={form.compliance_prior_requirement} onChange={(event) => setField("compliance_prior_requirement", event.target.value)} placeholder="Peticion, requerimiento o solicitud previa que ya hiciste" />
        </Field>
        <Field label="Forma concreta del incumplimiento">
          <TextArea value={form.compliance_breach_detail} onChange={(event) => setField("compliance_breach_detail", event.target.value)} placeholder="Explica que debia cumplirse y como la autoridad sigue incumpliendolo." style={{ minHeight: 90 }} />
        </Field>
      </>
    );
  } else if (action === "impugnacion de tutela" || action === "impugnación de tutela") {
    title = "Preguntas finas para impugnacion de tutela";
    fields = (
      <>
        <Field label="Juzgado o despacho que decidio la tutela">
          <TextInput value={form.tutela_court_name} onChange={(event) => setField("tutela_court_name", event.target.value)} placeholder="Juzgado o tribunal que emitio la decision" />
        </Field>
        <Field label="Fecha del fallo o decision">
          <TextInput value={form.tutela_ruling_date} onChange={(event) => setField("tutela_ruling_date", event.target.value)} placeholder="Ej: 13 de marzo de 2026" />
        </Field>
        <Field label="Resultado de la decision de tutela">
          <TextInput value={form.tutela_decision_result} onChange={(event) => setField("tutela_decision_result", event.target.value)} placeholder="Ej: negada, improcedente, concedida parcialmente" />
        </Field>
        <Field label="Motivos concretos de impugnacion">
          <TextArea value={form.tutela_appeal_reason} onChange={(event) => setField("tutela_appeal_reason", event.target.value)} placeholder="Explica por que la decision esta equivocada o deja sin proteccion suficiente el derecho." style={{ minHeight: 90 }} />
        </Field>
      </>
    );
  } else if (action === "incidente de desacato") {
    title = "Preguntas finas para incidente de desacato";
    fields = (
      <>
        <Field label="Juzgado o despacho de tutela">
          <TextInput value={form.tutela_court_name} onChange={(event) => setField("tutela_court_name", event.target.value)} placeholder="Juzgado que emitio el fallo de tutela" />
        </Field>
        <Field label="Fecha del fallo de tutela">
          <TextInput value={form.tutela_ruling_date} onChange={(event) => setField("tutela_ruling_date", event.target.value)} placeholder="Ej: 10 de marzo de 2026" />
        </Field>
        <Field label="Orden judicial incumplida">
          <TextInput value={form.tutela_order_summary} onChange={(event) => setField("tutela_order_summary", event.target.value)} placeholder="Ej: autorizar procedimiento, entregar medicamento, responder de fondo" />
        </Field>
        <Field label="Detalle del incumplimiento">
          <TextArea value={form.tutela_noncompliance_detail} onChange={(event) => setField("tutela_noncompliance_detail", event.target.value)} placeholder="Explica como, desde cuando y con que evidencia se incumplio la orden del juez." style={{ minHeight: 90 }} />
        </Field>
      </>
    );
  }

  if (!fields) return null;

  return (
    <div className="glass-card" style={{ padding: 18, background: "#F8FAFD", border: `1px solid ${C.border}` }}>
      <div style={{ fontSize: 12, fontWeight: 800, letterSpacing: 0.4, color: C.textMuted }}>AJUSTE FINO POR PRODUCTO</div>
      <div style={{ marginTop: 8, color: C.text, fontWeight: 800 }}>{title}</div>
      {!!missingFields.length && (
        <div style={{ marginTop: 12, display: "flex", gap: 8, flexWrap: "wrap" }}>
          {missingFields.map((item) => <Badge key={item} color={C.warning}>Falta: {item}</Badge>)}
        </div>
      )}
      {!!issues.length && (
        <div style={{ display: "grid", gap: 10, marginTop: 14 }}>
          {issues.map((issue) => (
            <div key={issue} style={{ color: "#92400E", background: "#FFFBEB", border: "1px solid #FDE68A", padding: 14, borderRadius: 14 }}>
              {issue}
            </div>
          ))}
        </div>
      )}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 16, marginTop: 16 }}>
        {fields}
      </div>
    </div>
  );
}

function PreviewGateCard({ missing = [], issues = [] }) {
  if (!missing.length && !issues.length) {
    return (
      <div className="glass-card" style={{ padding: 18, background: "#F0FDF4", border: "1px solid #86EFAC" }}>
        <div style={{ fontSize: 12, fontWeight: 800, letterSpacing: 0.4, color: C.textMuted }}>CALIDAD MINIMA PARA ANALISIS</div>
        <div style={{ marginTop: 8, color: C.text, fontWeight: 800 }}>La informacion actual ya permite generar el analisis inicial.</div>
      </div>
    );
  }

  return (
    <div className="glass-card" style={{ padding: 18, background: "#FFF7ED", border: "1px solid #FDBA74" }}>
      <div style={{ fontSize: 12, fontWeight: 800, letterSpacing: 0.4, color: C.textMuted }}>ANTES DEL PREVIEW</div>
      <div style={{ marginTop: 8, color: C.text, fontWeight: 800 }}>
        Todavia faltan datos minimos para que la IA produzca un analisis juridico serio.
      </div>
      {!!missing.length && (
        <div style={{ marginTop: 14, display: "flex", gap: 8, flexWrap: "wrap" }}>
          {missing.map((item) => <Badge key={item} color={C.warning}>Falta: {item}</Badge>)}
        </div>
      )}
      <div style={{ display: "grid", gap: 10, marginTop: 14 }}>
        {issues.map((issue) => (
          <div key={issue} style={{ color: "#9A3412", background: "#FFEDD5", border: "1px solid #FDBA74", padding: 14, borderRadius: 14 }}>
            {issue}
          </div>
        ))}
      </div>
    </div>
  );
}

const AI_OWNED_REVIEW_PATTERNS = [
  "declaracion de no temeridad",
  "subsidiariedad",
  "perjuicio irremediable",
  "inmediatez",
  "articulo 42",
  "procedencia con base",
  "urgencia, vulneracion o procedencia",
  "jurisprudencia sin soporte oficial verificado",
  "soporte jurisprudencial",
  "fuentes verificadas",
];

const isAiOwnedReviewIssue = (issue) => {
  const normalized = normalizeAction(issue);
  return AI_OWNED_REVIEW_PATTERNS.some((pattern) => normalized.includes(normalizeAction(pattern)));
};

const humanizeAiOwnedIssue = (issue) => {
  const normalized = normalizeAction(issue);
  if (normalized.includes("declaracion de no temeridad")) {
    return "La IA incorporara este control interno y, si hace falta, solo te pedira confirmar si ya hubo otra tutela o solicitud previa.";
  }
  if (normalized.includes("juramento")) {
    return "La IA dejara listo este control interno dentro del documento final usando la informacion del expediente.";
  }
  if (normalized.includes("subsidiariedad") || normalized.includes("perjuicio irremediable")) {
    return "La IA reforzara internamente por que este caso necesita intervenirse ya, con base en lo que paso antes y en el dano actual.";
  }
  if (normalized.includes("inmediatez")) {
    return "La IA explicara por que el problema sigue ocurriendo hoy o por que la accion se presenta en este momento.";
  }
  if (normalized.includes("articulo 42") || normalized.includes("procedencia con base")) {
    return "Si la tutela va contra un particular, la IA construira internamente esa justificacion sin pedirtela en lenguaje tecnico.";
  }
  if (normalized.includes("urgencia") || normalized.includes("procedencia")) {
    return "La IA reforzara internamente la procedencia con base en tus hechos; tu solo debes contar que pasa hoy, que ordenaron y que hizo la entidad.";
  }
  if (normalized.includes("jurisprudencia") || normalized.includes("fuentes verificadas")) {
    return "La IA verificara y reforzara internamente la jurisprudencia y las fuentes oficiales antes de entregar el documento.";
  }
  return "La IA reforzara este punto juridico dentro del documento final.";
};

function IntakeReviewCard({ review }) {
  if (!review || review.status === "not_scored") {
    return null;
  }

  const originalBlockingIssues = review.blocking_issues || [];
  const originalWarnings = review.warnings || [];
  const aiOwnedBlockingIssues = originalBlockingIssues.filter(isAiOwnedReviewIssue);
  const blockingIssues = originalBlockingIssues.filter((issue) => !isAiOwnedReviewIssue(issue));
  const aiOwnedWarnings = originalWarnings.filter(isAiOwnedReviewIssue);
  const warnings = originalWarnings.filter((issue) => !isAiOwnedReviewIssue(issue));
  const canProceed = blockingIssues.length === 0;

  return (
    <div
      className="glass-card"
      style={{
        padding: 18,
        background: canProceed ? "#F8FAFD" : "#FFF7ED",
        border: `1px solid ${canProceed ? C.border : "#FDBA74"}`,
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
        <div>
          <div style={{ fontSize: 12, fontWeight: 800, letterSpacing: 0.4, color: C.textMuted }}>REVISION JURIDICA INICIAL</div>
          <div style={{ marginTop: 8, color: C.text, fontWeight: 800 }}>
            {canProceed ? "La informacion base permite seguir con advertencias." : "Faltan datos criticos antes de guardar el expediente."}
          </div>
        </div>
        <Badge color={canProceed ? C.primary : C.warning}>{review.status}</Badge>
      </div>

      {!!blockingIssues.length && (
        <div style={{ display: "grid", gap: 10, marginTop: 14 }}>
          {blockingIssues.map((issue) => (
            <div key={issue} style={{ color: "#9A3412", background: "#FFEDD5", border: "1px solid #FDBA74", padding: 14, borderRadius: 14 }}>
              {issue}
            </div>
          ))}
        </div>
      )}

      {!!aiOwnedBlockingIssues.length && (
        <div style={{ display: "grid", gap: 10, marginTop: 14 }}>
          {aiOwnedBlockingIssues.map((issue) => (
            <div key={issue} style={{ color: "#1D4ED8", background: "#EFF6FF", border: "1px solid #BFDBFE", padding: 14, borderRadius: 14 }}>
              {humanizeAiOwnedIssue(issue)}
            </div>
          ))}
        </div>
      )}

      {!!warnings.length && (
        <div style={{ display: "grid", gap: 10, marginTop: 14 }}>
          {warnings.map((warning) => (
            <div key={warning} style={{ color: "#92400E", background: "#FFFBEB", border: "1px solid #FDE68A", padding: 14, borderRadius: 14 }}>
              {warning}
            </div>
          ))}
        </div>
      )}

      {!!aiOwnedWarnings.length && (
        <div style={{ display: "grid", gap: 10, marginTop: 14 }}>
          {aiOwnedWarnings.map((warning) => (
            <div key={warning} style={{ color: "#1D4ED8", background: "#EFF6FF", border: "1px solid #BFDBFE", padding: 14, borderRadius: 14 }}>
              {humanizeAiOwnedIssue(warning)}
            </div>
          ))}
        </div>
      )}

      <div style={{ marginTop: 14, color: C.textMuted, fontSize: 13, lineHeight: 1.6 }}>
        {canProceed
          ? "La IA ya puede continuar con el expediente. Si quieres, luego afinas hechos o soportes para mejorar aun mas la calidad final."
          : "Vuelve al paso anterior y mejora el relato antes de continuar. La plataforma no deberia cobrar ni generar un documento con informacion debil."}
      </div>
    </div>
  );
}

function DocumentRuleReviewCard({ review }) {
  if (!review || !review.rule) {
    return null;
  }

  const originalBlockingIssues = review.blocking_issues || [];
  const aiOwnedIssues = originalBlockingIssues.filter(isAiOwnedReviewIssue);
  const blockingIssues = originalBlockingIssues.filter((issue) => !isAiOwnedReviewIssue(issue));
  const originalWarnings = review.warnings || [];
  const aiOwnedWarnings = originalWarnings.filter(isAiOwnedReviewIssue);
  const warnings = originalWarnings.filter((issue) => !isAiOwnedReviewIssue(issue));
  const canProceed = blockingIssues.length === 0;

  return (
    <div
      className="glass-card"
      style={{
        padding: 18,
        background: canProceed ? "#F8FAFD" : "#FFF7ED",
        border: `1px solid ${canProceed ? C.border : "#FDBA74"}`,
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
        <div>
          <div style={{ fontSize: 12, fontWeight: 800, letterSpacing: 0.4, color: C.textMuted }}>REGLAS DEL PRODUCTO</div>
          <div style={{ marginTop: 8, color: C.text, fontWeight: 800 }}>{review.rule.document_title}</div>
          <div style={{ marginTop: 6, color: C.textMuted }}>{review.rule.goal}</div>
        </div>
        <Badge color={canProceed ? C.primary : C.warning}>{review.status}</Badge>
      </div>

      <div style={{ marginTop: 14, color: C.textMuted, fontSize: 13, lineHeight: 1.6 }}>
        La plataforma ya evalua internamente la estructura del documento, si hacen falta mas hechos y el nivel de soporte requerido para esta ruta.
      </div>

      {!!blockingIssues.length && (
        <div style={{ display: "grid", gap: 10, marginTop: 14 }}>
          {blockingIssues.map((issue) => (
            <div key={issue} style={{ color: "#9A3412", background: "#FFEDD5", border: "1px solid #FDBA74", padding: 14, borderRadius: 14 }}>
              {issue}
            </div>
          ))}
        </div>
      )}

      {!!aiOwnedIssues.length && (
        <div style={{ display: "grid", gap: 10, marginTop: 14 }}>
          {aiOwnedIssues.map((issue) => (
            <div key={issue} style={{ color: "#1D4ED8", background: "#EFF6FF", border: "1px solid #BFDBFE", padding: 14, borderRadius: 14 }}>
              {humanizeAiOwnedIssue(issue)}
            </div>
          ))}
        </div>
      )}

      {!!warnings.length && (
        <div style={{ display: "grid", gap: 10, marginTop: 14 }}>
          {warnings.map((warning) => (
            <div key={warning} style={{ color: "#92400E", background: "#FFFBEB", border: "1px solid #FDE68A", padding: 14, borderRadius: 14 }}>
              {warning}
            </div>
          ))}
        </div>
      )}

      {!!aiOwnedWarnings.length && (
        <div style={{ display: "grid", gap: 10, marginTop: 14 }}>
          {aiOwnedWarnings.map((warning) => (
            <div key={warning} style={{ color: "#1D4ED8", background: "#EFF6FF", border: "1px solid #BFDBFE", padding: 14, borderRadius: 14 }}>
              {humanizeAiOwnedIssue(warning)}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function GuidedIntakeFields({
  form,
  setForm,
  missingFields,
  entityLookupLoading = false,
  entitySuggestions = [],
  onApplyEntitySuggestion = () => {},
}) {
  const setField = (key, value) => setForm((current) => ({ ...current, [key]: value }));
  const writingAid = getWritingAid(form.category);
  const isHealthAgentLed = form.category === "Salud";
  const isPetitionTrack = ["Laboral", "Bancos", "Servicios", "Consumidor"].includes(form.category);
  const interviewSteps = buildGuidedIntakeInterviewSteps(form);
  const activeInterviewStep = interviewSteps[0] || null;
  const isCorrectionStep = activeInterviewStep && ["target_entity", "prior_claim_result", "acting_capacity", "special_protection", "urgency_detail"].includes(activeInterviewStep.id);
  const [assistantDraft, setAssistantDraft] = useState("");
  const evidenceHints = evidenceTypeHints[form.category] || evidenceTypeHints.default;
  const assistantProgress = interviewSteps.length ? `1 de ${interviewSteps.length}` : null;

  const quickChannels = ["Correo electronico", "WhatsApp", "Direccion fisica", "Correo y WhatsApp"];
  const quickRequestTypes = ["Interes particular", "Informacion", "Documentos", "Consulta"];
  const applyEvidenceHint = (hint) => {
    const current = String(form.evidence_summary || "").trim();
    if (current.toLowerCase().includes(hint.toLowerCase())) return;
    setField("evidence_summary", current ? `${current}, ${hint}` : hint);
  };

  const answerInterviewStep = () => {
    if (!activeInterviewStep || !assistantDraft.trim()) return;
    const value = assistantDraft.trim();
    if (form.category === "Salud" && activeInterviewStep.id === "target_entity") {
      setForm((current) => ({ ...current, target_entity: value, eps_name: current.eps_name || value }));
    } else if (form.category === "Salud" && activeInterviewStep.id === "prior_claim_result") {
      setForm((current) => ({
        ...current,
        prior_claim_result: value,
        eps_response_detail: current.eps_response_detail || value,
        prior_claim: current.prior_claim === "no" ? "si" : current.prior_claim,
      }));
    } else if (form.category === "Salud" && activeInterviewStep.id === "evidence_summary") {
      setForm((current) => ({
        ...current,
        evidence_summary: value,
        supporting_documents: current.supporting_documents || value,
      }));
    } else {
      setField(activeInterviewStep.id, value);
    }
    setAssistantDraft("");
  };

  if (isHealthAgentLed) {
    return (
      <div style={{ display: "grid", gap: 16 }}>
        <div className="glass-card" style={{ padding: 18, background: "#FCFDFF" }}>
          <div style={{ fontSize: 12, fontWeight: 800, letterSpacing: 0.4, color: C.textMuted }}>ENTREVISTA GUIADA POR IA</div>
          <div style={{ marginTop: 10, color: C.text, fontWeight: 700 }}>
            El agente juridico dirige el interrogatorio del caso. Ya no tienes que llenar todo el formulario manualmente.
          </div>
          {!!missingFields.length && (
            <div style={{ marginTop: 12, display: "flex", gap: 8, flexWrap: "wrap" }}>
              {missingFields.map((item) => <Badge key={item} color={C.warning}>Falta: {item}</Badge>)}
            </div>
          )}
          <div style={{ marginTop: 12, color: C.textMuted, fontSize: 13, lineHeight: 1.7 }}>
            Ayuda de redaccion: {writingAid}
          </div>
          <div style={{ marginTop: 12, display: "flex", gap: 8, flexWrap: "wrap" }}>
            <Badge color={C.primary}>Continuidad del tratamiento</Badge>
            <Badge color={C.primary}>Menor de edad</Badge>
            <Badge color={C.primary}>Embarazo de riesgo</Badge>
            <Badge color={C.primary}>Discapacidad</Badge>
            <Badge color={C.primary}>Dolor o empeoramiento actual</Badge>
          </div>
        </div>

        <div className="glass-card" style={{ padding: 18, background: "#EEF4FF", border: "1px solid #BFDBFE", display: "grid", gap: 12 }}>
          <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
            <div style={{ fontSize: 12, fontWeight: 800, letterSpacing: 0.4, color: C.primary }}>AGENTE DEL CASO</div>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              {!!interviewSteps.length && <Badge color={C.primary}>Pregunta 1 de {interviewSteps.length}</Badge>}
              {isCorrectionStep && <Badge color={C.warning}>Corrigiendo inconsistencia</Badge>}
            </div>
          </div>
          <div style={{ color: C.text, fontWeight: 700, lineHeight: 1.6 }}>
            {activeInterviewStep
              ? activeInterviewStep.question
              : "El agente ya tiene lo minimo para continuar. Si quieres, puedes ampliar el relato general antes de generar el analisis."}
          </div>
          {activeInterviewStep ? (
            activeInterviewStep.multiline ? (
              <TextArea
                value={assistantDraft}
                onChange={(event) => setAssistantDraft(event.target.value)}
                placeholder={activeInterviewStep.placeholder}
                style={{ minHeight: 96 }}
              />
            ) : (
              <TextInput
                value={assistantDraft}
                onChange={(event) => setAssistantDraft(event.target.value)}
                placeholder={activeInterviewStep.placeholder}
              />
            )
          ) : (
            <TextArea
              value={form.description}
              onChange={(event) => setField("description", event.target.value)}
              placeholder="Si quieres, agrega aqui mas contexto clinico, fechas o hechos que ayuden al agente."
              style={{ minHeight: 96 }}
            />
          )}
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
            {activeInterviewStep ? (
              <Button variant="secondary" onClick={answerInterviewStep} disabled={!assistantDraft.trim()}>
                Guardar respuesta y seguir
              </Button>
            ) : (
              <Badge color={C.success}>El agente ya consolido lo minimo para seguir</Badge>
            )}
            <div style={{ color: C.textMuted, fontSize: 13 }}>
              El agente pregunta primero lo mas importante para que el analisis y el documento salgan mejor.
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: "grid", gap: 16 }}>
      <div className="glass-card" style={{ padding: 18, background: "#FCFDFF" }}>
        <div style={{ fontSize: 12, fontWeight: 800, letterSpacing: 0.4, color: C.textMuted }}>INTAKE GUIADO</div>
        <div style={{ marginTop: 10, color: C.text, fontWeight: 700 }}>
          La IA trabaja mejor si le entregas entidad, fechas, solicitud concreta y afectacion actual. No dependas solo de una caja de texto.
        </div>
        {!!missingFields.length && (
          <div style={{ marginTop: 12, display: "flex", gap: 8, flexWrap: "wrap" }}>
            {missingFields.map((item) => <Badge key={item} color={C.warning}>Falta: {item}</Badge>)}
          </div>
        )}
        <div style={{ marginTop: 12, color: C.textMuted, fontSize: 13, lineHeight: 1.7 }}>
          Ayuda de redaccion: {writingAid}
        </div>
      </div>

      {!!activeInterviewStep && (
        <div className="glass-card" style={{ padding: 18, background: "#EEF4FF", border: "1px solid #BFDBFE", display: "grid", gap: 12 }}>
          <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
            <div style={{ fontSize: 12, fontWeight: 800, letterSpacing: 0.4, color: C.primary }}>ASISTENTE DEL CASO</div>
            {assistantProgress && <Badge color={C.primary}>Pregunta {assistantProgress}</Badge>}
          </div>
          <div style={{ color: C.text, fontWeight: 700, lineHeight: 1.6 }}>
            {activeInterviewStep.question}
          </div>
          {activeInterviewStep.multiline ? (
            <TextArea
              value={assistantDraft}
              onChange={(event) => setAssistantDraft(event.target.value)}
              placeholder={activeInterviewStep.placeholder}
              style={{ minHeight: 96 }}
            />
          ) : (
            <TextInput
              value={assistantDraft}
              onChange={(event) => setAssistantDraft(event.target.value)}
              placeholder={activeInterviewStep.placeholder}
            />
          )}
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
            <Button variant="secondary" onClick={answerInterviewStep} disabled={!assistantDraft.trim()}>
              Guardar respuesta y seguir
            </Button>
            <div style={{ color: C.textMuted, fontSize: 13 }}>
              El asistente pregunta primero lo más importante para que el análisis y el documento salgan mejor.
            </div>
          </div>
        </div>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 16 }}>
        <Field label="Entidad o destinatario">
          <div style={{ position: "relative" }}>
            <TextInput value={form.target_entity} onChange={(event) => setField("target_entity", event.target.value)} placeholder="Ej: Nueva EPS, Datacredito, Alcaldia, Banco X" />
            {entityLookupLoading && <div style={{ marginTop: 8, fontSize: 12, color: C.textMuted }}>Buscando entidades...</div>}
            {!entityLookupLoading && !!entitySuggestions.length && (
              <div style={{ position: "absolute", top: "calc(100% + 8px)", left: 0, right: 0, zIndex: 20, background: "#fff", border: `1px solid ${C.border}`, borderRadius: 16, boxShadow: "0 18px 40px rgba(15, 23, 42, 0.12)", overflow: "hidden" }}>
                {entitySuggestions.map((entity, index) => (
                  <button
                    key={`${entity.name}-${entity.nit || entity.source || index}`}
                    type="button"
                    onMouseDown={(event) => {
                      event.preventDefault();
                      onApplyEntitySuggestion(entity);
                    }}
                    onClick={() => onApplyEntitySuggestion(entity)}
                    style={{ width: "100%", textAlign: "left", border: "none", background: "#fff", padding: "14px 16px", display: "grid", gap: 4, cursor: "pointer", borderBottom: index === entitySuggestions.length - 1 ? "none" : `1px solid ${C.border}` }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "center" }}>
                      <strong style={{ color: C.text }}>{entity.name}</strong>
                      <span style={{ fontSize: 12, color: C.textMuted }}>{entity.type || entity.source || "entidad"}</span>
                    </div>
                    <div style={{ fontSize: 12, color: C.textMuted }}>
                      {[entity.nit ? `NIT ${entity.nit}` : "", entity.superintendence || "", entity.pqrs_emails?.[0] || ""].filter(Boolean).join(" · ")}
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        </Field>
        <Field label="Fecha o periodo aproximado">
          <TextInput value={form.event_date} onChange={(event) => setField("event_date", event.target.value)} placeholder="Ej: 12 de marzo de 2026 / desde enero de 2026" />
        </Field>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 16 }}>
        <Field label="Detalle de la cronologia">
          <TextInput value={form.event_period_detail} onChange={(event) => setField("event_period_detail", event.target.value)} placeholder="Ej: me respondieron 8 dias despues / el corte fue ayer / llevo 3 meses esperando" />
        </Field>
        <Field label="Estado de respuesta previa">
          <select
            value={form.prior_response_status}
            onChange={(event) => setField("prior_response_status", event.target.value)}
            style={{ width: "100%", padding: "14px 16px", borderRadius: 12, border: `1px solid ${C.border}`, background: "#fff", color: C.text }}
          >
            <option value="sin_respuesta">Sin respuesta</option>
            <option value="respuesta_parcial">Respuesta parcial</option>
            <option value="respuesta_negativa">Respuesta negativa</option>
            <option value="respuesta_favorable_incumplida">Respuesta favorable incumplida</option>
            <option value="sin_gestion_previa">Aun no hice gestion previa</option>
          </select>
        </Field>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 16 }}>
        <Field label="Que solucion concreta necesitas">
          <TextInput value={form.concrete_request} onChange={(event) => setField("concrete_request", event.target.value)} placeholder="Ej: entrega de medicamento, devolucion del dinero o correccion del reporte" />
        </Field>
        <Field label="Canal para recibir respuesta">
          <TextInput value={form.response_channel} onChange={(event) => setField("response_channel", event.target.value)} placeholder="Ej: correo electronico, direccion fisica o ambos" />
        </Field>
      </div>

      {isPetitionTrack && (
        <div className="glass-card" style={{ padding: 18, background: "#F8FAFD" }}>
          <div style={{ fontSize: 12, fontWeight: 800, letterSpacing: 0.4, color: C.textMuted }}>PREGUNTAS DINAMICAS PARA DERECHO DE PETICION</div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 16, marginTop: 14 }}>
            <Field label="Tipo de peticion">
              <select
                value={form.request_type}
                onChange={(event) => setField("request_type", event.target.value)}
                style={{ width: "100%", padding: "14px 16px", borderRadius: 12, border: `1px solid ${C.border}`, background: "#fff", color: C.text }}
              >
                <option value="interes_particular">Interes particular</option>
                <option value="informacion">Informacion</option>
                <option value="documentos">Documentos</option>
                <option value="consulta">Consulta</option>
                <option value="interes_general">Interes general</option>
              </select>
            </Field>
            <Field label="2 o 3 soluciones concretas que necesitas">
              <TextInput value={form.numbered_requests} onChange={(event) => setField("numbered_requests", event.target.value)} placeholder="Ej: entregar copia del contrato, corregir el cobro y certificar el estado del caso" />
            </Field>
          </div>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 12 }}>
            {quickRequestTypes.map((option) => (
              <button
                key={option}
                type="button"
                onClick={() => setField("request_type", option.toLowerCase().replaceAll(" ", "_"))}
                style={{ border: `1px solid ${C.border}`, background: "#fff", color: C.text, borderRadius: 999, padding: "8px 12px", cursor: "pointer", fontWeight: 700 }}
              >
                {option}
              </button>
            ))}
          </div>
          <div style={{ marginTop: 12, color: C.textMuted, fontSize: 13, lineHeight: 1.7 }}>
            Usa esta ruta cuando necesitas una respuesta formal de fondo, entrega de informacion, documentos o correccion de una actuacion de la entidad.
          </div>
        </div>
      )}

      <Field label="Afectacion actual o riesgo concreto">
        <TextArea value={form.current_harm} onChange={(event) => setField("current_harm", event.target.value)} placeholder="Explica por que esto te afecta hoy: salud, minimo vital, reporte negativo, corte de servicio, falta de respuesta, etc." style={{ minHeight: 110 }} />
      </Field>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 16 }}>
        <Field label="Respuesta previa o antecedente">
          <TextArea value={form.previous_response} onChange={(event) => setField("previous_response", event.target.value)} placeholder="Que te respondio la entidad, o si guardo silencio." style={{ minHeight: 100 }} />
        </Field>
        <Field label="Numero o referencia relacionada">
          <TextInput value={form.case_reference} onChange={(event) => setField("case_reference", event.target.value)} placeholder="Ej: numero de radicado, afiliacion, contrato o caso" />
        </Field>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 16 }}>
        <Field label="Acto, decision o barrera relevante">
          <TextInput value={form.authority_act_type} onChange={(event) => setField("authority_act_type", event.target.value)} placeholder="Ej: negativa del servicio, cobro indebido, reporte negativo, despido, respuesta evasiva" />
        </Field>
        <Field label="Fecha del acto o decision">
          <TextInput value={form.authority_act_date} onChange={(event) => setField("authority_act_date", event.target.value)} placeholder="Ej: 10 de marzo de 2026" />
        </Field>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 16 }}>
        <Field label="Pruebas o soportes disponibles">
          <TextArea value={form.evidence_summary} onChange={(event) => setField("evidence_summary", event.target.value)} placeholder="Ej: orden medica, historia clinica, factura, correo de respuesta, captura del reporte, contrato, desprendible" style={{ minHeight: 100 }} />
        </Field>
        <Field label="Documentos o anexos que deberian mencionarse">
          <TextArea value={form.supporting_documents} onChange={(event) => setField("supporting_documents", event.target.value)} placeholder="Ej: cedula, tutela previa, radicado, formula, capturas, certificado laboral" style={{ minHeight: 100 }} />
        </Field>
      </div>

      <div className="glass-card" style={{ padding: 18, background: "#F8FAFD", display: "grid", gap: 10 }}>
        <div style={{ fontSize: 12, fontWeight: 800, letterSpacing: 0.4, color: C.textMuted }}>PRUEBAS QUE PUEDES SUBIR</div>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          {evidenceHints.map((hint) => (
            <button
              key={hint}
              type="button"
              onClick={() => applyEvidenceHint(hint)}
              style={{ border: `1px solid ${C.border}`, background: "#fff", color: C.text, borderRadius: 999, padding: "8px 12px", cursor: "pointer", fontWeight: 700 }}
            >
              + {hint}
            </button>
          ))}
        </div>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          {quickChannels.map((option) => (
            <button
              key={option}
              type="button"
              onClick={() => setField("response_channel", option)}
              style={{ border: `1px solid ${C.border}`, background: "#fff", color: C.text, borderRadius: 999, padding: "8px 12px", cursor: "pointer", fontWeight: 700 }}
            >
              {option}
            </button>
          ))}
        </div>
      </div>

      {form.category === "Laboral" && (
        <div className="glass-card" style={{ padding: 18, background: "#FFF7ED" }}>
          <div style={{ fontSize: 12, fontWeight: 800, letterSpacing: 0.4, color: C.textMuted }}>PREGUNTAS DINAMICAS PARA LABORAL</div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 16, marginTop: 14 }}>
            <Field label="Empleador o contratante">
              <TextInput value={form.labor_employer_name} onChange={(event) => setField("labor_employer_name", event.target.value)} placeholder="Ej: Empresa X SAS / Alcaldia / Persona natural" />
            </Field>
            <Field label="Tipo de relacion laboral">
              <TextInput value={form.labor_relation_type} onChange={(event) => setField("labor_relation_type", event.target.value)} placeholder="Ej: contrato laboral, prestacion de servicios, relacion de hecho" />
            </Field>
            <Field label="Fecha de la medida o despido">
              <TextInput value={form.labor_measure_date} onChange={(event) => setField("labor_measure_date", event.target.value)} placeholder="Ej: 5 de marzo de 2026" />
            </Field>
            <Field label="Despido, sancion o medida cuestionada">
              <TextInput value={form.dismissal_or_measure} onChange={(event) => setField("dismissal_or_measure", event.target.value)} placeholder="Ej: despido sin justa causa, suspension, no pago de salarios" />
            </Field>
            <Field label="Salario, honorarios o pagos pendientes">
              <TextInput value={form.labor_salary_detail} onChange={(event) => setField("labor_salary_detail", event.target.value)} placeholder="Ej: salario de 1.600.000, dos quincenas pendientes, honorarios de febrero" />
            </Field>
            <Field label="Impacto en minimo vital">
              <TextInput value={form.minimum_vital_impact} onChange={(event) => setField("minimum_vital_impact", event.target.value)} placeholder="Ej: no puedo pagar arriendo, alimentacion o medicamentos" />
            </Field>
            <Field label="Estabilidad reforzada o condicion especial">
              <TextInput value={form.reinforced_stability} onChange={(event) => setField("reinforced_stability", event.target.value)} placeholder="Ej: embarazo, discapacidad, enfermedad, fuero sindical" />
            </Field>
          </div>
        </div>
      )}

      {form.category === "Bancos" && (
        <div className="glass-card" style={{ padding: 18, background: "#F5F3FF" }}>
          <div style={{ fontSize: 12, fontWeight: 800, letterSpacing: 0.4, color: C.textMuted }}>PREGUNTAS DINAMICAS PARA BANCOS</div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 16, marginTop: 14 }}>
            <Field label="Producto financiero involucrado">
              <TextInput value={form.bank_product_type} onChange={(event) => setField("bank_product_type", event.target.value)} placeholder="Ej: tarjeta de credito, credito, cuenta de ahorros, Nequi" />
            </Field>
            <Field label="Monto o valor discutido">
              <TextInput value={form.bank_amount_involved} onChange={(event) => setField("bank_amount_involved", event.target.value)} placeholder="Ej: 450000 COP, cuota de marzo, cargo no reconocido" />
            </Field>
            <Field label="Cobro, mora o valor discutido">
              <TextInput value={form.disputed_charge} onChange={(event) => setField("disputed_charge", event.target.value)} placeholder="Ej: cobro de 450.000, mora reportada, cuota no reconocida" />
            </Field>
            <Field label="Reporte, bloqueo o causa principal">
              <TextInput value={form.report_or_block_reason} onChange={(event) => setField("report_or_block_reason", event.target.value)} placeholder="Ej: bloqueo injustificado, reporte negativo, debito no autorizado" />
            </Field>
            <Field label="Fecha del cargo, bloqueo o reporte">
              <TextInput value={form.bank_event_date} onChange={(event) => setField("bank_event_date", event.target.value)} placeholder="Ej: 11 de marzo de 2026" />
            </Field>
            <Field label="Que esperas que haga el banco">
              <TextInput value={form.bank_claim_goal} onChange={(event) => setField("bank_claim_goal", event.target.value)} placeholder="Ej: reversar el cobro, desbloquear cuenta, corregir reporte" />
            </Field>
          </div>
        </div>
      )}

      {form.category === "Servicios" && (
        <div className="glass-card" style={{ padding: 18, background: "#ECFEFF" }}>
          <div style={{ fontSize: 12, fontWeight: 800, letterSpacing: 0.4, color: C.textMuted }}>PREGUNTAS DINAMICAS PARA SERVICIOS PUBLICOS</div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 16, marginTop: 14 }}>
            <Field label="Empresa de servicios">
              <TextInput value={form.service_company_name} onChange={(event) => setField("service_company_name", event.target.value)} placeholder="Ej: Enel, Acueducto, Vanti, Claro" />
            </Field>
            <Field label="Tipo de servicio afectado">
              <TextInput value={form.service_type} onChange={(event) => setField("service_type", event.target.value)} placeholder="Ej: energia, agua, gas, internet, telefonia" />
            </Field>
            <Field label="Numero de suscriptor o referencia">
              <TextInput value={form.subscriber_reference} onChange={(event) => setField("subscriber_reference", event.target.value)} placeholder="Ej: NIC, contrato, cuenta o suscriptor" />
            </Field>
            <Field label="Impacto del servicio o corte">
              <TextInput value={form.service_impact} onChange={(event) => setField("service_impact", event.target.value)} placeholder="Ej: corte total, suspension parcial, afectacion a salud o trabajo" />
            </Field>
            <Field label="Detalle de corte o facturacion discutida">
              <TextInput value={form.cutoff_or_billing_detail} onChange={(event) => setField("cutoff_or_billing_detail", event.target.value)} placeholder="Ej: factura excesiva, reconexion negada, corte sin aviso" />
            </Field>
            <Field label="Factura o periodo discutido">
              <TextInput value={form.invoice_period} onChange={(event) => setField("invoice_period", event.target.value)} placeholder="Ej: factura de febrero 2026 / consumo de enero" />
            </Field>
          </div>
        </div>
      )}

      {form.category === "Consumidor" && (
        <div className="glass-card" style={{ padding: 18, background: "#F0FDF4" }}>
          <div style={{ fontSize: 12, fontWeight: 800, letterSpacing: 0.4, color: C.textMuted }}>PREGUNTAS DINAMICAS PARA CONSUMIDOR</div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 16, marginTop: 14 }}>
            <Field label="Proveedor o comercio">
              <TextInput value={form.provider_name} onChange={(event) => setField("provider_name", event.target.value)} placeholder="Ej: exito.com, tienda X, aerolinea, aseguradora" />
            </Field>
            <Field label="Fecha de compra o contratacion">
              <TextInput value={form.purchase_date} onChange={(event) => setField("purchase_date", event.target.value)} placeholder="Ej: 2 de marzo de 2026" />
            </Field>
            <Field label="Pedido, factura o referencia">
              <TextInput value={form.order_reference} onChange={(event) => setField("order_reference", event.target.value)} placeholder="Ej: pedido 12345, factura FV-88, tiquete ABC" />
            </Field>
            <Field label="Falla del producto o servicio">
              <TextInput value={form.product_or_service_issue} onChange={(event) => setField("product_or_service_issue", event.target.value)} placeholder="Ej: producto defectuoso, incumplimiento, publicidad engañosa" />
            </Field>
            <Field label="Garantia, cambio o devolucion solicitada">
              <TextInput value={form.guarantee_or_refund_request} onChange={(event) => setField("guarantee_or_refund_request", event.target.value)} placeholder="Ej: devolucion total, cambio del producto, cumplimiento de garantia" />
            </Field>
            <Field label="Que respondio el proveedor">
              <TextInput value={form.seller_response_detail} onChange={(event) => setField("seller_response_detail", event.target.value)} placeholder="Ej: negaron la garantia, ofrecieron bono, no respondieron" />
            </Field>
          </div>
        </div>
      )}

      {form.category === "Salud" && (
        <div className="glass-card" style={{ padding: 18, background: "#F5FAFF" }}>
          <div style={{ fontSize: 12, fontWeight: 800, letterSpacing: 0.4, color: C.textMuted }}>PREGUNTAS DINAMICAS PARA SALUD / EPS</div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 16, marginTop: 14 }}>
            <Field label="Quien presenta el caso">
              <select
                value={form.acting_capacity}
                onChange={(event) => setField("acting_capacity", event.target.value)}
                style={{ width: "100%", padding: "14px 16px", borderRadius: 12, border: `1px solid ${C.border}`, background: "#fff", color: C.text }}
              >
                <option value="nombre_propio">El mismo paciente</option>
                <option value="madre_padre_menor">Madre o padre de menor</option>
                <option value="acudiente">Acudiente o cuidador</option>
                <option value="agente_oficioso">Agente oficioso</option>
                <option value="representante_legal">Representante legal</option>
              </select>
            </Field>
            <Field label="EPS">
              <TextInput value={form.eps_name} onChange={(event) => setField("eps_name", event.target.value)} placeholder="Ej: Nueva EPS" />
            </Field>
            <Field label="IPS o clinica">
              <TextInput value={form.ips_name} onChange={(event) => setField("ips_name", event.target.value)} placeholder="Ej: Clinica San Rafael" />
            </Field>
            {form.acting_capacity !== "nombre_propio" && (
              <>
                <Field label="Nombre del menor o paciente representado">
                  <TextInput value={form.represented_person_name} onChange={(event) => setField("represented_person_name", event.target.value)} placeholder="Ej: Jeronimo Perez Lopez" />
                </Field>
                <Field label="Documento del menor o paciente">
                  <TextInput value={form.represented_person_document} onChange={(event) => setField("represented_person_document", event.target.value)} placeholder="Ej: Registro civil, TI o NUIP" />
                </Field>
                <Field label="Edad o fecha de nacimiento">
                  <TextInput value={form.represented_person_age} onChange={(event) => setField("represented_person_age", event.target.value)} placeholder="Ej: 7 años / 12 de abril de 2018" />
                </Field>
                <Field label="Condicion relevante del paciente">
                  <TextInput value={form.represented_person_condition} onChange={(event) => setField("represented_person_condition", event.target.value)} placeholder="Ej: menor con anemia falciforme" />
                </Field>
              </>
            )}
        <Field label="Diagnostico o condicion medica">
          <TextInput value={form.diagnosis} onChange={(event) => setField("diagnosis", event.target.value)} placeholder="Ej: cancer, embarazo de alto riesgo, depresion severa" />
        </Field>
        <Field label="Tratamiento, orden o servicio requerido">
          <TextInput value={form.treatment_needed} onChange={(event) => setField("treatment_needed", event.target.value)} placeholder="Ej: medicamento X, cita con especialista, procedimiento Y" />
        </Field>
        <Field label="Fecha de la orden medica o consulta">
          <TextInput value={form.medical_order_date} onChange={(event) => setField("medical_order_date", event.target.value)} placeholder="Ej: 12 de marzo de 2026" />
        </Field>
        <Field label="Medico tratante">
          <TextInput value={form.treating_doctor_name} onChange={(event) => setField("treating_doctor_name", event.target.value)} placeholder="Ej: Dra. Ana Gomez" />
        </Field>
        <Field label="IPS o clinica tratante">
          <TextInput value={form.treating_ips_name} onChange={(event) => setField("treating_ips_name", event.target.value)} placeholder="Ej: Clinica Medellin" />
        </Field>
        <Field label="Fecha de solicitud a la EPS">
          <TextInput value={form.eps_request_date} onChange={(event) => setField("eps_request_date", event.target.value)} placeholder="Ej: 14 de marzo de 2026" />
        </Field>
        <Field label="Canal usado ante la EPS">
          <TextInput value={form.eps_request_channel} onChange={(event) => setField("eps_request_channel", event.target.value)} placeholder="Ej: portal web, call center, oficina, IPS" />
        </Field>
        <Field label="Radicado o referencia de la EPS">
          <TextInput value={form.eps_request_reference} onChange={(event) => setField("eps_request_reference", event.target.value)} placeholder="Ej: AUT-23991 o no lo entregaron" />
        </Field>
          </div>
          <Field label="Que sigue pasando hoy al paciente">
            <TextArea value={form.urgency_detail} onChange={(event) => setField("urgency_detail", event.target.value)} placeholder="Describe si sigue sin medicamento, sin examen, con dolor, empeorando o sin poder iniciar el tratamiento." style={{ minHeight: 100, marginTop: 16 }} />
          </Field>
          <Field label="Respuesta o barrera concreta de la EPS">
            <TextArea value={form.eps_response_detail} onChange={(event) => setField("eps_response_detail", event.target.value)} placeholder="Ej: negaron la autorizacion, no respondieron, dejaron el caso en tramite o no dieron agenda." style={{ minHeight: 100, marginTop: 16 }} />
          </Field>
        </div>
      )}

      {form.category === "Datos" && (
        <div className="glass-card" style={{ padding: 18, background: "#F8FAFD" }}>
          <div style={{ fontSize: 12, fontWeight: 800, letterSpacing: 0.4, color: C.textMuted }}>PREGUNTAS DINAMICAS PARA HABEAS DATA</div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 16, marginTop: 14 }}>
            <Field label="Dato o reporte cuestionado">
              <TextInput value={form.disputed_data} onChange={(event) => setField("disputed_data", event.target.value)} placeholder="Ej: reporte negativo por obligacion ya pagada" />
            </Field>
        <Field label="Como debe quedar corregido el dato">
              <select
                value={form.requested_data_action}
                onChange={(event) => setField("requested_data_action", event.target.value)}
                style={{ width: "100%", padding: "14px 16px", borderRadius: 12, border: `1px solid ${C.border}`, background: "#fff", color: C.text }}
              >
                <option value="corregir">Corregir</option>
                <option value="actualizar">Actualizar</option>
                <option value="suprimir">Suprimir</option>
                <option value="probar_autorizacion">Probar autorizacion</option>
              </select>
            </Field>
          </div>
        </div>
      )}
    </div>
  );
}

function PaymentCard({ title, caseItem, catalog, onCreateWompiSession, onGetPayment, onReconcilePayment, onRefreshCase, loading }) {
  const [includeFiling, setIncludeFiling] = useState(true);
  const [paymentMessage, setPaymentMessage] = useState("");
  const [selectedCode, setSelectedCode] = useState("");
  const [consentAccepted, setConsentAccepted] = useState(false);
  const [latestReference, setLatestReference] = useState("");

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
  const paymentEntitlements = caseItem?.submission_summary?.payment_entitlements || {};
  const isBasePaid = caseItem?.payment_status === "pagado";
  const bundlePaid = !!paymentEntitlements.filing_bundle_paid || (!!paymentEntitlements.filing_auto_paid && !!paymentEntitlements.follow_up_paid);
  const paymentOffer = useMemo(
    () => buildPaymentOfferCopy(caseItem?.recommended_action, caseItem?.category),
    [caseItem?.recommended_action, caseItem?.category]
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

  const pollPayment = async (reference, transactionId) => {
    for (let attempt = 0; attempt < 8; attempt += 1) {
      if (transactionId && onReconcilePayment) {
        try {
          const reconciled = await onReconcilePayment({ transaction_id: transactionId, reference });
          if (reconciled?.status === "approved") {
            await onRefreshCase(caseItem.id);
            setPaymentMessage("Pago aprobado. Ya puedes continuar.");
            return;
          }
        } catch {
          // si la reconciliacion no aplica todavia, seguimos con el polling local
        }
      }
      const order = await onGetPayment(reference);
      if (order.status === "approved") {
        await onRefreshCase(caseItem.id);
        setPaymentMessage("Pago aprobado. Ya puedes continuar.");
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
    setPaymentMessage("El pago quedo en validacion. Refresca en unos segundos para ver el estado final.");
  };

  const startPayment = async () => {
    if (!selectedProduct) {
      setPaymentMessage("No hay producto seleccionado para cobrar.");
      return;
    }
    if (!consentAccepted) {
      setPaymentMessage("Debes aceptar los terminos, privacidad y condiciones del pago antes de continuar.");
      return;
    }
    setPaymentMessage("");
    const session = await onCreateWompiSession(
      caseItem.id,
      isBasePaid
        ? { add_on_type: "filing_bundle" }
        : {
          product_code: selectedProduct.code,
          include_filing: includeFiling,
        }
    );
    setLatestReference(session.order.reference);
    const widgetResult = await launchWidget(session.checkout);
    const transactionId = widgetResult?.transaction?.id || widgetResult?.id || widgetResult?.transactionId || widgetResult?.transaction_id || "";
    setPaymentMessage("Pago iniciado. Esperando confirmacion segura de Wompi.");
    await pollPayment(session.order.reference, transactionId);
  };

  if (!caseItem) {
    return null;
  }

  const finalPrice = isBasePaid ? 9900 : includeFiling ? selectedProduct?.price_with_filing_cop : selectedProduct?.price_cop;
  const filingPrice = selectedProduct ? selectedProduct.price_with_filing_cop - selectedProduct.price_cop : 0;

  return (
    <SessionCard title={title} subtitle={isBasePaid ? "Tu documento ya esta activo. Aqui agregas un solo paquete adicional." : "El analisis es gratis. Te llevamos a una compra principal simple."}>
      <div style={{ display: "grid", gap: 14 }}>
        <div style={{ padding: 16, borderRadius: 16, background: "linear-gradient(135deg, #EEF4FF 0%, #F8FBFF 100%)", border: "1px solid #BFDBFE" }}>
          <div style={{ fontWeight: 800, color: C.text }}>{isBasePaid ? "Activa radicacion y seguimiento" : paymentOffer.headline}</div>
          <div style={{ color: C.textMuted, marginTop: 8 }}>
            {isBasePaid
              ? "El documento ya quedo pagado. Si quieres que 123tutela radique por ti y te acompañe con el seguimiento inicial, activas un solo paquete."
              : paymentOffer.body}
          </div>
        </div>

        {isBasePaid ? (
          <div className="glass-card" style={{ padding: 18, display: "grid", gap: 14 }}>
            <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "center" }}>
              <strong style={{ color: C.text }}>Paquete de radicacion y seguimiento</strong>
              <Badge color={bundlePaid ? C.success : C.primary}>
                {bundlePaid ? "Activado" : (finalPrice || 0).toLocaleString("es-CO", { style: "currency", currency: "COP", maximumFractionDigits: 0 })}
              </Badge>
            </div>
            <div style={{ color: C.textMuted }}>
              Incluye la radicacion por 123tutela cuando el canal lo permita, comprobante en panel y seguimiento inicial del expediente.
            </div>
            <div style={{ display: "grid", gap: 8 }}>
              {[
                "Radicacion por 123tutela cuando el canal este disponible.",
                "Comprobante o radicado visible en el panel cuando exista.",
                "Seguimiento inicial para revisar respuesta, admision o requerimientos.",
              ].map((item) => (
                <div key={item} style={{ display: "flex", gap: 12, padding: 12, borderRadius: 12, background: "#F8FAFD", border: `1px solid ${C.border}`, color: C.text }}>
                  <span>{item}</span>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <>
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
                  Incluye analisis gratis, estrategia y documento completo despues del pago.
                </div>
                <label style={{ display: "flex", gap: 10, alignItems: "center", marginTop: 16, color: C.text }}>
                  <input type="checkbox" checked={includeFiling} onChange={(event) => setIncludeFiling(event.target.checked)} />
                  Agregar radicacion y seguimiento
                  <strong>+{filingPrice.toLocaleString("es-CO")} COP</strong>
                </label>
                <div style={{ color: C.textMuted, fontSize: 13, marginTop: 10 }}>
                  Si activas el paquete, 123tutela intenta gestionar la radicacion, te comparte el comprobante cuando exista y deja seguimiento inicial en tu panel.
                </div>
                <div style={{ marginTop: 16, padding: 14, borderRadius: 14, background: "#F8FAFD", border: `1px solid ${C.border}` }}>
                  <div style={{ fontSize: 12, color: C.textMuted, fontWeight: 800 }}>LO QUE RECIBES</div>
                  <div style={{ display: "grid", gap: 8, marginTop: 10, color: C.text }}>
                    {paymentOffer.unlocks.map((line, index) => (
                      <div key={`${selectedProduct.code}-unlock-${index}`}>{index + 1}. {line}</div>
                    ))}
                    <div>4. {includeFiling ? "Radicacion y seguimiento inicial por parte de la plataforma cuando el caso lo permita." : "Firma y radicacion disponibles despues de activar el documento."}</div>
                  </div>
                </div>
              </div>
            )}
          </>
        )}

        <div style={{ marginTop: 14, padding: 14, borderRadius: 14, background: "#EEF4FF", border: "1px solid #BFDBFE", color: C.text }}>
          <strong style={{ color: C.primary }}>Pago seguro con Wompi.</strong>
          <div style={{ marginTop: 6, color: C.textMuted, fontSize: 13 }}>
            El cobro se procesa a traves de Wompi. La activacion final del servicio depende de la confirmacion segura del pago por webhook.
          </div>
        </div>
        <label style={{ display: "flex", gap: 10, alignItems: "flex-start", marginTop: 4, color: C.text }}>
          <input type="checkbox" checked={consentAccepted} onChange={(event) => setConsentAccepted(event.target.checked)} />
          <span style={{ fontSize: 14, lineHeight: 1.6 }}>
            Confirmo que entiendo que estoy comprando, acepto los terminos y la politica de privacidad, y autorizo el procesamiento del pago mediante Wompi.
          </span>
        </label>
        <div style={{ color: C.textMuted, fontSize: 13 }}>
          Consulta: <a href="/terminos" style={{ color: C.primary }}>Terminos</a> · <a href="/privacidad" style={{ color: C.primary }}>Privacidad</a> · <a href="/contacto" style={{ color: C.primary }}>Contacto</a>
        </div>
        {latestReference && (
          <div style={{ color: C.textMuted, fontSize: 13, marginTop: 6 }}>
            Referencia del intento: <strong style={{ color: C.text }}>{latestReference}</strong>
          </div>
        )}
        <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
          <Button onClick={startPayment} disabled={loading || (isBasePaid && bundlePaid)} icon={CreditCard}>
            {isBasePaid ? (bundlePaid ? "Paquete ya activado" : "Activar radicacion y seguimiento") : includeFiling ? "Activar documento + radicacion" : "Activar documento"}
          </Button>
        </div>
        {paymentMessage && <div style={{ color: C.textMuted }}>{paymentMessage}</div>}
      </div>
    </SessionCard>
  );
}

function DetailPanel({
  detail,
  postPayForm = {
    full_name: "",
    document_number: "",
    phone: "",
    address: "",
    copy_email: "",
    target_entity: "",
    target_identifier: "",
    target_address: "",
    legal_representative: "",
    target_pqrs_email: "",
    target_notification_email: "",
    target_phone: "",
    target_website: "",
    target_superintendence: "",
    case_story: "",
    concrete_request: "",
    key_dates: "",
    evidence_summary: "",
    diagnosis: "",
    treatment_needed: "",
    urgency_detail: "",
    medical_order_date: "",
    treating_doctor_name: "",
    treating_ips_name: "",
    eps_request_date: "",
    eps_request_channel: "",
    eps_request_reference: "",
    eps_response_detail: "",
    bank_product_type: "",
    bank_amount_involved: "",
    bank_event_date: "",
    disputed_charge: "",
    bank_account_reference: "",
    refund_destination: "",
    tutela_previous_action_detail: "",
    tutela_oath_statement: "",
    tutela_no_temperity_detail: "",
    tutela_other_means_detail: "",
    tutela_immediacy_detail: "",
    tutela_special_protection_detail: "",
    tutela_private_party_ground: "",
    prior_claim: "no",
    prior_claim_date: "",
    prior_claim_result: "",
    special_protection: "No aplica",
    prior_tutela: "no",
    prior_tutela_reason: "",
  },
  setPostPayForm = () => {},
  documentReview,
  entityLookupLoading = false,
  entitySuggestions = [],
  onApplyEntitySuggestion = () => {},
  regenerationReason = "",
  setRegenerationReason = () => {},
  regenerationContext = "",
  setRegenerationContext = () => {},
  actionError = "",
  loading,
  detailStepOverride = null,
  onSetDetailStep = () => {},
  onViewDocument,
  onSaveFlowDraft,
  onGenerateFromFlow,
  onSubmitCase,
  onManualRadicado,
  onReportFollowUp = async () => {},
  onUploadEvidence = async () => {},
}) {
  const [manualContact, setManualContact] = useState("");
  const [submissionNote, setSubmissionNote] = useState("");
  const [radicadoManual, setRadicadoManual] = useState("");
  const [radicadoNote, setRadicadoNote] = useState("");
  const [evidenceNote, setEvidenceNote] = useState("");
  const [followUpNote, setFollowUpNote] = useState("");
  const [interviewDraft, setInterviewDraft] = useState("");
  const [documentReviewed, setDocumentReviewed] = useState(false);
  const [signatureAccepted, setSignatureAccepted] = useState(false);
  const [judicialDestinationConfirmed, setJudicialDestinationConfirmed] = useState(false);
  const [signatureForm, setSignatureForm] = useState({
    full_name: "",
    document_number: "",
    city: "Bogota",
    date: new Date().toLocaleDateString("es-CO"),
    consent_version: SIMPLE_SIGNATURE_CONSENT_VERSION,
  });

  if (!detail) {
    return <div className="glass-card" style={{ padding: 24, color: C.textMuted }}>Abre un expediente para continuar el wizard del caso activo.</div>;
  }

  const { case: item, files } = detail;
  const submissionSummary = item.submission_summary || {};
  const submissionAttempts = detail.submission_attempts || [];
  const timelineEvents = detail.timeline || [];
  const guidance = submissionSummary.guidance || {};
  const paymentEntitlements = submissionSummary.payment_entitlements || {};
  const deliveryResult = submissionSummary.delivery_result || {};
  const review = documentReview || submissionSummary.document_quality || null;
  const effectivePostPayForm = mergeDetectedFormValues(postPayForm, item.facts?.intake_form || item.facts?.autofill_suggestions || {});
  const rights = item.legal_analysis?.derechos_vulnerados || [];
  const rules = item.legal_analysis?.normas_relevantes || [];
  const baseFlowStep = getActiveFlowStep(item);
  const flowStep = detailStepOverride || baseFlowStep;
  const normalizedDetailAction = normalizeAction(item.recommended_action || item.workflow_type || "");
  const isTutelaFlow = normalizedDetailAction === "accion de tutela";
  const missingFields = getPostPayMissingFields(effectivePostPayForm, item);
  const backendPendingQuestions = item.pending_questions || item.facts?.pending_questions || [];
  const healthAgentState = item.facts?.agent_state || {};
  const useBackendHealthAgent = item.payment_status === "pagado" && (item.category || "").toLowerCase() === "salud" && !!healthAgentState?.enabled;
  const autofillSuggestions = item.facts?.autofill_suggestions || {};
  const missingQuestions = (
    useBackendHealthAgent
      ? (
        healthAgentState.can_generate
          ? []
          : [...(healthAgentState.user_owned_missing || []), ...backendPendingQuestions.map((question) => question?.question).filter(Boolean)]
      )
      : [...backendPendingQuestions.map((question) => question?.question).filter(Boolean), ...getPostPayQuestionPrompts(effectivePostPayForm, item)]
  ).filter((value, index, array) => array.indexOf(value) === index);
  const interviewSteps = useBackendHealthAgent
    ? (
      healthAgentState.next_prompt
        ? [healthAgentState.next_prompt]
        : (healthAgentState.optional_prompt ? [healthAgentState.optional_prompt] : [])
    )
    : buildPostPayInterviewSteps(effectivePostPayForm, item);
  const activeInterviewStep = interviewSteps[0] || null;
  const checklist = buildDocumentChecklist(item, review, files);
  const whatsappCopy = effectivePostPayForm.phone || item.user_phone || "";
  const evidenceHints = evidenceTypeHints[item.category] || evidenceTypeHints.default;
  const detailRights = item.legal_analysis?.derechos_vulnerados || [];
  const detailNorms = item.legal_analysis?.normas_relevantes || [];
  const detailDx = item.dx_result || {};
  const finalValidation = item.final_validation || submissionSummary.final_validation || null;
  const actionableGaps = buildActionableGaps(item, backendPendingQuestions);
  const detailViability = getViabilityConfig(detailDx);
  const detailPrimaryTarget = item.routing?.primary_target || {};
  const requiresJudicialConfirmation = detailPrimaryTarget?.type === "juzgado";
  const judicialTerritorialNote = item.routing?.territorial_note || guidance.routing_snapshot?.territorial_note || "";
  const judicialTerritorialMismatch = requiresJudicialConfirmation && item.routing?.territorial_match === false;
  const judicialScopeLabelMap = {
    local: "Destino local",
    department: "Destino departamental",
    national: "Fallback nacional",
    mismatch: "Revisar destino",
  };
  const judicialScopeLabel = judicialScopeLabelMap[item.routing?.target_scope] || "";
  const detailRoutingChannel = getRoutingChannelLabel(item.routing?.channel || detailPrimaryTarget?.channel);
  const detailRoutingContact = detailPrimaryTarget?.contact || effectivePostPayForm.target_pqrs_email || effectivePostPayForm.target_website || effectivePostPayForm.target_phone || "Canal por confirmar";
  const detailRouteSteps = [
    ...((item.prerequisites || []).slice(0, 2).map((step) => shortenRouteLabel(step.label))),
    shortenRouteLabel(item.recommended_action || item.workflow_type, "Documento"),
  ].filter(Boolean).slice(0, 3);
  const revealOperationalRouting = item.payment_status === "pagado" || baseFlowStep >= 3;
  const postPayChatMode = item.payment_status === "pagado";
  const commercialDiagnosisCopy = buildCommercialDiagnosisCopy(item.recommended_action || item.workflow_type, item.category);
  const visibleAutofillEntries = Object.entries(autofillSuggestions).filter(([key]) => (
    revealOperationalRouting || ![
      "target_pqrs_email",
      "target_phone",
      "target_website",
      "target_identifier",
      "target_superintendence",
      "tutela_other_means_detail",
    ].includes(key)
  ));
  const progressSteps = [
    { id: 1, label: "Diagnostico" },
    { id: 2, label: "Completa datos" },
    { id: 3, label: "Documento listo" },
    { id: 4, label: "Radicacion" },
  ];
  const visibleSubmissionAttempts = submissionAttempts.slice(0, 5);
  const visibleTimelineEvents = timelineEvents.filter(isMeaningfulTimelineEvent).slice(0, 4);
  const primarySubmissionAttempt = visibleSubmissionAttempts.find((attempt) => {
    const status = String(attempt?.response_payload?.delivery_result?.status || attempt?.status || "").toLowerCase();
    return ["sent", "success", "delivered"].includes(status) || !!attempt?.radicado;
  }) || visibleSubmissionAttempts[0] || null;
  const deliveryStatusLabel = submissionSummary.radicado
    ? "Radicado registrado"
    : formatDeliveryStatusLabel(deliveryResult.status || submissionSummary.last_channel || "");
  const filingAutoPaid = !!paymentEntitlements.filing_auto_paid;
  const signatureReady =
    documentReviewed &&
    signatureAccepted &&
    (!requiresJudicialConfirmation || judicialDestinationConfirmed) &&
    signatureForm.full_name.trim().length > 3 &&
    signatureForm.document_number.trim().length >= 6 &&
    signatureForm.city.trim().length > 2 &&
    signatureForm.date.trim().length > 4;
  const chatGenerationBlocked = loading || item.payment_status !== "pagado" || (useBackendHealthAgent ? !healthAgentState.can_generate : !!activeInterviewStep);
  const suppressHealthAgentError = useBackendHealthAgent
    && healthAgentState.can_generate
    && /todavia faltan datos minimos|todavía faltan datos mínimos|tutela necesita/i.test(String(actionError || ""));
  const visibleActionError = suppressHealthAgentError ? "" : actionError;
  useEffect(() => {
    setSignatureForm((current) => ({
      ...current,
      full_name: effectivePostPayForm.full_name || item.user_name || current.full_name,
      document_number: effectivePostPayForm.document_number || item.user_document || current.document_number,
      city: effectivePostPayForm.city || item.user_city || current.city,
      date: current.date || new Date().toLocaleDateString("es-CO"),
    }));
  }, [effectivePostPayForm.full_name, effectivePostPayForm.document_number, effectivePostPayForm.city, item.user_name, item.user_document, item.user_city]);

  const uploadEvidence = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    await onUploadEvidence(file, evidenceNote);
    setEvidenceNote("");
  };

  const answerInterviewStep = () => {
    const nextAnswer = interviewDraft.trim();
    if (!nextAnswer) return;
    if (activeInterviewStep) {
      setPostPayForm((current) => {
        if (activeInterviewStep.id === "represented_person_identity") {
          return {
            ...current,
            represented_person_identity: nextAnswer,
            ...parseRepresentedPersonIdentity(nextAnswer),
          };
        }
        return (
          Object.prototype.hasOwnProperty.call(current, activeInterviewStep.id)
            ? { ...current, [activeInterviewStep.id]: nextAnswer }
            : {
                ...current,
                case_story: [current.case_story, nextAnswer].filter(Boolean).join("\n"),
              }
        );
      });
      if (!Object.prototype.hasOwnProperty.call(postPayForm, activeInterviewStep.id)) {
        setRegenerationContext((current) => [current, nextAnswer].filter(Boolean).join("\n\n"));
      }
    } else {
      setRegenerationContext((current) => [current, nextAnswer].filter(Boolean).join("\n\n"));
      setPostPayForm((current) => ({
        ...current,
        case_story: [current.case_story, nextAnswer].filter(Boolean).join("\n"),
      }));
    }
    setInterviewDraft("");
  };

  return (
    <div style={{ display: "grid", gap: 18 }}>
      <div className="glass-card" style={{ padding: 0, overflow: "hidden" }}>
        <div style={{ display: "grid", gridTemplateColumns: "220px 1fr" }}>
          <div style={{ padding: 22, borderRight: `1px solid ${C.border}`, background: "linear-gradient(180deg, #F4F7FB 0%, #EDF3FB 100%)", display: "grid", alignContent: "space-between", minHeight: 720 }}>
            <div style={{ display: "grid", gap: 14 }}>
              <div>
                <div style={{ fontSize: 12, color: C.textMuted, fontWeight: 800 }}>EXPEDIENTE</div>
                <div style={{ marginTop: 6, color: C.text, fontWeight: 800 }}>{item.id.slice(0, 18)}</div>
              </div>
              <div style={{ padding: 18, borderRadius: 20, background: "linear-gradient(180deg, #101827 0%, #182338 100%)", color: "#fff", boxShadow: "0 18px 30px rgba(15,23,42,0.18)" }}>
                <div style={{ fontSize: 12, color: "rgba(255,255,255,0.65)", fontWeight: 700 }}>Estado actual</div>
                <div style={{ marginTop: 8, fontSize: 22, lineHeight: 1.15, fontWeight: 800 }}>
                  {flowStep === 1 ? "Diagnostico listo" : flowStep === 2 ? "Faltan tus datos" : flowStep === 3 ? "Documento listo" : "Radicado"}
                </div>
                <div style={{ marginTop: 12, fontSize: 13, color: "rgba(255,255,255,0.72)", lineHeight: 1.6 }}>
                  {baseFlowStep >= 3
                    ? "Ya puedes revisar el documento y elegir como radicarlo."
                    : item.payment_status === "pagado"
                      ? "El pago ya esta confirmado y solo falta completar el caso."
                      : "Primero validas el diagnostico y luego decides si pagas."}
                </div>
              </div>
              <div style={{ padding: 16, borderRadius: 18, background: "#FFFFFF", border: `1px solid ${C.border}`, display: "grid", gap: 10 }}>
                <div style={{ fontSize: 12, color: C.textMuted, fontWeight: 800 }}>RESUMEN RAPIDO</div>
                <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "center" }}>
                  <span style={{ color: C.textMuted, fontSize: 13 }}>Pago</span>
                  <Badge color={item.payment_status === "pagado" ? C.success : C.warning}>
                    {item.payment_status === "pagado" ? "Confirmado" : "Pendiente"}
                  </Badge>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "center" }}>
                  <span style={{ color: C.textMuted, fontSize: 13 }}>Ruta</span>
                  <span style={{ color: C.text, fontWeight: 700, textAlign: "right" }}>{item.recommended_action || item.workflow_type}</span>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "center" }}>
                  <span style={{ color: C.textMuted, fontSize: 13 }}>Viabilidad</span>
                  <span style={{ color: detailViability.color, fontWeight: 800 }}>{detailViability.label}</span>
                </div>
              </div>
              <div style={{ padding: 16, borderRadius: 18, background: "#FFFFFF", border: `1px solid ${C.border}`, display: "grid", gap: 8 }}>
                <div style={{ fontSize: 12, color: C.textMuted, fontWeight: 800 }}>SIGUIENTE ACCION</div>
                <div style={{ color: C.text, fontWeight: 800, lineHeight: 1.45 }}>
                  {flowStep === 1
                    ? "Revisar el diagnostico y decidir si continúas al pago."
                    : flowStep === 2
                      ? (postPayChatMode ? "Hablar con el agente y subir soportes del caso." : "Completar los datos y soportes del caso.")
                      : flowStep === 3
                        ? "Ver el documento y escoger la radicacion."
                        : "Guardar el comprobante y hacer seguimiento."}
                </div>
              </div>
            </div>
            <div style={{ padding: 14, borderRadius: 18, background: "#0F172A", color: "#fff", boxShadow: "0 12px 24px rgba(15,23,42,0.16)" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                <div style={{ width: 34, height: 34, borderRadius: 10, background: C.primary, display: "grid", placeItems: "center", fontWeight: 800 }}>
                  {(item.user_name || "U").slice(0, 2).toUpperCase()}
                </div>
                <div>
                  <div style={{ fontWeight: 800 }}>{item.user_name}</div>
                  <div style={{ fontSize: 12, color: "rgba(255,255,255,0.6)" }}>{item.user_phone || "Sin telefono"}</div>
                </div>
              </div>
            </div>
          </div>

          <div style={{ padding: 28, display: "grid", gap: 22 }}>
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "start", flexWrap: "wrap" }}>
                <div>
                  <div style={{ color: C.textMuted, fontSize: 13, fontWeight: 700 }}>{item.recommended_action || item.workflow_type}</div>
                  <h2 style={{ marginTop: 6, fontSize: 38, lineHeight: 1.05, color: C.text, fontFamily: "'Playfair Display', serif" }}>{item.category}</h2>
                </div>
                <Badge color={baseFlowStep >= 3 ? C.success : item.payment_status === "pagado" ? C.primary : C.warning}>
                  {flowStep === 2 && baseFlowStep >= 3 ? "Editando datos" : baseFlowStep >= 3 ? "Documento listo" : item.payment_status === "pagado" ? "Pago confirmado" : "Pago pendiente"}
                </Badge>
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 10, marginTop: 18 }}>
                {progressSteps.map((step) => {
                  const active = step.id === flowStep;
                  const completed = step.id < flowStep;
                  return (
                    <div key={step.id} style={{ display: "grid", gap: 8 }}>
                      <div style={{ height: 6, borderRadius: 999, background: completed || active ? (step.id === 3 ? "#84CC16" : C.primary) : "#D5DCE8" }} />
                      <div style={{ color: completed || active ? C.text : C.textMuted, fontWeight: active ? 800 : 700, fontSize: 14 }}>{`${step.id}. ${step.label}`}</div>
                    </div>
                  );
                })}
              </div>
            </div>

            {!!visibleAutofillEntries.length && (
              <div className="glass-card" style={{ padding: 18, background: "#F0FDF4", border: "1px solid #86EFAC" }}>
                <div style={{ fontSize: 12, fontWeight: 800, letterSpacing: 0.4, color: "#166534" }}>
                  {revealOperationalRouting ? "DATOS DETECTADOS AUTOMATICAMENTE" : "DATOS DETECTADOS PARA EL DIAGNOSTICO"}
                </div>
                <div style={{ marginTop: 8, color: C.text, fontWeight: 800 }}>
                  {revealOperationalRouting
                    ? "Encontramos estos datos en tu relato o anexos y los usamos para acelerar el expediente:"
                    : "Con estos datos la plataforma preparo el diagnostico y la ruta sugerida. El detalle operativo se habilita al activar el documento."}
                </div>
                        <div style={{ display: "grid", gap: 8, marginTop: 12 }}>
                          {visibleAutofillEntries.slice(0, 5).map(([key, value]) => (
                            <div key={key} style={{ color: "#166534" }}>{`• ${formatAutofillEntry([key, value])}`}</div>
                          ))}
                </div>
              </div>
            )}

            {revealOperationalRouting ? (
              <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 16 }}>
                <div className="glass-card" style={{ padding: 18, background: "#FCFDFF", border: `1px solid ${C.border}` }}>
                  <div style={{ fontSize: 12, fontWeight: 800, letterSpacing: 0.4, color: C.textMuted }}>CANAL DE RADICACION</div>
                  <div style={{ marginTop: 8, color: C.text, fontWeight: 800 }}>{detailRoutingChannel}</div>
                  <div style={{ marginTop: 8, color: C.textMuted, lineHeight: 1.5 }}>{detailRoutingContact}</div>
                </div>
                <div className="glass-card" style={{ padding: 18, background: item.routing?.automatable ? "#EEF4FF" : "#FFF7ED", border: item.routing?.automatable ? "1px solid #BFDBFE" : "1px solid #FED7AA" }}>
                  <div style={{ fontSize: 12, fontWeight: 800, letterSpacing: 0.4, color: item.routing?.automatable ? C.primary : "#C2410C" }}>ESTADO OPERATIVO</div>
                  <div style={{ marginTop: 8, color: C.text, fontWeight: 800 }}>
                    {item.routing?.automatable ? "Radicacion automatizable" : "Requiere apoyo manual"}
                  </div>
                  <div style={{ marginTop: 8, color: C.textMuted, lineHeight: 1.5 }}>
                    {item.routing?.automatable ? "La entidad ya tiene un canal listo para usar dentro del flujo." : "Conviene revisar o confirmar contacto antes del envio definitivo."}
                  </div>
                </div>
                <div className="glass-card" style={{ padding: 18, background: "#F8FAFD", border: `1px solid ${C.border}` }}>
                  <div style={{ fontSize: 12, fontWeight: 800, letterSpacing: 0.4, color: C.textMuted }}>ENTIDAD ACTIVA</div>
                  <div style={{ marginTop: 8, color: C.text, fontWeight: 800 }}>{detailPrimaryTarget?.name || effectivePostPayForm.target_entity || "Entidad por confirmar"}</div>
                  <div style={{ marginTop: 8, color: C.textMuted, lineHeight: 1.5 }}>
                    {item.routing?.subject || "Asunto se ajusta automaticamente al documento."}
                  </div>
                  {!!judicialScopeLabel && (
                    <div style={{ marginTop: 10, color: judicialTerritorialMismatch ? C.danger : C.primary, fontSize: 13, fontWeight: 800 }}>
                      {judicialScopeLabel}
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="glass-card" style={{ padding: 20, background: "linear-gradient(180deg, #FCFDFF 0%, #F8FAFD 100%)", border: `1px solid ${C.border}` }}>
                <div style={{ fontSize: 12, fontWeight: 800, letterSpacing: 0.4, color: C.textMuted }}>ACTIVACION Y RADICACION</div>
                <div style={{ marginTop: 8, color: C.text, fontWeight: 800, fontSize: 22 }}>Primero activas el documento. Luego se libera la radicacion.</div>
                <div style={{ marginTop: 10, color: C.textMuted, lineHeight: 1.7, maxWidth: 760 }}>
                  Al activar el documento final, la plataforma confirma el canal disponible, prepara la version lista para firma y te muestra la opcion de radicar con apoyo o por tu cuenta.
                </div>
              </div>
            )}

            <div style={{ padding: 22, borderRadius: 22, border: `1px solid ${C.border}`, background: "#FCFDFF" }}>
              {flowStep === 1 && (
                <div style={{ display: "grid", gap: 16 }}>
                  <div style={{ display: "grid", gap: 10 }}>
                    <div style={{ color: C.textMuted, fontSize: 13, fontWeight: 700 }}>{item.recommended_action || item.workflow_type}</div>
                    <div style={{ color: C.text, fontSize: 40, fontWeight: 800, fontFamily: "'Playfair Display', serif", lineHeight: 1.02 }}>{item.category}</div>
                  </div>
                  <div style={{ display: "grid", gridTemplateColumns: "1.1fr 0.9fr", gap: 16 }}>
                    <div style={{ padding: 20, borderRadius: 22, background: "linear-gradient(180deg, #101827 0%, #17233A 100%)", color: "#fff", display: "grid", gap: 14 }}>
                      <div style={{ fontSize: 12, color: "#93C5FD", fontWeight: 800, letterSpacing: 0.4 }}>DIAGNOSTICO GRATIS</div>
                      <div style={{ fontSize: 28, fontWeight: 800, lineHeight: 1.08 }}>Tu diagnostico ya esta listo</div>
                      <div style={{ color: "rgba(255,255,255,0.78)", lineHeight: 1.7 }}>
                        {item.payment_status === "pagado" ? item.strategy_text : commercialDiagnosisCopy}
                      </div>
                      <div style={{ marginTop: 4 }}>
                        <div style={{ fontWeight: 800 }}>Viabilidad del caso</div>
                        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 6, marginTop: 10 }}>
                          {detailViability.segments.map((active, index) => (
                            <div
                              key={`${detailViability.label}-${index}`}
                              style={{
                                height: 8,
                                borderRadius: 999,
                                background: active ? detailViability.color : "rgba(148,163,184,0.28)",
                              }}
                            />
                          ))}
                        </div>
                        <div style={{ marginTop: 10, color: detailViability.color, fontWeight: 800 }}>
                          {detailViability.label} — {detailViability.note}
                        </div>
                      </div>
                      {item.payment_status === "pagado" ? (
                        <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
                        {detailRouteSteps.map((step, index) => (
                          <React.Fragment key={`${step}-${index}`}>
                            <div style={{ padding: "8px 12px", borderRadius: 999, background: index === 0 ? "rgba(59,130,246,0.18)" : "rgba(255,255,255,0.06)", border: "1px solid rgba(148,163,184,0.24)", fontWeight: 700 }}>
                              {index + 1}. {step}
                            </div>
                            {index < detailRouteSteps.length - 1 && <div style={{ alignSelf: "center", color: "rgba(255,255,255,0.55)" }}>→</div>}
                          </React.Fragment>
                        ))}
                      </div>
                      ) : (
                        <div style={{ padding: 14, borderRadius: 18, background: "rgba(255,255,255,0.08)", border: "1px solid rgba(148,163,184,0.24)", color: "rgba(255,255,255,0.84)", lineHeight: 1.6 }}>
                          Al activar el documento final se libera la estrategia completa, la version lista para firma y la radicacion dentro del flujo.
                        </div>
                      )}
                    </div>
                    <div style={{ display: "grid", gap: 14 }}>
                      <div style={{ padding: 16, borderRadius: 18, background: "#FCE7F3", border: "1px solid #F9A8D4" }}>
                        <div style={{ fontSize: 12, color: "#BE185D", fontWeight: 800 }}>DERECHOS IDENTIFICADOS</div>
                        <div style={{ marginTop: 10, color: C.text, fontWeight: 800, lineHeight: 1.45 }}>
                          {detailRights.length ? detailRights.join(", ") : "Se consolidan con los datos del expediente."}
                        </div>
                      </div>
                      <div style={{ padding: 16, borderRadius: 18, background: "#FFF7ED", border: "1px solid #FED7AA" }}>
                        <div style={{ fontSize: 12, color: "#C2410C", fontWeight: 800 }}>RECETA JURIDICA BLOQUEADA</div>
                        <div style={{ marginTop: 10, color: C.text, fontWeight: 800, lineHeight: 1.5 }}>
                          Las normas sectoriales, la jurisprudencia y la argumentacion completa se habilitan cuando activas el documento.
                        </div>
                      </div>
                      <div style={{ padding: 16, borderRadius: 18, background: "#18181B", border: "1px solid #3F3F46", color: "#fff" }}>
                        <div style={{ fontSize: 12, color: "#FCA5A5", fontWeight: 800 }}>SE DESBLOQUEA AL PAGAR</div>
                        <div style={{ display: "grid", gap: 8, marginTop: 10, color: "#E4E4E7" }}>
                          <div>🔒 Argumentacion juridica completa</div>
                          <div>🔒 Documento final listo para presentar</div>
                          <div>🔒 Opciones de radicacion despues del pago</div>
                        </div>
                      </div>
                    </div>
                  </div>
                  <div style={{ padding: 18, borderRadius: 18, background: "#FFF7ED", border: "1px solid #FED7AA", color: "#9A3412", display: "grid", gap: 8 }}>
                    <div style={{ fontWeight: 800 }}>Que sigue ahora</div>
                    <div>Si este diagnostico te hace sentido, ya puedes pagar para activar el documento final.</div>
                  </div>
                  <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
                    <Button variant="secondary" onClick={() => onSetDetailStep(2)}>
                      Probar asistente del caso
                    </Button>
                  </div>
                </div>
              )}

              {flowStep === 2 && (
                postPayChatMode ? (
                <PaidCaseAgentWorkspace
                  item={item}
                  agentState={healthAgentState}
                  activeInterviewStep={activeInterviewStep}
                  interviewDraft={interviewDraft}
                  setInterviewDraft={setInterviewDraft}
                  answerInterviewStep={answerInterviewStep}
                  regenerationContext={regenerationContext}
                  evidenceHints={evidenceHints}
                  evidenceNote={evidenceNote}
                  setEvidenceNote={setEvidenceNote}
                  uploadEvidence={uploadEvidence}
                  files={files}
                  missingQuestions={missingQuestions}
                  loading={loading}
                  onSaveFlowDraft={onSaveFlowDraft}
                  onGenerateFromFlow={onGenerateFromFlow}
                  generateDisabled={chatGenerationBlocked}
                />
                ) : (
                <div style={{ display: "grid", gap: 18 }}>
                  <div>
                    <div style={{ color: C.text, fontSize: 24, fontWeight: 800 }}>Completa los datos de tu caso</div>
                    <div style={{ marginTop: 6, color: C.textMuted }}>Necesitamos esta informacion para generar un documento solido con fundamentos legales.</div>
                  </div>
                  {(baseFlowStep >= 3 || item.payment_status !== "pagado") && (
                    <div style={{ padding: 14, borderRadius: 16, background: "#EEF4FF", border: "1px solid #BFDBFE", color: C.text, display: "flex", justifyContent: "space-between", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
                      <div>
                        {baseFlowStep >= 3
                          ? "Estas editando nuevamente el paso 2 para mejorar el documento o probar el asistente."
                          : "Puedes completar y guardar tus datos antes de activar el documento final."}
                      </div>
                      <Button variant="ghost" onClick={() => onSetDetailStep(baseFlowStep)}>
                        {baseFlowStep >= 3 ? "Volver al documento" : "Volver al diagnostico"}
                      </Button>
                    </div>
                  )}
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 16 }}>
                    <Field label="Tu nombre completo *"><TextInput value={postPayForm.full_name} onChange={(event) => setPostPayForm((current) => ({ ...current, full_name: event.target.value }))} /></Field>
                    <Field label="Cedula de ciudadania *"><TextInput value={postPayForm.document_number} onChange={(event) => setPostPayForm((current) => ({ ...current, document_number: event.target.value }))} /></Field>
                    <Field label="Direccion de residencia *"><TextInput value={postPayForm.address} onChange={(event) => setPostPayForm((current) => ({ ...current, address: event.target.value }))} /></Field>
                    <Field label="WhatsApp / celular *"><TextInput value={postPayForm.phone} onChange={(event) => setPostPayForm((current) => ({ ...current, phone: event.target.value }))} /></Field>
                    <Field label="Correo electronico"><TextInput value={postPayForm.copy_email} onChange={(event) => setPostPayForm((current) => ({ ...current, copy_email: event.target.value }))} placeholder="Para recibir copia del documento" /></Field>
                  </div>
                  <div style={{ borderTop: `1px solid ${C.border}`, paddingTop: 18, display: "grid", gap: 16 }}>
                    <Field label="Entidad contra la que reclamas *">
                      <div style={{ position: "relative" }}>
                        <TextInput value={postPayForm.target_entity} onChange={(event) => setPostPayForm((current) => ({ ...current, target_entity: event.target.value }))} placeholder="Ej: Bancolombia, EPS Sura, Claro" />
                        {entityLookupLoading && <div style={{ marginTop: 8, fontSize: 12, color: C.textMuted }}>Buscando entidades...</div>}
                        {!entityLookupLoading && !!entitySuggestions.length && (
                          <div style={{ position: "absolute", top: "calc(100% + 8px)", left: 0, right: 0, zIndex: 20, background: "#fff", border: `1px solid ${C.border}`, borderRadius: 16, boxShadow: "0 18px 40px rgba(15, 23, 42, 0.12)", overflow: "hidden" }}>
                            {entitySuggestions.map((entity, index) => (
                              <button
                                key={`${entity.name}-${entity.nit || entity.source || index}`}
                                type="button"
                                onMouseDown={(event) => {
                                  event.preventDefault();
                                  onApplyEntitySuggestion(entity);
                                }}
                                onClick={() => onApplyEntitySuggestion(entity)}
                                style={{ width: "100%", textAlign: "left", border: "none", background: "#fff", padding: "14px 16px", display: "grid", gap: 4, cursor: "pointer", borderBottom: index === entitySuggestions.length - 1 ? "none" : `1px solid ${C.border}` }}
                              >
                                <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "center" }}>
                                  <strong style={{ color: C.text }}>{entity.name}</strong>
                                  <span style={{ fontSize: 12, color: C.textMuted }}>{entity.type || entity.source || "entidad"}</span>
                                </div>
                                <div style={{ fontSize: 12, color: C.textMuted }}>
                                  {[entity.nit ? `NIT ${entity.nit}` : "", entity.superintendence || "", entity.pqrs_emails?.[0] || ""].filter(Boolean).join(" · ")}
                                </div>
                              </button>
                            ))}
                          </div>
                        )}
                      </div>
                    </Field>
                    <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 16 }}>
                      <Field label="NIT o identificacion"><TextInput value={postPayForm.target_identifier} onChange={(event) => setPostPayForm((current) => ({ ...current, target_identifier: event.target.value }))} /></Field>
                      <Field label="Direccion de la entidad"><TextInput value={postPayForm.target_address} onChange={(event) => setPostPayForm((current) => ({ ...current, target_address: event.target.value }))} /></Field>
                      <Field label="Representante legal"><TextInput value={postPayForm.legal_representative} onChange={(event) => setPostPayForm((current) => ({ ...current, legal_representative: event.target.value }))} /></Field>
                    </div>
                    {item.payment_status === "pagado" && (postPayForm.target_pqrs_email || postPayForm.target_phone || postPayForm.target_superintendence || postPayForm.target_website) && (
                      <div style={{ padding: 16, borderRadius: 16, background: "#F8FAFD", border: `1px solid ${C.border}`, display: "grid", gap: 8 }}>
                        <div style={{ fontSize: 12, color: C.textMuted, fontWeight: 800 }}>DATOS PRECARGADOS PARA DOCUMENTO Y RADICACION</div>
                        {postPayForm.target_pqrs_email && <div style={{ color: C.textMuted }}>Correo PQRS: <strong style={{ color: C.text }}>{postPayForm.target_pqrs_email}</strong></div>}
                        {postPayForm.target_phone && <div style={{ color: C.textMuted }}>Telefono: <strong style={{ color: C.text }}>{postPayForm.target_phone}</strong></div>}
                        {postPayForm.target_superintendence && <div style={{ color: C.textMuted }}>Entidad de control: <strong style={{ color: C.text }}>{postPayForm.target_superintendence}</strong></div>}
                        {postPayForm.target_website && <div style={{ color: C.textMuted }}>Portal: <strong style={{ color: C.text }}>{postPayForm.target_website}</strong></div>}
                      </div>
                    )}
                  </div>
                  <div style={{ borderTop: `1px solid ${C.border}`, paddingTop: 18, display: "grid", gap: 16 }}>
                    {!!activeInterviewStep && (
                      <div style={{ padding: 18, borderRadius: 18, background: "#EEF4FF", border: "1px solid #BFDBFE", display: "grid", gap: 12 }}>
                        <div style={{ fontSize: 12, fontWeight: 800, color: C.primary }}>ASISTENTE DEL CASO</div>
                        <div style={{ color: C.text, fontWeight: 700, lineHeight: 1.6 }}>{activeInterviewStep.question}</div>
                        {activeInterviewStep.multiline ? (
                          <TextArea
                            value={interviewDraft}
                            onChange={(event) => setInterviewDraft(event.target.value)}
                            style={{ minHeight: 90 }}
                            placeholder={activeInterviewStep.placeholder}
                          />
                        ) : (
                          <TextInput
                            value={interviewDraft}
                            onChange={(event) => setInterviewDraft(event.target.value)}
                            placeholder={activeInterviewStep.placeholder}
                          />
                        )}
                        <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
                          <Button variant="secondary" onClick={answerInterviewStep} disabled={!interviewDraft.trim()}>
                            Guardar respuesta y seguir
                          </Button>
                          <div style={{ color: C.textMuted, fontSize: 13, alignSelf: "center" }}>
                            La app te pregunta lo que falta para que el documento quede completo antes de redactarlo.
                          </div>
                        </div>
                      </div>
                    )}
                    <Field label="Cuenta con detalle que paso *">
                      <TextArea value={postPayForm.case_story} onChange={(event) => setPostPayForm((current) => ({ ...current, case_story: event.target.value }))} style={{ minHeight: 140 }} placeholder="Fechas, que te negaron, que respuesta te dieron, como te afecta." />
                    </Field>
                    <Field label="Que solucion concreta necesitas *">
                      <TextArea
                        value={postPayForm.concrete_request}
                        onChange={(event) => setPostPayForm((current) => ({ ...current, concrete_request: event.target.value }))}
                        style={{ minHeight: 96 }}
                        placeholder="Ej: eliminar el cobro del seguro no autorizado, devolver los valores cobrados y responder formalmente mi reclamacion."
                      />
                    </Field>
                    <Field label="Fechas importantes *"><TextInput value={postPayForm.key_dates} onChange={(event) => setPostPayForm((current) => ({ ...current, key_dates: event.target.value }))} placeholder="Cuando paso, cuando reclamaste y cuando respondieron" /></Field>
                    {item.category === "Bancos" && (
                      <div style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: 14 }}>
                        <Field label="Producto financiero *">
                          <TextInput value={postPayForm.bank_product_type} onChange={(event) => setPostPayForm((current) => ({ ...current, bank_product_type: event.target.value }))} placeholder="Ej: tarjeta de credito, cuenta de ahorros, prestamo" />
                        </Field>
                        <Field label="Cobro o concepto discutido *">
                          <TextInput value={postPayForm.disputed_charge} onChange={(event) => setPostPayForm((current) => ({ ...current, disputed_charge: event.target.value }))} placeholder="Ej: seguro, cuota de manejo, interes, reporte" />
                        </Field>
                        <Field label="Valor o monto cobrado *">
                          <TextInput value={postPayForm.bank_amount_involved} onChange={(event) => setPostPayForm((current) => ({ ...current, bank_amount_involved: event.target.value }))} placeholder="Ej: $38.500 mensuales o $154.000 acumulados" />
                        </Field>
                        <Field label="Fecha del primer cobro o hecho *">
                          <TextInput value={postPayForm.bank_event_date} onChange={(event) => setPostPayForm((current) => ({ ...current, bank_event_date: event.target.value }))} placeholder="Ej: 12 de octubre de 2025" />
                        </Field>
                        <Field label="Referencia de tarjeta o cuenta">
                          <TextInput value={postPayForm.bank_account_reference} onChange={(event) => setPostPayForm((current) => ({ ...current, bank_account_reference: event.target.value }))} placeholder="Ej: tarjeta terminada en 4821 o cuenta terminada en 9912" />
                        </Field>
                        <Field label="A donde deben devolver el dinero">
                          <TextInput value={postPayForm.refund_destination} onChange={(event) => setPostPayForm((current) => ({ ...current, refund_destination: event.target.value }))} placeholder="Ej: a la misma tarjeta, a mi cuenta Bancolombia o consignacion a..." />
                        </Field>
                      </div>
                    )}
                    <div style={{ display: "grid", gap: 10 }}>
                      <div style={{ fontSize: 13, fontWeight: 700, color: C.text }}>Ya reclamaste directamente ante la entidad? *</div>
                      <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
                        {[["si", "Si, reclame"], ["no", "No, aun no"]].map(([value, label]) => (
                          <button key={value} onClick={() => setPostPayForm((current) => ({ ...current, prior_claim: value }))} style={{ border: `1px solid ${postPayForm.prior_claim === value ? C.primary : C.border}`, background: postPayForm.prior_claim === value ? C.primaryLight : "#fff", color: postPayForm.prior_claim === value ? C.primary : C.text, borderRadius: 14, padding: "10px 16px", fontWeight: 700, cursor: "pointer" }}>{label}</button>
                        ))}
                      </div>
                    </div>
                    {postPayForm.prior_claim === "si" && (
                      <div style={{ display: "grid", gap: 14 }}>
                        <Field label="Fecha del reclamo previo *">
                          <TextInput value={postPayForm.prior_claim_date} onChange={(event) => setPostPayForm((current) => ({ ...current, prior_claim_date: event.target.value }))} placeholder="Ej: 14 de enero de 2026 por PQRS web o llamada" />
                        </Field>
                        <Field label="Que respuesta te dieron? *">
                          <TextArea value={postPayForm.prior_claim_result} onChange={(event) => setPostPayForm((current) => ({ ...current, prior_claim_result: event.target.value }))} style={{ minHeight: 90 }} placeholder="Ej: el banco dijo que el seguro estaba activo, pero no envio autorizacion ni soporte." />
                        </Field>
                      </div>
                    )}
                    <Field label="Que pruebas tienes disponibles *">
                      <TextArea value={postPayForm.evidence_summary} onChange={(event) => setPostPayForm((current) => ({ ...current, evidence_summary: event.target.value }))} style={{ minHeight: 96 }} placeholder="Ej: extractos, capturas, chats, correo de respuesta, PDF del contrato o audio del asesor." />
                    </Field>
                    {isTutelaFlow && (
                      <>
                        <Field label="Sujeto de especial proteccion *">
                          <select value={postPayForm.special_protection} onChange={(event) => setPostPayForm((current) => ({ ...current, special_protection: event.target.value }))} style={{ width: "100%", padding: "14px 16px", borderRadius: 12, border: `1px solid ${C.border}`, background: "#fff", color: C.text }}>
                            {specialProtectionOptions.map((option) => <option key={option} value={option}>{option}</option>)}
                          </select>
                        </Field>
                        <div style={{ display: "grid", gap: 10 }}>
                          <div style={{ fontSize: 13, fontWeight: 700, color: C.text }}>Has presentado tutela antes por esto? *</div>
                          <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
                            {[["no", "No"], ["si", "Si"]].map(([value, label]) => (
                              <button key={value} onClick={() => setPostPayForm((current) => ({ ...current, prior_tutela: value }))} style={{ border: `1px solid ${postPayForm.prior_tutela === value ? C.primary : C.border}`, background: postPayForm.prior_tutela === value ? C.primaryLight : "#fff", color: postPayForm.prior_tutela === value ? C.primary : C.text, borderRadius: 14, padding: "10px 16px", fontWeight: 700, cursor: "pointer" }}>{label}</button>
                            ))}
                          </div>
                        </div>
                        {postPayForm.prior_tutela === "si" && (
                          <Field label="Si si, por que es diferente?">
                            <TextArea value={postPayForm.prior_tutela_reason} onChange={(event) => setPostPayForm((current) => ({ ...current, prior_tutela_reason: event.target.value }))} style={{ minHeight: 90 }} />
                          </Field>
                        )}
                      </>
                    )}
                  </div>
                  <div style={{ borderTop: `1px solid ${C.border}`, paddingTop: 18, display: "grid", gap: 12 }}>
                    <div>
                      <div style={{ fontSize: 13, fontWeight: 800, color: C.text }}>Sube tus pruebas</div>
                      <div style={{ color: C.textMuted, marginTop: 4 }}>PDF, imagen o Word. Maximo 10MB por archivo.</div>
                      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 10 }}>
                        {evidenceHints.map((hint) => <Badge key={hint} color={C.primary}>{hint}</Badge>)}
                      </div>
                    </div>
                    <input id="postpay-evidence-upload" type="file" style={{ display: "none" }} onChange={uploadEvidence} />
                    <div style={{ border: `1px dashed ${C.border}`, borderRadius: 18, padding: 24, background: "#F8FAFD", display: "grid", gap: 12, justifyItems: "center" }}>
                      <TextInput value={evidenceNote} onChange={(event) => setEvidenceNote(event.target.value)} placeholder="Descripcion del archivo" style={{ maxWidth: 420 }} />
                      <Button variant="secondary" onClick={() => document.getElementById("postpay-evidence-upload").click()} icon={Upload}>Arrastra archivos o haz clic</Button>
                    </div>
                    <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
                      {files.map((file) => <Badge key={file.id} color={C.accent}>{file.original_name}</Badge>)}
                    </div>
                  </div>
                  {!!missingFields.length && (
                    <div style={{ padding: 14, borderRadius: 16, background: "#FFF7ED", border: "1px solid #FED7AA", color: "#9A3412" }}>
                      Faltan estos campos antes de generar el documento: {missingFields.join(", ")}.
                    </div>
                  )}
                  {!!missingQuestions.length && (
                    <div style={{ padding: 14, borderRadius: 16, background: "#EEF4FF", border: "1px solid #BFDBFE", color: C.text, display: "grid", gap: 8 }}>
                      <div style={{ fontWeight: 800 }}>Antes de redactar un documento serio, la app necesita estas respuestas:</div>
                      {missingQuestions.map((question) => <div key={question}>{`• ${question}`}</div>)}
                    </div>
                  )}
                  <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
                    <div style={{ color: C.textMuted, fontSize: 13 }}>* Campos obligatorios</div>
                    <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
                      <Button variant="secondary" onClick={onSaveFlowDraft} disabled={loading}>
                        {loading ? "Guardando..." : "Guardar respuestas"}
                      </Button>
                      <Button onClick={onGenerateFromFlow} disabled={loading || !!missingFields.length || item.payment_status !== "pagado"} icon={ArrowRight}>
                        {loading ? "Generando..." : item.payment_status !== "pagado" ? "Paga para generar el documento" : "Generar mi documento"}
                      </Button>
                    </div>
                  </div>
                </div>
                )
              )}

              {flowStep === 3 && (
                <div style={{ display: "grid", gap: 18 }}>
                  <div style={{ padding: 18, borderRadius: 18, background: "#14532D", color: "#ECFDF5" }}>
                    <div style={{ fontSize: 28, fontWeight: 800 }}>Tu documento esta listo</div>
                    <div style={{ marginTop: 8, fontSize: 18 }}>{item.recommended_action} generado el {item.updated_at ? shortDate(item.updated_at) : "hace unos minutos"}</div>
                  </div>
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 16 }}>
                    <div style={{ padding: 18, borderRadius: 18, background: "#111827", color: "#fff" }}>
                      <div style={{ fontSize: 13, fontWeight: 800, color: "#86EFAC" }}>CALIDAD DEL DOCUMENTO</div>
                      <div style={{ marginTop: 10, fontSize: 48, lineHeight: 1, fontWeight: 900 }}>{review?.score || "--"}/100</div>
                      <div style={{ marginTop: 8, color: "rgba(255,255,255,0.75)" }}>{review?.passed ? "Aprobado, buena fundamentacion" : "Pendiente de validacion"}</div>
                    </div>
                    <div style={{ padding: 18, borderRadius: 18, background: "#F8FAFD", border: `1px solid ${C.border}` }}>
                      <div style={{ fontSize: 13, fontWeight: 800, color: C.textMuted }}>DERECHOS IDENTIFICADOS</div>
                      <div style={{ marginTop: 10, color: C.text, fontWeight: 800, fontSize: 24 }}>{rights.length ? rights.join(" · ") : "Se consolidaron los derechos base del caso."}</div>
                    </div>
                  </div>
                  <div style={{ padding: 18, borderRadius: 18, border: `1px solid ${C.border}`, background: "#FCFDFF" }}>
                    <div style={{ fontSize: 13, fontWeight: 800, color: C.text }}>Tu documento incluye</div>
                    <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 10, marginTop: 14 }}>
                      {checklist.map((line) => <div key={line} style={{ color: C.textMuted }}>{`✓ ${line}`}</div>)}
                    </div>
                  </div>
                  <div style={{ padding: 18, borderRadius: 18, border: `1px solid ${C.border}`, background: "#FCFDFF", display: "grid", gap: 14 }}>
                    <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
                      <div>
                        <div style={{ fontSize: 13, fontWeight: 800, color: C.text }}>Revisa el documento antes de firmar</div>
                        <div style={{ marginTop: 6, color: C.textMuted }}>El orden correcto es revisar, firmar, confirmar envio y despues radicar.</div>
                      </div>
                      <Button variant="outline" onClick={() => onViewDocument(item)}>Abrir vista completa</Button>
                    </div>
                    <div style={{ padding: 16, borderRadius: 16, background: "#F8FAFD", border: `1px solid ${C.border}`, maxHeight: 240, overflow: "auto", color: C.text, lineHeight: 1.7, whiteSpace: "pre-wrap" }}>
                      {item.generated_document ? `${item.generated_document.slice(0, 1800)}${item.generated_document.length > 1800 ? "\n\n[...] abre la vista completa para revisar todo el documento." : ""}` : "Todavia no hay vista previa disponible."}
                    </div>
                    <label style={{ display: "flex", gap: 10, alignItems: "flex-start", color: C.text }}>
                      <input type="checkbox" checked={documentReviewed} onChange={(event) => setDocumentReviewed(event.target.checked)} />
                      <span style={{ lineHeight: 1.6 }}>Ya revise el documento completo y puedo pasar a la firma.</span>
                    </label>
                    <div>
                      <div style={{ fontSize: 13, fontWeight: 800, color: C.text }}>Firma electronica simple para el envio</div>
                      <div style={{ marginTop: 6, color: C.textMuted }}>
                        Nombre, cedula, ciudad y fecha como aceptacion expresa del documento revisado. La app guarda esta aceptacion con trazabilidad tecnica basica.
                      </div>
                    </div>
                    <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 14 }}>
                      <Field label="Nombre completo">
                        <TextInput value={signatureForm.full_name} onChange={(event) => setSignatureForm((current) => ({ ...current, full_name: event.target.value }))} />
                      </Field>
                      <Field label="Cedula">
                        <TextInput value={signatureForm.document_number} onChange={(event) => setSignatureForm((current) => ({ ...current, document_number: event.target.value }))} />
                      </Field>
                      <Field label="Ciudad">
                        <TextInput value={signatureForm.city} onChange={(event) => setSignatureForm((current) => ({ ...current, city: event.target.value }))} />
                      </Field>
                      <Field label="Fecha">
                        <TextInput value={signatureForm.date} onChange={(event) => setSignatureForm((current) => ({ ...current, date: event.target.value }))} />
                      </Field>
                    </div>
                    <label style={{ display: "flex", gap: 10, alignItems: "flex-start", color: C.text }}>
                      <input type="checkbox" checked={signatureAccepted} onChange={(event) => setSignatureAccepted(event.target.checked)} />
                      <span style={{ lineHeight: 1.6 }}>Acepto el consentimiento de firma electronica simple version {SIMPLE_SIGNATURE_CONSENT_VERSION}.</span>
                    </label>
                    <div style={{ padding: 14, borderRadius: 16, background: "#F8FAFD", border: `1px solid ${C.border}`, color: C.textMuted, fontSize: 13, lineHeight: 1.6 }}>
                      <div style={{ fontWeight: 800, color: C.text, marginBottom: 8 }}>Texto de consentimiento</div>
                      <div>{SIMPLE_SIGNATURE_CONSENT_TEXT}</div>
                      <div style={{ marginTop: 10 }}>
                        La evidencia guardada incluye nombre, documento, ciudad, fecha declarada, aceptacion, version del consentimiento y metadatos tecnicos basicos del envio.
                      </div>
                    </div>
                    {!signatureReady && (
                      <div style={{ padding: 14, borderRadius: 16, background: "#FFF7ED", border: "1px solid #FED7AA", color: "#9A3412" }}>
                        La firma y la radicacion se habilitan cuando revisas el documento completo y completas esta confirmacion.
                      </div>
                    )}
                  </div>
                  <div style={{ padding: 18, borderRadius: 18, border: `1px solid ${C.border}`, background: "#F8FAFD", display: "grid", gap: 12 }}>
                    <div style={{ fontSize: 13, fontWeight: 800, color: C.text }}>Si quieres regenerarlo, explica que debe corregir la IA</div>
                    <Field label="Por que no te gusto este documento o que debe mejorar">
                      <TextArea
                        value={regenerationReason}
                        onChange={(event) => setRegenerationReason(event.target.value)}
                        style={{ minHeight: 90 }}
                        placeholder="Ej: falta mejor justificacion juridica, la cronologia esta floja o la entidad no quedo bien descrita."
                      />
                    </Field>
                    <Field label="Informacion adicional para la nueva version">
                      <TextArea
                        value={regenerationContext}
                        onChange={(event) => setRegenerationContext(event.target.value)}
                        style={{ minHeight: 110 }}
                        placeholder="Ej: reclame por telefono el 12 de enero, me dijeron que el seguro estaba activo desde noviembre y nunca firme autorizacion."
                      />
                    </Field>
                  </div>
                  {!!actionableGaps.length && (finalValidation?.status === "requires_changes" || !review?.passed) && (
                    <div style={{ padding: 18, borderRadius: 18, background: "#FFF7ED", border: "1px solid #FDBA74", display: "grid", gap: 12 }}>
                      <div style={{ fontSize: 14, fontWeight: 800, color: "#9A3412" }}>
                        Faltan datos criticos para corregir este documento
                      </div>
                      <div style={{ color: "#9A3412", lineHeight: 1.6 }}>
                        Completa estos puntos y luego vuelve a generar el documento.
                      </div>
                      <div style={{ display: "grid", gap: 10 }}>
                        {actionableGaps.slice(0, 6).map((gap, index) => (
                          <div key={`${gap.label}-${index}`} style={{ padding: 14, borderRadius: 14, background: "#FFF", border: "1px solid #FED7AA" }}>
                            <div style={{ fontWeight: 800, color: C.text }}>{gap.label}</div>
                            <div style={{ marginTop: 6, color: C.textMuted }}>{gap.prompt}</div>
                            <div style={{ marginTop: 8, fontSize: 13, color: "#9A3412", fontWeight: 700 }}>
                              Donde lo completas: {gap.where_to_fix}
                            </div>
                          </div>
                        ))}
                      </div>
                      <div style={{ display: "flex", justifyContent: "flex-end" }}>
                        <Button variant="secondary" onClick={() => onSetDetailStep(2)}>Ir a completar datos</Button>
                      </div>
                    </div>
                  )}
                  <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
                    <Button onClick={() => onViewDocument(item)}>Ver documento completo</Button>
                    <Button variant="outline" onClick={() => onViewDocument(item)}>Descargar PDF</Button>
                    <Button variant="secondary" onClick={onGenerateFromFlow} disabled={loading} icon={FileText}>
                      {loading ? "Regenerando..." : "Regenerar documento"}
                    </Button>
                    <Button variant="outline" onClick={() => onSetDetailStep(2)} icon={ArrowLeft}>
                      Volver a completar datos
                    </Button>
                    <Button variant="ghost" style={{ background: "#EEF4FF", color: C.primary }} onClick={() => onViewDocument(item)}>Ver en lenguaje simple</Button>
                  </div>
                  <div style={{ padding: 16, borderRadius: 18, background: "#EEF4FF", border: "1px solid #BFDBFE", color: C.text }}>
                    {guidance.customer_copy_channels?.includes("email")
                      ? `Te enviaremos al correo del caso una copia del documento enviado y, cuando exista, el comprobante disponible desde ${guidance.operational_mailboxes?.notifications || "notificaciones@123tutelaapp.com"}. Si el juzgado o la EPS responde al correo del cliente o por llamada directa, debes reportarlo para que el seguimiento quede actualizado en tu panel.`
                      : "La copia del documento queda visible en tu panel. Si habilitamos mas canales, apareceran aqui."}
                  </div>
                </div>
              )}

              {flowStep === 4 && (
                <div style={{ display: "grid", gap: 18 }}>
                  <div style={{ padding: 18, borderRadius: 18, background: "#EEF4FF", border: "1px solid #BFDBFE" }}>
                    <div style={{ fontSize: 24, fontWeight: 800, color: C.text }}>Tu documento fue radicado</div>
                    <div style={{ marginTop: 8, color: C.textMuted }}>
                      {submissionSummary.radicado ? `Comprobante ${submissionSummary.radicado} disponible para este expediente.` : "Ya registramos el cierre operativo de la radicacion."}
                    </div>
                  </div>
                  <div className="glass-card" style={{ padding: 18, background: "#FCFDFF" }}>
                    <div style={{ fontSize: 13, fontWeight: 800, color: C.textMuted }}>SIGUIENTE PASO</div>
                    <div style={{ marginTop: 8, color: C.text, fontWeight: 800, fontSize: 24 }}>{guidance.next_step_suggestion || "Haz seguimiento a la respuesta de la entidad."}</div>
                    <div style={{ marginTop: 8, color: C.textMuted }}>{guidance.estimated_response_window || "Te avisaremos si hay novedades importantes."}</div>
                  </div>
                </div>
              )}
            </div>

            {flowStep === 3 && (
              <div style={{ padding: 22, borderRadius: 22, border: `1px solid ${C.border}`, background: "#FCFDFF" }}>
                <div style={{ fontSize: 24, fontWeight: 800, color: C.text }}>Siguiente paso: radicacion</div>
                <div style={{ marginTop: 8, color: C.textMuted }}>Puedes radicar tu misma o activar el paquete para que nosotros lo hagamos por ti.</div>
                <div style={{ marginTop: 16, padding: 18, borderRadius: 18, background: "#F8FAFD", border: `1px solid ${C.border}`, display: "grid", gap: 14 }}>
                  <div>
                    <div style={{ fontSize: 13, fontWeight: 800, color: C.text }}>Confirmacion final antes del envio</div>
                    <div style={{ marginTop: 6, color: C.textMuted, lineHeight: 1.6 }}>
                      Si ya revisaste el documento, puedes confirmar aqui mismo la revision y la firma electronica simple para desbloquear la radicacion.
                    </div>
                  </div>
                  {!!judicialTerritorialNote && (
                    <div style={{ padding: 14, borderRadius: 14, background: judicialTerritorialMismatch ? "#FEF2F2" : "#EEF4FF", border: judicialTerritorialMismatch ? "1px solid #FECACA" : "1px solid #BFDBFE", color: judicialTerritorialMismatch ? "#991B1B" : C.text, lineHeight: 1.6 }}>
                      {judicialTerritorialNote}
                    </div>
                  )}
                  <label style={{ display: "flex", gap: 10, alignItems: "flex-start", color: C.text }}>
                    <input type="checkbox" checked={documentReviewed} onChange={(event) => setDocumentReviewed(event.target.checked)} />
                    <span style={{ lineHeight: 1.6 }}>Ya verifique el documento completo y autorizo continuar con la radicacion.</span>
                  </label>
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 12 }}>
                    <Field label="Nombre completo">
                      <TextInput value={signatureForm.full_name} onChange={(event) => setSignatureForm((current) => ({ ...current, full_name: event.target.value }))} />
                    </Field>
                    <Field label="Cedula">
                      <TextInput value={signatureForm.document_number} onChange={(event) => setSignatureForm((current) => ({ ...current, document_number: event.target.value }))} />
                    </Field>
                    <Field label="Ciudad">
                      <TextInput value={signatureForm.city} onChange={(event) => setSignatureForm((current) => ({ ...current, city: event.target.value }))} />
                    </Field>
                    <Field label="Fecha">
                      <TextInput value={signatureForm.date} onChange={(event) => setSignatureForm((current) => ({ ...current, date: event.target.value }))} />
                    </Field>
                  </div>
                  <label style={{ display: "flex", gap: 10, alignItems: "flex-start", color: C.text }}>
                    <input type="checkbox" checked={signatureAccepted} onChange={(event) => setSignatureAccepted(event.target.checked)} />
                    <span style={{ lineHeight: 1.6 }}>Acepto el consentimiento de firma electronica simple version {SIMPLE_SIGNATURE_CONSENT_VERSION}.</span>
                  </label>
                  {requiresJudicialConfirmation && (
                    <label style={{ display: "flex", gap: 10, alignItems: "flex-start", color: C.text }}>
                      <input type="checkbox" checked={judicialDestinationConfirmed} onChange={(event) => setJudicialDestinationConfirmed(event.target.checked)} />
                      <span style={{ lineHeight: 1.6 }}>
                        {judicialTerritorialMismatch
                          ? "Confirmo que revise el destino judicial sugerido, que entiendo que no coincide exactamente con la ciudad del caso y que aun asi autorizo este envio."
                          : "Confirmo que este envio va a un juzgado o correo real de reparto, que ya verifique el documento final y que autorizo expresamente ese envio judicial."}
                      </span>
                    </label>
                  )}
                </div>
                {!signatureReady && (
                  <div style={{ marginTop: 14, padding: 14, borderRadius: 16, background: "#FEF2F2", border: "1px solid #FECACA", color: "#991B1B" }}>
                    Antes del envio debes revisar el documento completo y confirmar la firma simple.
                  </div>
                )}
                {!filingAutoPaid && (
                  <div style={{ marginTop: 14, padding: 14, borderRadius: 16, background: "#FFF7ED", border: "1px solid #FDBA74", color: "#9A3412", lineHeight: 1.6 }}>
                    Para usar la radicacion por 123tutela debes activar primero el paquete de radicacion y seguimiento.
                  </div>
                )}
                <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 12, marginTop: 18 }}>
                  <Button disabled={!signatureReady || !filingAutoPaid} onClick={() => onSubmitCase({ mode: "auto", notes: buildSubmissionSignatureNote(signatureForm, submissionNote), signature: { ...signatureForm, accepted: signatureAccepted, consent_version: SIMPLE_SIGNATURE_CONSENT_VERSION, consent_text: SIMPLE_SIGNATURE_CONSENT_TEXT }, reviewed_document: documentReviewed, judicial_destination_confirmed: !requiresJudicialConfirmation || judicialDestinationConfirmed })}>Radicar por mi (+$9.900)</Button>
                  <Button disabled={!signatureReady} variant="ghost" style={{ background: "#F8FAFD", border: `1px solid ${C.border}` }} onClick={() => onManualRadicado({ radicado: radicadoManual || `AUTO-${Date.now()}`, notes: buildSubmissionSignatureNote(signatureForm, radicadoNote || "Usuario decidio radicar por su cuenta."), signature: { ...signatureForm, accepted: signatureAccepted, consent_version: SIMPLE_SIGNATURE_CONSENT_VERSION, consent_text: SIMPLE_SIGNATURE_CONSENT_TEXT }, reviewed_document: documentReviewed })}>Yo lo radico por mi cuenta</Button>
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginTop: 16 }}>
                  <TextInput value={manualContact} onChange={(event) => setManualContact(event.target.value)} placeholder="Correo o canal de apoyo interno" />
                  <TextInput value={submissionNote} onChange={(event) => setSubmissionNote(event.target.value)} placeholder="Notas para la radicacion" />
                  <TextInput value={radicadoManual} onChange={(event) => setRadicadoManual(event.target.value)} placeholder="Radicado manual si lo haces tu" />
                  <TextInput value={radicadoNote} onChange={(event) => setRadicadoNote(event.target.value)} placeholder="Notas del cierre manual" />
                </div>
              </div>
            )}

            {flowStep >= 4 && (
              <div style={{ padding: 22, borderRadius: 22, border: `1px solid ${C.border}`, background: "#FCFDFF" }}>
                <div style={{ fontSize: 22, fontWeight: 800, color: C.text }}>Seguimiento de tu caso</div>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 14, marginTop: 16 }}>
                  <div>
                    <div style={{ fontSize: 12, color: C.textMuted, fontWeight: 800 }}>COMPROBANTE</div>
                    <div style={{ marginTop: 6, color: C.text, fontWeight: 800 }}>{submissionSummary.radicado || "Aun no visible"}</div>
                  </div>
                  <div>
                    <div style={{ fontSize: 12, color: C.textMuted, fontWeight: 800 }}>ESTADO ACTUAL</div>
                    <div style={{ marginTop: 6, color: C.text, fontWeight: 800 }}>{deliveryStatusLabel}</div>
                  </div>
                  <div>
                    <div style={{ fontSize: 12, color: C.textMuted, fontWeight: 800 }}>SIGUIENTE PASO</div>
                    <div style={{ marginTop: 6, color: C.text, fontWeight: 800 }}>{guidance.next_step_suggestion || "Espera la respuesta de la entidad o del juzgado."}</div>
                  </div>
                </div>
                {!!judicialTerritorialNote && (
                  <div style={{ marginTop: 14, padding: 14, borderRadius: 16, background: judicialTerritorialMismatch ? "#FEF2F2" : "#F8FAFD", border: judicialTerritorialMismatch ? "1px solid #FECACA" : `1px solid ${C.border}`, color: judicialTerritorialMismatch ? "#991B1B" : C.text, lineHeight: 1.6 }}>
                    {judicialTerritorialNote}
                  </div>
                )}
                {!!guidance.judicial_radicado_note && (
                  <div style={{ marginTop: 16, padding: 18, borderRadius: 18, background: "#FFF7ED", border: "1px solid #FDBA74", color: "#9A3412", lineHeight: 1.6 }}>
                    <div style={{ fontSize: 12, fontWeight: 800, letterSpacing: "0.08em" }}>SOBRE ESTE COMPROBANTE</div>
                    <div style={{ marginTop: 8 }}>
                      Este comprobante corresponde al registro que la plataforma pudo guardar para tu expediente. Si el juzgado, la EPS o la entidad te responde directamente a tu correo o por llamada, debes reportarlo o subir la evidencia para mantener el seguimiento actualizado.
                    </div>
                  </div>
                )}
                <div style={{ marginTop: 16, padding: 18, borderRadius: 18, background: "#EEF4FF", border: "1px solid #BFDBFE", color: C.text, lineHeight: 1.7 }}>
                  <div style={{ fontSize: 12, fontWeight: 800, letterSpacing: "0.08em", color: C.primary }}>COMO HACER SEGUIMIENTO</div>
                  <div style={{ marginTop: 8 }}>
                    Revisa aqui si ya hay comprobante, respuesta o una novedad registrada. Si el juzgado, la EPS o la entidad te escribe a tu correo, te llama o te pide algo por fuera de la plataforma, debes reportarlo o subir la evidencia para que el seguimiento quede completo y podamos definir el siguiente paso.
                  </div>
                </div>
                <div style={{ marginTop: 16, padding: 18, borderRadius: 18, background: "#FCFDFF", border: `1px solid ${C.border}`, display: "grid", gap: 12 }}>
                  <div style={{ fontSize: 12, color: C.textMuted, fontWeight: 800 }}>REPORTAR NOVEDAD</div>
                  <div style={{ color: C.textMuted, lineHeight: 1.6 }}>
                    Si recibiste una llamada, un correo, un requerimiento o cualquier respuesta nueva, repórtala aquí. Si tienes soporte, súbelo también.
                  </div>
                  <TextArea
                    value={followUpNote}
                    onChange={(event) => setFollowUpNote(event.target.value)}
                    placeholder="Ejemplo: hoy me llamo la EPS, me pidieron formula actualizada, o el juzgado envio un requerimiento al correo."
                    style={{ minHeight: 100 }}
                  />
                  <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
                    <Button
                      variant="secondary"
                      disabled={loading || followUpNote.trim().length < 8}
                      onClick={async () => {
                        await onReportFollowUp({
                          note: followUpNote.trim(),
                          source: "cliente",
                        });
                        setFollowUpNote("");
                      }}
                    >
                      Reportar novedad
                    </Button>
                    <Button variant="outline" onClick={() => document.getElementById("followup-evidence-upload").click()} icon={Upload}>
                      Subir evidencia
                    </Button>
                  </div>
                  <input id="followup-evidence-upload" type="file" style={{ display: "none" }} onChange={uploadEvidence} />
                </div>
                {!!primarySubmissionAttempt && (
                  <div style={{ marginTop: 16, padding: 18, borderRadius: 18, background: "#FCFDFF", border: `1px solid ${C.border}`, display: "grid", gap: 12 }}>
                    <div style={{ fontSize: 12, color: C.textMuted, fontWeight: 800 }}>ULTIMO MOVIMIENTO REGISTRADO</div>
                    <div style={{ padding: 14, borderRadius: 16, background: "#F8FAFD", border: `1px solid ${C.border}`, display: "grid", gap: 8 }}>
                      <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap", alignItems: "center" }}>
                        <div style={{ color: C.text, fontWeight: 800 }}>{primarySubmissionAttempt.destination_name || "Radicacion registrada"}</div>
                        <Badge color={submissionSummary.radicado ? C.success : C.primary}>
                          {deliveryStatusLabel}
                        </Badge>
                      </div>
                      <div style={{ color: C.textMuted, lineHeight: 1.6 }}>
                        {primarySubmissionAttempt.created_at ? `Registrado el ${shortDate(primarySubmissionAttempt.created_at)}.` : "Ya registramos una novedad reciente en tu expediente."}
                        {" "}
                        {submissionSummary.radicado ? `Comprobante asociado: ${submissionSummary.radicado}.` : ""}
                      </div>
                      {(primarySubmissionAttempt.destination_contact || primarySubmissionAttempt.destination_name) && (
                        <div style={{ color: C.text, fontWeight: 700, wordBreak: "break-word" }}>
                          Destino: {primarySubmissionAttempt.destination_name || primarySubmissionAttempt.destination_contact}
                        </div>
                      )}
                    </div>
                  </div>
                )}
                {!!visibleTimelineEvents.length && (
                  <div style={{ marginTop: 16, padding: 18, borderRadius: 18, background: "#FCFDFF", border: `1px solid ${C.border}`, display: "grid", gap: 12 }}>
                    <div style={{ fontSize: 12, color: C.textMuted, fontWeight: 800 }}>ULTIMAS NOVEDADES</div>
                    {visibleTimelineEvents.map((event) => (
                      <div key={event.id} style={{ display: "grid", gridTemplateColumns: "180px 1fr", gap: 12, alignItems: "start", paddingTop: 10, borderTop: `1px solid ${C.border}` }}>
                        <div style={{ color: C.textMuted, fontSize: 13 }}>{shortDate(event.created_at)}</div>
                        <div style={{ display: "grid", gap: 4 }}>
                          <div style={{ color: C.text, fontWeight: 700 }}>{formatTimelineEventLabel(event)}</div>
                          <div style={{ color: C.textMuted, fontSize: 13, lineHeight: 1.6 }}>{formatTimelineEventDetail(event)}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
                <div style={{ marginTop: 14, color: C.textMuted, lineHeight: 1.7 }}>
                  {guidance.post_radicado_copy?.body || "Te enviaremos copia del documento y cualquier comprobante disponible. Si recibes una llamada, correo o requerimiento directo, repórtalo desde el caso para mantener actualizado el seguimiento."}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function PaidCaseAgentWorkspace({
  item,
  agentState = {},
  activeInterviewStep,
  interviewDraft,
  setInterviewDraft,
  answerInterviewStep,
  regenerationContext = "",
  evidenceHints = [],
  evidenceNote = "",
  setEvidenceNote = () => {},
  uploadEvidence = async () => {},
  files = [],
  missingQuestions = [],
  loading = false,
  onSaveFlowDraft = () => {},
  onGenerateFromFlow = () => {},
  generateDisabled = false,
}) {
  return (
    <div style={{ display: "grid", gap: 18 }}>
      <div>
        <div style={{ color: C.text, fontSize: 24, fontWeight: 800 }}>Habla con el agente juridico de tu caso</div>
        <div style={{ marginTop: 6, color: C.textMuted, lineHeight: 1.7 }}>
          Ya no tienes que llenar el formulario largo. El agente conoce la ruta legal, revisa tus anexos, identifica el riesgo actual del paciente y la barrera que esta imponiendo la EPS, y te hara una pregunta a la vez hasta dejar el expediente listo para redactar.
        </div>
      </div>

      <div style={{ padding: 18, borderRadius: 18, background: "#EEF4FF", border: "1px solid #BFDBFE", display: "grid", gap: 12 }}>
        <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
          <div style={{ fontSize: 12, fontWeight: 800, color: C.primary }}>AGENTE DEL CASO</div>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            <Badge color={C.primary}>Chat activo</Badge>
            {agentState.can_generate && <Badge color={C.success}>Listo para redactar</Badge>}
          </div>
        </div>
        <div style={{ color: C.text, fontWeight: 700, lineHeight: 1.65 }}>
          {activeInterviewStep
            ? activeInterviewStep.question
            : agentState.summary || "El agente ya tiene lo minimo para seguir, pero puedes agregar cualquier dato nuevo y lo incorporare al expediente antes de redactar."}
        </div>
        {activeInterviewStep ? (
          activeInterviewStep.multiline ? (
            <TextArea
              value={interviewDraft}
              onChange={(event) => setInterviewDraft(event.target.value)}
              style={{ minHeight: 110 }}
              placeholder={activeInterviewStep.placeholder}
            />
          ) : (
            <TextInput
              value={interviewDraft}
              onChange={(event) => setInterviewDraft(event.target.value)}
              placeholder={activeInterviewStep.placeholder}
            />
          )
        ) : (
          <div style={{ padding: 14, borderRadius: 14, background: "#FFFFFF", border: `1px solid ${C.border}`, color: C.textMuted, lineHeight: 1.6 }}>
            El agente ya consolidó los hechos principales con tus respuestas y los soportes cargados.
          </div>
        )}
        {!activeInterviewStep && (
          <div style={{ display: "grid", gap: 10 }}>
            <TextArea
              value={interviewDraft}
              onChange={(event) => setInterviewDraft(event.target.value)}
              style={{ minHeight: 100 }}
              placeholder="Agrega cualquier dato nuevo: sintomas actuales, barrera de la EPS, fechas, respuesta recibida o algo importante para el caso."
            />
            {!!regenerationContext.trim() && (
              <div style={{ padding: 12, borderRadius: 14, background: "#F8FAFD", border: `1px solid ${C.border}`, color: C.textMuted, fontSize: 13, lineHeight: 1.6 }}>
                Contexto adicional guardado para la siguiente generación.
              </div>
            )}
          </div>
        )}
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
          <Button variant="secondary" onClick={answerInterviewStep} disabled={!interviewDraft.trim()}>
            {activeInterviewStep ? "Guardar respuesta y seguir" : "Agregar al expediente"}
          </Button>
          <div style={{ color: C.textMuted, fontSize: 13 }}>
            El agente formula las preguntas jurídicamente útiles y se encarga de detectar riesgo actual, barrera de la EPS, urgencia, procedencia y argumentación.
          </div>
        </div>
        {!!agentState?.documents_available?.length && (
          <div style={{ display: "grid", gap: 8 }}>
            <div style={{ fontSize: 12, fontWeight: 800, color: C.textMuted }}>BLOQUE SALUD</div>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              {agentState.documents_available.map((doc) => (
                <Badge key={doc.code} color={doc.recommended_action === item.recommended_action ? C.success : C.textMuted}>
                  {doc.name}
                </Badge>
              ))}
            </div>
          </div>
        )}
        {!!agentState?.ai_owned_tasks?.length && (
          <div style={{ padding: 12, borderRadius: 14, background: "#F8FAFD", border: `1px solid ${C.border}`, color: C.textMuted, fontSize: 13, lineHeight: 1.6 }}>
            El agente se encarga internamente de:
            {" "}
            {agentState.ai_owned_tasks.join(" · ")}.
          </div>
        )}
      </div>

      <div style={{ padding: 18, borderRadius: 18, background: "#FCFDFF", border: `1px solid ${C.border}`, display: "grid", gap: 12 }}>
        <div>
          <div style={{ fontSize: 13, fontWeight: 800, color: C.text }}>Sube tus pruebas</div>
          <div style={{ color: C.textMuted, marginTop: 4 }}>PDF, imagen o Word. Maximo 10MB por archivo.</div>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 10 }}>
            {evidenceHints.map((hint) => <Badge key={hint} color={C.primary}>{hint}</Badge>)}
          </div>
        </div>
        <input id="postpay-evidence-upload" type="file" style={{ display: "none" }} onChange={uploadEvidence} />
        <div style={{ border: `1px dashed ${C.border}`, borderRadius: 18, padding: 24, background: "#F8FAFD", display: "grid", gap: 12, justifyItems: "center" }}>
          <TextInput value={evidenceNote} onChange={(event) => setEvidenceNote(event.target.value)} placeholder="Descripcion del archivo" style={{ maxWidth: 420 }} />
          <Button variant="secondary" onClick={() => document.getElementById("postpay-evidence-upload").click()} icon={Upload}>Arrastra archivos o haz clic</Button>
        </div>
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
          {files.map((file) => <Badge key={file.id} color={C.accent}>{file.original_name}</Badge>)}
        </div>
      </div>

      {!!missingQuestions.length && (
        <div style={{ padding: 14, borderRadius: 16, background: "#F8FAFD", border: `1px solid ${C.border}`, color: C.textMuted, lineHeight: 1.7 }}>
          El agente seguira preguntando hasta cerrar el expediente. No tienes que traducir nada a lenguaje juridico.
        </div>
      )}

      <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
        <div style={{ color: C.textMuted, fontSize: 13 }}>
          {activeInterviewStep
            ? "Primero responde la pregunta actual del agente."
            : agentState.can_generate
              ? `Puedes generar el ${String(item.recommended_action || item.workflow_type || "documento").toLowerCase()} o seguir agregando contexto por el chat.`
              : "El agente sigue activo y te hará falta una respuesta factual más antes de redactar."}
        </div>
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
          <Button variant="secondary" onClick={onSaveFlowDraft} disabled={loading}>
            {loading ? "Guardando..." : "Guardar avance"}
          </Button>
          <Button onClick={onGenerateFromFlow} disabled={generateDisabled} icon={ArrowRight}>
            {loading ? "Generando..." : "Generar mi documento"}
          </Button>
        </div>
      </div>
    </div>
  );
}

function StepShell({ stepNumber, title, subtitle, children, onBack, onNext, nextDisabled = false, nextLabel = "Siguiente" }) {
  return (
    <SessionCard title={`${stepNumber}. ${title}`} subtitle={subtitle}>
      <div style={{ display: "grid", gap: 14 }}>
        {children}
        <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
          {onBack && (
            <Button variant="outline" onClick={onBack} icon={ArrowLeft}>
              Retroceder
            </Button>
          )}
          {onNext && (
            <Button onClick={onNext} disabled={nextDisabled} icon={ArrowRight}>
              {nextLabel}
            </Button>
          )}
        </div>
      </div>
    </SessionCard>
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
    onUpdateCaseIntake,
    onConfirmPayment,
    onCreateWompiSession,
    onGetPayment,
    onReconcilePayment,
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
    ...defaultIntakeFields,
  });
  const [tempFiles, setTempFiles] = useState([]);
  const [preview, setPreview] = useState(null);
  const [draftDetail, setDraftDetail] = useState(null);
  const [postPayForm, setPostPayForm] = useState({
    ...defaultIntakeFields,
    full_name: session.user.name || "",
    document_number: session.user.document_number || "",
    phone: session.user.phone || "",
    address: session.user.address || "",
    copy_email: session.user.email || "",
    prior_claim: "no",
    special_protection: "No aplica",
    prior_tutela: "no",
  });
  const [documentReviews, setDocumentReviews] = useState({});
  const [wizardEntitySuggestions, setWizardEntitySuggestions] = useState([]);
  const [wizardEntityLookupLoading, setWizardEntityLookupLoading] = useState(false);
  const [entitySuggestions, setEntitySuggestions] = useState([]);
  const [entityLookupLoading, setEntityLookupLoading] = useState(false);
  const [manualContact, setManualContact] = useState("");
  const [submissionNote, setSubmissionNote] = useState("");
  const [radicadoManual, setRadicadoManual] = useState("");
  const [radicadoNote, setRadicadoNote] = useState("");
  const [evidenceNote, setEvidenceNote] = useState("");
  const [regenerationReason, setRegenerationReason] = useState("");
  const visibleActionError = actionError || "";
  const [regenerationContext, setRegenerationContext] = useState("");
  const [internalStatus, setInternalStatus] = useState("seguimiento");
  const [internalNote, setInternalNote] = useState("");
  const [wizardStep, setWizardStep] = useState(1);
  const [detailStepOverride, setDetailStepOverride] = useState(null);

  const profileReady = useMemo(
    () => [profile.name, profile.document_number, profile.phone, profile.city, profile.department, profile.address].every((value) => value?.trim()),
    [profile]
  );
  const activeDocumentReview = activeCaseDetail?.case?.id ? documentReviews[activeCaseDetail.case.id] : null;
  const persistedSignature = activeCaseDetail?.case?.submission_summary?.signature || {};
  const activePaymentEntitlements = activeCaseDetail?.case?.submission_summary?.payment_entitlements || {};
  const persistedSignaturePayload = {
    full_name: String(persistedSignature.full_name || "").trim(),
    document_number: String(persistedSignature.document_number || "").trim(),
    city: String(persistedSignature.city || "").trim(),
    date: String(persistedSignature.date || "").trim(),
    accepted: !!persistedSignature.accepted,
  };
  const persistedSignatureReady =
    !!persistedSignature.reviewed_document &&
    !!persistedSignature.accepted &&
    persistedSignaturePayload.full_name.length > 3 &&
    persistedSignaturePayload.document_number.length >= 6 &&
    persistedSignaturePayload.city.length > 2 &&
    persistedSignaturePayload.date.length > 4;

  useEffect(() => {
    if (!activeCaseDetail?.case) return;
    const intakeForm = activeCaseDetail.case.facts?.intake_form || {};
    const hydratedPostPayForm = mergeDetectedFormValues({
      ...defaultIntakeFields,
      full_name: intakeForm.full_name || activeCaseDetail.case.user_name || session.user.name || "",
      document_number: intakeForm.document_number || activeCaseDetail.case.user_document || session.user.document_number || "",
      phone: intakeForm.phone || activeCaseDetail.case.user_phone || session.user.phone || "",
      address: intakeForm.address || activeCaseDetail.case.user_address || session.user.address || "",
      copy_email: intakeForm.copy_email || activeCaseDetail.case.user_email || session.user.email || "",
      case_story: intakeForm.case_story || activeCaseDetail.case.description || "",
      key_dates: intakeForm.key_dates || normalizeMentionedDates(activeCaseDetail.case.facts?.fechas_mencionadas) || "",
      prior_claim: intakeForm.prior_claim || "no",
      special_protection: intakeForm.special_protection || "No aplica",
      prior_tutela: intakeForm.prior_tutela || "no",
    }, activeCaseDetail.case.facts?.autofill_suggestions || {});
    setPostPayForm(hydratedPostPayForm);
    setRegenerationReason(intakeForm.regeneration_reason || "");
    setRegenerationContext(intakeForm.regeneration_additional_context || "");
  }, [activeCaseDetail, session.user]);

  useEffect(() => {
    setDetailStepOverride(null);
  }, [activeCaseDetail?.case?.id]);

  useEffect(() => {
    const query = form.target_entity.trim();
    if (query.length < 2) {
      setWizardEntitySuggestions([]);
      setWizardEntityLookupLoading(false);
      return;
    }

    let cancelled = false;
    const timer = setTimeout(async () => {
      try {
        setWizardEntityLookupLoading(true);
        const response = await api.get("/catalog/entities", { params: { q: query, limit: 8 } });
        if (!cancelled) {
          setWizardEntitySuggestions(response.data || []);
        }
      } catch {
        if (!cancelled) {
          setWizardEntitySuggestions([]);
        }
      } finally {
        if (!cancelled) {
          setWizardEntityLookupLoading(false);
        }
      }
    }, 300);

    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [form.target_entity]);

  useEffect(() => {
    const query = postPayForm.target_entity.trim();
    if (query.length < 2) {
      setEntitySuggestions([]);
      setEntityLookupLoading(false);
      return;
    }

    let cancelled = false;
    const timer = setTimeout(async () => {
      try {
        setEntityLookupLoading(true);
        const response = await api.get("/catalog/entities", { params: { q: query, limit: 8 } });
        if (!cancelled) {
          setEntitySuggestions(response.data || []);
        }
      } catch {
        if (!cancelled) {
          setEntitySuggestions([]);
        }
      } finally {
        if (!cancelled) {
          setEntityLookupLoading(false);
        }
      }
    }, 300);

    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [postPayForm.target_entity]);

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
  if (!isInternal) {
    sideItems.splice(
      0,
      sideItems.length,
      { id: "tramites", label: "Mis expedientes", icon: Briefcase },
      { id: "detalle", label: "Expediente activo", icon: FileText },
      { id: "nuevo", label: "Nuevo tramite", icon: Plus },
      { id: "ayuda", label: "Ayuda", icon: HelpCircle }
    );
  }
  if (isInternal) sideItems.push({ id: "interno", label: "Backoffice", icon: Shield });
  const activeTabIndex = sideItems.findIndex((item) => item.id === activeTab);
  const previousTab = activeTabIndex > 0 ? sideItems[activeTabIndex - 1] : null;
  const nextTab = activeTabIndex >= 0 && activeTabIndex < sideItems.length - 1 ? sideItems[activeTabIndex + 1] : null;

  const selectedPriorActions = priorActionMap[form.category] || [];
  const canOperateActiveCase = !!activeCaseDetail?.case && activeCaseDetail.case.user_id === session.user.id;
  const guidedMissing = useMemo(() => getGuidedIntakeMissing(form, tempFiles), [form, tempFiles]);
  const previewGateIssues = useMemo(() => getPreviewGateIssues(form, tempFiles), [form, tempFiles]);
  const composedDescription = useMemo(() => buildStructuredDescription(form), [form]);
  const analysisReady = !!form.category && guidedMissing.length === 0 && previewGateIssues.length === 0;
  const writingGuide = buildWritingGuide(form.category);
  const wizardAction = normalizeAction(form.recommended_action);
  const showRepresentedPersonCard = form.category === "Salud" || wizardAction === "accion de tutela";
  const isThirdPartyCase = form.acting_capacity !== "nombre_propio";
  const wizardSteps = [
    { id: 1, label: "Perfil", ready: profileReady },
    { id: 2, label: "Análisis", ready: analysisReady || !!preview },
    { id: 3, label: "Preview", ready: !!preview },
    { id: 4, label: "Pago", ready: !!draftDetail },
  ];

  const resetWizard = () => {
    setForm({
      category: "",
      city: session.user.city || "Bogotá",
      department: session.user.department || "Cundinamarca",
      description: "",
      prior_actions: [],
      ...defaultIntakeFields,
    });
    setTempFiles([]);
    setPreview(null);
    setDraftDetail(null);
    setWizardStep(1);
  };

  const uploadTemp = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    const uploaded = await onTempUpload(file);
    setTempFiles((current) => [...current, uploaded]);
    const uploadedName = uploaded?.original_name || uploaded?.name || "";
    if (uploadedName) {
      setForm((current) => {
        if ((current.evidence_summary || "").toLowerCase().includes(uploadedName.toLowerCase())) {
          return current;
        }
        const mergedEvidence = current.evidence_summary?.trim() ? `${current.evidence_summary}, ${uploadedName}` : uploadedName;
        const mergedSupporting = current.supporting_documents?.trim() ? `${current.supporting_documents}, ${uploadedName}` : uploadedName;
        return {
          ...current,
          evidence_summary: mergedEvidence,
          supporting_documents: mergedSupporting,
        };
      });
    }
  };

  const uploadEvidence = async (event) => {
    const file = event.target.files?.[0];
    if (!file || !activeCaseDetail?.case?.id) return;
    await onUploadEvidence(activeCaseDetail.case.id, file, evidenceNote);
    setEvidenceNote("");
  };

  const openCaseAndFocusDetail = async (caseId, scope = "citizen") => {
    await onOpenCase(caseId, scope);
    setActiveTab("detalle");
  };

  const applyEntitySuggestion = (entity) => {
    setPostPayForm((current) => ({
      ...current,
      target_entity: entity.name || current.target_entity,
      target_identifier: entity.nit || current.target_identifier,
      target_address: entity.address || current.target_address,
      legal_representative: entity.legal_representative || current.legal_representative,
      target_pqrs_email: entity.pqrs_emails?.[0] || current.target_pqrs_email,
      target_notification_email: entity.notification_emails?.[0] || current.target_notification_email,
      target_phone: entity.phone || entity.phones?.[0] || current.target_phone,
      target_website: entity.website || current.target_website,
      target_superintendence: entity.superintendence || current.target_superintendence,
    }));
    setEntitySuggestions([]);
  };

  const applyWizardEntitySuggestion = (entity) => {
    setForm((current) => ({
      ...current,
      target_entity: entity.name || current.target_entity,
      case_reference: current.case_reference || entity.nit || "",
    }));
    setWizardEntitySuggestions([]);
  };

  const runWizardPreview = async () => {
    const previewResult = await onPreview({
      ...form,
      description: composedDescription,
      form_data: { ...form },
      attachment_ids: tempFiles.map((item) => item.id),
    });
    setForm((current) => mergeDetectedFormValues(current, previewResult?.facts?.intake_form || previewResult?.facts?.autofill_suggestions || {}));
    setPreview(previewResult);
    setWizardStep(3);
    return previewResult;
  };

  const jumpToNextStage = () => {
    const target = document.getElementById("case-next-stage");
    if (target) {
      target.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  };

  const content = {
    inicio: (
      <div style={{ display: "grid", gap: 24 }}>
        <div style={{ background: "linear-gradient(135deg, #08172E 0%, #10264A 100%)", borderRadius: 24, padding: "40px 34px", color: "#fff" }}>
          <Badge color={C.accent}>Panel del cliente</Badge>
          <h2 style={{ fontSize: 42, margin: "18px 0 10px", fontWeight: 800, fontFamily: "'Playfair Display', serif" }}>Todo tu caso, en un solo lugar.</h2>
          <p style={{ maxWidth: 640, color: "rgba(255,255,255,0.74)", lineHeight: 1.75 }}>
            Desde aqui puedes crear un tramite, pagar el documento, revisar si ya fue radicado y entender cual es el siguiente paso sin salirte del flujo.
          </p>
          <div style={{ display: "grid", gridTemplateColumns: "1.05fr 0.95fr", gap: 18, marginTop: 24 }}>
            <div style={{ padding: 22, borderRadius: 22, background: "rgba(255,255,255,0.06)", border: "1px solid rgba(255,255,255,0.12)" }}>
              <div style={{ fontSize: 13, fontWeight: 800, color: "#7DD3FC", letterSpacing: "0.08em" }}>QUE PUEDES HACER AHORA</div>
              <div style={{ display: "grid", gap: 12, marginTop: 18, color: "rgba(255,255,255,0.88)", lineHeight: 1.7 }}>
                <div>1. Completar tus datos personales una sola vez.</div>
                <div>2. Contarnos tu caso con preguntas guiadas y generar el analisis gratis.</div>
                <div>3. Pagar solo si decides activar el documento o la radicacion.</div>
              </div>
              <div style={{ display: "flex", gap: 12, flexWrap: "wrap", marginTop: 24 }}>
                <Button onClick={() => setActiveTab("nuevo")}>Crear nuevo tramite</Button>
                <Button variant="ghost" onClick={() => setActiveTab("tramites")}>Ver mis expedientes</Button>
              </div>
            </div>
            <div style={{ padding: 22, borderRadius: 22, background: "rgba(255,255,255,0.06)", border: "1px solid rgba(255,255,255,0.12)" }}>
              <div style={{ fontSize: 13, fontWeight: 800, color: "#7DD3FC", letterSpacing: "0.08em" }}>PROMESA DEL SERVICIO</div>
              <div style={{ marginTop: 20, fontSize: 28, lineHeight: 1.35, fontWeight: 800 }}>
                Analisis gratis y radicacion en menos de 5 minutos cuando el canal lo permite.
              </div>
            </div>
          </div>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 20 }}>
          {stats.map((item) => (
            <div key={item.label} className="glass-card" style={{ padding: 26 }}>
              <div style={{ color: C.textMuted, fontWeight: 700 }}>{item.label}</div>
              <div style={{ marginTop: 18, fontSize: 44, lineHeight: 1, fontWeight: 800, color: C.text }}>{item.value}</div>
            </div>
          ))}
        </div>
        <div className="glass-card" style={{ padding: 24, color: C.textMuted }}>
          Abre un expediente para ver timeline, archivos y trazabilidad.
        </div>
      </div>
    ),
    nuevo: (
      <div style={{ display: "grid", gap: 22 }}>
        <div className="glass-card" style={{ padding: 24 }}>
          <Badge color={C.primary}>Nuevo tramite guiado</Badge>
          <h2 style={{ marginTop: 12, fontSize: 34, lineHeight: 1.08, color: C.text, fontFamily: "'Playfair Display', serif" }}>
            Dinos que paso y te guiamos paso a paso.
          </h2>
          <p style={{ marginTop: 10, color: C.textMuted, maxWidth: 760 }}>
            Primero completas tus datos personales. Luego nos cuentas el caso con preguntas simples. Despues ves el analisis gratis, confirmas el expediente y solo al final decides si pagas el documento.
          </p>
        </div>
        {(form.category === "Salud" || normalizeAction(form.recommended_action) === "accion de tutela") && (
          <div className="glass-card" style={{ padding: 18, background: "#EEF4FF", border: "1px solid #BFDBFE" }}>
            <div style={{ fontSize: 12, fontWeight: 800, letterSpacing: 0.4, color: C.primary }}>SI EL CASO ES DE TU HIJO O DE OTRA PERSONA</div>
            <div style={{ marginTop: 8, color: C.text, lineHeight: 1.6 }}>
              Mas abajo, en <strong>Preguntas finas para accion de tutela</strong>, cambia <strong>Calidad en que actuas</strong> a
              {" "}
              <strong>Madre o padre de menor de edad</strong>, <strong>acudiente</strong> o <strong>agente oficioso</strong>.
              Ahi mismo se abren los datos del menor o del representado.
            </div>
          </div>
        )}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12 }}>
          {wizardSteps.map((item) => (
            <div
              key={item.id}
              style={{
                padding: 16,
                borderRadius: 18,
                border: `1px solid ${wizardStep === item.id ? C.primary : C.border}`,
                background: wizardStep === item.id ? "#EFF6FF" : C.card,
                display: "grid",
                gap: 6,
              }}
            >
              <div style={{ fontSize: 12, color: C.textMuted, fontWeight: 800 }}>{`PASO ${item.id}`}</div>
              <div style={{ fontWeight: 800, color: C.text }}>{item.label}</div>
              <div style={{ color: item.ready ? C.success : C.textMuted, fontSize: 13 }}>{item.ready ? "Listo" : "Pendiente"}</div>
            </div>
          ))}
        </div>
        {wizardStep === 1 && (
          <StepShell
            stepNumber={1}
            title="Tus datos personales"
            subtitle="Se usan en la tutela, la carta, el derecho de peticion y el correo de radicacion."
            onNext={() => setWizardStep(2)}
            nextDisabled={!profileReady}
            nextLabel="Continuar al analisis"
          >
            <div className="glass-card" style={{ padding: 18, background: "#F8FAFD", display: "grid", gap: 8 }}>
              <div style={{ fontWeight: 800, color: C.text }}>Que debes llenar aqui</div>
              <div style={{ color: C.textMuted }}>Tu nombre, cedula, celular, correo y direccion. Estos datos se insertan automaticamente en el documento final.</div>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 16 }}>
              <Field label="Correo electronico">
                <TextInput value={session.user.email || ""} disabled />
              </Field>
              {[
                ["Nombre completo", "name"],
                ["Cedula", "document_number"],
                ["Celular", "phone"],
                ["Ciudad", "city"],
                ["Departamento", "department"],
                ["Direccion", "address"],
              ].map(([label, key]) => (
                <Field key={key} label={label}>
                  <TextInput value={profile[key]} onChange={(event) => setProfile((current) => ({ ...current, [key]: event.target.value }))} />
                </Field>
              ))}
            </div>
            <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
              <Button onClick={() => onSaveProfile(profile)}>Guardar datos personales</Button>
              <Badge color={profileReady ? C.success : C.warning}>{profileReady ? "Perfil completo" : "Faltan datos obligatorios"}</Badge>
            </div>
          </StepShell>
        )}
        {wizardStep === 2 && (
          <StepShell
            stepNumber={2}
            title="Cuentanos tu problema"
            subtitle="Usa tus palabras. La plataforma te ayuda con preguntas guiadas."
            onBack={() => setWizardStep(1)}
            onNext={async () => {
              if (preview) {
                setWizardStep(3);
                return;
              }
              await runWizardPreview();
            }}
            nextDisabled={!analysisReady || loading}
            nextLabel={preview ? "Continuar al análisis" : "Generar análisis inicial"}
          >
            <div className="glass-card" style={{ padding: 18, background: "#F8FAFD", display: "grid", gap: 10 }}>
              <div style={{ fontWeight: 800, color: C.text }}>Procedimiento simple</div>
              <div style={{ color: C.textMuted }}>1. Elige el tipo de problema. 2. Explica que paso. 3. Responde solo las preguntas que aparezcan. 4. Genera el analisis gratis.</div>
            </div>
            {showRepresentedPersonCard && (
              <div className="glass-card" style={{ padding: 18, background: "#FFF7ED", display: "grid", gap: 12 }}>
                <div style={{ fontSize: 12, fontWeight: 800, color: C.textMuted }}>QUIEN ES LA PERSONA AFECTADA</div>
                <div style={{ color: C.text, fontWeight: 700 }}>
                  Antes de seguir, confirma si este trámite es por ti o si lo presentas por un hijo, familiar o tercero.
                </div>
                <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
                  <button
                    type="button"
                    onClick={() =>
                      setForm((current) => ({
                        ...current,
                        acting_capacity: "nombre_propio",
                        represented_person_name: "",
                        represented_person_document: "",
                        represented_person_age: "",
                        represented_person_condition: "",
                      }))
                    }
                    style={{
                      border: isThirdPartyCase ? `1px solid ${C.border}` : `2px solid ${C.primary}`,
                      background: isThirdPartyCase ? "#fff" : "#EFF6FF",
                      color: C.text,
                      borderRadius: 999,
                      padding: "10px 14px",
                      cursor: "pointer",
                      fontWeight: 700,
                    }}
                  >
                    El trámite es por mí
                  </button>
                  <button
                    type="button"
                    onClick={() => setForm((current) => ({ ...current, acting_capacity: current.acting_capacity === "nombre_propio" ? "madre_padre_menor" : current.acting_capacity }))}
                    style={{
                      border: isThirdPartyCase ? `2px solid ${C.primary}` : `1px solid ${C.border}`,
                      background: isThirdPartyCase ? "#EFF6FF" : "#fff",
                      color: C.text,
                      borderRadius: 999,
                      padding: "10px 14px",
                      cursor: "pointer",
                      fontWeight: 700,
                    }}
                  >
                    Lo presento por otra persona
                  </button>
                </div>
                {isThirdPartyCase && (
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 16 }}>
                    <Field label="Calidad en que presentas el caso">
                      <select
                        value={form.acting_capacity}
                        onChange={(event) => setForm((current) => ({ ...current, acting_capacity: event.target.value }))}
                        style={{ width: "100%", padding: "14px 16px", borderRadius: 12, border: `1px solid ${C.border}`, background: "#fff", color: C.text }}
                      >
                        <option value="madre_padre_menor">Madre o padre de menor</option>
                        <option value="acudiente">Acudiente o cuidador</option>
                        <option value="agente_oficioso">Agente oficioso</option>
                        <option value="representante_legal">Representante legal</option>
                      </select>
                    </Field>
                    <Field label="Nombre del menor o representado">
                      <TextInput value={form.represented_person_name} onChange={(event) => setForm((current) => ({ ...current, represented_person_name: event.target.value }))} placeholder="Ej: Jeronimo Perez Lopez" />
                    </Field>
                    <Field label="Documento del menor o representado">
                      <TextInput value={form.represented_person_document} onChange={(event) => setForm((current) => ({ ...current, represented_person_document: event.target.value }))} placeholder="Ej: Registro civil, TI o NUIP" />
                    </Field>
                    <Field label="Edad o fecha de nacimiento">
                      <TextInput value={form.represented_person_age} onChange={(event) => setForm((current) => ({ ...current, represented_person_age: event.target.value }))} placeholder="Ej: 10 años / 12 de abril de 2016" />
                    </Field>
                    <Field label="Condicion relevante del menor o paciente">
                      <TextInput value={form.represented_person_condition} onChange={(event) => setForm((current) => ({ ...current, represented_person_condition: event.target.value }))} placeholder="Ej: menor con anemia de celulas falciformes tipo SS" />
                    </Field>
                  </div>
                )}
                <div style={{ color: C.textMuted, fontSize: 13 }}>
                  Si el trámite es por ti, no mostraremos datos de tercero. Si es por otra persona, el agente seguirá el interrogatorio con esos datos.
                </div>
              </div>
            )}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12 }}>
              {ACTIVE_CASE_CATEGORIES.map((item) => (
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
            <div style={{ color: C.textMuted, fontSize: 13 }}>
              Por ahora solo estamos habilitando casos de salud mientras terminamos de estabilizar los demas bloques.
            </div>
            <div className="glass-card" style={{ padding: 18, background: "#FCFDFF", display: "grid", gap: 10 }}>
              <div style={{ fontSize: 12, fontWeight: 800, color: C.textMuted }}>{writingGuide.title.toUpperCase()}</div>
              <div style={{ display: "grid", gap: 6 }}>
                {writingGuide.bullets.map((bullet) => (
                  <div key={bullet} style={{ color: C.textMuted }}>{`- ${bullet}`}</div>
                ))}
              </div>
            </div>
            <Field label={form.category === "Salud" ? "Primer relato para que el agente arranque" : "Explica el caso con detalle"}>
              <TextArea
                value={form.description}
                onChange={(event) => setForm((current) => ({ ...current, description: event.target.value }))}
                placeholder={
                  form.category === "Salud"
                    ? "Escribe en tus palabras que está pasando. El agente seguirá preguntando una cosa a la vez, incluso diagnóstico, barrera de la EPS, urgencia y gestión previa."
                    : "Cuenta que paso, desde cuando, con quien, que pediste antes, que pruebas tienes y que solucion necesitas."
                }
              />
            </Field>
            <GuidedIntakeFields
              form={form}
              setForm={setForm}
              missingFields={guidedMissing}
              entityLookupLoading={wizardEntityLookupLoading}
              entitySuggestions={wizardEntitySuggestions}
              onApplyEntitySuggestion={applyWizardEntitySuggestion}
            />
            <PreviewGateCard missing={guidedMissing} issues={previewGateIssues} />
            <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 16 }}>
              <Field label="Ciudad"><TextInput value={form.city} onChange={(event) => setForm((current) => ({ ...current, city: event.target.value }))} /></Field>
              <Field label="Departamento"><TextInput value={form.department} onChange={(event) => setForm((current) => ({ ...current, department: event.target.value }))} /></Field>
            </div>
            {!!selectedPriorActions.length && (
              <div style={{ display: "grid", gap: 8 }}>
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
            <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
              <input id="wizard-upload" type="file" style={{ display: "none" }} onChange={uploadTemp} />
              <Button variant="secondary" onClick={() => document.getElementById("wizard-upload").click()} icon={Upload}>Subir anexo</Button>
              {tempFiles.map((item) => <Badge key={item.id} color={C.accent}>{item.original_name}</Badge>)}
            </div>
            {visibleActionError && (
                <div style={{ color: C.danger, background: "#FEF2F2", border: "1px solid #FECACA", padding: 14, borderRadius: 14 }}>
                {visibleActionError}
                </div>
            )}
            <div style={{ color: C.textMuted, fontSize: 13, lineHeight: 1.6 }}>
              El sistema usa tus datos del paso 1 y tu relato del paso 2 para construir el analisis. Las pruebas en esta etapa son opcionales: si las tienes, ayudan; si no, el analisis inicial igual debe poder generarse.
            </div>
          </StepShell>
        )}
        {wizardStep === 3 && (() => {
          const previewForm = mergeDetectedFormValues(form, preview?.facts?.intake_form || preview?.facts?.autofill_suggestions || {});
          const intakeReview = preview?.facts?.intake_review || null;
          const documentRuleReview = preview?.facts?.document_rule_review || null;
          const hasBlockingIssues = !!(intakeReview?.blocking_issues || []).length;
          const hasDocumentRuleBlockers = !!(documentRuleReview?.blocking_issues || []).filter((issue) => !isAiOwnedReviewIssue(issue)).length;
          const actionSpecificMissing = getActionSpecificMissing(preview?.recommended_action, previewForm);
          const actionSpecificIssues = getActionSpecificIssues(preview?.recommended_action, previewForm);
          const hasActionSpecificBlockers = actionSpecificMissing.length > 0 || actionSpecificIssues.length > 0;
          const rightsPreview = buildPreviewRights(preview);
          const viability = getViabilityConfig(preview?.dx_result || {});
          const routeSteps = buildRouteSteps(preview);
          const previewPrimaryTarget = preview?.routing?.primary_target || {};
          const previewRoutingChannel = getRoutingChannelLabel(preview?.routing?.channel || previewPrimaryTarget?.channel);
          const previewRoutingContact = previewPrimaryTarget?.contact || "Canal por confirmar";
          const backendPendingQuestions = preview?.pending_questions || preview?.facts?.pending_questions || [];
          const autofillSuggestions = preview?.facts?.autofill_suggestions || {};
          const previewFixes = summarizePreviewFixes({
            intakeReview,
            documentRuleReview,
            actionSpecificMissing,
            actionSpecificIssues,
            previewWarnings: preview?.warnings || [],
            pendingQuestions: backendPendingQuestions,
          });
          const paidLocks = [
            "Normas aplicables al caso",
            "Jurisprudencia especifica",
            "Argumentacion juridica completa",
            "Documento legal listo para radicar",
            "Paso a paso de pruebas y soportes",
            "Radicacion y seguimiento",
          ];

          return (
            <StepShell
              stepNumber={3}
              title="Diagnostico gratis de tu caso"
              subtitle="Aqui ves el derecho detectado, la ruta sugerida y la viabilidad. La receta completa se desbloquea al pagar."
              onBack={() => setWizardStep(2)}
            >
              {!preview ? (
                <div style={{ color: "#92400E", background: "#FFFBEB", border: "1px solid #FDE68A", padding: 14, borderRadius: 14 }}>
                  Primero genera el preview desde el paso anterior para ver la recomendacion, el destino sugerido y las advertencias.
                </div>
              ) : (
                <>
                  <div style={{ display: "grid", gridTemplateColumns: "1.15fr 0.95fr", gap: 18 }}>
                    <div className="glass-card" style={{ padding: 22, background: "#131722", border: "1px solid #2B3345", color: "#F8FAFC" }}>
                      <div style={{ fontSize: 12, fontWeight: 800, letterSpacing: 0.4, color: "#94A3B8" }}>ANALISIS DE TU CASO</div>
                      <div style={{ display: "grid", gap: 12, marginTop: 14 }}>
                        {rightsPreview[0] && (
                          <div style={{ padding: 16, borderRadius: 16, background: "#6B1F1A" }}>
                            <div style={{ fontSize: 13, fontWeight: 800, color: "#FCA5A5" }}>Derecho vulnerado detectado</div>
                            <div style={{ marginTop: 6, fontSize: 18, fontWeight: 800 }}>{rightsPreview[0].title}</div>
                            <div style={{ marginTop: 6, color: "#FDE2E2" }}>{rightsPreview[0].article}</div>
                          </div>
                        )}
                        {rightsPreview[1] && (
                          <div style={{ padding: 16, borderRadius: 16, background: "#5B480D" }}>
                            <div style={{ fontSize: 13, fontWeight: 800, color: "#FCD34D" }}>Tambien aplica</div>
                            <div style={{ marginTop: 6, fontSize: 18, fontWeight: 800 }}>{rightsPreview[1].title}</div>
                            <div style={{ marginTop: 6, color: "#FEF3C7" }}>{rightsPreview[1].article}</div>
                          </div>
                        )}
                        <div style={{ padding: 16, borderRadius: 16, background: "#1E3A6E" }}>
                          <div style={{ fontSize: 13, fontWeight: 800, color: "#93C5FD" }}>Accion recomendada</div>
                          <div style={{ marginTop: 6, fontSize: 18, fontWeight: 800 }}>{preview.recommended_action}</div>
                          <div style={{ marginTop: 8, color: "#DBEAFE", lineHeight: 1.6 }}>
                            {buildCommercialDiagnosisCopy(preview.recommended_action, form.category)}
                          </div>
                        </div>
                      </div>

                      <div style={{ marginTop: 18 }}>
                        <div style={{ fontWeight: 800 }}>Viabilidad del caso</div>
                        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 6, marginTop: 10 }}>
                          {viability.segments.map((active, index) => (
                            <div
                              key={`${viability.label}-${index}`}
                              style={{
                                height: 10,
                                borderRadius: 999,
                                background: active ? viability.color : "#334155",
                              }}
                            />
                          ))}
                        </div>
                        <div style={{ marginTop: 10, color: viability.color, fontWeight: 800 }}>
                          {viability.label} — {viability.note}
                        </div>
                      </div>

                      <div style={{ marginTop: 18, paddingTop: 18, borderTop: "1px solid #334155" }}>
                        <div style={{ fontWeight: 800 }}>Ruta legal sugerida</div>
                        <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginTop: 12 }}>
                          {routeSteps.map((step, index) => (
                            <React.Fragment key={`${step}-${index}`}>
                              <div
                                style={{
                                  padding: "8px 12px",
                                  borderRadius: 999,
                                  background: index === 0 ? "#1F2937" : "#202938",
                                  border: "1px solid #334155",
                                  fontWeight: 700,
                                }}
                              >
                                {index + 1}. {step}
                              </div>
                              {index < routeSteps.length - 1 && <div style={{ alignSelf: "center", color: "#94A3B8" }}>→</div>}
                            </React.Fragment>
                          ))}
                        </div>
                      </div>

                      <div style={{ marginTop: 18, paddingTop: 18, borderTop: "1px solid #334155", color: "#94A3B8", lineHeight: 1.6 }}>
                        Gratis: sabes qué derecho aparece afectado, qué camino seguir y qué tan viable se ve el caso.
                      </div>
                    </div>

                    <div className="glass-card" style={{ padding: 22, background: "#1E1E1B", border: "1px solid #3F3F46", color: "#F8FAFC" }}>
                      <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
                        <div>
                          <div style={{ fontSize: 12, fontWeight: 800, letterSpacing: 0.4, color: "#FCA5A5" }}>BLOQUEADO HASTA PAGAR</div>
                          <div style={{ marginTop: 8, fontWeight: 800 }}>La receta juridica completa</div>
                        </div>
                        <div style={{ color: "#FBBF24", fontWeight: 800 }}>Candado premium</div>
                      </div>
                      <div style={{ display: "grid", gap: 10, marginTop: 16 }}>
                        {paidLocks.map((item) => (
                          <div
                            key={item}
                            style={{
                              padding: 14,
                              borderRadius: 14,
                              background: "#27272A",
                              border: "1px solid #3F3F46",
                              display: "flex",
                              justifyContent: "space-between",
                              gap: 12,
                              alignItems: "center",
                            }}
                          >
                            <span style={{ color: "#D4D4D8" }}>{item}</span>
                            <span style={{ color: "#FBBF24", fontSize: 18 }}>🔒</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>

                  <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 16 }}>
                    <div className="glass-card" style={{ padding: 18, background: "#F0FDF4", border: "1px solid #86EFAC" }}>
                      <div style={{ fontSize: 12, fontWeight: 800, letterSpacing: 0.4, color: "#166534" }}>GRATIS: EL DIAGNOSTICO</div>
                      <div style={{ marginTop: 8, color: "#166534", fontWeight: 700, lineHeight: 1.6 }}>
                        Qué derecho aparece comprometido y qué camino tomar.
                      </div>
                    </div>
                    <div className="glass-card" style={{ padding: 18, background: "#FFFBEB", border: "1px solid #FDE68A" }}>
                      <div style={{ fontSize: 12, fontWeight: 800, letterSpacing: 0.4, color: "#92400E" }}>PAGO: LA RECETA</div>
                      <div style={{ marginTop: 8, color: "#92400E", fontWeight: 700, lineHeight: 1.6 }}>
                        Normas, jurisprudencia, argumentacion y estructura completa.
                      </div>
                    </div>
                    <div className="glass-card" style={{ padding: 18, background: "#FEF2F2", border: "1px solid #FECACA" }}>
                      <div style={{ fontSize: 12, fontWeight: 800, letterSpacing: 0.4, color: "#B91C1C" }}>NUNCA GRATIS: EL DOCUMENTO</div>
                      <div style={{ marginTop: 8, color: "#B91C1C", fontWeight: 700, lineHeight: 1.6 }}>
                        El texto listo para radicar y la radicacion no se entregan sin pago.
                      </div>
                    </div>
                  </div>

                  <div className="glass-card" style={{ padding: 18, background: "#F8FAFD", border: `1px solid ${C.border}` }}>
                    <div style={{ fontSize: 12, fontWeight: 800, letterSpacing: 0.4, color: C.textMuted }}>QUE SIGUE</div>
                    <div style={{ marginTop: 8, color: C.text, fontWeight: 800 }}>
                      Si este diagnostico se ve correcto, pulsa <span style={{ color: C.primary }}>Guardar expediente y abrir pago</span>.
                    </div>
                    <div style={{ marginTop: 10, color: C.textMuted, fontSize: 13, lineHeight: 1.6 }}>
                      Aun no ves el documento final porque este paso solo entrega el diagnostico gratis. Despues del pago se activa la redaccion completa.
                    </div>
                  </div>

                  <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 16 }}>
                    <div className="glass-card" style={{ padding: 18 }}>
                      <strong style={{ color: C.text }}>Destino sugerido</strong>
                      <div style={{ color: C.textMuted, marginTop: 12 }}>{preview.routing?.primary_target?.name || "Sin destino automatico"}</div>
                      <div style={{ color: C.textMuted, marginTop: 6 }}>{preview.routing?.subject || "Sin asunto sugerido"}</div>
                    </div>
                    <div className="glass-card" style={{ padding: 18 }}>
                      <strong style={{ color: C.text }}>Via previa detectada</strong>
                      <div style={{ display: "grid", gap: 8, marginTop: 12 }}>
                        {preview.prerequisites.length ? preview.prerequisites.map((item) => (
                          <Badge key={item.id} color={item.completed ? C.success : C.warning}>{item.completed ? "Cumplido" : "Pendiente"} - {item.label}</Badge>
                        )) : <span style={{ color: C.textMuted }}>Sin via previa obligatoria detectada.</span>}
                      </div>
                    </div>
                  </div>

                  <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 16 }}>
                    <div className="glass-card" style={{ padding: 18, background: "#FCFDFF", border: `1px solid ${C.border}` }}>
                      <div style={{ fontSize: 12, fontWeight: 800, letterSpacing: 0.4, color: C.textMuted }}>CANAL DETECTADO</div>
                      <div style={{ marginTop: 8, color: C.text, fontWeight: 800 }}>{previewRoutingChannel}</div>
                      <div style={{ marginTop: 8, color: C.textMuted, lineHeight: 1.5 }}>{previewRoutingContact}</div>
                    </div>
                    <div className="glass-card" style={{ padding: 18, background: preview?.routing?.automatable ? "#EEF4FF" : "#FFF7ED", border: preview?.routing?.automatable ? "1px solid #BFDBFE" : "1px solid #FED7AA" }}>
                      <div style={{ fontSize: 12, fontWeight: 800, letterSpacing: 0.4, color: preview?.routing?.automatable ? C.primary : "#C2410C" }}>RADICACION</div>
                      <div style={{ marginTop: 8, color: C.text, fontWeight: 800 }}>
                        {preview?.routing?.automatable ? "Lista para radicacion digital" : "Puede requerir gestion manual"}
                      </div>
                      <div style={{ marginTop: 8, color: C.textMuted, lineHeight: 1.5 }}>
                        {preview?.routing?.automatable ? "La app ya encontro un canal operativo para avanzar sin pedirte mas datos de contacto." : "Todavia puede hacer falta confirmar el canal exacto antes del envio final."}
                      </div>
                    </div>
                    <div className="glass-card" style={{ padding: 18, background: "#F8FAFD", border: `1px solid ${C.border}` }}>
                      <div style={{ fontSize: 12, fontWeight: 800, letterSpacing: 0.4, color: C.textMuted }}>PLAN DE FALLBACK</div>
                      <div style={{ marginTop: 8, color: C.text, fontWeight: 800 }}>
                        {preview?.routing?.fallback?.mode === "none" ? "Sin bloqueo operativo" : "Hay fallback preparado"}
                      </div>
                      <div style={{ marginTop: 8, color: C.textMuted, lineHeight: 1.5 }}>
                        {(preview?.routing?.fallback?.instructions || [])[0] || "Si el canal principal falla, la app conserva una ruta operativa alternativa."}
                      </div>
                    </div>
                  </div>

                  {!!backendPendingQuestions.length && (
                    <div className="glass-card" style={{ padding: 18, background: "#EEF4FF", border: "1px solid #BFDBFE" }}>
                      <div style={{ fontSize: 12, fontWeight: 800, letterSpacing: 0.4, color: C.primary }}>PREGUNTAS CLAVE QUE FALTAN</div>
                      <div style={{ marginTop: 8, color: C.text, fontWeight: 800 }}>
                        Antes del documento final conviene completar estas respuestas:
                      </div>
                      <div style={{ display: "grid", gap: 8, marginTop: 12 }}>
                        {backendPendingQuestions.slice(0, 5).map((question) => (
                          <div key={question.id || question.question} style={{ color: C.text }}>{`• ${question.question}`}</div>
                        ))}
                      </div>
                    </div>
                  )}

                  {!!Object.keys(autofillSuggestions).length && (
                    <div className="glass-card" style={{ padding: 18, background: "#F0FDF4", border: "1px solid #86EFAC" }}>
                      <div style={{ fontSize: 12, fontWeight: 800, letterSpacing: 0.4, color: "#166534" }}>DATOS DETECTADOS EN TUS ANEXOS</div>
                      <div style={{ marginTop: 8, color: C.text, fontWeight: 800 }}>
                        La app ya detecto estos datos para no hacerte repetir informacion:
                      </div>
                <div style={{ display: "grid", gap: 8, marginTop: 12 }}>
                  {Object.entries(autofillSuggestions).slice(0, 5).map(([key, value]) => (
                    <div key={key} style={{ color: "#166534" }}>{`• ${formatAutofillEntry([key, value])}`}</div>
                  ))}
                </div>
              </div>
                  )}

                  {!!previewFixes.length && (
                    <div className="glass-card" style={{ padding: 18, background: "#FFFBEB", border: "1px solid #FDE68A" }}>
                      <div style={{ fontSize: 12, fontWeight: 800, letterSpacing: 0.4, color: "#92400E" }}>ANTES DEL DOCUMENTO FINAL</div>
                      <div style={{ marginTop: 8, color: C.text, fontWeight: 800 }}>
                        Conviene reforzar estos puntos para que el documento salga mas completo:
                      </div>
                      <div style={{ display: "grid", gap: 8, marginTop: 12 }}>
                        {previewFixes.map((item) => (
                          <div key={item} style={{ color: "#92400E" }}>• {item}</div>
                        ))}
                      </div>
                    </div>
                  )}

                  <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
                    <Button
                      onClick={async () => {
                        const detail = await onCreateCase({
                          ...previewForm,
                          description: composedDescription,
                          form_data: { ...previewForm },
                          attachment_ids: tempFiles.map((item) => item.id),
                        });
                        setDraftDetail(detail);
                        setWizardStep(4);
                      }}
                      disabled={!profileReady || hasBlockingIssues || hasActionSpecificBlockers || hasDocumentRuleBlockers}
                    >
                      Guardar expediente y abrir pago
                    </Button>
                    <Button variant="outline" onClick={() => setWizardStep(2)}>Corregir respuestas</Button>
                    <Button variant="outline" onClick={resetWizard}>Reiniciar</Button>
                  </div>
                </>
              )}
            </StepShell>
          );
        })()}
        {wizardStep === 4 && (
          <div style={{ display: "grid", gap: 16 }}>
            <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
              <Button variant="outline" onClick={() => setWizardStep(3)} icon={ArrowLeft}>
                Volver al preview
              </Button>
              {draftDetail && (
                <Button variant="ghost" onClick={() => setActiveTab("detalle")} icon={ArrowRight}>
                  Ir al detalle del expediente
                </Button>
              )}
            </div>
            {draftDetail ? (
              <PaymentCard
                title="4. Pago real y activacion del documento"
                caseItem={draftDetail.case}
                catalog={catalog}
                onCreateWompiSession={onCreateWompiSession}
                onGetPayment={onGetPayment}
                onReconcilePayment={onReconcilePayment}
                onRefreshCase={onRefreshCase}
                loading={loading}
              />
            ) : (
              <div className="glass-card" style={{ padding: 24, color: C.textMuted }}>
                Guarda primero el expediente en el paso 3 para habilitar el pago y la activacion del documento.
              </div>
            )}
          </div>
        )}
      </div>
    ),
    tramites: cases.length ? (
      <div style={{ display: "grid", gap: 16 }}>
        <div className="glass-card" style={{ padding: 24 }}>
          <Badge color={C.primary}>Mis expedientes</Badge>
          <h2 style={{ marginTop: 12, fontSize: 34, lineHeight: 1.08, color: C.text, fontFamily: "'Playfair Display', serif" }}>
            Aquí ves qué ya está listo y qué falta en cada caso.
          </h2>
          <p style={{ marginTop: 10, color: C.textMuted, maxWidth: 700 }}>
            Cada tarjeta resume el estado del pago, si el canal es automático o manual y te deja volver al expediente sin perder contexto.
          </p>
        </div>
        {cases.map((item) => (
          <div key={item.id} className="glass-card" style={{ padding: 22, display: "grid", gap: 14 }}>
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
            <div style={{ padding: 14, borderRadius: 16, background: "#F8FAFD", border: `1px solid ${C.border}` }}>
              <div style={{ fontSize: 12, color: C.textMuted, fontWeight: 800 }}>SIGUIENTE MOVIMIENTO</div>
              <div style={{ marginTop: 8, color: C.text, fontWeight: 700 }}>
                {item.payment_status !== "pagado"
                  ? "Completar el pago para activar el documento."
                  : item.status === "radicado"
                    ? "Revisar el radicado y los pasos posteriores del caso."
                    : item.routing?.automatable
                      ? "Abrir el expediente y ejecutar la radicación automática."
                      : "Abrir el expediente y completar el canal manual."}
              </div>
            </div>
            <div style={{ display: "flex", gap: 10 }}>
              <Button variant="secondary" onClick={() => openCaseAndFocusDetail(item.id)}>Abrir expediente</Button>
              {item.generated_document && <Button variant="outline" onClick={() => setDocumentCase(item)}>Ver documento</Button>}
            </div>
          </div>
        ))}
      </div>
    ) : <div className="glass-card" style={{ padding: 30, color: C.textMuted }}>Todavía no tienes expedientes guardados. Empieza con el análisis gratis y desde ahí creamos el primer caso.</div>,
    detalle: (
      <div style={{ display: "grid", gap: 18 }}>
        <DetailPanel detail={activeCaseDetail} onViewDocument={setDocumentCase} onGoNextStage={jumpToNextStage} />
        {activeCaseDetail && canOperateActiveCase && (
          <>
            <PaymentCard
              title="Pago y activación del documento"
              caseItem={activeCaseDetail.case}
              catalog={catalog}
              onCreateWompiSession={onCreateWompiSession}
              onGetPayment={onGetPayment}
              onReconcilePayment={onReconcilePayment}
              onRefreshCase={onRefreshCase}
              loading={loading}
            />
            {activeCaseDetail.case.payment_status === "pagado" && !activeCaseDetail.case.generated_document && (
              <SessionCard title="Pago confirmado" subtitle="Tu pago ya fue aprobado. El siguiente paso es generar el documento final.">
                <div style={{ display: "grid", gap: 14 }}>
                  <div className="glass-card" style={{ padding: 18, background: "#ECFDF5", border: "1px solid #86EFAC", color: "#166534" }}>
                    Gracias. Tu expediente ya quedó activado y listo para generar el documento jurídico final.
                  </div>
                  <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
                    <Button
                      onClick={() => document.getElementById("case-next-stage")?.scrollIntoView({ behavior: "smooth", block: "start" })}
                      icon={ArrowRight}
                    >
                      Ir a generar documento
                    </Button>
                  </div>
                </div>
              </SessionCard>
            )}
            <div id="case-next-stage">
              <SessionCard title="Acciones operativas" subtitle="Solo ves las acciones del siguiente paso: documento, envio y radicado.">
                <div style={{ display: "grid", gap: 18 }}>
                  <div style={{ padding: 18, borderRadius: 18, border: `1px solid ${C.border}`, background: "#FCFDFF", display: "grid", gap: 12 }}>
                    <div style={{ fontSize: 12, fontWeight: 800, letterSpacing: "0.08em", color: C.textMuted }}>DOCUMENTO</div>
                    <div style={{ color: C.textMuted }}>Genera el escrito final cuando el pago ya este confirmado.</div>
                    <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
                      <Button variant="secondary" onClick={() => onGenerateDocument(activeCaseDetail.case.id)} disabled={activeCaseDetail.case.payment_status !== "pagado"} icon={FileText}>Generar documento</Button>
                    </div>
                  </div>
                  <div style={{ padding: 18, borderRadius: 18, border: `1px solid ${C.border}`, background: "#FCFDFF", display: "grid", gap: 12 }}>
                    <div style={{ fontSize: 12, fontWeight: 800, letterSpacing: "0.08em", color: C.textMuted }}>ENVIO O RADICACION</div>
                    <TextInput value={manualContact} onChange={(event) => setManualContact(event.target.value)} placeholder="Correo o contacto manual" />
                    <TextArea value={submissionNote} onChange={(event) => setSubmissionNote(event.target.value)} placeholder="Notas del envio o fallback" style={{ minHeight: 90 }} />
                    {!persistedSignatureReady && (
                      <div style={{ padding: 12, borderRadius: 14, background: "#FEF2F2", border: "1px solid #FECACA", color: "#991B1B" }}>
                        Antes de enviar debes abrir el expediente, revisar el documento y guardar la firma simple.
                      </div>
                    )}
                    {!activePaymentEntitlements.filing_auto_paid && (
                      <div style={{ padding: 12, borderRadius: 14, background: "#FFF7ED", border: "1px solid #FDBA74", color: "#9A3412" }}>
                        El envio automatico requiere que el paquete de radicacion y seguimiento ya este pago.
                      </div>
                    )}
                    <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
                      <Button onClick={() => onSubmitCase(activeCaseDetail.case.id, { mode: "auto", notes: buildSubmissionSignatureNote(persistedSignaturePayload, submissionNote), signature: { ...persistedSignaturePayload, accepted: true, consent_version: persistedSignature.consent_version || SIMPLE_SIGNATURE_CONSENT_VERSION, consent_text: persistedSignature.consent_text || SIMPLE_SIGNATURE_CONSENT_TEXT }, reviewed_document: !!persistedSignature.reviewed_document })} disabled={!activeCaseDetail.case.generated_document || !persistedSignatureReady || !activePaymentEntitlements.filing_auto_paid}>Ejecutar envio automatico</Button>
                      <Button variant="ghost" onClick={() => onSubmitCase(activeCaseDetail.case.id, { mode: "presencial", notes: buildSubmissionSignatureNote(persistedSignaturePayload, submissionNote), signature: { ...persistedSignaturePayload, accepted: true, consent_version: persistedSignature.consent_version || SIMPLE_SIGNATURE_CONSENT_VERSION, consent_text: persistedSignature.consent_text || SIMPLE_SIGNATURE_CONSENT_TEXT }, reviewed_document: !!persistedSignature.reviewed_document })} disabled={!persistedSignatureReady}>Activar modo presencial</Button>
                    </div>
                  </div>
                  <div style={{ padding: 18, borderRadius: 18, border: `1px solid ${C.border}`, background: "#FCFDFF", display: "grid", gap: 12 }}>
                    <div style={{ fontSize: 12, fontWeight: 800, letterSpacing: "0.08em", color: C.textMuted }}>RADICADO MANUAL Y EVIDENCIA</div>
                    <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
                      <TextInput value={radicadoManual} onChange={(event) => setRadicadoManual(event.target.value)} placeholder="Numero de radicado manual" />
                      <Button variant="secondary" onClick={() => onManualRadicado(activeCaseDetail.case.id, { radicado: radicadoManual, notes: buildSubmissionSignatureNote(persistedSignaturePayload, radicadoNote), signature: { ...persistedSignaturePayload, accepted: true, consent_version: persistedSignature.consent_version || SIMPLE_SIGNATURE_CONSENT_VERSION, consent_text: persistedSignature.consent_text || SIMPLE_SIGNATURE_CONSENT_TEXT }, reviewed_document: !!persistedSignature.reviewed_document })} disabled={!persistedSignatureReady}>Registrar radicado manual</Button>
                    </div>
                    <TextArea value={radicadoNote} onChange={(event) => setRadicadoNote(event.target.value)} placeholder="Notas del radicado manual" style={{ minHeight: 80 }} />
                    <input id="evidence-upload" type="file" style={{ display: "none" }} onChange={uploadEvidence} />
                    <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
                      <TextInput value={evidenceNote} onChange={(event) => setEvidenceNote(event.target.value)} placeholder="Nota sobre la evidencia" />
                      <Button variant="outline" onClick={() => document.getElementById("evidence-upload").click()} icon={Upload}>Subir evidencia</Button>
                    </div>
                  </div>
                </div>
              </SessionCard>
            </div>
          </>
        )}
      </div>
    ),
    ayuda: (
      <div style={{ display: "grid", gap: 12 }}>
        <div className="glass-card" style={{ padding: 24 }}>
          <Badge color={C.primary}>Ayuda rápida</Badge>
          <h2 style={{ marginTop: 12, fontSize: 30, lineHeight: 1.1, color: C.text, fontFamily: "'Playfair Display', serif" }}>
            Qué significa cada etapa del proceso.
          </h2>
        </div>
        {[
          "Análisis gratis: identificamos el derecho vulnerado y la acción recomendada antes de cobrar.",
          "Pago: solo después del pago aprobado se activa el documento final.",
          "Radicación automática: se usa cuando existe un canal confiable en la base operativa.",
          "Fallback manual: si no hay canal digital seguro, te guiamos por contacto manual o presencial.",
          "Seguimiento: despues del radicado veras novedades y siguientes pasos desde el panel.",
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
              <Button variant="secondary" onClick={() => openCaseAndFocusDetail(item.id, "internal")}>Abrir</Button>
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

  content.detalle = canOperateActiveCase ? (
    <div style={{ display: "grid", gap: 18 }}>
      <DetailPanel
        detail={activeCaseDetail}
        postPayForm={postPayForm}
        setPostPayForm={setPostPayForm}
        documentReview={activeDocumentReview}
        entityLookupLoading={entityLookupLoading}
        entitySuggestions={entitySuggestions}
        onApplyEntitySuggestion={applyEntitySuggestion}
        regenerationReason={regenerationReason}
        setRegenerationReason={setRegenerationReason}
        regenerationContext={regenerationContext}
        setRegenerationContext={setRegenerationContext}
        loading={loading}
        detailStepOverride={detailStepOverride}
        onSetDetailStep={setDetailStepOverride}
        onViewDocument={setDocumentCase}
        onSaveFlowDraft={async () => {
          if (!activeCaseDetail?.case?.id) return;
          const effectiveDetailForm = mergeDetectedFormValues(postPayForm, activeCaseDetail.case.facts?.intake_form || activeCaseDetail.case.facts?.autofill_suggestions || {});
          const nextProfile = {
            ...profile,
            name: effectiveDetailForm.full_name,
            document_number: effectiveDetailForm.document_number,
            phone: effectiveDetailForm.phone,
            address: effectiveDetailForm.address,
          };
          setProfile(nextProfile);
          await onSaveProfile(nextProfile);
          await onUpdateCaseIntake(activeCaseDetail.case.id, {
            description: buildPostPayDescription(effectiveDetailForm, activeCaseDetail.case),
            form_data: {
              ...effectiveDetailForm,
              regeneration_reason: regenerationReason,
              regeneration_additional_context: regenerationContext,
            },
          });
        }}
        onGenerateFromFlow={async () => {
          if (!activeCaseDetail?.case?.id) return;
          const effectiveDetailForm = mergeDetectedFormValues(postPayForm, activeCaseDetail.case.facts?.intake_form || activeCaseDetail.case.facts?.autofill_suggestions || {});
          const nextProfile = {
            ...profile,
            name: effectiveDetailForm.full_name,
            document_number: effectiveDetailForm.document_number,
            phone: effectiveDetailForm.phone,
            address: effectiveDetailForm.address,
          };
          setProfile(nextProfile);
          await onSaveProfile(nextProfile);
          await onUpdateCaseIntake(activeCaseDetail.case.id, {
            description: buildPostPayDescription(effectiveDetailForm, activeCaseDetail.case),
            form_data: {
              ...effectiveDetailForm,
              regeneration_reason: regenerationReason,
              regeneration_additional_context: regenerationContext,
            },
          });
          const generated = await onGenerateDocument(activeCaseDetail.case.id, {
            regeneration_reason: regenerationReason,
            additional_context: regenerationContext,
          });
          setDocumentReviews((current) => ({ ...current, [activeCaseDetail.case.id]: generated?.quality_review || null }));
          setDetailStepOverride(null);
        }}
        onSubmitCase={(payload) => onSubmitCase(activeCaseDetail.case.id, payload)}
        onManualRadicado={(payload) => onManualRadicado(activeCaseDetail.case.id, payload)}
        onUploadEvidence={(file, note) => onUploadEvidence(activeCaseDetail.case.id, file, note)}
      />
      {activeCaseDetail?.case?.payment_status !== "pagado" && (
        <PaymentCard
          title="Pago y activacion del documento"
          caseItem={activeCaseDetail.case}
          catalog={catalog}
          onCreateWompiSession={onCreateWompiSession}
          onGetPayment={onGetPayment}
          onReconcilePayment={onReconcilePayment}
          onRefreshCase={onRefreshCase}
          loading={loading}
        />
      )}
    </div>
  ) : <div className="glass-card" style={{ padding: 24, color: C.textMuted }}>Abre un expediente del cliente desde Mis expedientes para continuar el flujo.</div>;
  content.tramites = cases.length ? (
    <div style={{ display: "grid", gap: 16 }}>
      <div style={{ display: "grid", gridTemplateColumns: "1.35fr 0.85fr", gap: 18 }}>
        <div
          className="glass-card"
          style={{
            padding: 28,
            background: "linear-gradient(135deg, #0F172A 0%, #13203A 60%, #183153 100%)",
            border: "1px solid #1E3A5F",
            color: "#F8FAFC",
            position: "relative",
            overflow: "hidden",
          }}
        >
          <div style={{ position: "absolute", inset: "auto -40px -50px auto", width: 180, height: 180, borderRadius: "50%", background: "rgba(59,130,246,0.14)" }} />
          <Badge color="#93C5FD">Mis expedientes</Badge>
          <h2 style={{ marginTop: 16, fontSize: 42, lineHeight: 1.02, color: "#F8FAFC", fontFamily: "'Playfair Display', serif", maxWidth: 760 }}>
            Aqui ves que ya avanzaste y que sigue en cada caso.
          </h2>
          <p style={{ marginTop: 14, color: "#CBD5E1", maxWidth: 720, fontSize: 18, lineHeight: 1.7 }}>
            Sin lenguaje tecnico. Solo el estado real, la siguiente accion clara y el acceso rapido a cada expediente.
          </p>
          <div style={{ display: "flex", gap: 12, flexWrap: "wrap", marginTop: 18 }}>
            <div style={{ padding: "10px 14px", borderRadius: 999, background: "rgba(16,185,129,0.16)", border: "1px solid rgba(16,185,129,0.34)", color: "#A7F3D0", fontWeight: 700 }}>
              {cases.length} expediente{cases.length === 1 ? "" : "s"} activo{cases.length === 1 ? "" : "s"}
            </div>
            <div style={{ padding: "10px 14px", borderRadius: 999, background: "rgba(59,130,246,0.14)", border: "1px solid rgba(147,197,253,0.3)", color: "#DBEAFE", fontWeight: 700 }}>
              {cases.filter((item) => item.payment_status === "pagado").length} pago{cases.filter((item) => item.payment_status === "pagado").length === 1 ? "" : "s"} confirmado{cases.filter((item) => item.payment_status === "pagado").length === 1 ? "" : "s"}
            </div>
          </div>
        </div>

        <div
          className="glass-card"
          style={{
            padding: 24,
            background: "linear-gradient(180deg, #F8FBFF 0%, #EEF4FF 100%)",
            border: "1px solid #C7D7FE",
            display: "grid",
            gap: 14,
            alignContent: "start",
          }}
        >
          <div style={{ fontSize: 12, fontWeight: 800, letterSpacing: 0.4, color: C.primary }}>DATOS DE TU CUENTA</div>
          <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
            <div style={{ width: 56, height: 56, borderRadius: 18, background: C.primary, color: "#fff", display: "grid", placeItems: "center", fontWeight: 800, fontSize: 20 }}>
              {session.user.name.slice(0, 2).toUpperCase()}
            </div>
            <div style={{ minWidth: 0 }}>
              <div style={{ fontWeight: 800, color: C.text, fontSize: 18 }}>{session.user.name}</div>
              <div style={{ color: C.textMuted, fontSize: 14, wordBreak: "break-word" }}>{session.user.email}</div>
            </div>
          </div>
          <div style={{ display: "grid", gap: 10 }}>
            <div style={{ padding: 12, borderRadius: 14, background: "#fff", border: `1px solid ${C.border}` }}>
              <div style={{ fontSize: 12, fontWeight: 800, color: C.textMuted }}>Documento</div>
              <div style={{ marginTop: 4, color: C.text, fontWeight: 700 }}>{session.user.document_number || "Falta completar"}</div>
            </div>
            <div style={{ padding: 12, borderRadius: 14, background: "#fff", border: `1px solid ${C.border}` }}>
              <div style={{ fontSize: 12, fontWeight: 800, color: C.textMuted }}>Celular</div>
              <div style={{ marginTop: 4, color: C.text, fontWeight: 700 }}>{session.user.phone || "Falta completar"}</div>
            </div>
            <div style={{ padding: 12, borderRadius: 14, background: "#fff", border: `1px solid ${C.border}` }}>
              <div style={{ fontSize: 12, fontWeight: 800, color: C.textMuted }}>Ciudad</div>
              <div style={{ marginTop: 4, color: C.text, fontWeight: 700 }}>
                {[session.user.city, session.user.department].filter(Boolean).join(", ") || "Falta completar"}
              </div>
            </div>
          </div>
          <div style={{ color: C.textMuted, fontSize: 13, lineHeight: 1.6 }}>
            Estos son los datos que la app usa para prellenar tus tramites y documentos.
          </div>
        </div>
      </div>
      {cases.map((item) => (
        <div key={item.id} className="glass-card" style={{ padding: 22, display: "grid", gap: 16, background: "#FFFFFF", border: `1px solid ${C.border}`, boxShadow: "0 20px 50px rgba(15,23,42,0.06)" }}>
          <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "start" }}>
            <div>
              <div style={{ display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
                <div style={{ width: 46, height: 46, borderRadius: 16, background: item.status === "radicado" ? "#DCFCE7" : item.generated_document ? "#DBEAFE" : item.payment_status === "pagado" ? "#E0E7FF" : "#FEF3C7", display: "grid", placeItems: "center", color: item.status === "radicado" ? "#166534" : item.generated_document ? "#1D4ED8" : item.payment_status === "pagado" ? "#4338CA" : "#B45309", fontWeight: 800 }}>
                  {(item.category || "?").slice(0, 1).toUpperCase()}
                </div>
                <div>
                  <div style={{ fontWeight: 800, color: C.text, fontSize: 22 }}>{item.recommended_action || item.workflow_type}</div>
                  <div style={{ color: C.textMuted, marginTop: 4 }}>{item.category} · {item.user_city}, {item.user_department}</div>
                </div>
              </div>
            </div>
            <Badge color={item.status === "radicado" ? C.success : item.generated_document ? C.primary : item.payment_status === "pagado" ? C.primary : C.warning}>
              {item.status === "radicado" ? "Radicado" : item.generated_document ? "Documento listo" : item.payment_status === "pagado" ? "Completa datos" : "Pago pendiente"}
            </Badge>
          </div>
          <div style={{ color: C.textMuted, lineHeight: 1.7 }}>
            {summarizeCaseCard(item) || "La plataforma ya organizo este expediente y te muestra el siguiente movimiento claro."}
          </div>
          <div style={{ padding: 16, borderRadius: 18, background: "#F8FAFD", border: `1px solid ${C.border}` }}>
            <div style={{ fontSize: 12, color: C.textMuted, fontWeight: 800 }}>SIGUIENTE PASO</div>
            <div style={{ marginTop: 8, color: C.text, fontWeight: 800 }}>
              {item.payment_status !== "pagado"
                ? "Confirma el pago para desbloquear el formulario."
                : item.generated_document
                  ? item.status === "radicado"
                    ? "Revisa el comprobante y haz seguimiento a la respuesta."
                    : "Revisa el documento y elige como radicarlo."
                  : "Completa tus datos para generar el documento final."}
            </div>
          </div>
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
            <Badge color={item.payment_status === "pagado" ? C.success : C.warning}>Pago: {item.payment_status}</Badge>
            <Badge color={item.routing?.automatable ? C.primary : C.textMuted}>{item.routing?.automatable ? "Canal automatico" : "Revision manual"}</Badge>
            {item.routing?.primary_target?.name && <Badge color={C.accent}>{item.routing.primary_target.name}</Badge>}
          </div>
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
            <Button variant="secondary" onClick={() => openCaseAndFocusDetail(item.id)}>Abrir expediente</Button>
            {item.generated_document && <Button variant="outline" onClick={() => setDocumentCase(item)}>Ver documento</Button>}
          </div>
        </div>
      ))}
    </div>
  ) : <div className="glass-card" style={{ padding: 30, color: C.textMuted }}>Todavia no tienes expedientes guardados.</div>;

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
        <div style={{ display: "flex", justifyContent: "space-between", gap: 12, marginBottom: 18, flexWrap: "wrap" }}>
          <Button variant="outline" onClick={() => previousTab && setActiveTab(previousTab.id)} disabled={!previousTab} icon={ArrowLeft}>
            {previousTab ? `Volver a ${previousTab.label}` : "Sin anterior"}
          </Button>
          <Button variant="outline" onClick={() => nextTab && setActiveTab(nextTab.id)} disabled={!nextTab} icon={ArrowRight}>
            {nextTab ? `Ir a ${nextTab.label}` : "Sin siguiente"}
          </Button>
        </div>
        <DashboardErrorBoundary>{content[activeTab]}</DashboardErrorBoundary>
        {visibleActionError && <div style={{ marginTop: 16, color: C.danger }}>{visibleActionError}</div>}
      </main>
    </div>
  );
}
