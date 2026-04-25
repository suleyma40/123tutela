import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { motion } from 'framer-motion';
import { Sparkles, ArrowRight, ShieldCheck, Clock, MessageSquare } from 'lucide-react';
import { api, extractError } from '../lib/api';

const DiagnosisPage = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [form, setForm] = useState({
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

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const response = await api.post("/public/leads/diagnosis", form);
      const guestCase = { 
        caseId: response.data.case.id, 
        publicToken: response.data.public_token,
        summary: response.data.commercial_summary,
        recommendedAction: response.data.case.recommended_action,
        strategyText: response.data.case.strategy_text
      };
      
      // Persist to localStorage for other pages
      localStorage.setItem("hazlopormi-guest-case", JSON.stringify(guestCase));
      
      navigate('/pago');
    } catch (err) {
      setError(extractError(err, "No fue posible analizar tu caso. Intenta resumir tu historia."));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-cream">
      <Navbar />
      
      <main className="pt-32 pb-20 px-6">
        <div className="max-w-6xl mx-auto grid lg:grid-cols-5 gap-12">
          
          {/* Form Side */}
          <div className="lg:col-span-3">
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-white rounded-[2.5rem] p-8 md:p-12 shadow-xl border border-brand/5"
            >
              <div className="flex items-center gap-3 mb-8">
                <div className="bg-brand p-3 rounded-2xl">
                  <Sparkles className="text-accent w-6 h-6" />
                </div>
                <div>
                  <h1 className="text-3xl font-extrabold text-brand">Diagnóstico Gratuito</h1>
                  <p className="text-brand/60 font-medium">Cuéntanos tu historia en menos de 5 minutos.</p>
                </div>
              </div>

              <form onSubmit={handleSubmit} className="space-y-6">
                <div className="grid md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <label className="text-sm font-bold text-brand ml-1">Nombre Completo</label>
                    <input 
                      required
                      type="text" 
                      placeholder="Ej: Juan Pérez"
                      className="input-field"
                      value={form.name}
                      onChange={e => setForm({...form, name: e.target.value})}
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-bold text-brand ml-1">Correo Electrónico</label>
                    <input 
                      required
                      type="email" 
                      placeholder="tu@correo.com"
                      className="input-field"
                      value={form.email}
                      onChange={e => setForm({...form, email: e.target.value})}
                    />
                  </div>
                </div>

                <div className="grid md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <label className="text-sm font-bold text-brand ml-1">Teléfono / WhatsApp</label>
                    <input 
                      required
                      type="tel" 
                      placeholder="300 123 4567"
                      className="input-field"
                      value={form.phone}
                      onChange={e => setForm({...form, phone: e.target.value})}
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-bold text-brand ml-1">Entidad de salud (EPS, IPS, operador, etc.)</label>
                    <input 
                      required
                      type="text" 
                      placeholder="Ej: EPS Sura, Sanitas, Nueva EPS..."
                      className="input-field"
                      value={form.entity_name}
                      onChange={e => setForm({...form, entity_name: e.target.value})}
                    />
                  </div>
                </div>

                <div className="grid md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <label className="text-sm font-bold text-brand ml-1">Categoría</label>
                    <select 
                      className="input-field"
                      value={form.category}
                      onChange={e => setForm({...form, category: e.target.value})}
                    >
                      <option>Salud</option>
                    </select>
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-bold text-brand ml-1">Ciudad</label>
                    <input 
                      required
                      type="text" 
                      placeholder="Ej: Medellín"
                      className="input-field"
                      value={form.city}
                      onChange={e => setForm({...form, city: e.target.value})}
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-bold text-brand ml-1 flex justify-between">
                    Cuéntanos qué pasó 
                    <span className="text-[10px] uppercase text-brand/40 font-black">Mínimo 50 caracteres</span>
                  </label>
                  <textarea 
                    required
                    minLength={50}
                    rows={6}
                    placeholder="Describe los hechos, fechas importantes y qué respuesta te dio la entidad (si te dio alguna)."
                    className="input-field resize-none"
                    value={form.description}
                    onChange={e => setForm({...form, description: e.target.value})}
                  />
                </div>

                {error && (
                  <div className="p-4 bg-red-50 border border-red-100 rounded-xl text-red-600 text-sm font-medium">
                    {error}
                  </div>
                )}

                <button 
                  type="submit" 
                  disabled={loading}
                  className="btn-primary w-full py-4 text-xl flex justify-center items-center gap-3 disabled:opacity-50 disabled:scale-100"
                >
                  {loading ? (
                    <>Analizando caso con IA...</>
                  ) : (
                    <>Obtener Diagnóstico Gratis <ArrowRight /></>
                  )}
                </button>
              </form>
            </motion.div>
          </div>

          {/* Info Side */}
          <div className="lg:col-span-2 space-y-6">
            <div className="bg-brand text-white p-8 rounded-[2.5rem] shadow-xl">
              <h3 className="text-2xl font-extrabold mb-6">¿Qué pasa después?</h3>
              <div className="space-y-8">
                <div className="flex gap-4">
                  <div className="bg-accent text-brand w-10 h-10 rounded-full flex items-center justify-center shrink-0 font-bold">1</div>
                  <div>
                    <p className="font-bold text-lg leading-tight">Análisis Inmediato</p>
                    <p className="text-white/60 text-sm mt-1">Nuestra IA procesa tu relato y determina la mejor estrategia legal para tu caso.</p>
                  </div>
                </div>
                <div className="flex gap-4">
                  <div className="bg-accent text-brand w-10 h-10 rounded-full flex items-center justify-center shrink-0 font-bold">2</div>
                  <div>
                    <p className="font-bold text-lg leading-tight">Hoja de Ruta</p>
                    <p className="text-white/60 text-sm mt-1">Te mostraremos qué documento necesitas radicar y cuáles son tus probabilidades.</p>
                  </div>
                </div>
                <div className="flex gap-4">
                  <div className="bg-accent text-brand w-10 h-10 rounded-full flex items-center justify-center shrink-0 font-bold">3</div>
                  <div>
                    <p className="font-bold text-lg leading-tight">Redacción Humana</p>
                    <p className="text-white/60 text-sm mt-1">Si decides continuar, nuestro equipo redactará tu documento personalizado en tiempo récord.</p>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white p-8 rounded-[2.5rem] shadow-lg border border-brand/5">
              <h4 className="font-extrabold text-brand mb-4 flex items-center gap-2">
                <ShieldCheck className="text-success" /> Seguridad y Privacidad
              </h4>
              <p className="text-brand/60 text-sm leading-relaxed">
                Tus datos están protegidos por cifrado de extremo a extremo. Solo los usaremos para generar tu documento legal y contactarte sobre tu caso.
              </p>
            </div>
          </div>

        </div>
      </main>
    </div>
  );
};

export default DiagnosisPage;
