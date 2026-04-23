import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { motion } from 'framer-motion';
import { CheckCircle2, Trophy, FileText, Upload, Send, ArrowRight, Loader2, Mail } from 'lucide-react';
import { api, extractError } from '../lib/api';

const SuccessPage = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [caseData, setCaseData] = useState(null);
  const [intakeFiles, setIntakeFiles] = useState([]);
  
  const [form, setForm] = useState({
    document_number: "",
    city: "",
    department: "Bogotá D.C.",
    address: "",
    concrete_request: "",
    extra_details: "",
  });

  const params = useMemo(() => new URLSearchParams(window.location.search), []);
  const transactionId = params.get("id");

  useEffect(() => {
    const saved = localStorage.getItem("hazlopormi-guest-case");
    if (!saved) {
      navigate('/');
      return;
    }
    
    const guestCase = JSON.parse(saved);
    
    const run = async () => {
      try {
        if (transactionId) {
          // Reconcile payment
          const response = await api.post("/public/payments/wompi/reconcile", {
            transaction_id: transactionId,
            public_token: guestCase.publicToken
          });
          setCaseData(response.data);
          // Pre-fill form if data exists
          if (response.data.case) {
             setForm(prev => ({
                ...prev,
                document_number: response.data.case.user_document || "",
                city: response.data.case.user_city || "",
                address: response.data.case.user_address || "",
             }));
          }
        } else {
          // Just fetch current status
          const response = await api.get(`/public/cases/${guestCase.caseId}`, {
            params: { public_token: guestCase.publicToken }
          });
          setCaseData(response.data);
        }
      } catch (err) {
        setError(extractError(err, "No pudimos verificar el estado de tu pago."));
      } finally {
        setLoading(false);
      }
    };
    
    run();
  }, [transactionId, navigate]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!caseData) return;
    setSubmitting(true);
    setError("");
    
    const saved = JSON.parse(localStorage.getItem("hazlopormi-guest-case"));

    try {
      // 1. Upload files if any
      for (const file of intakeFiles) {
        const formData = new FormData();
        formData.append("public_token", saved.publicToken);
        formData.append("file_kind", "supporting_evidence");
        formData.append("file", file);
        await api.post(`/public/cases/${saved.caseId}/uploads`, formData, { 
          headers: { "Content-Type": "multipart/form-data" } 
        });
      }

      // 2. Submit intake
      const response = await api.patch(`/public/cases/${saved.caseId}/intake`, {
        public_token: saved.publicToken,
        ...form,
        form_data: {
          concrete_request: form.concrete_request,
          extra_details: form.extra_details,
        }
      });
      
      setCaseData(response.data);
      alert("Información recibida. Estamos redactando tu documento.");
    } catch (err) {
      setError(extractError(err, "No pudimos guardar la información."));
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
        <div className="max-w-4xl mx-auto">
          
          {/* Header Success */}
          <div className="text-center mb-12">
            <motion.div 
              initial={{ scale: 0 }} 
              animate={{ scale: 1 }}
              className="bg-success text-white w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-6 shadow-xl"
            >
              <CheckCircle2 size={40} />
            </motion.div>
            <h1 className="text-4xl font-extrabold text-brand mb-4">
              {isPaid ? "¡Pago Confirmado con Éxito!" : "Pago en Procesamiento"}
            </h1>
            <p className="text-brand/60 text-lg max-w-2xl mx-auto font-medium">
              {isPaid 
                ? "Hemos recibido tu pago. Ahora necesitamos unos detalles finales para que nuestro equipo redacte tu kit legal."
                : "Estamos esperando la confirmación de tu banco. Esto puede tardar unos minutos."}
            </p>
          </div>

          <div className="grid lg:grid-cols-5 gap-8">
            
            {/* Main Content: Form or Status */}
            <div className="lg:col-span-3 space-y-8">
              
              {/* Raffle Card */}
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
                    <p className="text-white/60 text-sm mt-4 font-medium">
                      Guarda este código. Al final del mes sortearemos un bono de <strong>$200.000 COP</strong> entre todos los ciudadanos.
                    </p>
                  </div>
                </motion.div>
              )}

              {/* Intake Form (Only if paid and not yet delivered) */}
              {isPaid && !isDelivered && (
                <div className="bg-white p-8 md:p-12 rounded-[2.5rem] shadow-xl border border-brand/5">
                  <h3 className="text-2xl font-extrabold text-brand mb-8 flex items-center gap-3">
                    <FileText className="text-accent" /> Información de Producción
                  </h3>
                  
                  <form onSubmit={handleSubmit} className="space-y-6">
                    <div className="grid md:grid-cols-2 gap-6">
                      <div className="space-y-2">
                        <label className="text-sm font-bold text-brand ml-1">Cédula de Ciudadanía</label>
                        <input 
                          required
                          type="text" 
                          className="input-field"
                          value={form.document_number}
                          onChange={e => setForm({...form, document_number: e.target.value})}
                        />
                      </div>
                      <div className="space-y-2">
                        <label className="text-sm font-bold text-brand ml-1">Ciudad de Radicación</label>
                        <input 
                          required
                          type="text" 
                          className="input-field"
                          value={form.city}
                          onChange={e => setForm({...form, city: e.target.value})}
                        />
                      </div>
                    </div>

                    <div className="space-y-2">
                      <label className="text-sm font-bold text-brand ml-1">Dirección de Notificación</label>
                      <input 
                        required
                        type="text" 
                        placeholder="Calle, Carrera, Apto..."
                        className="input-field"
                        value={form.address}
                        onChange={e => setForm({...form, address: e.target.value})}
                      />
                    </div>

                    <div className="space-y-2">
                      <label className="text-sm font-bold text-brand ml-1">Petición Concreta</label>
                      <textarea 
                        required
                        rows={3}
                        placeholder="Ej: Solicito que me entreguen el medicamento X de forma inmediata."
                        className="input-field resize-none"
                        value={form.concrete_request}
                        onChange={e => setForm({...form, concrete_request: e.target.value})}
                      />
                    </div>

                    <div className="space-y-4">
                      <label className="text-sm font-bold text-brand ml-1 flex items-center gap-2">
                        <Upload size={16} /> Adjuntar Soportes (PDF/Imagen)
                      </label>
                      <div className="border-2 border-dashed border-brand/10 rounded-2xl p-8 text-center hover:bg-brand/5 transition-colors cursor-pointer relative">
                        <input 
                          type="file" 
                          multiple 
                          className="absolute inset-0 opacity-0 cursor-pointer"
                          onChange={e => setIntakeFiles(Array.from(e.target.files))}
                        />
                        <FileText className="mx-auto text-brand/20 mb-2" size={32} />
                        <p className="text-sm text-brand/60 font-bold">
                          {intakeFiles.length > 0 
                            ? `${intakeFiles.length} archivos seleccionados` 
                            : "Click o arrastra para subir tus anexos"}
                        </p>
                      </div>
                    </div>

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

              {/* Success View after form submission */}
              {isDelivered && (
                <div className="bg-white p-12 rounded-[2.5rem] shadow-xl border border-success/20 text-center">
                  <div className="bg-success/10 text-success w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-6">
                    <Mail size={32} />
                  </div>
                  <h3 className="text-3xl font-extrabold text-brand mb-4">¡Documento Entregado!</h3>
                  <p className="text-brand/60 mb-8 font-medium">
                    Hemos enviado tu kit legal completo a tu correo electrónico. Por favor revisa tu bandeja de entrada y la carpeta de spam.
                  </p>
                  <button onClick={() => navigate('/')} className="btn-secondary px-8">Volver al Inicio</button>
                </div>
              )}
            </div>

            {/* Side Info */}
            <div className="lg:col-span-2 space-y-6">
              <div className="bg-white p-8 rounded-[2.5rem] shadow-lg border border-brand/5">
                <h4 className="font-extrabold text-brand mb-6 flex items-center gap-2">
                   Línea de Tiempo
                </h4>
                <div className="space-y-6">
                  <div className="flex gap-4">
                    <div className="bg-success text-white w-6 h-6 rounded-full flex items-center justify-center shrink-0 text-[10px] font-bold">✓</div>
                    <div>
                      <p className="font-bold text-brand text-sm">Pago Aprobado</p>
                      <p className="text-brand/40 text-[11px] font-medium tracking-tight">Confirmado vía Wompi</p>
                    </div>
                  </div>
                  <div className="flex gap-4">
                    <div className={`w-6 h-6 rounded-full flex items-center justify-center shrink-0 text-[10px] font-bold ${isDelivered ? 'bg-success text-white' : 'bg-accent text-brand'}`}>
                      {isDelivered ? '✓' : '2'}
                    </div>
                    <div>
                      <p className="font-bold text-brand text-sm">Formulario de Producción</p>
                      <p className="text-brand/40 text-[11px] font-medium tracking-tight">Estamos procesando tu información</p>
                    </div>
                  </div>
                  <div className="flex gap-4">
                    <div className={`w-6 h-6 rounded-full flex items-center justify-center shrink-0 text-[10px] font-bold ${isDelivered ? 'bg-success text-white' : 'bg-brand/10 text-brand/30'}`}>
                      {isDelivered ? '✓' : '3'}
                    </div>
                    <div>
                      <p className="font-bold text-brand text-sm">Entrega del Kit</p>
                      <p className="text-brand/40 text-[11px] font-medium tracking-tight">Máximo 24 horas hábiles</p>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-brand/5 p-8 rounded-[2.5rem] border border-brand/5">
                <p className="text-xs text-brand/60 leading-relaxed font-medium">
                  <strong>Nota:</strong> El plazo de 24 horas comienza a contar desde que envías el formulario con toda la información completa y soportes.
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
