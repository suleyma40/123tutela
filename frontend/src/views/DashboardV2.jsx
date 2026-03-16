import React, { useEffect, useMemo, useState } from "react";
import { ArrowLeft, ArrowRight, Briefcase, CreditCard, FileText, HelpCircle, Layout, LogOut, Plus, Scale, Search, Shield, Upload } from "lucide-react";

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
  tutela_no_temperity_detail: "",
  tutela_other_means_detail: "",
  tutela_immediacy_detail: "",
  tutela_special_protection_detail: "",
  tutela_private_party_ground: "",
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

const shortDate = (value) => new Date(value).toLocaleString("es-CO", { dateStyle: "medium", timeStyle: "short" });
const apiBase = import.meta.env.VITE_API_URL || "http://localhost:8000";
const widgetScriptUrl = "https://checkout.wompi.co/widget.js";

const normalizeAction = (value) =>
  String(value || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .trim();

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
    form.tutela_no_temperity_detail ? `No temeridad o tutela previa: ${form.tutela_no_temperity_detail}` : "",
    form.tutela_other_means_detail ? `Subsidiariedad o ausencia de otro medio eficaz: ${form.tutela_other_means_detail}` : "",
    form.tutela_immediacy_detail ? `Inmediatez o justificacion temporal: ${form.tutela_immediacy_detail}` : "",
    form.tutela_special_protection_detail ? `Sujeto de especial proteccion: ${form.tutela_special_protection_detail}` : "",
    form.tutela_private_party_ground ? `Fundamento contra particular: ${form.tutela_private_party_ground}` : "",
    form.petition_target_nature ? `Naturaleza del destinatario de la peticion: ${form.petition_target_nature}` : "",
    form.petition_private_ground ? `Fundamento para peticion a particular: ${form.petition_private_ground}` : "",
    form.petition_previous_submission_date ? `Fecha de radicacion o gestion previa: ${form.petition_previous_submission_date}` : "",
    form.petition_sector_rule ? `Norma sectorial o contexto especial: ${form.petition_sector_rule}` : "",
    form.description ? `Relato del usuario: ${form.description}` : "",
  ].filter(Boolean);

  return sections.join("\n");
};

const getGuidedIntakeMissing = (form) => {
  const missing = [];

  if (!form.target_entity.trim()) missing.push("Entidad o destinatario");
  if (!form.event_date.trim()) missing.push("Fecha o periodo");
  if (!form.concrete_request.trim()) missing.push("Solicitud concreta");
  if (!form.response_channel.trim()) missing.push("Canal de respuesta");
  if (!form.evidence_summary.trim()) missing.push("Pruebas o soportes disponibles");

  if (form.category === "Salud") {
    if (!form.eps_name.trim()) missing.push("EPS");
    if (!form.diagnosis.trim()) missing.push("Diagnostico o condicion medica");
    if (!form.treatment_needed.trim()) missing.push("Tratamiento, orden o servicio requerido");
  }

  if (form.category === "Datos") {
    if (!form.disputed_data.trim()) missing.push("Dato o reporte cuestionado");
    if (!form.requested_data_action.trim()) missing.push("Accion solicitada sobre el dato");
  }

  if (["Laboral", "Bancos", "Servicios", "Consumidor"].includes(form.category)) {
    if (!form.numbered_requests.trim()) missing.push("Solicitudes numeradas esperadas");
  }

  if (form.category === "Laboral") {
    if (!form.labor_relation_type.trim()) missing.push("Tipo de relacion laboral");
    if (!form.labor_employer_name.trim()) missing.push("Empleador o contratante");
    if (!form.labor_measure_date.trim()) missing.push("Fecha de la medida o despido");
    if (!form.dismissal_or_measure.trim()) missing.push("Despido, sancion o medida cuestionada");
  }

  if (form.category === "Bancos") {
    if (!form.bank_product_type.trim()) missing.push("Producto financiero involucrado");
    if (!form.bank_amount_involved.trim()) missing.push("Monto o valor discutido");
    if (!form.bank_claim_goal.trim()) missing.push("Resultado esperado frente al banco");
    if (!form.report_or_block_reason.trim()) missing.push("Reporte, bloqueo o causa principal");
  }

  if (form.category === "Servicios") {
    if (!form.service_company_name.trim()) missing.push("Empresa de servicios");
    if (!form.service_type.trim()) missing.push("Tipo de servicio afectado");
    if (!form.subscriber_reference.trim()) missing.push("Numero de suscriptor o referencia");
    if (!form.cutoff_or_billing_detail.trim()) missing.push("Detalle de corte o facturacion");
  }

  if (form.category === "Consumidor") {
    if (!form.provider_name.trim()) missing.push("Proveedor o comercio");
    if (!form.purchase_date.trim()) missing.push("Fecha de compra o contratacion");
    if (!form.order_reference.trim()) missing.push("Pedido, factura o referencia");
    if (!form.product_or_service_issue.trim()) missing.push("Falla del producto o servicio");
  }

  return missing;
};

const getPreviewGateIssues = (form) => {
  const issues = [];
  const descriptionLength = form.description.trim().length;
  const harmLength = form.current_harm.trim().length;
  const evidenceLength = form.evidence_summary.trim().length;

  if (descriptionLength < 60) {
    issues.push("El relato libre todavia es muy corto. Describe mejor que paso, en que orden y con que fechas.");
  }

  if (harmLength < 25) {
    issues.push("Debes explicar mejor la afectacion actual o el riesgo concreto que justifica el documento.");
  }

  if (evidenceLength < 20) {
    issues.push("Falta explicar que pruebas, soportes o documentos tienes disponibles.");
  }

  if (form.prior_response_status === "sin_gestion_previa" && ["Laboral", "Bancos", "Servicios", "Consumidor", "Datos"].includes(form.category)) {
    issues.push("Todavia no reportas una gestion previa. Revisa si primero conviene un derecho de peticion o una reclamacion formal.");
  }

  if (form.category === "Salud" && form.urgency_detail.trim().length < 20) {
    issues.push("En salud debes explicar mejor la urgencia o el riesgo clinico actual.");
  }

  if (["Laboral", "Bancos", "Servicios", "Consumidor"].includes(form.category) && form.numbered_requests.trim().length < 15) {
    issues.push("Para un derecho de peticion fuerte debes dejar mas claras las solicitudes numeradas esperadas.");
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

  if (form.category === "Servicios" && form.service_impact.trim().length < 20) {
    issues.push("En servicios debes explicar con mas detalle el impacto del corte, cobro o incumplimiento.");
  }

  if (form.category === "Servicios" && form.subscriber_reference.trim().length < 6) {
    issues.push("En servicios conviene incluir numero de suscriptor, contrato o referencia del servicio.");
  }

  if (form.category === "Consumidor" && form.guarantee_or_refund_request.trim().length < 15) {
    issues.push("En consumidor debes explicar con mas claridad la garantia, cambio o devolucion que solicitas.");
  }

  if (form.category === "Consumidor" && form.seller_response_detail.trim().length < 15) {
    issues.push("En consumidor debes contar que respondio el proveedor o si guardo silencio frente a la reclamacion.");
  }

  return issues;
};

const getWritingAid = (category) => {
  if (category === "Salud") {
    return "Cuenta los hechos en orden: que te ordenaron, que negaron o demoraron, desde cuando pasa y por que hoy existe urgencia o riesgo.";
  }
  if (category === "Datos") {
    return "Explica que dato esta mal, donde aparece, desde cuando lo conoces, si ya reclamaste y que accion exacta quieres: corregir, actualizar o suprimir.";
  }
  if (["Laboral", "Bancos", "Servicios", "Consumidor"].includes(category)) {
    return "Escribe como una peticion o reclamacion seria: identifica a quien va dirigida, que paso, que soporte tienes, que exiges exactamente y por que eso te afecta hoy.";
  }
  return "Describe hechos concretos, fechas, entidad involucrada y una solicitud clara. Evita opiniones generales y enfocate en lo verificable.";
};

const getActionSpecificMissing = (recommendedAction, form) => {
  const action = normalizeAction(recommendedAction);
  const missing = [];

  if (action === "queja formal") {
    if (!form.complaint_reason.trim()) missing.push("Motivo principal de la queja");
    if (!form.complaint_expected_response.trim()) missing.push("Respuesta o intervencion esperada");
  }

  if (action === "accion de tutela") {
    if (!form.tutela_no_temperity_detail.trim()) missing.push("No temeridad o tutela previa");
    if (!form.tutela_other_means_detail.trim()) missing.push("Subsidiariedad o ausencia de otro medio eficaz");
    if (!form.tutela_immediacy_detail.trim()) missing.push("Inmediatez o justificacion temporal");
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
    if (form.tutela_no_temperity_detail.trim().length < 20) issues.push("La tutela debe aclarar bajo juramento si existe o no otra tutela por los mismos hechos y derechos.");
    if (form.tutela_other_means_detail.trim().length < 25) issues.push("La tutela debe explicar mejor por que no existe otro medio judicial eficaz o por que hay perjuicio irremediable.");
    if (form.tutela_immediacy_detail.trim().length < 20) issues.push("La tutela debe justificar la inmediatez o explicar por que se presenta ahora.");
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
        <Field label="No temeridad o tutela previa">
          <TextArea value={form.tutela_no_temperity_detail} onChange={(event) => setField("tutela_no_temperity_detail", event.target.value)} placeholder="Indica si ya presentaste otra tutela por los mismos hechos. Si no, dilo expresamente. Si si, explica que cambio." style={{ minHeight: 90 }} />
        </Field>
        <Field label="Subsidiariedad o ausencia de otro medio eficaz">
          <TextArea value={form.tutela_other_means_detail} onChange={(event) => setField("tutela_other_means_detail", event.target.value)} placeholder="Explica por que la tutela si procede: no hay otro medio eficaz, o existe urgencia o perjuicio irremediable." style={{ minHeight: 90 }} />
        </Field>
        <Field label="Inmediatez o justificacion temporal">
          <TextInput value={form.tutela_immediacy_detail} onChange={(event) => setField("tutela_immediacy_detail", event.target.value)} placeholder="Ej: la vulneracion sigue ocurriendo hoy / el hecho es reciente / el riesgo es actual" />
        </Field>
        <Field label="Sujeto de especial proteccion, si aplica">
          <TextInput value={form.tutela_special_protection_detail} onChange={(event) => setField("tutela_special_protection_detail", event.target.value)} placeholder="Ej: menor, embarazada, adulto mayor, discapacidad, paciente de alto riesgo" />
        </Field>
        <Field label="Fundamento contra particular, si aplica">
          <TextInput value={form.tutela_private_party_ground} onChange={(event) => setField("tutela_private_party_ground", event.target.value)} placeholder="Ej: prestador de servicio publico, indefension, subordinacion, habeas data" />
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

function PreviewGateCard({ issues }) {
  if (!issues.length) {
    return (
      <div className="glass-card" style={{ padding: 18, background: "#F0FDF4", border: "1px solid #86EFAC" }}>
        <div style={{ fontSize: 12, fontWeight: 800, letterSpacing: 0.4, color: C.textMuted }}>CALIDAD MINIMA PARA ANALISIS</div>
        <div style={{ marginTop: 8, color: C.text, fontWeight: 800 }}>La informacion actual ya permite generar un preview juridico mas confiable.</div>
      </div>
    );
  }

  return (
    <div className="glass-card" style={{ padding: 18, background: "#FFF7ED", border: "1px solid #FDBA74" }}>
      <div style={{ fontSize: 12, fontWeight: 800, letterSpacing: 0.4, color: C.textMuted }}>ANTES DEL PREVIEW</div>
      <div style={{ marginTop: 8, color: C.text, fontWeight: 800 }}>
        Todavia faltan detalles minimos para que la IA produzca un analisis juridico serio.
      </div>
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

function IntakeReviewCard({ review }) {
  if (!review || review.status === "not_scored") {
    return null;
  }

  const blockingIssues = review.blocking_issues || [];
  const warnings = review.warnings || [];
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

      {!!warnings.length && (
        <div style={{ display: "grid", gap: 10, marginTop: 14 }}>
          {warnings.map((warning) => (
            <div key={warning} style={{ color: "#92400E", background: "#FFFBEB", border: "1px solid #FDE68A", padding: 14, borderRadius: 14 }}>
              {warning}
            </div>
          ))}
        </div>
      )}

      <div style={{ marginTop: 14, color: C.textMuted, fontSize: 13, lineHeight: 1.6 }}>
        {canProceed
          ? "Puedes guardar el expediente, pero conviene reforzar hechos, fechas y pretensiones para mejorar la calidad del documento final."
          : "Vuelve al paso anterior y mejora el relato antes de continuar. La plataforma no deberia cobrar ni generar un documento con informacion debil."}
      </div>
    </div>
  );
}

function DocumentRuleReviewCard({ review }) {
  if (!review || !review.rule) {
    return null;
  }

  const blockingIssues = review.blocking_issues || [];
  const warnings = review.warnings || [];
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

      <div style={{ marginTop: 14, display: "grid", gap: 10 }}>
        <div style={{ color: C.textMuted, fontSize: 13 }}>Secciones minimas: {review.rule.required_sections?.join(", ")}</div>
        <div style={{ color: C.textMuted, fontSize: 13 }}>Foco juridico: {review.rule.quality_focus}</div>
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

      {!!warnings.length && (
        <div style={{ display: "grid", gap: 10, marginTop: 14 }}>
          {warnings.map((warning) => (
            <div key={warning} style={{ color: "#92400E", background: "#FFFBEB", border: "1px solid #FDE68A", padding: 14, borderRadius: 14 }}>
              {warning}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function GuidedIntakeFields({ form, setForm, missingFields }) {
  const setField = (key, value) => setForm((current) => ({ ...current, [key]: value }));
  const writingAid = getWritingAid(form.category);
  const isPetitionTrack = ["Laboral", "Bancos", "Servicios", "Consumidor"].includes(form.category);

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

      <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 16 }}>
        <Field label="Entidad o destinatario">
          <TextInput value={form.target_entity} onChange={(event) => setField("target_entity", event.target.value)} placeholder="Ej: Nueva EPS, Datacredito, Alcaldia, Banco X" />
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
        <Field label="Que solicitas exactamente">
          <TextInput value={form.concrete_request} onChange={(event) => setField("concrete_request", event.target.value)} placeholder="Ej: entrega de medicamento, respuesta de fondo, correccion del reporte" />
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
            <Field label="Solicitudes numeradas esperadas">
              <TextInput value={form.numbered_requests} onChange={(event) => setField("numbered_requests", event.target.value)} placeholder="Ej: 1) Responder de fondo 2) Entregar copia 3) Corregir cobro" />
            </Field>
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
            <Field label="EPS">
              <TextInput value={form.eps_name} onChange={(event) => setField("eps_name", event.target.value)} placeholder="Ej: Nueva EPS" />
            </Field>
            <Field label="IPS o clinica">
              <TextInput value={form.ips_name} onChange={(event) => setField("ips_name", event.target.value)} placeholder="Ej: Clinica San Rafael" />
            </Field>
            <Field label="Diagnostico o condicion medica">
              <TextInput value={form.diagnosis} onChange={(event) => setField("diagnosis", event.target.value)} placeholder="Ej: cancer, embarazo de alto riesgo, depresion severa" />
            </Field>
            <Field label="Tratamiento, orden o servicio requerido">
              <TextInput value={form.treatment_needed} onChange={(event) => setField("treatment_needed", event.target.value)} placeholder="Ej: medicamento X, cita con especialista, procedimiento Y" />
            </Field>
          </div>
          <Field label="Urgencia o riesgo clinico">
            <TextArea value={form.urgency_detail} onChange={(event) => setField("urgency_detail", event.target.value)} placeholder="Describe si hay dolor, agravacion, riesgo vital, suspension de tratamiento o afectacion grave." style={{ minHeight: 100, marginTop: 16 }} />
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
            <Field label="Accion solicitada sobre el dato">
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
  const [includeFiling, setIncludeFiling] = useState(false);
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
            setPaymentMessage("Pago aprobado. Ya puedes generar el documento final.");
            return;
          }
        } catch {
          // si la reconciliacion no aplica todavia, seguimos con el polling local
        }
      }
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
    if (!consentAccepted) {
      setPaymentMessage("Debes aceptar los términos, privacidad y condiciones del pago antes de continuar.");
      return;
    }
    setPaymentMessage("");
    const session = await onCreateWompiSession(caseItem.id, {
      product_code: selectedProduct.code,
      include_filing: includeFiling,
    });
    setLatestReference(session.order.reference);
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
            <div style={{ marginTop: 16, padding: 14, borderRadius: 14, background: "#F8FAFD", border: `1px solid ${C.border}` }}>
              <div style={{ fontSize: 12, color: C.textMuted, fontWeight: 800 }}>LO QUE RECIBES AL PAGAR</div>
              <div style={{ display: "grid", gap: 8, marginTop: 10, color: C.text }}>
                <div>1. Documento jurídico final listo para usar.</div>
                <div>2. Acceso al expediente y trazabilidad del caso desde tu panel.</div>
                <div>3. {includeFiling ? "Radicación por parte de la plataforma cuando el canal lo permita." : "Opción de radicación según el producto que elijas."}</div>
              </div>
            </div>
            <div style={{ marginTop: 14, padding: 14, borderRadius: 14, background: "#EEF4FF", border: "1px solid #BFDBFE", color: C.text }}>
              <strong style={{ color: C.primary }}>Pago seguro con Wompi.</strong>
              <div style={{ marginTop: 6, color: C.textMuted, fontSize: 13 }}>
                El cobro se procesa a través de Wompi. La activación final del documento depende de la confirmación segura del pago por webhook.
              </div>
            </div>
            <label style={{ display: "flex", gap: 10, alignItems: "flex-start", marginTop: 16, color: C.text }}>
              <input type="checkbox" checked={consentAccepted} onChange={(event) => setConsentAccepted(event.target.checked)} />
              <span style={{ fontSize: 14, lineHeight: 1.6 }}>
                Confirmo que entiendo qué estoy comprando, acepto los términos y la política de privacidad, y autorizo el procesamiento del pago mediante Wompi.
              </span>
            </label>
            <div style={{ color: C.textMuted, fontSize: 13 }}>
              Consulta: <a href="/terminos" style={{ color: C.primary }}>Términos</a> · <a href="/privacidad" style={{ color: C.primary }}>Privacidad</a> · <a href="/contacto" style={{ color: C.primary }}>Contacto</a>
            </div>
            {latestReference && (
              <div style={{ color: C.textMuted, fontSize: 13, marginTop: 6 }}>
                Referencia del intento: <strong style={{ color: C.text }}>{latestReference}</strong>
              </div>
            )}
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

function DetailPanel({ detail, onViewDocument, onGoNextStage }) {
  if (!detail) {
    return <div className="glass-card" style={{ padding: 24, color: C.textMuted }}>Abre un expediente para ver timeline, archivos y trazabilidad.</div>;
  }

  const { case: item, files, submission_attempts: attempts, timeline } = detail;
  const submissionSummary = item.submission_summary || {};
  const guidance = submissionSummary.guidance || {};
  const emailStatus = submissionSummary.post_radicado_email || {};
  const routingSnapshot = guidance.routing_snapshot || {};
  const proofDeliveryChannels = guidance.proof_delivery_channels || [];
  const continuityOffers = guidance.continuity_offers || [];
  const nextStep =
    guidance.next_step_suggestion ||
    (item.payment_status !== "pagado"
      ? "Completar el pago para activar el documento final."
      : !item.generated_document
        ? "Generar el documento final desde acciones operativas."
        : item.status === "radicado"
          ? "Revisar el comprobante y continuar con seguimiento si aplica."
          : item.routing?.automatable
            ? "Ejecutar la radicacion automatica o revisar el ultimo intento."
            : "Completar el envio manual o presencial y registrar el radicado.");
  const estimatedTime =
    guidance.estimated_response_window ||
    (item.payment_status !== "pagado"
      ? "Pendiente de pago"
      : item.status === "radicado"
        ? "Radicado emitido"
        : item.routing?.automatable
          ? "Menos de 5 minutos cuando el canal responde"
          : "Depende del canal manual elegido");
  const continuationOptions = buildContinuationOptions(item);
  const postRadicadoStatusLabel =
    emailStatus.status === "sent"
      ? "Enviado"
      : emailStatus.status === "pending_configuration"
        ? "Pendiente de configurar"
        : emailStatus.status === "error"
          ? "Error"
          : "Aun no procesado";
  const postRadicadoStatusColor =
    emailStatus.status === "sent"
      ? C.success
      : emailStatus.status === "pending_configuration"
        ? C.warning
        : emailStatus.status === "error"
          ? C.danger
          : C.textMuted;
  const emailStatusDetails =
    emailStatus.reason === "smtp_not_configured"
      ? "Falta configurar SMTP en produccion para que este correo salga automaticamente."
      : emailStatus.reason === "missing_recipient"
        ? "El expediente no tiene correo del cliente para enviar la notificacion."
        : emailStatus.reason
          ? `Detalle tecnico: ${emailStatus.reason}`
          : guidance.post_radicado_copy?.body || "El cliente vera el siguiente paso y los tiempos esperados desde el panel y el correo.";

  return (
    <div style={{ display: "grid", gap: 18 }}>
      <SessionCard title="Expediente activo" subtitle={`${item.category} - ${item.workflow_type.replaceAll("_", " ")}`}>
        <div style={{ display: "grid", gap: 12 }}>
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
            <Badge color={statusColors[item.status] || C.primary}>{statusLabels[item.status] || item.status}</Badge>
            <Badge color={item.payment_status === "pagado" ? C.success : C.warning}>Pago: {item.payment_status}</Badge>
            <Badge color={item.routing?.automatable ? C.primary : C.danger}>{item.routing?.automatable ? "Canal automatico" : "Fallback manual"}</Badge>
          </div>
          <div style={{ color: C.text }}>{item.description}</div>
          <div style={{ display: "grid", gridTemplateColumns: "1.05fr 0.95fr", gap: 14 }}>
            <div style={{ padding: 18, borderRadius: 18, background: "#08172E", color: "#fff" }}>
              <div style={{ fontSize: 12, fontWeight: 800, letterSpacing: 0.4, color: "#8FD3FF" }}>SIGUIENTE PASO</div>
              <div style={{ marginTop: 10, fontSize: 24, lineHeight: 1.2, fontWeight: 800 }}>{nextStep}</div>
              <div style={{ marginTop: 12, color: "rgba(255,255,255,0.72)" }}>
                Tiempo estimado: {estimatedTime}
              </div>
            </div>
            <div className="glass-card" style={{ padding: 18, background: "#FCFDFF" }}>
              <div style={{ fontSize: 12, fontWeight: 800, letterSpacing: 0.4, color: C.textMuted }}>RESUMEN DEL CASO</div>
              <div style={{ display: "grid", gap: 10, marginTop: 14 }}>
                <div style={{ display: "flex", justifyContent: "space-between", gap: 12 }}>
                  <span style={{ color: C.textMuted }}>Analisis</span>
                  <strong style={{ color: C.success }}>Listo</strong>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between", gap: 12 }}>
                  <span style={{ color: C.textMuted }}>Pago</span>
                  <strong style={{ color: item.payment_status === "pagado" ? C.success : C.warning }}>
                    {item.payment_status === "pagado" ? "Confirmado" : "Pendiente"}
                  </strong>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between", gap: 12 }}>
                  <span style={{ color: C.textMuted }}>Documento</span>
                  <strong style={{ color: item.generated_document ? C.success : C.textMuted }}>
                    {item.generated_document ? "Disponible" : "Aun no generado"}
                  </strong>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between", gap: 12 }}>
                  <span style={{ color: C.textMuted }}>Radicacion</span>
                  <strong style={{ color: item.status === "radicado" ? C.success : C.textMuted }}>
                    {item.status === "radicado" ? "Completada" : "Pendiente"}
                  </strong>
                </div>
              </div>
            </div>
          </div>
          <div style={{ padding: 16, borderRadius: 16, background: C.primaryLight }}>
            <div style={{ fontWeight: 800, color: C.text }}>{item.routing?.primary_target?.name || "Sin destino"}</div>
            <div style={{ color: C.textMuted, marginTop: 6 }}>{item.routing?.subject || "Sin asunto sugerido"}</div>
          </div>
          <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
            {item.generated_document && <Button variant="outline" onClick={() => onViewDocument(item)} style={{ width: "fit-content" }}>Abrir documento</Button>}
            <Button variant="ghost" style={{ background: "#EEF4FF", color: C.primary }} onClick={onGoNextStage}>
              Ver siguiente etapa
            </Button>
          </div>
        </div>
      </SessionCard>

      <SessionCard title="Continuidad del caso" subtitle="Esto es lo siguiente que puede necesitar tu tramite despues del estado actual.">
        <div style={{ display: "grid", gap: 12 }}>
          {continuationOptions.map((option) => (
            <div key={option} className="glass-card" style={{ padding: 16, background: "#FCFDFF" }}>
              <div style={{ color: C.text, fontWeight: 700 }}>{option}</div>
            </div>
          ))}
          <div style={{ color: C.textMuted, fontSize: 14 }}>
            Cuando una continuidad implique nuevo cobro, lo veras claramente dentro del panel y tambien en las notificaciones del caso.
          </div>
        </div>
      </SessionCard>

      <SessionCard title="Trazabilidad post-radicado" subtitle="Comprobante, estado del correo al cliente y siguiente paso operativo.">
        <div style={{ display: "grid", gridTemplateColumns: "1.05fr 0.95fr", gap: 14 }}>
          <div className="glass-card" style={{ padding: 18, background: "#FCFDFF" }}>
            <div style={{ fontSize: 12, fontWeight: 800, letterSpacing: 0.4, color: C.textMuted }}>COMPROBANTE Y CANAL</div>
            <div style={{ display: "grid", gap: 10, marginTop: 14 }}>
              <div style={{ display: "flex", justifyContent: "space-between", gap: 12 }}>
                <span style={{ color: C.textMuted }}>Tipo de soporte</span>
                <strong style={{ color: C.text }}>{guidance.proof_type || "Pendiente"}</strong>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", gap: 12 }}>
                <span style={{ color: C.textMuted }}>Radicado o comprobante</span>
                <strong style={{ color: item.status === "radicado" ? C.success : C.text }}>
                  {submissionSummary.radicado || routingSnapshot.radicado || "Pendiente"}
                </strong>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", gap: 12 }}>
                <span style={{ color: C.textMuted }}>Canal usado</span>
                <strong style={{ color: C.text }}>{submissionSummary.last_channel || guidance.channel || "Pendiente"}</strong>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", gap: 12 }}>
                <span style={{ color: C.textMuted }}>Destino</span>
                <strong style={{ color: C.text }}>{submissionSummary.last_destination || routingSnapshot.destination_name || "Pendiente"}</strong>
              </div>
              <div style={{ color: C.textMuted, fontSize: 14, lineHeight: 1.6 }}>
                {proofDeliveryChannels.length
                  ? `Recibiras o podras validar este soporte por: ${proofDeliveryChannels.join(", ")}.`
                  : "Cuando el canal responda, el comprobante quedara visible tambien en este panel."}
              </div>
            </div>
          </div>
          <div className="glass-card" style={{ padding: 18, background: "#FCFDFF" }}>
            <div style={{ fontSize: 12, fontWeight: 800, letterSpacing: 0.4, color: C.textMuted }}>NOTIFICACION AL CLIENTE</div>
              <div style={{ display: "grid", gap: 10, marginTop: 14 }}>
                <div style={{ display: "flex", justifyContent: "space-between", gap: 12 }}>
                  <span style={{ color: C.textMuted }}>Correo post-radicado</span>
                  <strong style={{ color: postRadicadoStatusColor }}>{postRadicadoStatusLabel}</strong>
                </div>
              <div style={{ display: "flex", justifyContent: "space-between", gap: 12 }}>
                <span style={{ color: C.textMuted }}>Se envia a</span>
                <strong style={{ color: C.text }}>{item.usuario_email || "Sin correo"}</strong>
              </div>
                <div style={{ display: "flex", justifyContent: "space-between", gap: 12 }}>
                  <span style={{ color: C.textMuted }}>Tiempo estimado de respuesta</span>
                  <strong style={{ color: C.text }}>{estimatedTime}</strong>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between", gap: 12 }}>
                  <span style={{ color: C.textMuted }}>Asunto</span>
                  <strong style={{ color: C.text, textAlign: "right" }}>{emailStatus.subject || "Pendiente"}</strong>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between", gap: 12 }}>
                  <span style={{ color: C.textMuted }}>Ultimo intento</span>
                  <strong style={{ color: C.text }}>{emailStatus.attempted_at ? shortDate(emailStatus.attempted_at) : "Pendiente"}</strong>
                </div>
                <div style={{ color: C.textMuted, fontSize: 14, lineHeight: 1.6 }}>
                  {emailStatusDetails}
                </div>
              </div>
            </div>
        </div>
        <div className="glass-card" style={{ padding: 18, background: "#F8FAFD", marginTop: 14 }}>
          <div style={{ fontSize: 12, fontWeight: 800, letterSpacing: 0.4, color: C.textMuted }}>SIGUIENTE PASO OPERATIVO</div>
          <div style={{ marginTop: 10, fontSize: 20, lineHeight: 1.3, fontWeight: 800, color: C.text }}>{nextStep}</div>
          {!!continuityOffers.length && (
            <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginTop: 14 }}>
              {continuityOffers.map((offer) => (
                <Badge key={offer} color={C.primary}>{offer}</Badge>
              ))}
            </div>
          )}
        </div>
      </SessionCard>

      <SessionCard title="Soportes y trazabilidad tecnica" subtitle="Solo abre estas secciones cuando necesites revisar detalle operativo o evidencia.">
        <div style={{ display: "grid", gap: 12 }}>
          <details style={{ border: `1px solid ${C.border}`, borderRadius: 16, background: "#FCFDFF", padding: 16 }}>
            <summary style={{ cursor: "pointer", fontWeight: 800, color: C.text }}>Archivos y evidencias</summary>
            <div style={{ display: "grid", gap: 10, marginTop: 14 }}>
              {files.length ? files.map((file) => (
                <div key={file.id} style={{ display: "flex", justifyContent: "space-between", gap: 12, padding: 14, borderRadius: 14, border: `1px solid ${C.border}` }}>
                  <div>
                    <div style={{ fontWeight: 700, color: C.text }}>{file.original_name}</div>
                    <div style={{ color: C.textMuted, fontSize: 13 }}>{file.file_kind} - {Math.round(file.file_size / 1024)} KB</div>
                  </div>
                  <a href={`${apiBase}/files/${file.id}`} target="_blank" rel="noreferrer" style={{ color: C.primary, textDecoration: "none", fontWeight: 700 }}>Abrir</a>
                </div>
              )) : <div style={{ color: C.textMuted }}>Sin archivos asociados.</div>}
            </div>
          </details>

          <details style={{ border: `1px solid ${C.border}`, borderRadius: 16, background: "#FCFDFF", padding: 16 }}>
            <summary style={{ cursor: "pointer", fontWeight: 800, color: C.text }}>Intentos de envio</summary>
            <div style={{ display: "grid", gap: 10, marginTop: 14 }}>
              {attempts.length ? attempts.map((attempt) => (
                <div key={attempt.id} style={{ padding: 14, borderRadius: 14, border: `1px solid ${C.border}` }}>
                  <div style={{ display: "flex", justifyContent: "space-between", gap: 12 }}>
                    <strong style={{ color: C.text }}>{attempt.channel}</strong>
                    <Badge color={attempt.radicado ? C.success : C.primary}>{attempt.status}</Badge>
                  </div>
                  <div style={{ color: C.textMuted, marginTop: 8 }}>{attempt.destination_name || "Destino manual"}</div>
                  <div style={{ color: C.textMuted }}>{attempt.destination_contact || "Sin contacto"}</div>
                  {attempt.radicado && <div style={{ marginTop: 8, color: C.success, fontWeight: 700 }}>Radicado: {attempt.radicado}</div>}
                </div>
              )) : <div style={{ color: C.textMuted }}>No hay envios registrados.</div>}
            </div>
          </details>

          <details style={{ border: `1px solid ${C.border}`, borderRadius: 16, background: "#FCFDFF", padding: 16 }}>
            <summary style={{ cursor: "pointer", fontWeight: 800, color: C.text }}>Timeline tecnico</summary>
            <div style={{ display: "grid", gap: 10, marginTop: 14 }}>
              {timeline.length ? timeline.map((event) => (
                <div key={event.id} style={{ padding: 14, borderRadius: 14, border: `1px solid ${C.border}` }}>
                  <div style={{ display: "flex", justifyContent: "space-between", gap: 12 }}>
                    <strong style={{ color: C.text }}>{event.event_type}</strong>
                    <span style={{ color: C.textMuted, fontSize: 13 }}>{shortDate(event.created_at)}</span>
                  </div>
                  <pre style={{ margin: "8px 0 0", whiteSpace: "pre-wrap", color: C.textMuted, fontFamily: "'DM Sans', sans-serif" }}>{JSON.stringify(event.payload || {}, null, 2)}</pre>
                </div>
              )) : <div style={{ color: C.textMuted }}>Sin eventos todavia.</div>}
            </div>
          </details>
        </div>
      </SessionCard>
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
    ...defaultIntakeFields,
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
  const [wizardStep, setWizardStep] = useState(1);

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
  const guidedMissing = useMemo(() => getGuidedIntakeMissing(form), [form]);
  const previewGateIssues = useMemo(() => getPreviewGateIssues(form), [form]);
  const composedDescription = useMemo(() => buildStructuredDescription(form), [form]);
  const analysisReady =
    !!form.category &&
    (form.description.trim().length >= 20 || composedDescription.trim().length >= 120) &&
    guidedMissing.length === 0 &&
    previewGateIssues.length === 0;
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
            Desde aquí puedes crear un trámite, pagar el documento, revisar si ya fue radicado y entender cuál es el siguiente paso sin salirte del flujo.
          </p>
          <div style={{ display: "grid", gridTemplateColumns: "1.05fr 0.95fr", gap: 18, marginTop: 24 }}>
            <div style={{ padding: 18, borderRadius: 18, background: "rgba(255,255,255,0.06)", border: "1px solid rgba(255,255,255,0.08)" }}>
              <div style={{ fontSize: 12, fontWeight: 800, letterSpacing: 0.4, color: "#8FD3FF" }}>QUÉ PUEDES HACER AHORA</div>
              <div style={{ marginTop: 12, display: "grid", gap: 10, color: "rgba(255,255,255,0.84)" }}>
                <div>1. Analizar un caso gratis y ver la recomendación.</div>
                <div>2. Pagar solo cuando decidas activar el documento.</div>
                <div>3. Seguir la radicación y los pasos posteriores desde el expediente.</div>
              </div>
            </div>
            <div style={{ padding: 18, borderRadius: 18, background: "rgba(255,255,255,0.06)", border: "1px solid rgba(255,255,255,0.08)" }}>
              <div style={{ fontSize: 12, fontWeight: 800, letterSpacing: 0.4, color: "#8FD3FF" }}>PROMESA DEL SERVICIO</div>
              <div style={{ marginTop: 12, fontSize: 24, fontWeight: 800 }}>Análisis gratis y radicación en menos de 5 minutos cuando el canal lo permite.</div>
            </div>
          </div>
          <div style={{ display: "flex", gap: 12, marginTop: 24, flexWrap: "wrap" }}>
            <Button onClick={() => setActiveTab("nuevo")}>Crear nuevo trámite</Button>
            <Button variant="ghost" style={{ color: "#fff", background: "rgba(255,255,255,0.08)", border: "1px solid rgba(255,255,255,0.1)" }} onClick={() => setActiveTab("tramites")}>
              Ver mis expedientes
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
        <div className="glass-card" style={{ padding: 24, display: "grid", gap: 18 }}>
          <div style={{ display: "flex", justifyContent: "space-between", gap: 16, alignItems: "end", flexWrap: "wrap" }}>
            <div>
              <Badge color={C.accent}>Flujo guiado</Badge>
              <h2 style={{ marginTop: 10, fontSize: 34, lineHeight: 1.1, color: C.text, fontFamily: "'Playfair Display', serif" }}>
                Nuevo trámite, paso a paso.
              </h2>
              <p style={{ marginTop: 10, color: C.textMuted, maxWidth: 620 }}>
                Ahora el cliente puede avanzar o retroceder con flechas visibles durante todo el proceso.
              </p>
            </div>
            <Button variant="ghost" onClick={resetWizard}>Reiniciar flujo</Button>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12 }}>
            {wizardSteps.map((step) => (
              <button
                key={step.id}
                type="button"
                onClick={() => setWizardStep(step.id)}
                style={{
                  textAlign: "left",
                  padding: 16,
                  borderRadius: 18,
                  border: wizardStep === step.id ? `2px solid ${C.primary}` : `1px solid ${C.border}`,
                  background: wizardStep === step.id ? "#EEF4FF" : "#fff",
                  cursor: "pointer",
                }}
              >
                <div style={{ fontSize: 12, color: step.ready ? C.accent : C.textMuted, fontWeight: 800 }}>PASO {step.id}</div>
                <div style={{ marginTop: 8, fontSize: 18, fontWeight: 800, color: C.text }}>{step.label}</div>
                <div style={{ marginTop: 6, color: C.textMuted, fontSize: 13 }}>{step.ready ? "Listo o en progreso" : "Pendiente"}</div>
              </button>
            ))}
          </div>
        </div>

        {wizardStep === 1 && (
          <StepShell
            stepNumber={1}
            title="Perfil jurídico obligatorio"
            subtitle="Se usa en el documento, el asunto del correo y la radicación."
            onNext={() => setWizardStep(2)}
            nextDisabled={!profileReady}
            nextLabel="Continuar al análisis"
          >
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
            <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
              <Button onClick={() => onSaveProfile(profile)}>Guardar perfil</Button>
              <Badge color={profileReady ? C.success : C.warning}>{profileReady ? "Perfil completo" : "Faltan datos"}</Badge>
            </div>
          </StepShell>
        )}

        {wizardStep === 2 && (
          <StepShell
            stepNumber={2}
            title="Análisis del caso"
            subtitle="Combina IA jurídica con reglas operativas y destino sugerido."
            onBack={() => setWizardStep(1)}
            onNext={() => setWizardStep(3)}
            nextDisabled={!analysisReady}
            nextLabel="Continuar al preview"
          >
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12 }}>
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
            <GuidedIntakeFields form={form} setForm={setForm} missingFields={guidedMissing} />
            <PreviewGateCard issues={previewGateIssues} />
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
              <Button onClick={async () => setPreview(await onPreview({ ...form, description: composedDescription }))} disabled={!analysisReady || loading} icon={Search}>
                {loading ? "Analizando..." : "Generar preview"}
              </Button>
            </div>
            <div style={{ color: C.textMuted, fontSize: 13, lineHeight: 1.6 }}>
              La plataforma combinará tus respuestas estructuradas y tu relato libre para construir un análisis más sólido.
            </div>
          </StepShell>
        )}

        {wizardStep === 3 && (() => {
          const intakeReview = preview?.facts?.intake_review || null;
          const documentRuleReview = preview?.facts?.document_rule_review || null;
          const hasBlockingIssues = !!(intakeReview?.blocking_issues || []).length;
          const hasDocumentRuleBlockers = !!(documentRuleReview?.blocking_issues || []).length;
          const actionSpecificMissing = getActionSpecificMissing(preview?.recommended_action, form);
          const actionSpecificIssues = getActionSpecificIssues(preview?.recommended_action, form);
          const hasActionSpecificBlockers = actionSpecificMissing.length > 0 || actionSpecificIssues.length > 0;

          return (
          <StepShell
            stepNumber={3}
            title="Preview gratis y expediente"
            subtitle="Se guarda antes del pago para que quede trazabilidad."
            onBack={() => setWizardStep(2)}
            onNext={() => setWizardStep(4)}
            nextDisabled={!preview || hasBlockingIssues || hasActionSpecificBlockers || hasDocumentRuleBlockers}
            nextLabel="Continuar al pago"
          >
            {!preview ? (
              <div style={{ color: "#92400E", background: "#FFFBEB", border: "1px solid #FDE68A", padding: 14, borderRadius: 14 }}>
                Primero genera el preview desde el paso anterior para ver recomendación, destino y advertencias.
              </div>
            ) : (
              <>
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
                <ActionSpecificQuestions
                  recommendedAction={preview.recommended_action}
                  form={form}
                  setForm={setForm}
                  missingFields={actionSpecificMissing}
                  issues={actionSpecificIssues}
                />
                <DocumentRuleReviewCard review={documentRuleReview} />
                <IntakeReviewCard review={intakeReview} />
                {preview.warnings?.map((warning) => <div key={warning} style={{ color: "#92400E", background: "#FFFBEB", border: "1px solid #FDE68A", padding: 14, borderRadius: 14 }}>{warning}</div>)}
                <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
                  <Button
                    onClick={async () => {
                      const detail = await onCreateCase({ ...form, description: composedDescription, attachment_ids: tempFiles.map((item) => item.id) });
                      setDraftDetail(detail);
                      setWizardStep(4);
                    }}
                    disabled={!profileReady || hasBlockingIssues || hasActionSpecificBlockers || hasDocumentRuleBlockers}
                  >
                    Guardar expediente
                  </Button>
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
                title="4. Pago real y documento"
                caseItem={draftDetail.case}
                catalog={catalog}
                onCreateWompiSession={onCreateWompiSession}
                onGetPayment={onGetPayment}
                onRefreshCase={onRefreshCase}
                loading={loading}
              />
            ) : (
              <div className="glass-card" style={{ padding: 24, color: C.textMuted }}>
                Guarda primero el expediente en el paso 3 para habilitar el pago y la activación del documento.
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
              onRefreshCase={onRefreshCase}
              loading={loading}
            />
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
                    <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
                      <Button onClick={() => onSubmitCase(activeCaseDetail.case.id, { mode: "auto", notes: submissionNote })} disabled={!activeCaseDetail.case.generated_document}>Ejecutar envio automatico</Button>
                      <Button variant="outline" onClick={() => onSubmitCase(activeCaseDetail.case.id, { mode: "manual_contact", manual_contact: manualContact, notes: submissionNote })}>Usar contacto manual</Button>
                      <Button variant="ghost" onClick={() => onSubmitCase(activeCaseDetail.case.id, { mode: "presencial", notes: submissionNote })}>Activar modo presencial</Button>
                    </div>
                  </div>
                  <div style={{ padding: 18, borderRadius: 18, border: `1px solid ${C.border}`, background: "#FCFDFF", display: "grid", gap: 12 }}>
                    <div style={{ fontSize: 12, fontWeight: 800, letterSpacing: "0.08em", color: C.textMuted }}>RADICADO MANUAL Y EVIDENCIA</div>
                    <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
                      <TextInput value={radicadoManual} onChange={(event) => setRadicadoManual(event.target.value)} placeholder="Numero de radicado manual" />
                      <Button variant="secondary" onClick={() => onManualRadicado(activeCaseDetail.case.id, { radicado: radicadoManual, notes: radicadoNote })}>Registrar radicado manual</Button>
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
          "Seguimiento: después del radicado verás qué puede pasar y cuál sería el siguiente cobro por continuidad, si aplica.",
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
