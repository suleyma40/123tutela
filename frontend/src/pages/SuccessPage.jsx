import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { motion } from 'framer-motion';
import { CheckCircle2, Trophy, FileText, Upload, Send, Loader2, Mail, MessageSquareMore } from 'lucide-react';
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

const SuccessPage = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [caseData, setCaseData] = useState(null);
  const [intakeFiles, setIntakeFiles] = useState([]);
  const [form, setForm] = useState({
    name: "",
    email: "",
    phone: "",
    document_number: "",
    city: "",
    department: "Bogotá D.C.",
    address: "",
    copy_email: "",
    target_entity: "",
    diagnosis: "",
    treatment_needed: "",
    urgency_detail: "",
    prior_claim_result: "",
    concrete_request: "",
    case_story: "",
    key_dates: "",
    medical_support_detail: "",
    extra_details: "",
  });

  const params = useMemo(() => new URLSearchParams(window.location.search), []);
  const transactionId = params.get("id");
  const prompts = useMemo(() => buildPromptList(caseData), [caseData]);
  const requiredAttachments = caseData?.customer_guide?.required_attachments || [];

  useEffect(() => {
    const saved = localStorage.getItem("hazlopormi-guest-case");
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
          const response = await api.post("/public/payments/wompi/reconcile", {
            transaction_id: transactionId,
            public_token: guestCase.publicToken
          });
          hydrate(response.data);
        } else {
          const response = await api.get(`/public/cases/${guestCase.caseId}`, {
            params: { public_token: guestCase.publicToken }
          });
          hydrate(response.data);
        }
      } catch (err) {
        setError(extractError(err, "No pudimos verificar el estado de tu pago."));
      } finally {
        setLoading(false);
      }
    };

    run();
  }, [transactionId, navigate]);

  const handleFieldChange = (field, value) => {
    setForm((current) => ({ ...current, [field]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!caseData) return;
    setSubmitting(true);
    setError("");
    setSuccessMessage("");

    const saved = JSON.parse(localStorage.getItem("hazlopormi-guest-case"));

    try {
      for (const file of intakeFiles) {
        const formData = new FormData();
        formData.append("public_token", saved.publicToken);
        formData.append("file_kind", "supporting_evidence");
        formData.append("file", file);
        await api.post(`/public/cases/${saved.caseId}/uploads`, formData, {
          headers: { "Content-Type": "multipart/form-data" }
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
      setSuccessMessage("Informacion recibida. El expediente ya quedo listo para produccion humana.");
      setIntakeFiles([]);
    } catch (err) {
      setError(extractError(err, "No pudimos guardar la informacion."));
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return (
    <div className="min-h-screen flex items-center justify-center bg-cream">
      <div className="text-center">
        <Loader2 className="w-12 h-12 text-brand animate-spin mx-auto mb-4" />
        <p className="font-bold text-brand">Verificando tu pago...</p>
      </div>
    </div>
  );

  const isPaid = caseData?.case?.payment_status === "pagado";
  const isDelivered = caseData?.case?.status === "entregado";
  const raffleCode = caseData?.latest_payment?.raffle?.code || caseData?.customer_summary?.raffle?.code;

  return (
    <div className="min-h-screen bg-cream">
      <Navbar />

      <main className="pt-32 pb-20 px-6">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-10">
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              className="bg-success text-white w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-6 shadow-xl"
            >
              <CheckCircle2 size={40} />
            </motion.div>
            <h1 className="text-4xl font-extrabold text-brand mb-4">
              {isPaid ? "Pago confirmado" : "Pago en procesamiento"}
            </h1>
            <p className="text-brand/60 text-lg max-w-2xl mx-auto font-medium">
              {isPaid
                ? "Ahora el agente debe dejar el expediente claro para produccion humana. Responde lo que falte y sube los soportes disponibles."
                : "Estamos esperando la confirmacion final del pago. Esto puede tardar unos minutos."}
            </p>
          </div>

          <div className="grid lg:grid-cols-5 gap-8">
            <div className="lg:col-span-3 space-y-8">
              {raffleCode && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="bg-brand text-white p-8 rounded-[2.5rem] shadow-xl relative overflow-hidden"
                >
                  <div className="absolute top-0 right-0 p-8 opacity-10">
                    <Trophy size={120} />
                  </div>
                  <div className="relative z-10">
                    <p className="text-accent font-black uppercase text-xs tracking-widest mb-2">Participación en Rifa Mensual</p>
                    <h3 className="text-2xl font-extrabold mb-4">Tu código único es:</h3>
                    <div className="bg-white/10 border border-white/20 inline-block px-6 py-3 rounded-2xl font-mono text-3xl font-black tracking-tighter">
                      {raffleCode}
                    </div>
                  </div>
                </motion.div>
              )}

              {isPaid && !isDelivered && (
                <div className="bg-white p-8 md:p-12 rounded-[2.5rem] shadow-xl border border-brand/5">
                  <h3 className="text-2xl font-extrabold text-brand mb-8 flex items-center gap-3">
                    <MessageSquareMore className="text-accent" /> Agente de Producción
                  </h3>

                  <form onSubmit={handleSubmit} className="space-y-8">
                    <div className="grid md:grid-cols-2 gap-6">
                      <div className="space-y-2">
                        <label className="text-sm font-bold text-brand ml-1">Nombre completo</label>
                        <input required type="text" className="input-field" value={form.name} onChange={(e) => handleFieldChange("name", e.target.value)} />
                      </div>
                      <div className="space-y-2">
                        <label className="text-sm font-bold text-brand ml-1">Correo electrónico</label>
                        <input required type="email" className="input-field" value={form.email} onChange={(e) => handleFieldChange("email", e.target.value)} />
                      </div>
                    </div>

                    <div className="grid md:grid-cols-2 gap-6">
                      <div className="space-y-2">
                        <label className="text-sm font-bold text-brand ml-1">WhatsApp / celular</label>
                        <input required type="text" className="input-field" value={form.phone} onChange={(e) => handleFieldChange("phone", e.target.value)} />
                      </div>
                      <div className="space-y-2">
                        <label className="text-sm font-bold text-brand ml-1">Cédula de ciudadanía</label>
                        <input required type="text" className="input-field" value={form.document_number} onChange={(e) => handleFieldChange("document_number", e.target.value)} />
                      </div>
                    </div>

                    <div className="grid md:grid-cols-2 gap-6">
                      <div className="space-y-2">
                        <label className="text-sm font-bold text-brand ml-1">Ciudad</label>
                        <input required type="text" className="input-field" value={form.city} onChange={(e) => handleFieldChange("city", e.target.value)} />
                      </div>
                      <div className="space-y-2">
                        <label className="text-sm font-bold text-brand ml-1">Departamento</label>
                        <input required type="text" className="input-field" value={form.department} onChange={(e) => handleFieldChange("department", e.target.value)} />
                      </div>
                    </div>

                    <div className="space-y-2">
                      <label className="text-sm font-bold text-brand ml-1">Dirección de notificación</label>
                      <input required type="text" className="input-field" value={form.address} onChange={(e) => handleFieldChange("address", e.target.value)} />
                    </div>

                    {!!prompts.length && (
                      <div className="space-y-6">
                        <div className="rounded-[2rem] border border-brand/10 bg-brand/5 p-6">
                          <p className="text-sm font-black uppercase tracking-wide text-brand mb-2">Preguntas del agente</p>
                          <p className="text-sm text-brand/70 font-medium">
                            Responde estas preguntas para que el humano reciba el expediente sin vacíos ni repreguntas innecesarias.
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
                                  placeholder={prompt.placeholder || "Escribe tu respuesta"}
                                  value={form[fieldName] || ""}
                                  onChange={(e) => handleFieldChange(fieldName, e.target.value)}
                                />
                              ) : (
                                <input
                                  type="text"
                                  className="input-field"
                                  placeholder={prompt.placeholder || "Escribe tu respuesta"}
                                  value={form[fieldName] || ""}
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
                      <label className="text-sm font-bold text-brand ml-1">Petición concreta</label>
                      <textarea
                        required
                        rows={3}
                        className="input-field resize-none"
                        placeholder="Ej: Solicito que autoricen el medicamento, programen el procedimiento o respondan de fondo."
                        value={form.concrete_request}
                        onChange={(e) => handleFieldChange("concrete_request", e.target.value)}
                      />
                    </div>

                    <div className="space-y-2">
                      <label className="text-sm font-bold text-brand ml-1">Hechos del caso en orden</label>
                      <textarea
                        required
                        rows={5}
                        className="input-field resize-none"
                        placeholder="Cuenta qué pasó, en qué fechas y cómo te afectó."
                        value={form.case_story}
                        onChange={(e) => handleFieldChange("case_story", e.target.value)}
                      />
                    </div>

                    <div className="space-y-2">
                      <label className="text-sm font-bold text-brand ml-1">Detalles adicionales</label>
                      <textarea
                        rows={4}
                        className="input-field resize-none"
                        placeholder="Agrega cualquier dato útil para producción humana."
                        value={form.extra_details}
                        onChange={(e) => handleFieldChange("extra_details", e.target.value)}
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
                          {intakeFiles.length > 0
                            ? `${intakeFiles.length} archivos seleccionados`
                            : "Click o arrastra para subir tus anexos"}
                        </p>
                      </div>
                    </div>

                    {successMessage && <p className="text-green-700 text-sm font-bold">{successMessage}</p>}
                    {error && <p className="text-red-600 text-sm font-bold">{error}</p>}

                    <button
                      type="submit"
                      disabled={submitting}
                      className="btn-primary w-full py-4 text-xl flex justify-center items-center gap-3 disabled:opacity-50"
                    >
                      {submitting ? "Enviando..." : "Enviar a Producción Humana"} <Send size={20} />
                    </button>
                  </form>
                </div>
              )}

              {isDelivered && (
                <div className="bg-white p-12 rounded-[2.5rem] shadow-xl border border-success/20 text-center">
                  <div className="bg-success/10 text-success w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-6">
                    <Mail size={32} />
                  </div>
                  <h3 className="text-3xl font-extrabold text-brand mb-4">Documento entregado</h3>
                  <p className="text-brand/60 mb-8 font-medium">
                    Hemos enviado tu kit legal completo a tu correo electrónico.
                  </p>
                  <button onClick={() => navigate('/')} className="btn-secondary px-8">Volver al inicio</button>
                </div>
              )}
            </div>

            <div className="lg:col-span-2 space-y-6">
              <div className="bg-white p-8 rounded-[2.5rem] shadow-lg border border-brand/5">
                <h4 className="font-extrabold text-brand mb-6">Línea de tiempo</h4>
                <div className="space-y-6">
                  <div className="flex gap-4">
                    <div className="bg-success text-white w-6 h-6 rounded-full flex items-center justify-center shrink-0 text-[10px] font-bold">1</div>
                    <div>
                      <p className="font-bold text-brand text-sm">Pago aprobado</p>
                      <p className="text-brand/40 text-[11px] font-medium tracking-tight">Confirmado vía Wompi</p>
                    </div>
                  </div>
                  <div className="flex gap-4">
                    <div className={`w-6 h-6 rounded-full flex items-center justify-center shrink-0 text-[10px] font-bold ${successMessage ? 'bg-success text-white' : 'bg-accent text-brand'}`}>
                      {successMessage ? '2' : '2'}
                    </div>
                    <div>
                      <p className="font-bold text-brand text-sm">Expediente para producción</p>
                      <p className="text-brand/40 text-[11px] font-medium tracking-tight">El agente cierra datos y soportes</p>
                    </div>
                  </div>
                  <div className="flex gap-4">
                    <div className={`w-6 h-6 rounded-full flex items-center justify-center shrink-0 text-[10px] font-bold ${isDelivered ? 'bg-success text-white' : 'bg-brand/10 text-brand/30'}`}>
                      3
                    </div>
                    <div>
                      <p className="font-bold text-brand text-sm">Redacción humana</p>
                      <p className="text-brand/40 text-[11px] font-medium tracking-tight">Máximo 24 horas hábiles desde información completa</p>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-brand/5 p-8 rounded-[2.5rem] border border-brand/5">
                <p className="text-xs text-brand/60 leading-relaxed font-medium">
                  <strong>Nota:</strong> El plazo de entrega corre desde que envías datos completos y soportes suficientes para producción humana.
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
