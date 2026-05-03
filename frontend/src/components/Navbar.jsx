import React, { useEffect, useMemo, useState } from 'react';
import { Scale, ArrowRight, Sparkles } from 'lucide-react';
import { Link, useLocation } from 'react-router-dom';
import { trackEvent } from '../lib/analytics';
import { api } from '../lib/api';
import { LAUNCH_PRICE_LABEL, RAFFLE_SHORT_LABEL } from '../lib/launchConfig';

const TEST_PAYMENT_LINK = '/diagnostico?test_code=TEST123';

const Navbar = () => {
  const location = useLocation();
  const isAdmin = location.pathname.startsWith('/admin');
  const isLanding = location.pathname === '/';
  const [marketingConfig, setMarketingConfig] = useState(null);

  useEffect(() => {
    let active = true;
    api.get('/public/marketing/config')
      .then((response) => {
        if (active) setMarketingConfig(response.data);
      })
      .catch(() => {});
    return () => { active = false; };
  }, []);

  const ctaLabel = useMemo(() => {
    const variant = String(marketingConfig?.cta_variant || 'default');
    if (marketingConfig?.cta_label) return marketingConfig.cta_label;
    if (variant === 'urgencia') return 'Activa hoy tu documento y evita más demoras';
    if (variant === 'confianza') return 'Tu caso en manos expertas, con ruta legal clara';
    if (variant === 'sorteo') return `Activa tu documento por ${LAUNCH_PRICE_LABEL} y participa`;
    return `Activa tu documento por ${LAUNCH_PRICE_LABEL}`;
  }, [marketingConfig]);
  const raffleLabel = marketingConfig?.raffle_label || RAFFLE_SHORT_LABEL;

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 border-b border-slate-200/80 bg-[rgba(245,247,251,0.82)] backdrop-blur-xl">
      <div className="max-w-7xl mx-auto px-6">
        <div className="min-h-[84px] flex items-center justify-between gap-4 flex-wrap">
          <Link to="/" className="flex items-center gap-3 no-underline">
            <div className="w-10 h-10 rounded-[14px] bg-[linear-gradient(135deg,#0D68FF_0%,#19B7FF_100%)] grid place-items-center text-white">
              <Scale className="w-5 h-5" />
            </div>
            <span className="text-[30px] leading-none font-black text-slate-900">
              123<span className="text-[#0D68FF]">tutela</span>
            </span>
          </Link>

          <div className="flex items-center gap-4 flex-wrap text-sm font-bold text-slate-500">
            {isLanding ? (
              <>
                <a href="#como-funciona" className="text-inherit no-underline hover:text-slate-900 transition-colors">Como funciona</a>
                <a href="#documentos-salud" className="text-inherit no-underline hover:text-slate-900 transition-colors">Documentos de salud</a>
                <a href="#precios" className="text-inherit no-underline hover:text-slate-900 transition-colors">Precios</a>
              </>
            ) : (
              <>
                {!isAdmin && <Link to="/" className="text-inherit no-underline hover:text-slate-900 transition-colors">Inicio</Link>}
                {!isAdmin && <Link to="/terminos" className="text-inherit no-underline hover:text-slate-900 transition-colors">Terminos</Link>}
                {!isAdmin && <Link to="/privacidad" className="text-inherit no-underline hover:text-slate-900 transition-colors">Privacidad</Link>}
                {!isAdmin && <Link to="/contacto" className="text-inherit no-underline hover:text-slate-900 transition-colors">Contacto</Link>}
              </>
            )}
            {isAdmin && (
              <Link to="/equipo" className="rounded-xl border border-slate-200 px-4 py-2 text-[#0D68FF] no-underline hover:bg-slate-50 transition-colors">
                Panel interno
              </Link>
            )}
            {!isAdmin && (
              <span className="hidden lg:inline-flex items-center rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-[11px] font-extrabold uppercase tracking-[0.16em] text-emerald-700">
                Solo salud
              </span>
            )}
            {!isAdmin && (
              <Link
                to={TEST_PAYMENT_LINK}
                onClick={() => trackEvent('cta_click', { cta: 'public_test_link', cta_variant: 'test' })}
                className="inline-flex items-center gap-2 rounded-xl border border-violet-200 bg-violet-50 px-4 py-2 text-violet-700 no-underline hover:bg-violet-100 transition-colors"
              >
                Link testeo
              </Link>
            )}
            {!isAdmin && (
              <Link
                to="/diagnostico"
                onClick={() => trackEvent('cta_click', { cta: 'rifa_topbar', cta_variant: marketingConfig?.cta_variant || 'default' })}
                className="inline-flex items-center gap-2 rounded-xl border border-amber-300 bg-amber-100 px-4 py-2 text-amber-800 no-underline hover:bg-amber-200 transition-colors animate-pulse"
              >
                <Sparkles size={15} />
                {raffleLabel}
              </Link>
            )}
            {!isAdmin && (
              <Link
                to="/diagnostico"
                onClick={() => trackEvent('cta_click', { cta: 'hero_topbar', cta_variant: marketingConfig?.cta_variant || 'default' })}
                className="inline-flex items-center gap-2 rounded-xl bg-[#0D68FF] px-4 py-2 text-white no-underline hover:bg-[#0D68FF]/90 transition-colors"
              >
                {ctaLabel} <ArrowRight size={16} />
              </Link>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
