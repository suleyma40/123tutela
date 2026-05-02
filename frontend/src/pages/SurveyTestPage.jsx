import React, { useState } from 'react';
import Navbar from '../components/Navbar';
import { api, extractError } from '../lib/api';

const initialForm = {
  name: '',
  email: '',
  phone: '',
  company: '',
  role: '',
  overall_rating: 4,
  ease_rating: 4,
  trust_rating: 4,
  would_pay: 'si',
  positives: '',
  blockers: '',
  improvement: '',
};

const SurveyTestPage = () => {
  const [form, setForm] = useState(initialForm);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const onChange = (key, value) => {
    setForm((current) => ({ ...current, [key]: value }));
  };

  const submit = async (event) => {
    event.preventDefault();
    setSending(true);
    setError('');
    setSuccess('');
    try {
      const payload = {
        ...form,
        overall_rating: Number(form.overall_rating),
        ease_rating: Number(form.ease_rating),
        trust_rating: Number(form.trust_rating),
      };
      const response = await api.post('/public/testing/survey', payload);
      setSuccess(`Gracias. Tu respuesta fue registrada. Codigo interno: ${response?.data?.case_id || 'OK'}`);
      setForm(initialForm);
    } catch (err) {
      setError(extractError(err, 'No fue posible registrar la encuesta.'));
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F5F7FB] text-slate-900">
      <Navbar />
      <main className="pt-28 pb-16 px-6">
        <div className="max-w-3xl mx-auto rounded-3xl border border-slate-200 bg-white p-8 md:p-10 shadow-[0_18px_55px_rgba(18,35,61,0.08)]">
          <p className="text-xs font-black uppercase tracking-[0.2em] text-slate-400 mb-3">Test privado fin de semana</p>
          <h1 className="text-4xl font-black leading-tight">Encuesta de validación</h1>
          <p className="text-slate-600 mt-3">
            Este formulario es solo para personas invitadas. Las respuestas quedan guardadas en el panel admin para revisión y análisis interno.
          </p>

          <form onSubmit={submit} className="grid gap-4 mt-8">
            <div className="grid md:grid-cols-2 gap-4">
              <input className="rounded-xl border border-slate-200 px-4 py-3" placeholder="Nombre completo" value={form.name} onChange={(e) => onChange('name', e.target.value)} required />
              <input className="rounded-xl border border-slate-200 px-4 py-3" placeholder="Correo" type="email" value={form.email} onChange={(e) => onChange('email', e.target.value)} required />
            </div>
            <div className="grid md:grid-cols-2 gap-4">
              <input className="rounded-xl border border-slate-200 px-4 py-3" placeholder="Celular" value={form.phone} onChange={(e) => onChange('phone', e.target.value)} required />
              <input className="rounded-xl border border-slate-200 px-4 py-3" placeholder="Empresa (opcional)" value={form.company} onChange={(e) => onChange('company', e.target.value)} />
            </div>
            <input className="rounded-xl border border-slate-200 px-4 py-3" placeholder="Rol / cargo (opcional)" value={form.role} onChange={(e) => onChange('role', e.target.value)} />

            <div className="grid md:grid-cols-3 gap-4">
              <label className="text-sm font-bold text-slate-700">Calificación general (1-5)
                <select className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2" value={form.overall_rating} onChange={(e) => onChange('overall_rating', e.target.value)}>
                  {[1, 2, 3, 4, 5].map((n) => <option key={`o-${n}`} value={n}>{n}</option>)}
                </select>
              </label>
              <label className="text-sm font-bold text-slate-700">Facilidad de uso (1-5)
                <select className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2" value={form.ease_rating} onChange={(e) => onChange('ease_rating', e.target.value)}>
                  {[1, 2, 3, 4, 5].map((n) => <option key={`e-${n}`} value={n}>{n}</option>)}
                </select>
              </label>
              <label className="text-sm font-bold text-slate-700">Confianza (1-5)
                <select className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2" value={form.trust_rating} onChange={(e) => onChange('trust_rating', e.target.value)}>
                  {[1, 2, 3, 4, 5].map((n) => <option key={`t-${n}`} value={n}>{n}</option>)}
                </select>
              </label>
            </div>

            <label className="text-sm font-bold text-slate-700">¿Pagarías por el servicio?
              <select className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2" value={form.would_pay} onChange={(e) => onChange('would_pay', e.target.value)}>
                <option value="si">Sí</option>
                <option value="no">No</option>
                <option value="depende">Depende</option>
              </select>
            </label>

            <textarea className="rounded-xl border border-slate-200 px-4 py-3" rows={3} placeholder="¿Qué fue lo más útil?" value={form.positives} onChange={(e) => onChange('positives', e.target.value)} />
            <textarea className="rounded-xl border border-slate-200 px-4 py-3" rows={3} placeholder="¿Qué te bloqueó o generó duda?" value={form.blockers} onChange={(e) => onChange('blockers', e.target.value)} />
            <textarea className="rounded-xl border border-slate-200 px-4 py-3" rows={3} placeholder="¿Qué mejorarías primero?" value={form.improvement} onChange={(e) => onChange('improvement', e.target.value)} />

            {error && <div className="rounded-xl border border-red-200 bg-red-50 text-red-700 px-4 py-3 text-sm font-semibold">{error}</div>}
            {success && <div className="rounded-xl border border-emerald-200 bg-emerald-50 text-emerald-700 px-4 py-3 text-sm font-semibold">{success}</div>}

            <button type="submit" disabled={sending} className="rounded-xl bg-[#0D68FF] text-white py-3 font-black disabled:opacity-60">
              {sending ? 'Enviando...' : 'Enviar encuesta'}
            </button>
          </form>
        </div>
      </main>
    </div>
  );
};

export default SurveyTestPage;

