import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { CheckCircle2, Trophy, FileText, Upload, Send, Loader2, Mail, MessageSquareMore } from 'lucide-react';
import Navbar from '../components/Navbar';
import { api, extractError } from '../lib/api';

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

const buildDescription = (form) => {
  return [
    form.case_story,
    form.key_dates ? `Fechas clave: ${form.key_dates}` : '',
    form.prior_claim_result ? `Barrera o respuesta: ${form.prior_claim_result}` : '',
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
  return payload;
};

const StatusPill = ({ children, tone = 'default' }) => {
  const styles = {
    default: 'bg-brand/10 text-brand',
    success: 'bg-success/10 text-success',
    danger: 'bg-red-100 text-red-600',
  };
  return <span className={`px-3 py-1 rounded-full text-xs font-black ${styles[tone] || styles.default}`}>{children}</span>;
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
  });

  const params = useMemo(() => new URLSearchParams(window.location.search), []);
  const transactionId = params.get('id');
  const prompts = useMemo(() => buildPromptList(caseData), [caseData]);
  const requiredAttachments = caseData?.customer_guide?.required_attachments || [];
  const uploadedFiles = caseData?.files || [];
  const opsSync = caseData?.case?.submission_summary?.ops_sync || {};
  const opsStatus = String(opsSync.status || '').toLowerCase();
  const opsSummary = caseData?.case?.facts?.agent_state?.ops_summary || '';
  const uploadedNames = uploadedFiles.map((item) => item?.original_name).filter(Boolean);

  useEffect(() => {
    const saved = localStorage.getItem('hazlopormi-guest-case');
    if (!saved) {
      navigate('/');
      return;
    }

    const guestCase = JSON.parse(saved);

    const hydrate = (responseData) => {
      setCaseData(responseData);
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
      }));
    };

    const run = async () => {
      try {
        if (transactionId) {
          const response = await api.post('/public/payments/wompi/reconcile', {
            transaction_id: transactionId,
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
  }, [transactionId, navigate]);

  const handleFieldChange = (field, value) => {
    setForm((current) => ({ ...current, [field]: value }));
  };

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
      setSuccessMessage('Informacion recibida. El expediente ya quedo listo para produccion humana.');
      setIntakeFiles([]);
    } catch (err) {
      setError(extractError(err, 'No pudimos guardar la informacion.'));
    } finally {
      setSubmitting(false);
    }
  };

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
                ? 'Tu pago ya quedo confirmado. Ahora necesitamos cerrar datos y soportes para que produccion humana redacte sin repreguntas ni retrasos.'
                : 'Estamos esperando la confirmacion final del pago. Esto puede tardar unos minutos.'}
            </p>
          </div>

          <div className="grid lg:grid-cols-5 gap-8">
            <div className="lg:col-span-3 space-y-8">
              {(customerCaseCode || invoiceNumber || paymentReference) && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                className="bg-white p-8 rounded-[2rem] shadow-[0_18px_55px_rgba(18,35,61,0.06)] border border-slate-200"
              >
                  <p className="text-xs font-black uppercase tracking-widest text-slate-400 mb-3">Identificadores de tu pago</p>
                  <h3 className="text-2xl font-extrabold text-slate-900 mb-3">Guarda estos codigos</h3>
                  <p className="text-sm text-slate-500 font-medium mb-6">
                    No usamos consecutivos visibles. Cada pago recibe codigos unicos para seguimiento operativo y para la rifa mensual.
                  </p>
                  <div className="grid md:grid-cols-3 gap-4">
                    {customerCaseCode && <CodeCard label="Expediente" value={customerCaseCode} subtle />}
                    {invoiceNumber && <CodeCard label="Factura operativa" value={invoiceNumber} />}
                    {paymentReference && <CodeCard label="Referencia de pago" value={paymentReference} />}
                  </div>
                </motion.div>
              )}

              {raffleCode && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                className="bg-[#08172E] text-white p-8 rounded-[2rem] shadow-[0_18px_55px_rgba(18,35,61,0.12)] relative overflow-hidden"
              >
                  <div className="absolute top-0 right-0 p-8 opacity-10">
                    <Trophy size={120} />
                  </div>
                  <div className="relative z-10">
                    <p className="text-[#19B7FF] font-black uppercase text-xs tracking-widest mb-2">Participacion en rifa mensual</p>
                    <h3 className="text-2xl font-extrabold mb-3">Tu codigo unico es:</h3>
                    <p className="text-white/80 text-sm font-medium mb-4 max-w-xl">
                      Este codigo identifica tu participacion al cierre del periodo promocional. Es unico por pago aprobado y no sigue una secuencia publica.
                    </p>
                    <div className="bg-white/10 border border-white/20 inline-block px-6 py-3 rounded-2xl font-mono text-3xl font-black tracking-tighter">
                      {raffleCode}
                    </div>
                  </div>
                </motion.div>
              )}

              {isPaid && !isDelivered && (
                <div className="bg-white p-8 md:p-12 rounded-[2rem] shadow-[0_18px_55px_rgba(18,35,61,0.06)] border border-slate-200">
                  <h3 className="text-2xl font-extrabold text-slate-900 mb-8 flex items-center gap-3">
                    <MessageSquareMore className="text-[#19B7FF]" /> Agente de Produccion
                  </h3>

                  <div className="grid gap-4 mb-8">
                    <div className="rounded-[2rem] border border-slate-200 bg-[#F8FBFF] p-6">
                      <div className="flex flex-wrap items-center justify-between gap-3">
                        <div>
                          <p className="text-sm font-black uppercase tracking-wide text-slate-900 mb-2">Estado del expediente</p>
                          <p className="text-sm text-slate-500 font-medium">
                            {opsSummary || 'Estamos consolidando tu expediente para que el equipo humano redacte sin repreguntas.'}
                          </p>
                        </div>
                        {opsStatus === 'sent' && <StatusPill tone="success">Sincronizado con produccion</StatusPill>}
                        {opsStatus === 'error' && <StatusPill tone="danger">Sincronizacion con incidencia</StatusPill>}
                        {!['sent', 'error'].includes(opsStatus) && <StatusPill>Pendiente de sincronizacion</StatusPill>}
                      </div>
                    </div>

                    <div className="grid md:grid-cols-2 gap-4">
                      <div className="rounded-[2rem] border border-slate-200 p-5">
                        <p className="text-xs font-black uppercase tracking-wide text-slate-400 mb-3">Ya tenemos</p>
                        <div className="flex flex-wrap gap-2">
                          <span className="px-3 py-1 rounded-full bg-success/10 text-success text-xs font-bold">Pago confirmado</span>
                          {customerCaseCode && <span className="px-3 py-1 rounded-full bg-brand/5 text-brand text-xs font-bold">Codigo de expediente</span>}
                          {form.name && <span className="px-3 py-1 rounded-full bg-brand/5 text-brand text-xs font-bold">Nombre</span>}
                          {form.document_number && <span className="px-3 py-1 rounded-full bg-brand/5 text-brand text-xs font-bold">Documento</span>}
                          {form.city && <span className="px-3 py-1 rounded-full bg-brand/5 text-brand text-xs font-bold">Ciudad</span>}
                          {uploadedNames.length > 0 && <span className="px-3 py-1 rounded-full bg-brand/5 text-brand text-xs font-bold">{uploadedNames.length} soporte(s)</span>}
                        </div>
                      </div>

                      <div className="rounded-[2rem] border border-slate-200 p-5">
                        <p className="text-xs font-black uppercase tracking-wide text-slate-400 mb-3">Falta para produccion</p>
                        <p className="text-sm text-slate-500 font-medium">
                          {prompts.length
                            ? `Responde ${prompts.length} bloque${prompts.length === 1 ? '' : 's'} de informacion y sube los soportes que tengas disponibles.`
                            : 'El expediente ya tiene base suficiente. Si quieres, solo agrega soportes o contexto adicional antes de enviarlo al equipo humano.'}
                        </p>
                      </div>
                    </div>

                    <div className="rounded-[2rem] border border-[#19B7FF]/20 bg-[#19B7FF]/10 p-5">
                      <p className="text-sm font-black text-slate-900 mb-2">Que pasa despues de enviar esto</p>
                      <p className="text-sm text-slate-600 font-medium">
                        Produccion humana revisara tus respuestas, validara anexos y te escribira solo si falta algo critico. El tiempo corre desde que el expediente quede completo.
                      </p>
                    </div>
                  </div>

                  <form onSubmit={handleSubmit} className="space-y-8">
                    <div className="grid md:grid-cols-2 gap-6">
                      <div className="space-y-2">
                        <label className="text-sm font-bold text-brand ml-1">Nombre completo</label>
                        <input required type="text" className="input-field" value={form.name} onChange={(e) => handleFieldChange('name', e.target.value)} />
                      </div>
                      <div className="space-y-2">
                        <label className="text-sm font-bold text-brand ml-1">Correo electronico</label>
                        <input required type="email" className="input-field" value={form.email} onChange={(e) => handleFieldChange('email', e.target.value)} />
                      </div>
                    </div>

                    <div className="grid md:grid-cols-2 gap-6">
                      <div className="space-y-2">
                        <label className="text-sm font-bold text-brand ml-1">WhatsApp / celular</label>
                        <input required type="text" className="input-field" value={form.phone} onChange={(e) => handleFieldChange('phone', e.target.value)} />
                      </div>
                      <div className="space-y-2">
                        <label className="text-sm font-bold text-brand ml-1">Cedula de ciudadania</label>
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
                      <label className="text-sm font-bold text-brand ml-1">Direccion de notificacion</label>
                      <input required type="text" className="input-field" value={form.address} onChange={(e) => handleFieldChange('address', e.target.value)} />
                    </div>

                    {!!prompts.length && (
                      <div className="space-y-6">
                        <div className="rounded-[2rem] border border-brand/10 bg-brand/5 p-6">
                          <p className="text-sm font-black uppercase tracking-wide text-brand mb-2">Preguntas del agente</p>
                          <p className="text-sm text-brand/70 font-medium">
                            Responde estas preguntas para que el humano reciba el expediente sin vacios ni repreguntas innecesarias.
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
                        rows={5}
                        className="input-field resize-none"
                        placeholder="Cuenta que paso, en que fechas y como te afecto."
                        value={form.case_story}
                        onChange={(e) => handleFieldChange('case_story', e.target.value)}
                      />
                    </div>

                    <div className="space-y-2">
                      <label className="text-sm font-bold text-brand ml-1">Detalles adicionales</label>
                      <textarea
                        rows={4}
                        className="input-field resize-none"
                        placeholder="Agrega cualquier dato util para produccion humana."
                        value={form.extra_details}
                        onChange={(e) => handleFieldChange('extra_details', e.target.value)}
                      />
                    </div>

                    <div className="space-y-4">
                      <label className="text-sm font-bold text-brand ml-1 flex items-center gap-2">
                        <Upload size={16} /> Adjuntar soportes
                      </label>
                      {!!requiredAttachments.length && (
                        <div className="flex flex-wrap gap-2">
                          {requiredAttachments.map((item) => (
                            <span key={item} className="px-3 py-1 rounded-full bg-brand/5 text-brand text-xs font-bold">
                              {item}
                            </span>
                          ))}
                        </div>
                      )}
                      <div className="border-2 border-dashed border-brand/10 rounded-2xl p-8 text-center hover:bg-brand/5 transition-colors cursor-pointer relative">
                        <input
                          type="file"
                          multiple
                          className="absolute inset-0 opacity-0 cursor-pointer"
                          onChange={(e) => setIntakeFiles(Array.from(e.target.files || []))}
                        />
                        <FileText className="mx-auto text-brand/20 mb-2" size={32} />
                        <p className="text-sm text-brand/60 font-bold">
                          {intakeFiles.length > 0 ? `${intakeFiles.length} archivos seleccionados` : 'Click o arrastra para subir tus anexos'}
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
                      {submitting ? 'Enviando...' : 'Enviar expediente a Produccion Humana'} <Send size={20} />
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

            <div className="lg:col-span-2 space-y-6">
              <div className="bg-white p-8 rounded-[2rem] shadow-[0_18px_55px_rgba(18,35,61,0.06)] border border-slate-200">
                <h4 className="font-extrabold text-slate-900 mb-6">Linea de tiempo</h4>
                <div className="space-y-6">
                  <TimelineStep step="1" title="Pago aprobado" detail="Confirmado via Wompi" done />
                  <TimelineStep
                    step="2"
                    title="Expediente para produccion"
                    detail="El agente cierra datos, anexos y contexto para el humano"
                    active={!successMessage}
                    done={Boolean(successMessage)}
                  />
                  <TimelineStep
                    step="3"
                    title="Redaccion humana"
                    detail="Maximo 24 horas habiles desde informacion completa"
                    done={isDelivered}
                  />
                  <TimelineStep
                    step="4"
                    title="Entrega y seguimiento"
                    detail="Te contactamos usando tu codigo de expediente y tu referencia de pago"
                  />
                </div>
              </div>

              <div className="bg-[#F8FBFF] p-8 rounded-[2rem] border border-slate-200">
                <p className="text-xs text-slate-500 leading-relaxed font-medium">
                  <strong>Nota:</strong> El plazo de entrega corre desde que envias datos completos y soportes suficientes para produccion humana. Conserva tu codigo de expediente y tu codigo de rifa para cualquier seguimiento.
                </p>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default SuccessPage;
