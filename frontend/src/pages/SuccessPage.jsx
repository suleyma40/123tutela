import React, { useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { CheckCircle2, Trophy, FileText, Upload, Send, Loader2, Mail, MessageSquareMore, UserCheck, Users } from 'lucide-react';
import Navbar from '../components/Navbar';
import { api, extractError } from '../lib/api';
import { trackEvent } from '../lib/analytics';
import { RAFFLE_LONG_COPY, RAFFLE_MONTH_LABEL, RAFFLE_PRIZE_LABEL } from '../lib/launchConfig';

const QUESTION_FIELD_MAP = {
  medical_support: 'medical_support_detail',
  eps_barrier: 'prior_claim_result',
};

const buildPromptList = (caseData) => {
  const caseItem = caseData?.case || {};
  const agentPrompts = (((caseItem.facts || {}).agent_state || {}).ops_follow_up_prompts || [])
    .filter((item) => item && item.id && item.question);
  if (agentPrompts.length) return agentPrompts;
  return ((caseItem.pending_questions || []).map((item) => ({
    id: item?.field || item?.id,
    question: item?.question,
    placeholder: '',
    multiline: true,
    why: item?.reason || '',
  }))).filter((item) => item.id && item.question);
};

const buildSuggestedAttachments = (caseData) => {
  const action = String(caseData?.case?.recommended_action || '').toLowerCase();
  const category = String(caseData?.case?.category || '').toLowerCase();
  if (action.includes('desacato') || action.includes('impugnacion')) {
    return ['Cédula', 'Fallo de tutela', 'Prueba de incumplimiento o inconformidad', 'Historia clínica o soporte actual'];
  }
  if (category.includes('salud') || action.includes('tutela')) {
    return ['Cédula', 'Orden médica o fórmula', 'Historia clínica reciente', 'Respuesta/negativa de EPS', 'Radicado o prueba de gestión previa'];
  }
  if (category.includes('trans')) {
    return ['Cédula', 'Comparendo o acto', 'Estado de cuenta/SIMIT', 'Radicado previo', 'Prueba de afectación actual'];
  }
  if (category.includes('banco') || category.includes('dato')) {
    return ['Cédula', 'Extracto o soporte de cobro/reporte', 'Reclamación previa', 'Respuesta de la entidad', 'Soporte de perjuicio actual'];
  }
  return ['Cédula', 'Documento o acto relacionado', 'Radicado previo', 'Respuesta recibida', 'Prueba de afectación actual'];
};

const buildDescription = (form) => {
  return [
    form.case_story,
    form.key_dates ? `Fechas clave: ${form.key_dates}` : '',
    form.prior_claim_result ? `Barrera o respuesta: ${form.prior_claim_result}` : '',
    form.prior_petition_same_cause ? `Peticion previa por misma causa: ${form.prior_petition_same_cause}` : '',
    form.prior_petition_date ? `Fecha de peticion previa: ${form.prior_petition_date}` : '',
    form.prior_petition_response ? `Respuesta a peticion previa: ${form.prior_petition_response}` : '',
    form.urgency_detail ? `Urgencia actual: ${form.urgency_detail}` : '',
    form.extra_details,
  ].filter(Boolean).join('\n\n');
};

const buildFormDataPayload = (form) => {
  const payload = { ...form };
  delete payload.name;
  delete payload.email;
  delete payload.phone;
  delete payload.document_number;
  delete payload.city;
  delete payload.department;
  delete payload.address;
  payload.is_third_party = Boolean(form.beneficiary_name || form.beneficiary_document || form.beneficiary_relationship);
  return payload;
};

const normalizeOperationalCopy = (text = '') =>
  String(text)
    .replace(/produccion humana/gi, 'equipo experto')
    .replace(/redaccion humana/gi, 'elaboracion por especialistas')
    .replace(/redacte sin repreguntas ni retrasos/gi, 'elabore el documento sin reprocesos ni demoras');

const isTutelaFlow = (caseData) => {
  const action = String(caseData?.case?.recommended_action || caseData?.case?.workflow_type || '').toLowerCase();
  return action.includes('tutela');
};

const StatusPill = ({ children, tone = 'default' }) => {
  const styles = {
    default: 'bg-brand/10 text-brand',
    success: 'bg-success/10 text-success',
    danger: 'bg-red-100 text-red-600',
  };
  return <span className={`px-3 py-1 rounded-full text-xs font-black ${styles[tone] || styles.default}`}>{children}</span>;
};

const completionRatio = ({ form, prompts, isThirdParty, uploadedCount, tutelaFlow }) => {
  const requiredFields = ['name', 'email', 'phone', 'document_number', 'city', 'department', 'address', 'concrete_request', 'case_story'];
  if (isThirdParty) {
    requiredFields.push('beneficiary_name', 'beneficiary_document', 'beneficiary_relationship');
  }
  if (tutelaFlow) {
    requiredFields.push('prior_petition_same_cause');
    if (String(form.prior_petition_same_cause || '').toLowerCase() === 'si') {
      requiredFields.push('prior_petition_date', 'prior_petition_response');
    }
  }
  for (const prompt of prompts || []) {
    const fieldName = QUESTION_FIELD_MAP[prompt.id] || prompt.id;
    if (fieldName && !requiredFields.includes(fieldName)) {
      requiredFields.push(fieldName);
    }
  }
  const completed = requiredFields.filter((key) => String(form[key] || '').trim()).length;
  const supportsCompleted = uploadedCount > 0 ? 1 : 0;
  const total = requiredFields.length + 1;
  return Math.round(((completed + supportsCompleted) / Math.max(1, total)) * 100);
};

const normalizePromptText = (value) =>
  String(value || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();

const dedupePrompts = (prompts = []) => {
  const seen = new Set();
  const unique = [];
  for (const item of prompts) {
    const key = normalizePromptText(item?.question);
    if (!key || seen.has(key)) continue;
    seen.add(key);
    unique.push(item);
  }
  return unique;
};

const buildStrategicQuestions = (caseData, form) => {
  const action = String(caseData?.case?.recommended_action || '').toLowerCase();
  const category = String(caseData?.case?.category || '').toLowerCase();
  const items = [];
  if (category.includes('salud') || action.includes('tutela')) {
    items.push(
      { id: 'target_entity', question: 'Entidad exacta que incumple hoy (EPS o IPS/clinica)', why: 'Define contra quien se dirige la accion principal.', multiline: false },
      { id: 'treatment_needed', question: 'Servicio exacto pendiente (terapia, cita, medicamento o cirugia)', why: 'Evita solicitudes ambiguas en el documento.', multiline: false },
      { id: 'urgency_detail', question: 'Riesgo medico actual si esto sigue igual 2-4 semanas', why: 'Sustenta urgencia y perjuicio irremediable.', multiline: true },
      { id: 'key_dates', question: 'Fechas clave: orden medica, autorizacion y ultimo reclamo', why: 'Permite linea de tiempo verificable.', multiline: true },
    );
  }
  if (action.includes('desacato')) {
    items.push(
      { id: 'key_dates', question: 'Fecha del fallo y fecha del ultimo incumplimiento', why: 'Base minima para incidente de desacato.', multiline: true },
      { id: 'prior_claim_result', question: 'Como incumplieron exactamente el fallo', why: 'Delimita hechos de incumplimiento.', multiline: true },
    );
  }
  return items.filter((item) => !String(form[item.id] || '').trim());
};

const CodeCard = ({ label, value, subtle = false }) => (
  <div className={`rounded-[2rem] border border-brand/10 p-5 ${subtle ? 'bg-brand/5' : 'bg-white'}`}>
    <p className="text-[11px] font-black uppercase tracking-wide text-brand/50 mb-2">{label}</p>
    <p className="font-mono text-lg font-black text-brand break-all">{value}</p>
  </div>
);

const TimelineStep = ({ step, title, detail, active = false, done = false }) => (
  <div className="flex gap-4">
    <div
      className={`w-6 h-6 rounded-full flex items-center justify-center shrink-0 text-[10px] font-bold ${
        done ? 'bg-success text-white' : active ? 'bg-accent text-brand' : 'bg-brand/10 text-brand/30'
      }`}
    >
      {step}
    </div>
    <div>
      <p className="font-bold text-brand text-sm">{title}</p>
      <p className="text-brand/40 text-[11px] font-medium tracking-tight">{detail}</p>
    </div>
  </div>
);

const SuccessPage = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [caseData, setCaseData] = useState(null);
  const [intakeFiles, setIntakeFiles] = useState([]);
  const fileInputRef = useRef(null);
  const [isThirdParty, setIsThirdParty] = useState(false);
  const [form, setForm] = useState({
    name: '',
    email: '',
    phone: '',
    document_number: '',
    city: '',
    department: 'Bogota D.C.',
    address: '',
    copy_email: '',
    target_entity: '',
    diagnosis: '',
    treatment_needed: '',
    urgency_detail: '',
    prior_claim_result: '',
    concrete_request: '',
    case_story: '',
    key_dates: '',
    medical_support_detail: '',
    extra_details: '',
    prior_petition_same_cause: '',
    prior_petition_date: '',
    prior_petition_response: '',
    // Datos del beneficiario (tercero)
    beneficiary_name: '',
    beneficiary_document: '',
    beneficiary_relationship: '',
  });

  const params = useMemo(() => new URLSearchParams(window.location.search), []);
  const transactionId = params.get('id');
  const paymentReferenceParam = params.get('reference');
  const caseIdParam = params.get('case_id');
  const publicTokenParam = params.get('public_token');
  const prompts = useMemo(() => dedupePrompts(buildPromptList(caseData)), [caseData]);
  const requiredAttachments = caseData?.customer_guide?.required_attachments || [];
  const suggestedAttachments = useMemo(
    () => (requiredAttachments.length ? requiredAttachments : buildSuggestedAttachments(caseData)),
    [requiredAttachments, caseData],
  );
  const uploadedFiles = caseData?.files || [];
  const opsSync = caseData?.case?.submission_summary?.ops_sync || {};
  const opsStatus = String(opsSync.status || '').toLowerCase();
  const opsSummary = normalizeOperationalCopy(caseData?.case?.facts?.agent_state?.ops_summary || '');
  const uploadedNames = uploadedFiles.map((item) => item?.original_name).filter(Boolean);

  useEffect(() => {
    const saved = localStorage.getItem('hazlopormi-guest-case');
    const stored = saved ? JSON.parse(saved) : {};
    const guestCase = {
      ...stored,
      caseId: caseIdParam || stored.caseId,
      publicToken: publicTokenParam || stored.publicToken,
    };
    if (guestCase?.caseId && guestCase?.publicToken) {
      localStorage.setItem('hazlopormi-guest-case', JSON.stringify(guestCase));
    }
    if (!guestCase?.caseId || !guestCase?.publicToken) {
      setError('No pudimos identificar tu expediente. Abre el enlace original de pago para continuar.');
      setLoading(false);
      return;
    }

    const hydrate = (responseData) => {
      setCaseData(responseData);
      setIntakeFiles([]);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
      const caseItem = responseData?.case || {};
      const intake = caseItem.facts?.intake_form || {};
      setForm((current) => ({
        ...current,
        name: caseItem.user_name || current.name,
        email: caseItem.user_email || current.email,
        phone: caseItem.user_phone || current.phone,
        document_number: intake.document_number || caseItem.user_document || current.document_number,
        city: intake.city || caseItem.user_city || current.city,
        department: intake.department || caseItem.user_department || current.department,
        address: intake.address || caseItem.user_address || current.address,
        copy_email: intake.copy_email || caseItem.user_email || current.copy_email,
        target_entity: intake.target_entity || current.target_entity,
        diagnosis: intake.diagnosis || current.diagnosis,
        treatment_needed: intake.treatment_needed || current.treatment_needed,
        urgency_detail: intake.urgency_detail || intake.ongoing_harm || current.urgency_detail,
        prior_claim_result: intake.prior_claim_result || intake.eps_response_detail || current.prior_claim_result,
        concrete_request: intake.concrete_request || current.concrete_request,
        case_story: intake.case_story || caseItem.description || current.case_story,
        key_dates: intake.key_dates || current.key_dates,
        medical_support_detail: intake.medical_support_detail || current.medical_support_detail,
        extra_details: intake.extra_details || current.extra_details,
        prior_petition_same_cause: intake.prior_petition_same_cause || current.prior_petition_same_cause,
        prior_petition_date: intake.prior_petition_date || current.prior_petition_date,
        prior_petition_response: intake.prior_petition_response || current.prior_petition_response,
        beneficiary_name: intake.beneficiary_name || current.beneficiary_name,
        beneficiary_document: intake.beneficiary_document || current.beneficiary_document,
        beneficiary_relationship: intake.beneficiary_relationship || current.beneficiary_relationship,
      }));
      setIsThirdParty(Boolean(intake.beneficiary_name || intake.beneficiary_document || intake.beneficiary_relationship));
    };

    const run = async () => {
      try {
        if (transactionId) {
          const isSimulated = transactionId.startsWith('simulated_');
          const response = isSimulated
            ? await api.post('/public/payments/simulate', {
                transaction_id: transactionId,
                reference: transactionId.replace('simulated_', ''),
                public_token: guestCase.publicToken,
              })
            : await api.post('/public/payments/wompi/reconcile', {
                transaction_id: transactionId,
                reference: paymentReferenceParam || undefined,
                public_token: guestCase.publicToken,
              });
          hydrate(response.data);
        } else if (paymentReferenceParam) {
          const response = await api.post('/public/payments/wompi/reconcile', {
            transaction_id: paymentReferenceParam,
            reference: paymentReferenceParam,
            public_token: guestCase.publicToken,
          });
          hydrate(response.data);
        } else {
          const response = await api.get(`/public/cases/${guestCase.caseId}`, {
            params: { public_token: guestCase.publicToken },
          });
          hydrate(response.data);
        }
      } catch (err) {
        setError(extractError(err, 'No pudimos verificar el estado de tu pago.'));
      } finally {
        setLoading(false);
      }
    };

    run();
  }, [transactionId, paymentReferenceParam, caseIdParam, publicTokenParam, navigate]);

  const handleFieldChange = (field, value) => {
    setForm((current) => ({ ...current, [field]: value }));
  };

  useEffect(() => {
    if (!caseData?.case?.id) return;
    const draftKey = `hazlopormi-intake-draft-${caseData.case.id}`;
    localStorage.setItem(draftKey, JSON.stringify(form));
  }, [form, caseData?.case?.id]);

  useEffect(() => {
    if (!caseData?.case?.id) return;
    const draftKey = `hazlopormi-intake-draft-${caseData.case.id}`;
    const raw = localStorage.getItem(draftKey);
    if (!raw) return;
    try {
      const draft = JSON.parse(raw);
      if (draft && typeof draft === 'object') {
        setForm((current) => ({ ...current, ...draft }));
      }
    } catch (_) {
      // ignore malformed draft
    }
  }, [caseData?.case?.id]);

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!caseData) return;
    setSubmitting(true);
    setError('');
    setSuccessMessage('');

    const saved = JSON.parse(localStorage.getItem('hazlopormi-guest-case'));

    try {
      for (const file of intakeFiles) {
        const formData = new FormData();
        formData.append('public_token', saved.publicToken);
        formData.append('file_kind', 'supporting_evidence');
        formData.append('file', file);
        await api.post(`/public/cases/${saved.caseId}/uploads`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });
      }

      const response = await api.patch(`/public/cases/${saved.caseId}/intake`, {
        public_token: saved.publicToken,
        name: form.name,
        email: form.email,
        phone: form.phone,
        document_number: form.document_number,
        city: form.city,
        department: form.department,
        address: form.address,
        description: buildDescription(form),
        form_data: buildFormDataPayload(form),
      });

      setCaseData(response.data);
      trackEvent('submit_intake', {
        case_id: saved.caseId,
        files_count: intakeFiles.length,
        is_third_party: Boolean(form.beneficiary_name || form.beneficiary_document || form.beneficiary_relationship),
      });
      setSuccessMessage('Información recibida. El expediente ya quedó listo para revisión por nuestro equipo jurídico.');
      if (saved?.caseId) {
        localStorage.removeItem(`hazlopormi-intake-draft-${saved.caseId}`);
      }
      setIntakeFiles([]);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    } catch (err) {
      setError(extractError(err, 'No pudimos guardar la informacion.'));
    } finally {
      setSubmitting(false);
    }
  };

  const strategicQuestions = useMemo(() => buildStrategicQuestions(caseData, form), [caseData, form]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#F5F7FB]">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-brand animate-spin mx-auto mb-4" />
          <p className="font-bold text-slate-900">Verificando tu pago...</p>
        </div>
      </div>
    );
  }

  const isPaid = caseData?.case?.payment_status === 'pagado';
  const isDelivered = caseData?.case?.status === 'entregado';
  const customerCaseCode = caseData?.latest_payment?.customer_case?.code || caseData?.customer_summary?.customer_case?.code;
  const invoiceNumber = caseData?.latest_payment?.invoice?.number || caseData?.customer_summary?.invoice?.number;
  const paymentReference = caseData?.latest_payment?.reference || caseData?.case?.payment_reference;
  const raffleCode = caseData?.latest_payment?.raffle?.code || caseData?.customer_summary?.raffle?.code;
  const fallbackCaseId = caseData?.case?.id ? String(caseData.case.id).slice(0, 8).toUpperCase() : '';
  const unifiedTrackingCode = raffleCode || customerCaseCode || paymentReference || (fallbackCaseId ? `EXP-${fallbackCaseId}` : '');
  const tutelaFlow = isTutelaFlow(caseData);
  const uploadedSupportCount = (uploadedFiles?.length || 0) + intakeFiles.length;
  const progress = completionRatio({
    form,
    prompts,
    isThirdParty,
    uploadedCount: uploadedSupportCount,
    tutelaFlow,
  });
  const caseStatus = String(caseData?.case?.status || '').toLowerCase();
  const isReadyForLegalTeam = ['pagado_en_revision', 'en_revision', 'entregado'].includes(caseStatus) || Boolean(successMessage);

  return (
    <div className="min-h-screen bg-[#F5F7FB] text-slate-900">
      <Navbar />

      <main className="pt-32 pb-20 px-6">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-10">
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              className="bg-[#36D399] text-white w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-6 shadow-xl"
            >
              <CheckCircle2 size={40} />
            </motion.div>
            <h1 className="text-4xl font-extrabold text-slate-900 mb-4">
              {isPaid ? 'Pago confirmado' : 'Pago en procesamiento'}
            </h1>
            <p className="text-slate-500 text-lg max-w-2xl mx-auto font-medium">
              {isPaid
                ? 'Tu pago ya quedó confirmado. Ahora necesitamos completar tus datos y documentos de soporte para que nuestro equipo jurídico elabore tu documento sin demoras.'
                : 'Estamos esperando la confirmación final del pago. Esto puede tardar unos minutos.'}
            </p>
          </div>

          <div className="grid lg:grid-cols-5 gap-8">
            <div className="lg:col-span-3 space-y-8">
              {(unifiedTrackingCode || invoiceNumber || paymentReference) && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                className="bg-white p-8 rounded-[2rem] shadow-[0_18px_55px_rgba(18,35,61,0.06)] border border-slate-200"
              >
                  <p className="text-xs font-black uppercase tracking-widest text-slate-400 mb-3">Tu expediente</p>
                  <h3 className="text-2xl font-extrabold text-slate-900 mb-3">Codigo unico de expediente</h3>
                  <p className="text-sm text-slate-500 font-medium mb-6">
                    Este es el mismo codigo para expediente y participacion en rifa.
                  </p>
                  <div className="grid gap-4">
                    {unifiedTrackingCode && <CodeCard label="Codigo unico" value={unifiedTrackingCode} subtle />}
                  </div>
                </motion.div>
              )}

              {unifiedTrackingCode && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                className="bg-[#08172E] text-white p-8 rounded-[2rem] shadow-[0_18px_55px_rgba(18,35,61,0.12)] relative overflow-hidden"
              >
                  <div className="absolute top-0 right-0 p-8 opacity-10">
                    <Trophy size={120} />
                  </div>
                  <div className="relative z-10">
                    <p className="text-[#19B7FF] font-black uppercase text-xs tracking-widest mb-2">Codigo de participacion</p>
                    <h3 className="text-2xl font-extrabold mb-3">Rifa {RAFFLE_MONTH_LABEL}</h3>
                    <p className="text-white/80 text-sm font-medium mb-4 max-w-xl">
                      Este codigo coincide con tu expediente y confirma tu participacion con pago aprobado.
                    </p>
                    <div className="bg-white/10 border border-white/20 inline-block px-6 py-3 rounded-2xl font-mono text-3xl font-black tracking-tighter">
                      {unifiedTrackingCode}
                    </div>
                    <div className="mt-4">
                      <button
                        type="button"
                        onClick={() => {
                          const content = `Codigo rifa y expediente: ${unifiedTrackingCode}\nFecha: ${new Date().toLocaleString('es-CO')}\nRifa: ${RAFFLE_MONTH_LABEL}`;
                          const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
                          const url = URL.createObjectURL(blob);
                          const a = document.createElement('a');
                          a.href = url;
                          a.download = `codigo-rifa-${String(unifiedTrackingCode).replace(/\s+/g, '-')}.txt`;
                          a.click();
                          URL.revokeObjectURL(url);
                        }}
                        className="inline-flex items-center rounded-xl border border-white/30 bg-white/10 px-4 py-2 text-xs font-black text-white hover:bg-white/20 transition-colors"
                      >
                        Descargar codigo
                      </button>
                    </div>
                  </div>
                </motion.div>
              )}

              {isPaid && !isDelivered && (
                <div className="bg-white p-8 md:p-12 rounded-[2rem] shadow-[0_18px_55px_rgba(18,35,61,0.06)] border border-slate-200">
                  <h3 className="text-2xl font-extrabold text-slate-900 mb-8 flex items-center gap-3">
                    <MessageSquareMore className="text-[#19B7FF]" /> Completar expediente
                  </h3>

                  <div className="grid gap-4 mb-8">
                    <div className="rounded-[2rem] border border-slate-200 bg-[#F8FBFF] p-6">
                      <div className="flex flex-wrap items-center justify-between gap-3">
                        <div>
                          <p className="text-sm font-black uppercase tracking-wide text-slate-900 mb-2">Estado del expediente</p>
                          <p className="text-sm text-slate-500 font-medium">
                            {opsSummary || 'Estamos consolidando tu expediente para que nuestros especialistas elaboren tu documento.'}
                          </p>
                        </div>
                        {isReadyForLegalTeam && <StatusPill tone="success">Listo para revisión jurídica</StatusPill>}
                        {!isReadyForLegalTeam && opsStatus === 'error' && <StatusPill tone="danger">Sincronización con incidencia</StatusPill>}
                        {!isReadyForLegalTeam && opsStatus !== 'error' && <StatusPill>Pendiente de completar</StatusPill>}
                      </div>
                    </div>

                    <div className="grid md:grid-cols-2 gap-4">
                      <div className="rounded-[2rem] border border-slate-200 p-5">
                        <p className="text-xs font-black uppercase tracking-wide text-slate-400 mb-3">Ya tenemos</p>
                        <div className="flex flex-wrap gap-2">
                          <span className="px-3 py-1 rounded-full bg-success/10 text-success text-xs font-bold">Pago confirmado</span>
                          {unifiedTrackingCode && <span className="px-3 py-1 rounded-full bg-brand/5 text-brand text-xs font-bold">Codigo unico</span>}
                          {form.name && <span className="px-3 py-1 rounded-full bg-brand/5 text-brand text-xs font-bold">Nombre</span>}
                          {form.document_number && <span className="px-3 py-1 rounded-full bg-brand/5 text-brand text-xs font-bold">Documento</span>}
                          {form.city && <span className="px-3 py-1 rounded-full bg-brand/5 text-brand text-xs font-bold">Ciudad</span>}
                          {uploadedNames.length > 0 && <span className="px-3 py-1 rounded-full bg-brand/5 text-brand text-xs font-bold">{uploadedNames.length} soporte(s)</span>}
                        </div>
                      </div>

                      <div className="rounded-[2rem] border border-slate-200 p-5">
                        <p className="text-xs font-black uppercase tracking-wide text-slate-400 mb-3">Pendiente para elaboración</p>
                        <p className="text-sm text-slate-500 font-medium">
                          {prompts.length
                            ? `Responde ${prompts.length} bloque${prompts.length === 1 ? '' : 's'} de información y sube los soportes que tengas disponibles.`
                            : 'El expediente ya tiene base suficiente. Si deseas, agrega soportes o contexto adicional antes de enviarlo a nuestros especialistas.'}
                        </p>
                      </div>
                    </div>

                    <div className="rounded-[2rem] border border-[#19B7FF]/20 bg-[#19B7FF]/10 p-5">
                      <p className="text-sm font-black text-slate-900 mb-2">¿Qué pasa después de enviar esto?</p>
                      <p className="text-sm text-slate-600 font-medium">
                        Nuestro equipo jurídico revisará tus respuestas, validará los anexos y te contactará solo si falta información crítica. El plazo de entrega corre desde que el expediente quede completo.
                      </p>
                    </div>
                  </div>

                  <form onSubmit={handleSubmit} className="space-y-8">
                    {/* Selector: nombre propio o tercero */}
                    <div className="rounded-[2rem] border border-brand/10 bg-brand/5 p-6">
                      <p className="text-sm font-black uppercase tracking-wide text-brand mb-4">¿Para quién es el documento?</p>
                      <div className="grid grid-cols-2 gap-4">
                        <button
                          type="button"
                          onClick={() => setIsThirdParty(false)}
                          className={`flex items-center gap-3 p-4 rounded-2xl border-2 transition-all font-bold text-sm ${
                            !isThirdParty
                              ? 'border-[#0D68FF] bg-[#0D68FF]/10 text-[#0D68FF]'
                              : 'border-slate-200 bg-white text-slate-500 hover:border-slate-300'
                          }`}
                        >
                          <UserCheck size={20} /> A mi nombre
                        </button>
                        <button
                          type="button"
                          onClick={() => setIsThirdParty(true)}
                          className={`flex items-center gap-3 p-4 rounded-2xl border-2 transition-all font-bold text-sm ${
                            isThirdParty
                              ? 'border-[#0D68FF] bg-[#0D68FF]/10 text-[#0D68FF]'
                              : 'border-slate-200 bg-white text-slate-500 hover:border-slate-300'
                          }`}
                        >
                          <Users size={20} /> A nombre de otra persona
                        </button>
                      </div>
                    </div>

                    <p className="text-xs font-black uppercase tracking-wide text-slate-400">
                      {isThirdParty ? 'Datos de quien solicita (tú)' : 'Tus datos personales'}
                    </p>
                    <div className="grid md:grid-cols-2 gap-6">
                      <div className="space-y-2">
                        <label className="text-sm font-bold text-brand ml-1">Nombre completo</label>
                        <input required type="text" className="input-field" value={form.name} onChange={(e) => handleFieldChange('name', e.target.value)} />
                      </div>
                      <div className="space-y-2">
                        <label className="text-sm font-bold text-brand ml-1">Correo electrónico</label>
                        <input required type="email" className="input-field" value={form.email} onChange={(e) => handleFieldChange('email', e.target.value)} />
                      </div>
                    </div>

                    <div className="grid md:grid-cols-2 gap-6">
                      <div className="space-y-2">
                        <label className="text-sm font-bold text-brand ml-1">WhatsApp / celular</label>
                        <input required type="text" className="input-field" value={form.phone} onChange={(e) => handleFieldChange('phone', e.target.value)} />
                      </div>
                      <div className="space-y-2">
                        <label className="text-sm font-bold text-brand ml-1">Cédula de ciudadanía</label>
                        <input required type="text" className="input-field" value={form.document_number} onChange={(e) => handleFieldChange('document_number', e.target.value)} />
                      </div>
                    </div>

                    <div className="grid md:grid-cols-2 gap-6">
                      <div className="space-y-2">
                        <label className="text-sm font-bold text-brand ml-1">Ciudad</label>
                        <input required type="text" className="input-field" value={form.city} onChange={(e) => handleFieldChange('city', e.target.value)} />
                      </div>
                      <div className="space-y-2">
                        <label className="text-sm font-bold text-brand ml-1">Departamento</label>
                        <input required type="text" className="input-field" value={form.department} onChange={(e) => handleFieldChange('department', e.target.value)} />
                      </div>
                    </div>

                    <div className="space-y-2">
                      <label className="text-sm font-bold text-brand ml-1">Dirección de notificación</label>
                      <input required type="text" className="input-field" value={form.address} onChange={(e) => handleFieldChange('address', e.target.value)} />
                    </div>

                    {/* Datos del beneficiario (tercero) */}
                    {isThirdParty && (
                      <>
                        <div className="rounded-[2rem] border border-amber-200 bg-amber-50 p-6">
                          <p className="text-sm font-black uppercase tracking-wide text-amber-700 mb-2">Datos del beneficiario</p>
                          <p className="text-sm text-amber-600 font-medium">
                            Completa los datos de la persona a cuyo nombre se elaborará el documento legal.
                          </p>
                        </div>
                        <div className="grid md:grid-cols-2 gap-6">
                          <div className="space-y-2">
                            <label className="text-sm font-bold text-brand ml-1">Nombre completo del beneficiario</label>
                            <input required type="text" className="input-field" placeholder="Nombre de la persona beneficiaria" value={form.beneficiary_name} onChange={(e) => handleFieldChange('beneficiary_name', e.target.value)} />
                          </div>
                          <div className="space-y-2">
                            <label className="text-sm font-bold text-brand ml-1">Cédula del beneficiario</label>
                            <input required type="text" className="input-field" placeholder="Número de documento" value={form.beneficiary_document} onChange={(e) => handleFieldChange('beneficiary_document', e.target.value)} />
                          </div>
                        </div>
                        <div className="space-y-2">
                          <label className="text-sm font-bold text-brand ml-1">Parentesco o relación</label>
                          <select
                            required
                            className="input-field"
                            value={form.beneficiary_relationship}
                            onChange={(e) => handleFieldChange('beneficiary_relationship', e.target.value)}
                          >
                            <option value="">Selecciona la relación</option>
                            <option value="hijo_menor">Hijo/a menor de edad</option>
                            <option value="hijo_mayor">Hijo/a mayor de edad</option>
                            <option value="padre_madre">Padre / Madre</option>
                            <option value="conyuge">Cónyuge o compañero/a permanente</option>
                            <option value="hermano">Hermano/a</option>
                            <option value="abuelo">Abuelo/a</option>
                            <option value="representante_legal">Representante legal</option>
                            <option value="otro">Otro</option>
                          </select>
                        </div>
                      </>
                    )}

                    {!!strategicQuestions.length && (
                      <div className="space-y-6">
                        <div className="rounded-[2rem] border border-emerald-200 bg-emerald-50 p-6">
                          <p className="text-sm font-black uppercase tracking-wide text-emerald-700 mb-2">Preguntas clave para tu caso</p>
                          <p className="text-sm text-emerald-700 font-medium">
                            Estas respuestas son las mas utiles para que el documento quede solido y sin repreguntas innecesarias.
                          </p>
                        </div>
                        {strategicQuestions.map((prompt) => (
                          <div key={`strategic_${prompt.id}`} className="space-y-2">
                            <label className="text-sm font-bold text-brand ml-1">{prompt.question}</label>
                            {prompt.multiline ? (
                              <textarea
                                rows={3}
                                className="input-field resize-none"
                                placeholder="Escribe tu respuesta"
                                value={form[prompt.id] || ''}
                                onChange={(e) => handleFieldChange(prompt.id, e.target.value)}
                              />
                            ) : (
                              <input
                                type="text"
                                className="input-field"
                                placeholder="Escribe tu respuesta"
                                value={form[prompt.id] || ''}
                                onChange={(e) => handleFieldChange(prompt.id, e.target.value)}
                              />
                            )}
                            {prompt.why && <p className="text-xs text-brand/50 font-medium">{prompt.why}</p>}
                          </div>
                        ))}
                      </div>
                    )}

                    {!!prompts.length && (
                      <div className="space-y-6">
                        <div className="rounded-[2rem] border border-brand/10 bg-brand/5 p-6">
                          <p className="text-sm font-black uppercase tracking-wide text-brand mb-2">Informacion complementaria</p>
                          <p className="text-sm text-brand/70 font-medium">
                            Solo responde los bloques que apliquen en tu caso. Si ya respondiste arriba, puedes dejar en blanco los repetidos.
                          </p>
                        </div>
                        {prompts.map((prompt) => {
                          const fieldName = QUESTION_FIELD_MAP[prompt.id] || prompt.id;
                          return (
                            <div key={prompt.id} className="space-y-2">
                              <label className="text-sm font-bold text-brand ml-1">{prompt.question}</label>
                              {prompt.multiline ? (
                                <textarea
                                  rows={3}
                                  className="input-field resize-none"
                                  placeholder={prompt.placeholder || 'Escribe tu respuesta'}
                                  value={form[fieldName] || ''}
                                  onChange={(e) => handleFieldChange(fieldName, e.target.value)}
                                />
                              ) : (
                                <input
                                  type="text"
                                  className="input-field"
                                  placeholder={prompt.placeholder || 'Escribe tu respuesta'}
                                  value={form[fieldName] || ''}
                                  onChange={(e) => handleFieldChange(fieldName, e.target.value)}
                                />
                              )}
                              {prompt.why && <p className="text-xs text-brand/50 font-medium">{prompt.why}</p>}
                            </div>
                          );
                        })}
                      </div>
                    )}

                    {tutelaFlow && (
                      <div className="space-y-6">
                        <div className="rounded-[2rem] border border-amber-200 bg-amber-50 p-6">
                          <p className="text-sm font-black uppercase tracking-wide text-amber-700 mb-2">Validacion para tutela</p>
                          <p className="text-sm text-amber-700 font-medium">
                            Estas respuestas son necesarias para evitar una tutela incompleta o con riesgo de rechazo por falta de contexto previo.
                          </p>
                        </div>

                        <div className="space-y-2">
                          <label className="text-sm font-bold text-brand ml-1">¿Ya presentaste una peticion previa por esta misma causa?</label>
                          <select
                            required
                            className="input-field"
                            value={form.prior_petition_same_cause}
                            onChange={(e) => handleFieldChange('prior_petition_same_cause', e.target.value)}
                          >
                            <option value="">Selecciona una opcion</option>
                            <option value="si">Si</option>
                            <option value="no">No</option>
                            <option value="no_recuerdo">No recuerdo</option>
                          </select>
                        </div>

                        {form.prior_petition_same_cause === 'si' && (
                          <>
                            <div className="space-y-2">
                              <label className="text-sm font-bold text-brand ml-1">Fecha aproximada de la peticion previa</label>
                              <input
                                required
                                type="text"
                                className="input-field"
                                placeholder="Ej: 15 de marzo de 2026"
                                value={form.prior_petition_date}
                                onChange={(e) => handleFieldChange('prior_petition_date', e.target.value)}
                              />
                            </div>
                            <div className="space-y-2">
                              <label className="text-sm font-bold text-brand ml-1">¿Que respondio la entidad o EPS?</label>
                              <textarea
                                required
                                rows={3}
                                className="input-field resize-none"
                                placeholder="Indica si negaron, guardaron silencio o respondieron parcialmente."
                                value={form.prior_petition_response}
                                onChange={(e) => handleFieldChange('prior_petition_response', e.target.value)}
                              />
                            </div>
                          </>
                        )}
                      </div>
                    )}

                    <div className="space-y-2">
                      <label className="text-sm font-bold text-brand ml-1">Peticion concreta</label>
                      <textarea
                        required
                        rows={3}
                        className="input-field resize-none"
                        placeholder="Ej: Solicito que autoricen el medicamento, programen el procedimiento o respondan de fondo."
                        value={form.concrete_request}
                        onChange={(e) => handleFieldChange('concrete_request', e.target.value)}
                      />
                    </div>

                    <div className="space-y-2">
                      <label className="text-sm font-bold text-brand ml-1">Hechos del caso en orden</label>
                      <textarea
                        required
                        rows={6}
                        className="input-field resize-none"
                        placeholder="Cuenta el caso con mas detalle: que paso primero, que gestiones hiciste, que respondieron y como te afecta hoy."
                        value={form.case_story}
                        onChange={(e) => handleFieldChange('case_story', e.target.value)}
                      />
                      <p className="text-xs text-brand/50 font-medium">
                        Entre mas completa sea la narracion (fechas, entidades, respuestas y riesgo actual), menos repreguntas tendra tu expediente.
                      </p>
                    </div>

                    <div className="space-y-2">
                      <label className="text-sm font-bold text-brand ml-1">Detalles adicionales</label>
                      <textarea
                        rows={4}
                        className="input-field resize-none"
                        placeholder="Agrega cualquier dato adicional que consideres relevante para tu caso."
                        value={form.extra_details}
                        onChange={(e) => handleFieldChange('extra_details', e.target.value)}
                      />
                    </div>

                    <div className="space-y-4 rounded-[2rem] border border-brand/10 bg-brand/5 p-6">
                      <label className="text-sm font-black uppercase tracking-wide text-brand mb-1 flex items-center gap-2">
                        <Upload size={16} /> Soportes del caso (adjunta aqui)
                      </label>
                      <p className="text-sm text-brand/70 font-medium">
                        Sube aqui los documentos que te pedimos. Si te queda mas facil, tambien puedes adjuntar un audio corto narrando el caso.
                      </p>
                      {!!suggestedAttachments.length && (
                        <div className="flex flex-wrap gap-2">
                          {suggestedAttachments.map((item) => (
                            <span key={item} className="px-3 py-1 rounded-full bg-brand/5 text-brand text-xs font-bold">
                              {item}
                            </span>
                          ))}
                        </div>
                      )}
                      <p className="text-xs text-brand/50 font-medium">
                        Formatos: PDF, JPG, PNG, DOC, DOCX y audio (MP3, WAV, M4A, AAC).
                      </p>
                      <div className="border-2 border-dashed border-brand/10 rounded-2xl p-8 text-center hover:bg-brand/5 transition-colors cursor-pointer relative">
                        <input
                          ref={fileInputRef}
                          type="file"
                          multiple
                          accept=".pdf,.jpg,.jpeg,.png,.doc,.docx,.mp3,.wav,.m4a,.aac,application/pdf,image/jpeg,image/png,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document,audio/mpeg,audio/wav,audio/mp4,audio/x-m4a,audio/aac"
                          className="absolute inset-0 opacity-0 cursor-pointer"
                          onChange={(e) => setIntakeFiles(Array.from(e.target.files || []))}
                        />
                        <FileText className="mx-auto text-brand/20 mb-2" size={32} />
                        <p className="text-sm text-brand/60 font-bold">
                          {intakeFiles.length > 0 ? `${intakeFiles.length} archivos seleccionados` : 'Click o arrastra para subir tus anexos'}
                        </p>
                        <p className="text-xs text-brand/50 mt-2">
                          Puedes combinar soportes escritos + una nota de voz con la narracion del caso.
                        </p>
                      </div>
                      {!!uploadedNames.length && (
                        <div className="flex flex-wrap gap-2">
                          {uploadedNames.map((name) => (
                            <span key={name} className="px-3 py-1 rounded-full bg-success/10 text-success text-xs font-bold">
                              {name}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>

                    {successMessage && <p className="text-green-700 text-sm font-bold">{successMessage}</p>}
                    {error && <p className="text-red-600 text-sm font-bold">{error}</p>}

                    <button
                      type="submit"
                      disabled={submitting}
                      className="w-full py-4 text-xl flex justify-center items-center gap-3 disabled:opacity-50 rounded-2xl bg-[#0D68FF] text-white font-black"
                    >
                      {submitting ? 'Enviando...' : 'Enviar expediente al equipo jurídico'} <Send size={20} />
                    </button>
                  </form>
                </div>
              )}

              {isDelivered && (
                <div className="bg-white p-12 rounded-[2rem] shadow-[0_18px_55px_rgba(18,35,61,0.06)] border border-emerald-200 text-center">
                  <div className="bg-emerald-50 text-emerald-600 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-6">
                    <Mail size={32} />
                  </div>
                  <h3 className="text-3xl font-extrabold text-slate-900 mb-4">Documento entregado</h3>
                  <p className="text-slate-500 mb-8 font-medium">Hemos enviado tu kit legal completo a tu correo electronico.</p>
                  <button onClick={() => navigate('/')} className="rounded-2xl bg-[#08172E] px-8 py-4 text-white font-black">Volver al inicio</button>
                </div>
              )}
            </div>

            <div className="lg:col-span-2">
              <div className="lg:sticky lg:top-28 space-y-6">
              <div className="bg-white p-8 rounded-[2rem] shadow-[0_18px_55px_rgba(18,35,61,0.06)] border border-slate-200">
                <h4 className="font-extrabold text-slate-900 mb-6">Linea de tiempo</h4>
                <div className="space-y-6">
                  <TimelineStep step="1" title="Pago aprobado" detail="Confirmado vía pasarela segura" done />
                  <TimelineStep
                    step="2"
                    title="Completar expediente"
                    detail="Completa tus datos y adjunta los documentos de soporte"
                    active={!successMessage}
                    done={Boolean(successMessage)}
                  />
                  <TimelineStep
                    step="3"
                    title="Elaboración por especialistas"
                    detail="Máximo 24 horas hábiles desde información completa"
                    done={isDelivered}
                  />
                  <TimelineStep
                    step="4"
                    title="Entrega y seguimiento"
                    detail="Recibirás tu documento listo para radicar"
                  />
                </div>
              </div>

              <div className="bg-white p-8 rounded-[2rem] border border-slate-200 shadow-[0_18px_55px_rgba(18,35,61,0.06)]">
                <p className="text-xs font-black uppercase tracking-wide text-slate-400 mb-3">Progreso del formulario</p>
                <div className="w-full h-3 bg-slate-100 rounded-full overflow-hidden">
                  <div className="h-full bg-[#0D68FF]" style={{ width: `${progress}%` }} />
                </div>
                <p className="text-sm text-slate-600 font-semibold mt-3">{progress}% completo</p>
                <p className="text-sm text-slate-500 mt-3">
                  Entre mas completo quede el expediente, mas rapido y preciso trabaja el equipo especialista.
                </p>
              </div>

              <div className="bg-[#08172E] text-white p-8 rounded-[2rem] border border-white/10 shadow-[0_18px_55px_rgba(18,35,61,0.12)]">
                <p className="text-xs font-black uppercase tracking-wide text-[#19B7FF] mb-3">Respaldo profesional</p>
                <p className="text-lg font-extrabold leading-tight mb-3">Tu caso lo prepara un equipo experto con control de calidad juridico.</p>
                <p className="text-sm text-white/75 leading-6 mb-4">
                  Revisa todo antes de enviar: hechos, fechas, respuesta de la entidad y soportes clave.
                </p>
                <div className="space-y-2 text-sm text-white/80">
                  <p>- Fundamentacion legal por tipo de tramite.</p>
                  <p>- Checklist de anexos y canal de radicacion.</p>
                  <p>- Trazabilidad por codigo unico de seguimiento.</p>
                </div>
                <div className="mt-6 rounded-2xl border border-white/15 bg-white/10 p-4">
                  <p className="text-xs font-black uppercase tracking-wide text-[#19B7FF] mb-2">Rifa {RAFFLE_MONTH_LABEL}</p>
                  <p className="text-sm text-white/85 leading-6">
                    Con pago aprobado participas en la rifa por {RAFFLE_PRIZE_LABEL}.
                  </p>
                  <p className="text-sm text-white/70 mt-2">
                    {RAFFLE_LONG_COPY}
                  </p>
                </div>
              </div>

              <div className="bg-[#F8FBFF] p-8 rounded-[2rem] border border-slate-200">
                <p className="text-xs text-slate-500 leading-relaxed font-medium">
                  <strong>Nota:</strong> El plazo de entrega corre desde que envías datos completos y soportes suficientes. Conserva tu número de expediente y tu código de rifa para cualquier seguimiento.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
      </main>
    </div>
  );
};

export default SuccessPage;
