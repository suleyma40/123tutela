import React from 'react';
import { Scale, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';

const Navbar = () => {
  return (
    <nav className="fixed top-0 left-0 right-0 z-50 px-6 py-4">
      <div className="max-w-7xl mx-auto flex justify-between items-center rounded-full border border-white/70 bg-white/78 backdrop-blur-xl shadow-[0_10px_35px_rgba(26,58,107,0.12)] px-5 py-3">
        <Link to="/" className="flex items-center gap-2">
          <div className="bg-brand p-2 rounded-xl shadow-sm">
            <Scale className="text-accent w-6 h-6" />
          </div>
          <span className="font-headings text-xl font-extrabold text-brand tracking-tight">
            HazloPorMi
          </span>
        </Link>
        
        <div className="hidden md:flex items-center gap-8">
          <a href="#proceso" className="font-bold text-brand/70 hover:text-accent transition-colors">Como funciona</a>
          <a href="#precio" className="font-bold text-brand/70 hover:text-accent transition-colors">Precio</a>
          <a href="#faq" className="font-bold text-brand/70 hover:text-accent transition-colors">FAQ</a>
          <Link to="/diagnostico" className="btn-primary flex items-center gap-2 py-2.5 text-sm">
            Empezar gratis <ArrowRight size={16} />
          </Link>
          <Link to="/admin" className="text-brand/40 hover:text-brand transition-colors text-sm font-bold">Admin</Link>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
