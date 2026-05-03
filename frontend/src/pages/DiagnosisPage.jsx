import React, { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { ArrowRight, CheckCircle2, FileText, HeartPulse, ShieldCheck, Sparkles, Trophy } from 'lucide-react';
import Navbar from '../components/Navbar';
import { api, extractError } from '../lib/api';
import { trackEvent } from '../lib/analytics';
import { LAUNCH_PRICE_LABEL, RAFFLE_LONG_COPY } from '../lib/launchConfig';

const DiagnosisPage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [form, setForm] = useState({
    name: '',
    email: '',
    phone: '',
    category: 'Salud',
    department: 'Bogota D.C.',
    city: 'Bogota',
    entity_name: '',
    urgency_level: '',
    description: '',
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const response = await api.post('/public/leads/diagnosis', form);
      const guestCase = {
        caseId: response.data.case.id,
        publicToken: response.data.public_token,
        summary: response.data.commercial_summary,
        recommendedAction: response.data.case.recommended_action,
        strategyText: response.data.case.strategy_text,
        email: form.email,
      };
      localStorage.setItem('hazlopormi-guest-case', JSON.stringify(guestCase));
      const testCode = new URLSearchParams(location.search).get('test_code') || '';
      if (testCode) {
        localStorage.setItem('hazlopormi-test-code', testCode);
      } else {
        localStorage.removeItem('hazlopormi-test-code');
      }
      trackEvent('start_diagnosis', {
        category: form.category,
        city: form.city,
        entity: form.entity_name,
        recommended_action: response?.data?.case?.recommended_action || '',
        case_id: response?.data?.case?.id || '',
      });
      navigate(testCode ? `/pago?test_code=${encodeURIComponent(testCode)}` : '/pago');
    } catch (err) {
      setError(extractError(err, 'No fue posible analizar tu caso. Intenta resumir tu historia.'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F5F7FB] text-slate-900">
      <Navbar />

      <main className="pt-32 pb-20 px-6">
        <div className="max-w-7xl mx-auto grid lg:grid-cols-[1.05fr_0.95fr] gap-8 items-start">
          <section className="bg-white border border-slate-200 rounded-[28px] shadow-[0_18px_55px_rgba(18,35,61,0.06)] p-8 md:p-10">
            <div className="flex items-start gap-4 mb-8">
              <div className="w-14 h-14 rounded-2xl bg-[linear-gradient(135deg,#0D68FF_0%,#19B7FF_100%)] grid place-items-center text-white shrink-0">
                <Sparkles className="w-6 h-6" />
              </div>
              <div>
                <p className="text-xs font-black uppercase tracking-[0.2em] text-slate-400 mb-2">Diagnostico inicial</p>
                <h1 className="text-4xl md:text-5xl leading-none font-black text-slate-900">Cuentanos tu caso</h1>
                <p className="text-slate-500 mt-3 max-w-2xl">
                  Revisamos tu caso de salud, te mostramos si la ruta correcta es peticion, tutela, impugnacion o desacato, y luego decides si activas el documento por {LAUNCH_PRICE_LABEL}.
                </p>
              </div>
            </div>

            <form onSubmit={handleSubmit} className="grid gap-6">
              <div className="grid md:grid-cols-2 gap-6">
                <label className="grid gap-2">
                  <span className="text-sm font-bold text-slate-700">Nombre completo</span>
                  <input
                    required
                    type="text"
                    placeholder="Ej: Juan Perez"
                    className="w-full rounded-2xl border border-slate-200 bg-[#FCFDFF] px-4 py-4 outline-none"
                    value={form.name}
                    onChange={(e) => setForm({ ...form, name: e.target.value })}
                  />
                </label>
                <label className="grid gap-2">
                  <span className="text-sm font-bold text-slate-700">Correo electronico</span>
                  <input
                    required
                    type="email"
                    placeholder="tu@correo.com"
                    className="w-full rounded-2xl border border-slate-200 bg-[#FCFDFF] px-4 py-4 outline-none"
                    value={form.email}
                    onChange={(e) => setForm({ ...form, email: e.target.value })}
                  />
                </label>
              </div>

              <div className="grid md:grid-cols-2 gap-6">
                <label className="grid gap-2">
                  <span className="text-sm font-bold text-slate-700">Telefono / WhatsApp</span>
                  <input
                    required
                    type="tel"
                    placeholder="300 123 4567"
                    className="w-full rounded-2xl border border-slate-200 bg-[#FCFDFF] px-4 py-4 outline-none"
                    value={form.phone}
                    onChange={(e) => setForm({ ...form, phone: e.target.value })}
                  />
                </label>
                <label className="grid gap-2">
                  <span className="text-sm font-bold text-slate-700">Entidad de salud</span>
                  <input
                    required
                    type="text"
                    placeholder="Ej: EPS Sura, Sanitas, Nueva EPS"
                    className="w-full rounded-2xl border border-slate-200 bg-[#FCFDFF] px-4 py-4 outline-none"
                    value={form.entity_name}
                    onChange={(e) => setForm({ ...form, entity_name: e.target.value })}
                  />
                </label>
              </div>

              <div className="grid md:grid-cols-2 gap-6">
                <label className="grid gap-2">
                  <span className="text-sm font-bold text-slate-700">Alcance habilitado</span>
                  <select
                    className="w-full rounded-2xl border border-slate-200 bg-[#FCFDFF] px-4 py-4 outline-none"
                    value={form.category}
                    onChange={(e) => setForm({ ...form, category: e.target.value })}
                  >
                    <option>Salud</option>
                  </select>
                </label>
                <label className="grid gap-2">
                  <span className="text-sm font-bold text-slate-700">Ciudad</span>
                  <input
                    required
                    type="text"
                    placeholder="Ej: Medellin"
                    className="w-full rounded-2xl border border-slate-200 bg-[#FCFDFF] px-4 py-4 outline-none"
                    value={form.city}
                    onChange={(e) => setForm({ ...form, city: e.target.value })}
                  />
                </label>
              </div>

              <label className="grid gap-2">
                <span className="text-sm font-bold text-slate-700">Cuentanos que paso</span>
                <textarea
                  required
                  minLength={50}
                  rows={7}
                  placeholder="Describe los hechos, las fechas importantes, lo que te nego la EPS o IPS y por que esto te afecta hoy."
                  className="w-full rounded-[24px] border border-slate-200 bg-[#FCFDFF] px-4 py-4 outline-none resize-none"
                  value={form.description}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                />
                <span className="text-xs font-bold uppercase tracking-wide text-slate-400">Minimo 50 caracteres</span>
              </label>

              {error && (
                <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-4 text-sm font-semibold text-red-600">
                  {error}
                </div>
              )}

              <button
                type="submit"
                disabled={loading}
                className="inline-flex items-center justify-center gap-3 rounded-2xl bg-[#0D68FF] px-6 py-5 text-lg font-black text-white disabled:opacity-60"
              >
                {loading ? 'Analizando caso...' : 'Quiero ver mi ruta legal'}
                <ArrowRight size={20} />
              </button>
            </form>
          </section>

          <aside className="grid gap-6">
            <div className="rounded-[28px] border border-white/10 bg-[#08172E] p-8 text-white shadow-[0_18px_55px_rgba(18,35,61,0.12)]">
              <p className="text-xs font-black uppercase tracking-[0.2em] text-[#36D399]">Lo que obtienes aqui</p>
              <div className="grid gap-5 mt-6">
                <div className="flex gap-4">
                  <div className="w-11 h-11 rounded-2xl bg-white/10 grid place-items-center shrink-0"><HeartPulse size={20} /></div>
                  <div>
                    <p className="font-black">Diagnostico inmediato</p>
                    <p className="text-sm text-white/70 mt-1">Te mostramos la ruta correcta dentro del bloque de salud: peticion, tutela, impugnacion o desacato.</p>
                  </div>
                </div>
                <div className="flex gap-4">
                  <div className="w-11 h-11 rounded-2xl bg-white/10 grid place-items-center shrink-0"><FileText size={20} /></div>
                  <div>
                    <p className="font-black">Documento por {LAUNCH_PRICE_LABEL}</p>
                    <p className="text-sm text-white/70 mt-1">Mismo precio para cualquiera de los cuatro tramites hoy habilitados en salud.</p>
                  </div>
                </div>
                <div className="flex gap-4">
                  <div className="w-11 h-11 rounded-2xl bg-white/10 grid place-items-center shrink-0"><Trophy size={20} /></div>
                  <div>
                    <p className="font-black">Rifa de lanzamiento</p>
                    <p className="text-sm text-white/70 mt-1">{RAFFLE_LONG_COPY}</p>
                  </div>
                </div>
              </div>
            </div>

            <div className="rounded-[28px] border border-slate-200 bg-white p-8 shadow-[0_18px_55px_rgba(18,35,61,0.06)]">
              <p className="text-xs font-black uppercase tracking-[0.2em] text-slate-400 mb-4">Antes de pagar</p>
              <div className="grid gap-4">
                <div className="flex items-start gap-3">
                  <CheckCircle2 size={18} className="text-[#36D399] mt-1 shrink-0" />
                  <p className="text-sm text-slate-600">Primero ves la ruta recomendada para tu caso de salud. No compras a ciegas.</p>
                </div>
                <div className="flex items-start gap-3">
                  <CheckCircle2 size={18} className="text-[#36D399] mt-1 shrink-0" />
                  <p className="text-sm text-slate-600">Si el caso no esta claro, el sistema te pide mejor informacion antes de cobrar.</p>
                </div>
                <div className="flex items-start gap-3">
                  <ShieldCheck size={18} className="text-[#0D68FF] mt-1 shrink-0" />
                  <p className="text-sm text-slate-600">Tus datos se usan para construir el expediente y mantener trazabilidad del caso.</p>
                </div>
              </div>
            </div>
          </aside>
        </div>
      </main>
    </div>
  );
};

export default DiagnosisPage;
