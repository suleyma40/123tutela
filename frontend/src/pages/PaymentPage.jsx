import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { motion } from 'framer-motion';
import { CreditCard, CheckCircle2, ShieldCheck, Trophy, ArrowRight, Scale, AlertCircle } from 'lucide-react';
import { api, extractError } from '../lib/api';

const widgetScriptUrl = "https://checkout.wompi.co/widget.js";

const PaymentPage = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [guestCase, setGuestCase] = useState(null);

  useEffect(() => {
    const saved = localStorage.getItem("hazlopormi-guest-case");
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
        return;
      }
      const script = document.createElement("script");
      script.src = widgetScriptUrl;
      script.async = true;
      script.dataset.wompiWidget = "true";
      script.onload = start;
      document.body.appendChild(script);
    });

  const handlePayment = async () => {
    if (!guestCase) return;
    setLoading(true);
    setError("");
    try {
      const response = await api.post(`/public/cases/${guestCase.caseId}/payments/wompi/session`, { 
        public_token: guestCase.publicToken 
      });
      await launchWidget(response.data.checkout);
    } catch (err) {
      setError(extractError(err, "No fue posible iniciar el pago. Intenta de nuevo."));
    } finally {
      setLoading(false);
    }
  };

  if (!guestCase) return null;

  return (
    <div className="min-h-screen bg-cream">
      <Navbar />
      
      <main className="pt-32 pb-20 px-6">
        <div className="max-w-4xl mx-auto">
          <motion.div 
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-white rounded-[3rem] shadow-2xl border-4 border-brand overflow-hidden"
          >
            <div className="grid md:grid-cols-2">
              
              {/* Summary Side */}
              <div className="p-8 md:p-12 border-b md:border-b-0 md:border-r border-brand/10">
                <div className="inline-flex items-center gap-2 bg-success/10 text-success px-4 py-1.5 rounded-full text-xs font-black uppercase mb-6">
                  <CheckCircle2 size={14} /> Caso Analizado
                </div>
                
                <h2 className="text-3xl font-extrabold text-brand mb-4">Estrategia Recomendada</h2>
                <div className="bg-brand/5 p-6 rounded-2xl mb-8">
                  <h4 className="font-bold text-brand flex items-center gap-2 mb-2">
                    <Scale size={18} className="text-accent" /> {guestCase.recommendedAction}
                  </h4>
                  <p className="text-brand/70 text-sm leading-relaxed">
                    {guestCase.strategyText}
                  </p>
                </div>

                <div className="space-y-4">
                  <h4 className="font-bold text-brand text-sm uppercase">Tu kit incluirá:</h4>
                  <ul className="space-y-3">
                    <li className="flex items-center gap-3 text-sm font-medium text-brand/80">
                      <CheckCircle2 size={16} className="text-success" /> Documento legal redactado
                    </li>
                    <li className="flex items-center gap-3 text-sm font-medium text-brand/80">
                      <CheckCircle2 size={16} className="text-success" /> Guía paso a paso de radicación
                    </li>
                    <li className="flex items-center gap-3 text-sm font-medium text-brand/80">
                      <CheckCircle2 size={16} className="text-success" /> Código para la Rifa Mensual
                    </li>
                  </ul>
                </div>
              </div>

              {/* Payment Side */}
              <div className="p-8 md:p-12 bg-brand/5 flex flex-col justify-center relative">
                <div className="absolute top-6 right-[-40px] bg-accent text-brand font-bold py-1 px-12 rotate-45 shadow-lg text-[10px]">
                  <Trophy size={12} className="inline mr-1" /> RIFA ACTIVA
                </div>

                <div className="text-center mb-8">
                  <p className="text-brand/60 font-bold uppercase text-xs mb-2">Total a pagar</p>
                  <div className="flex items-baseline justify-center gap-2">
                    <span className="text-5xl font-black text-brand">$59.900</span>
                    <span className="text-brand/60 font-bold">COP</span>
                  </div>
                </div>

                <div className="space-y-4 mb-8">
                  <div className="flex items-center gap-3 bg-white p-4 rounded-xl shadow-sm border border-brand/5">
                    <ShieldCheck className="text-success shrink-0" />
                    <p className="text-xs text-brand/70 font-medium">Pago procesado de forma segura por Wompi (Bancolombia).</p>
                  </div>
                  <div className="flex items-center gap-3 bg-white p-4 rounded-xl shadow-sm border border-brand/5">
                    <AlertCircle className="text-accent shrink-0" />
                    <p className="text-xs text-brand/70 font-medium">Recibirás tu kit en tu correo en menos de 24 horas hábiles.</p>
                  </div>
                </div>

                {error && (
                  <p className="text-red-600 text-xs font-bold text-center mb-4">{error}</p>
                )}

                <button 
                  onClick={handlePayment}
                  disabled={loading}
                  className="btn-primary w-full py-5 text-xl flex justify-center items-center gap-3 shadow-[0_10px_30px_rgba(245,166,35,0.4)]"
                >
                  {loading ? "Iniciando..." : "Pagar y Activar Kit"} <ArrowRight />
                </button>

                <div className="mt-6 flex justify-center gap-4">
                  <img src="https://checkout.wompi.co/images/payment-methods.png" alt="Métodos de pago" className="h-6 opacity-60 grayscale" />
                </div>
              </div>

            </div>
          </motion.div>
          
          <p className="text-center mt-8 text-brand/40 text-sm font-medium">
            Al realizar el pago, aceptas nuestros términos de servicio y políticas de privacidad.
          </p>
        </div>
      </main>
    </div>
  );
};

export default PaymentPage;
