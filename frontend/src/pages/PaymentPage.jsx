import React, { useCallback, useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { AlertCircle, ArrowRight, CheckCircle2, ShieldCheck, Trophy } from 'lucide-react';
import Navbar from '../components/Navbar';
import { api, extractError } from '../lib/api';
import { trackEvent } from '../lib/analytics';
import { LAUNCH_PRICE_LABEL, RAFFLE_LONG_COPY, RAFFLE_PRIZE_LABEL } from '../lib/launchConfig';

const widgetScriptUrl = 'https://checkout.wompi.co/widget.js';
const QA_MIN_PAYMENT_EMAILS = new Set([
  'su-ley23@hotmail.com',
  'm22perezia@gmail.com',
  'mariibpa25@gmail.com',
]);
const PUBLIC_TEST_CODES = new Set(
  String(import.meta.env.VITE_PUBLIC_TEST_CODES || 'TEST123,TESTMAYO,QA2026')
    .split(',')
    .map((v) => v.trim().toLowerCase())
    .filter(Boolean)
);

const PaymentPage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [guestCase, setGuestCase] = useState(null);
  const [selectedPlan, setSelectedPlan] = useState('base');
  const testCodeFromUrl = new URLSearchParams(location.search).get('test_code') || '';
  const storedTestCode = localStorage.getItem('hazlopormi-test-code') || '';
  const effectiveTestCode = testCodeFromUrl || storedTestCode;

  const withTestCode = useCallback((basePath) => {
    if (!effectiveTestCode) return basePath;
    const separator = basePath.includes('?') ? '&' : '?';
    return `${basePath}${separator}test_code=${encodeURIComponent(effectiveTestCode)}`;
  }, [effectiveTestCode]);

  useEffect(() => {
    if (testCodeFromUrl) {
      localStorage.setItem('hazlopormi-test-code', testCodeFromUrl);
    }
    const saved = localStorage.getItem('hazlopormi-guest-case');
    if (saved) {
      const parsed = JSON.parse(saved);
      setGuestCase(parsed);
      if (parsed?.caseId && parsed?.publicToken) {
        api
          .get(`/public/cases/${parsed.caseId}`, { params: { public_token: parsed.publicToken } })
          .then((response) => {
            const freshCase = response?.data?.case || {};
            const refreshed = {
              ...parsed,
              recommendedAction: freshCase.recommended_action || parsed.recommendedAction,
              strategyText: freshCase.strategy_text || parsed.strategyText,
              paymentStatus: freshCase.payment_status || parsed.paymentStatus || 'pendiente',
            };
            setGuestCase(refreshed);
            localStorage.setItem('hazlopormi-guest-case', JSON.stringify(refreshed));
          })
          .catch(() => {});
      }
    } else {
      navigate(withTestCode('/diagnostico'));
    }
  }, [navigate, location.search, testCodeFromUrl, withTestCode]);

  const diagnosisCopy = (guestCase?.strategyText || '').trim();
  const hasStructuredDiagnosis = diagnosisCopy.includes('🔴 Derecho vulnerado:');
  const isAlreadyPaid = String(guestCase?.paymentStatus || '').toLowerCase() === 'pagado';
  const testCode = effectiveTestCode;
  const isPublicTestMode = PUBLIC_TEST_CODES.has(String(testCode).trim().toLowerCase());
  const canShowTesterButtons =
    !isAlreadyPaid &&
    (import.meta.env.DEV ||
      QA_MIN_PAYMENT_EMAILS.has((guestCase?.email || '').trim().toLowerCase()) ||
      isPublicTestMode);

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
        } catch (launchError) {
          reject(launchError);
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

  const redirectAfterWidget = ({ checkout, widgetResult }) => {
    const tx =
      widgetResult?.transaction?.id ||
      widgetResult?.transactionId ||
      widgetResult?.id ||
      '';
    const reference =
      widgetResult?.transaction?.reference ||
      widgetResult?.reference ||
      checkout?.reference ||
      '';
    if (tx) {
      navigate(withTestCode(`/pago/resultado?id=${encodeURIComponent(String(tx))}&case_id=${encodeURIComponent(String(guestCase?.caseId || ''))}&public_token=${encodeURIComponent(String(guestCase?.publicToken || ''))}`));
      return;
    }
    if (reference) {
      navigate(withTestCode(`/pago/resultado?reference=${encodeURIComponent(String(reference))}&case_id=${encodeURIComponent(String(guestCase?.caseId || ''))}&public_token=${encodeURIComponent(String(guestCase?.publicToken || ''))}`));
      return;
    }
    navigate(withTestCode(`/pago/resultado?case_id=${encodeURIComponent(String(guestCase?.caseId || ''))}&public_token=${encodeURIComponent(String(guestCase?.publicToken || ''))}`));
  };

  const handlePayment = async () => {
    if (!guestCase) return;
    if (isAlreadyPaid) {
      navigate(withTestCode(`/pago/resultado?case_id=${encodeURIComponent(String(guestCase.caseId || ''))}&public_token=${encodeURIComponent(String(guestCase.publicToken || ''))}`));
      return;
    }
    setLoading(true);
    setError('');
    try {
      const response = await api.post(`/public/cases/${guestCase.caseId}/payments/wompi/session`, {
        public_token: guestCase.publicToken,
        add_on_type: selectedPlan === 'full' ? 'full_support_pack' : undefined,
      });
      trackEvent('start_checkout', {
        case_id: guestCase.caseId,
        recommended_action: guestCase.recommendedAction,
      });
      const widgetResult = await launchWidget(response.data.checkout);
      redirectAfterWidget({ checkout: response.data.checkout, widgetResult });
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
              Ya tienes una ruta recomendada dentro del bloque de salud. Activa tu documento con pago seguro y, despues del pago, completa tus datos y anexa soportes para que el equipo experto lo elabore.
            </p>

            <div className="mt-8 rounded-[24px] border border-white/10 bg-white/5 p-6 relative overflow-hidden">
              <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-bl from-white/5 to-transparent rounded-bl-full pointer-events-none"></div>
              <p className="text-xs font-black uppercase tracking-[0.18em] text-white/45 mb-3">Resultado del analisis</p>
              <h2 className="text-2xl font-black">{guestCase.recommendedAction}</h2>
              {hasStructuredDiagnosis ? (
                <pre className="text-sm text-white/80 mt-4 leading-6 whitespace-pre-wrap font-sans">
                  {diagnosisCopy}
                </pre>
              ) : (
                <>
                  <p className="text-sm text-white/70 mt-4 leading-6">
                    Hemos evaluado la viabilidad de tu caso y la ruta legal recomendada es iniciar una <strong>{guestCase.recommendedAction}</strong>.
                    Al activar el servicio, especialistas juridicos elaboraran el documento con el <strong>sustento legal necesario</strong>, segun la informacion y soportes que compartas.
                  </p>
                  <p className="text-sm text-white/70 mt-3 leading-6">
                    Adicionalmente, te entregaremos una <strong>guia paso a paso</strong> indicandote exactamente:
                  </p>
                  <ul className="mt-3 space-y-1 text-sm text-white/70 list-disc list-inside">
                    <li>A que entidad dirigirte y por que canal.</li>
                    <li>Los tiempos exactos de respuesta que dicta la ley.</li>
                    <li>Que esperar y que hacer si no te responden.</li>
                  </ul>
                </>
              )}
            </div>

            <div className="grid gap-4 mt-8">
              <div className="flex items-start gap-3">
                <CheckCircle2 size={18} className="text-[#36D399] mt-1 shrink-0" />
                <p className="text-sm text-white/72">Documento de salud elaborado por especialistas, listo para presentar.</p>
              </div>
              <div className="flex items-start gap-3">
                <ShieldCheck size={18} className="text-[#19B7FF] mt-1 shrink-0" />
                <p className="text-sm text-white/72">Pago seguro por Wompi. La elaboracion inicia cuando completes datos y anexos del expediente.</p>
              </div>
              <div className="flex items-start gap-3">
                <Trophy size={18} className="text-[#F59E0B] mt-1 shrink-0" />
                <p className="text-sm text-white/72">Acceso automatico a la rifa de lanzamiento por {RAFFLE_PRIZE_LABEL}, con pago aprobado.</p>
              </div>
            </div>
          </section>

          <section className="rounded-[28px] border border-slate-200 bg-white p-8 md:p-10 shadow-[0_18px_55px_rgba(18,35,61,0.06)]">
            <p className="text-xs font-black uppercase tracking-[0.18em] text-slate-400 mb-3">Checkout</p>
            <h2 className="text-4xl font-black leading-none">{selectedPlan === 'full' ? '$114.900' : LAUNCH_PRICE_LABEL}</h2>
            <p className="text-slate-500 mt-3">
              {selectedPlan === 'full'
                ? 'Incluye elaboracion, radicacion y seguimiento del mismo caso hasta desacato (no demandas).'
                : 'Precio unico para cualquiera de los cuatro tramites hoy habilitados en salud.'}
            </p>

            <div className="mt-6 grid gap-3">
              <button
                type="button"
                onClick={() => setSelectedPlan('base')}
                className={`w-full rounded-2xl border px-4 py-4 text-left transition-colors ${selectedPlan === 'base' ? 'border-[#0D68FF] bg-blue-50' : 'border-slate-200 bg-white hover:bg-slate-50'}`}
              >
                <p className="text-sm font-black text-slate-900">Plan base - {LAUNCH_PRICE_LABEL}</p>
                <p className="text-xs text-slate-600 mt-1">Documento recomendado y guia de radicacion.</p>
              </button>
              <button
                type="button"
                onClick={() => setSelectedPlan('full')}
                className={`w-full rounded-2xl border px-4 py-4 text-left transition-colors ${selectedPlan === 'full' ? 'border-[#0D68FF] bg-blue-50' : 'border-slate-200 bg-white hover:bg-slate-50'}`}
              >
                <p className="text-sm font-black text-slate-900">Paquete completo - $114.900</p>
                <p className="text-xs text-slate-600 mt-1">Incluye elaboracion, radicacion y seguimiento del mismo tema hasta desacato (sin demandas), segun lineamientos y tiempos disponibles.</p>
              </button>
            </div>

            <div className="grid gap-4 mt-8">
              <div className="rounded-[22px] border border-slate-200 bg-[#FCFDFF] p-5">
                <div className="flex justify-between gap-4 text-sm">
                  <span className="text-slate-500">Analisis inicial del caso</span>
                  <strong>Gratis</strong>
                </div>
                <div className="flex justify-between gap-4 text-sm mt-3">
                  <span className="text-slate-500">Documento de salud recomendado</span>
                  <strong>{LAUNCH_PRICE_LABEL}</strong>
                </div>
                {selectedPlan === 'full' && (
                  <div className="flex justify-between gap-4 text-sm mt-3">
                    <span className="text-slate-500">Paquete completo adicional</span>
                    <strong>$65.000</strong>
                  </div>
                )}
                <div className="flex justify-between gap-4 text-sm mt-3">
                  <span className="text-slate-500">Participacion rifa lanzamiento</span>
                  <strong>Incluida</strong>
                </div>
                <div className="mt-4 border-t border-slate-200 pt-3 flex justify-between gap-4 text-sm">
                  <span className="font-bold text-slate-800">Total a pagar</span>
                  <strong>{selectedPlan === 'full' ? '$114.900' : LAUNCH_PRICE_LABEL}</strong>
                </div>
              </div>

              <div className="rounded-[22px] border border-slate-200 bg-gradient-to-br from-[#F8FBFF] to-[#EFF5FF] p-5 relative overflow-hidden">
                <div className="absolute -right-6 -top-6 text-[#0D68FF]/5">
                  <Trophy size={100} />
                </div>
                <p className="text-xs font-black uppercase tracking-[0.18em] text-[#0D68FF] mb-2">Beneficio exclusivo</p>
                <p className="text-lg font-black text-slate-900">Rifa de {RAFFLE_PRIZE_LABEL}</p>
                <p className="text-sm text-slate-500 mt-2 leading-6 relative z-10">
                  {RAFFLE_LONG_COPY}
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

            <div className="mt-6 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-4">
              <p className="text-sm font-bold text-amber-800">
                Importante: en Wompi el cobro puede aparecer a nombre de <strong>Educolombia</strong>, empresa operadora de 123tutela.
              </p>
              <p className="text-xs text-amber-700 mt-1">
                Es normal y corresponde a este servicio.
              </p>
            </div>

            {error && (
              <div className="mt-6 rounded-2xl border border-red-200 bg-red-50 px-4 py-4 text-sm font-semibold text-red-600">
                {error}
              </div>
            )}

            {isAlreadyPaid ? (
              <button
                onClick={() => navigate(withTestCode(`/pago/resultado?case_id=${encodeURIComponent(String(guestCase.caseId || ''))}&public_token=${encodeURIComponent(String(guestCase.publicToken || ''))}`))}
                className="mt-8 inline-flex w-full items-center justify-center gap-3 rounded-2xl bg-emerald-700 px-6 py-5 text-lg font-black text-white hover:bg-emerald-600 transition-colors"
              >
                Continuar y completar datos
                <ArrowRight size={20} />
              </button>
            ) : (
              <button
                onClick={handlePayment}
                disabled={loading}
                className="mt-8 inline-flex w-full items-center justify-center gap-3 rounded-2xl bg-[#0D68FF] px-6 py-5 text-lg font-black text-white hover:bg-blue-700 transition-colors disabled:opacity-60"
              >
                {loading ? 'Iniciando pago...' : selectedPlan === 'full' ? 'Pagar paquete completo' : 'Pagar y activar documento'}
                <ArrowRight size={20} />
              </button>
            )}

            {canShowTesterButtons && (
              <>
                {isPublicTestMode && (
                  <button
                    onClick={async () => {
                      setLoading(true);
                      setError('');
                      try {
                        const sess = await api.post(`/public/cases/${guestCase.caseId}/payments/wompi/session`, {
                          public_token: guestCase.publicToken,
                          add_on_type: selectedPlan === 'full' ? 'full_support_pack' : undefined,
                        });
                        const ref = sess.data.checkout.reference;
                        await api.post(`/public/payments/simulate`, {
                          transaction_id: `simulated_${ref}`,
                          reference: ref,
                          public_token: guestCase.publicToken,
                          test_code: testCode || undefined,
                        });
                        navigate(withTestCode(`/pago/resultado?id=simulated_${ref}&test_mode=1`));
                      } catch (e) {
                        const msg = extractError(e);
                        if (msg && msg.toLowerCase().includes('pago aprobado')) {
                          navigate(withTestCode('/pago/resultado?simulated=true&test_mode=1'));
                        } else {
                          setError(`Error en simulacion: ${msg}`);
                        }
                      } finally {
                        setLoading(false);
                      }
                    }}
                    disabled={loading}
                    className="mt-3 inline-flex w-full items-center justify-center gap-3 rounded-2xl bg-violet-700 px-6 py-4 text-sm font-black text-white hover:bg-violet-600 transition-colors disabled:opacity-60"
                  >
                    Continuar sin pago (test)
                  </button>
                )}
              </>
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
