import React from 'react';
import { Scale, ArrowRight } from 'lucide-react';
import { Link, useLocation } from 'react-router-dom';

const Navbar = () => {
  const location = useLocation();
  const isAdmin = location.pathname.startsWith('/admin');
  const isLanding = location.pathname === '/';

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
                <a href="#categorias" className="text-inherit no-underline hover:text-slate-900 transition-colors">Categorias</a>
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
            <Link to="/admin" className="rounded-xl border border-slate-200 px-4 py-2 text-[#0D68FF] no-underline hover:bg-slate-50 transition-colors">
              Admin
            </Link>
            {!isAdmin && (
              <Link
                to="/diagnostico"
                className="inline-flex items-center gap-2 rounded-xl bg-[#0D68FF] px-4 py-2 text-white no-underline hover:bg-[#0D68FF]/90 transition-colors"
              >
                Quiero mi documento <ArrowRight size={16} />
              </Link>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
