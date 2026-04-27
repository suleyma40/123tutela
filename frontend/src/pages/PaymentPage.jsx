import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { AlertCircle, ArrowRight, CheckCircle2, ShieldCheck, Trophy } from 'lucide-react';
import Navbar from '../components/Navbar';
import { api, extractError } from '../lib/api';

const widgetScriptUrl = 'https://checkout.wompi.co/widget.js';

const PaymentPage = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [guestCase, setGuestCase] = useState(null);

  useEffect(() => {
    const saved = localStorage.getItem('hazlopormi-guest-case');
    if (saved) {
      setGuestCase(JSON.parse(saved));
    } else {
      navigate('/diagnostico');
    }
  }, [navigate]);

  const launchWidget = (checkout) =>
    new Promise((resolve, reject) => {
      const start = () => {
        if (!window.WidgetCheckout) {
          reject(new Error('Widget de Wompi no disponible.'));
          return;
        }
        try {
          const widget = new window.WidgetCheckout({
            currency: checkout.currency,
            amountInCents: checkout.amount_in_cents,
            reference: checkout.reference,
            publicKey: checkout.public_key,
            redirectUrl: checkout['redirect-url'],
            customerData: { email: checkout['customer-data:email'] },
            signature: { integrity: checkout['signature:integrity'] },
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
        existing.addEventListener('load', start, { once: true });
        return;
      }
      const script = document.createElement('script');
      script.src = widgetScriptUrl;
      script.async = true;
      script.dataset.wompiWidget = 'true';
      script.onload = start;
      document.body.appendChild(script);
    });

  const handlePayment = async () => {
    if (!guestCase) return;
    setLoading(true);
    setError('');
    try {
      const response = await api.post(`/public/cases/${guestCase.caseId}/payments/wompi/session`, {
        public_token: guestCase.publicToken,
      });
      await launchWidget(response.data.checkout);
    } catch (err) {
      setError(extractError(err, 'No fue posible iniciar el pago. Intenta de nuevo.'));
    } finally {
      setLoading(false);
    }
  };

  if (!guestCase) return null;

  return (
    <div className="min-h-screen bg-[#F5F7FB] text-slate-900">
      <Navbar />

      <main className="pt-32 pb-20 px-6">
        <div className="max-w-6xl mx-auto grid lg:grid-cols-[0.95fr_1.05fr] gap-8">
          <section className="rounded-[28px] border border-white/10 bg-[#08172E] p-8 md:p-10 text-white shadow-[0_18px_55px_rgba(18,35,61,0.12)]">
            <div className="inline-flex items-center gap-2 rounded-full bg-[#36D399]/15 px-4 py-2 text-xs font-black uppercase tracking-[0.16em] text-[#36D399]">
              <CheckCircle2 size={14} />
              Caso analizado
            </div>

            <h1 className="mt-6 text-4xl md:text-5xl font-black leading-none">Activa tu documento</h1>
            <p className="mt-4 text-white/72 text-lg leading-7">
              Ya tienes una ruta recomendada. Ahora puedes activar tu documento con pago seguro y entrar al sorteo especial de mayo.
            </p>

            <div className="mt-8 rounded-[24px] border border-white/10 bg-white/5 p-6 relative overflow-hidden">
              <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-bl from-white/5 to-transparent rounded-bl-full pointer-events-none"></div>
              <p className="text-xs font-black uppercase tracking-[0.18em] text-white/45 mb-3">Resultado del Análisis</p>
              <h2 className="text-2xl font-black">{guestCase.recommendedAction}</h2>
              <p className="text-sm text-white/70 mt-4 leading-6">
                Hemos evaluado la viabilidad de tu caso y la ruta legal recomendada es iniciar una <strong>{guestCase.recommendedAction}</strong>. 
                Al adquirir el documento, nuestro sistema preparará la redacción con todo el <strong>sustento jurídico necesario</strong>.
              </p>
              <p className="text-sm text-white/70 mt-3 leading-6">
                Adicionalmente, te entregaremos una <strong>guía paso a paso</strong> indicándote exactamente:
              </p>
              <ul className="mt-3 space-y-1 text-sm text-white/70 list-disc list-inside">
                <li>A qué entidad dirigirte y por qué canal.</li>
                <li>Los tiempos exactos de respuesta que dicta la ley.</li>
                <li>Qué esperar y qué hacer si no te responden.</li>
              </ul>
            </div>

            <div className="grid gap-4 mt-8">
              <div className="flex items-start gap-3">
                <CheckCircle2 size={18} className="text-[#36D399] mt-1 shrink-0" />
                <p className="text-sm text-white/72">Documento legal robusto y listo para presentar, sin que tengas que redactar nada.</p>
              </div>
              <div className="flex items-start gap-3">
                <ShieldCheck size={18} className="text-[#19B7FF] mt-1 shrink-0" />
                <p className="text-sm text-white/72">Seguridad total en tu pago a través de Wompi. Tu documento se generará de inmediato.</p>
              </div>
              <div className="flex items-start gap-3">
                <Trophy size={18} className="text-[#F59E0B] mt-1 shrink-0" />
                <p className="text-sm text-white/72">Acceso automático al sorteo de $2.500.000 COP, solo para usuarios registrados.</p>
              </div>
            </div>
          </section>

          <section className="rounded-[28px] border border-slate-200 bg-white p-8 md:p-10 shadow-[0_18px_55px_rgba(18,35,61,0.06)]">
            <p className="text-xs font-black uppercase tracking-[0.18em] text-slate-400 mb-3">Checkout</p>
            <h2 className="text-4xl font-black leading-none">$49.900</h2>
            <p className="text-slate-500 mt-3">Precio unico para cualquier documento del catalogo activo de salud.</p>

            <div className="grid gap-4 mt-8">
              <div className="rounded-[22px] border border-slate-200 bg-[#FCFDFF] p-5">
                <div className="flex justify-between gap-4 text-sm">
                  <span className="text-slate-500">Analisis inicial del caso</span>
                  <strong>Gratis</strong>
                </div>
                <div className="flex justify-between gap-4 text-sm mt-3">
                  <span className="text-slate-500">Documento</span>
                  <strong>$49.900</strong>
                </div>
                <div className="flex justify-between gap-4 text-sm mt-3">
                  <span className="text-slate-500">Participacion bono mayo</span>
                  <strong>Incluida</strong>
                </div>
              </div>

              <div className="rounded-[22px] border border-slate-200 bg-gradient-to-br from-[#F8FBFF] to-[#EFF5FF] p-5 relative overflow-hidden">
                <div className="absolute -right-6 -top-6 text-[#0D68FF]/5">
                  <Trophy size={100} />
                </div>
                <p className="text-xs font-black uppercase tracking-[0.18em] text-[#0D68FF] mb-2">Beneficio Exclusivo</p>
                <p className="text-lg font-black text-slate-900">Sorteo de $2.5 Millones COP</p>
                <p className="text-sm text-slate-500 mt-2 leading-6 relative z-10">
                  Al completar tu solicitud hoy, participas automáticamente por un bono de $2.500.000 pesos colombianos que sortearemos en vivo el próximo 30 de mayo de 2026.
                </p>
              </div>

              <div className="grid gap-3">
                <div className="flex items-center gap-3 rounded-2xl border border-slate-200 bg-white px-4 py-4">
                  <ShieldCheck className="text-[#36D399] shrink-0" />
                  <p className="text-sm text-slate-600">Pago procesado de forma segura por Wompi.</p>
                </div>
                <div className="flex items-center gap-3 rounded-2xl border border-slate-200 bg-white px-4 py-4">
                  <AlertCircle className="text-[#F59E0B] shrink-0" />
                  <p className="text-sm text-slate-600">Despues del pago veras el estado real del expediente y el siguiente paso operativo.</p>
                </div>
              </div>
            </div>

            {error && (
              <div className="mt-6 rounded-2xl border border-red-200 bg-red-50 px-4 py-4 text-sm font-semibold text-red-600">
                {error}
              </div>
            )}

            <button
              onClick={handlePayment}
              disabled={loading}
              className="mt-8 inline-flex w-full items-center justify-center gap-3 rounded-2xl bg-[#0D68FF] px-6 py-5 text-lg font-black text-white hover:bg-blue-700 transition-colors disabled:opacity-60"
            >
              {loading ? 'Iniciando pago...' : 'Pagar y activar documento'}
              <ArrowRight size={20} />
            </button>

            {(import.meta.env.DEV || guestCase.email?.trim().toLowerCase() === 'su-ley23@hotmail.com' || guestCase.email?.trim().toLowerCase() === 'mariibpa25@gmail.com') && (
              <button
                onClick={async () => {
                  setLoading(true);
                  try {
                    const sess = await api.post(`/public/cases/${guestCase.caseId}/payments/wompi/session`, { public_token: guestCase.publicToken });
                    await api.post(`/public/payments/simulate`, { 
                      transaction_id: `simulated_${sess.data.checkout.reference}`,
                      reference: sess.data.checkout.reference, 
                      public_token: guestCase.publicToken 
                    });
                    navigate(`/pago/resultado?id=simulated_${sess.data.checkout.reference}`);
                  } catch(e) {
                    setError('Error en simulación: ' + extractError(e));
                  } finally { setLoading(false); }
                }}
                disabled={loading}
                className="mt-3 inline-flex w-full items-center justify-center gap-3 rounded-2xl bg-slate-800 px-6 py-4 text-sm font-black text-white hover:bg-slate-700 transition-colors disabled:opacity-60"
              >
                Simular Pago (Modo Prueba)
              </button>
            )}

            <img
              src="https://checkout.wompi.co/images/payment-methods.png"
              alt="Metodos de pago"
              className="h-6 opacity-60 grayscale mx-auto mt-6"
            />
          </section>
        </div>
      </main>
    </div>
  );
};

export default PaymentPage;
