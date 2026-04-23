import React from 'react';
import { motion } from 'framer-motion';
import { ShieldCheck, FileText, MapPin, Calendar, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';

const Hero = () => {
  return (
    <section className="pt-32 pb-20 px-6 overflow-hidden">
      <div className="max-w-7xl mx-auto grid lg:grid-cols-2 gap-12 items-center">
        <motion.div 
          initial={{ opacity: 0, x: -50 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.6 }}
        >
          <div className="inline-flex items-center gap-2 bg-accent/10 border border-accent/20 px-4 py-2 rounded-full text-accent font-bold text-sm mb-6 animate-pulse">
            <span className="w-2 h-2 bg-accent rounded-full"></span>
            Diagnóstico inicial + redacción humana + guía detallada
          </div>
          
          <h1 className="text-5xl md:text-6xl font-extrabold leading-tight mb-6 text-brand">
            ¿Tu EPS, tránsito o banco <span className="text-accent">no responde?</span>
          </h1>
          
          <p className="text-xl text-brand/70 mb-8 max-w-xl">
            Cuéntanos tu caso, te decimos qué camino tomar y, si pagas, un humano prepara tu documento y tu paso a paso completo en hasta 24 horas hábiles.
          </p>
          
          <div className="bg-brand/5 border border-brand/10 p-6 rounded-2xl mb-10">
            <h3 className="font-bold text-lg mb-4 flex items-center gap-2">
              <ShieldCheck className="text-success" /> Tu Kit incluye:
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm font-medium">
              <div className="flex items-center gap-2 text-brand">
                <FileText size={16} className="text-brand" /> Documento legal redactado
              </div>
              <div className="flex items-center gap-2 text-brand">
                <ShieldCheck size={16} className="text-brand" /> Checklist paso a paso
              </div>
              <div className="flex items-center gap-2 text-brand">
                <Calendar size={16} className="text-brand" /> Cronograma legal
              </div>
              <div className="flex items-center gap-2 text-brand">
                <MapPin size={16} className="text-brand" /> Guía de radicación
              </div>
            </div>
          </div>
          
          <div className="flex flex-col sm:flex-row gap-4">
            <Link to="/diagnostico" className="btn-primary text-center px-8 py-4 text-lg">
              Empezar diagnóstico gratis
            </Link>
            <a href="#precio" className="btn-secondary text-center px-8 py-4 text-lg bg-transparent border-2 border-brand text-brand hover:bg-brand hover:text-white">
              Ver precio único
            </a>
          </div>
        </motion.div>
        
        <motion.div 
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.8 }}
          className="relative"
        >
          <div className="absolute -z-10 top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[120%] h-[120%] bg-accent/10 rounded-full blur-3xl"></div>
          <div className="bg-white p-2 rounded-[2.5rem] shadow-2xl rotate-3">
            <img 
              src="https://images.unsplash.com/photo-1589829545856-d10d557cf95f?auto=format&fit=crop&q=80&w=800" 
              className="rounded-[2rem] object-cover h-[500px] w-full"
              alt="Justicia y Legalidad"
            />
            <div className="absolute -bottom-6 -left-6 glass p-6 rounded-2xl shadow-xl max-w-[200px] -rotate-3">
              <p className="font-headings font-bold text-brand leading-tight">"Recibí mi documento en menos de 12 horas. ¡Increíble!"</p>
              <div className="mt-2 text-xs font-bold text-accent">Juan P. · Bogotá</div>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
};

export default Hero;
