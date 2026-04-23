import React from 'react';
import { Scale, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';

const Navbar = () => {
  return (
    <nav className="fixed top-0 left-0 right-0 z-50 glass px-6 py-4">
      <div className="max-w-7xl mx-auto flex justify-between items-center">
        <Link to="/" className="flex items-center gap-2">
          <div className="bg-brand p-2 rounded-lg">
            <Scale className="text-accent w-6 h-6" />
          </div>
          <span className="font-headings text-xl font-extrabold text-brand tracking-tight">
            HazloPorMi
          </span>
        </Link>
        
        <div className="hidden md:flex items-center gap-8">
          <a href="#proceso" className="font-medium hover:text-accent transition-colors">Proceso</a>
          <a href="#precio" className="font-medium hover:text-accent transition-colors">Precio</a>
          <Link to="/diagnostico" className="btn-primary flex items-center gap-2 py-2 text-sm">
            Obtener mi documento <ArrowRight size={16} />
          </Link>
          <Link to="/admin" className="text-brand/40 hover:text-brand transition-colors text-sm font-bold">Admin</Link>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
