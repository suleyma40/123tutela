import React from 'react';
import { motion } from 'framer-motion';
import { ArrowRight, Check, ShieldCheck, Sparkles, Trophy } from 'lucide-react';
import { Link } from 'react-router-dom';

const features = [
  'Documento legal redactado para tu caso',
  'Checklist de radicacion paso a paso',
  'Ruta de anexos y soportes necesarios',
  'Cronograma legal y siguientes pasos',
  'Revision humana antes de entrega',
  'Codigo unico para seguimiento y rifa',
];

const Pricing = () => {
  return (
    <section id="precio" className="py-24 px-6 bg-[linear-gradient(180deg,#f7f5f0_0%,#fffaf1_100%)]">
      <div className="max-w-7xl mx-auto">
        <div className="max-w-3xl mb-14">
          <p className="text-accent uppercase tracking-[0.22em] text-xs font-black mb-4">Precio</p>
          <h2 className="text-4xl md:text-5xl font-extrabold text-brand leading-tight mb-4">
            Un precio claro para salir del bloqueo y actuar con un documento serio.
          </h2>
          <p className="text-brand/60 text-lg leading-relaxed">
            El diagnostico inicial es gratis. Solo pagas cuando decides que HazloPorMi y el equipo humano preparen tu kit de accion.
          </p>
        </div>

        <div className="grid lg:grid-cols-[1.05fr_0.95fr] gap-8 items-stretch">
          <motion.div
            initial={{ opacity: 0, y: 24 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="rounded-[2.8rem] bg-brand text-white p-8 md:p-10 shadow-[0_30px_80px_rgba(26,58,107,0.18)] relative overflow-hidden"
          >
            <div className="absolute top-0 right-0 w-72 h-72 bg-accent/16 rounded-full blur-3xl" />
            <div className="relative z-10">
              <div className="inline-flex items-center gap-2 rounded-full bg-white/10 border border-white/10 px-4 py-2 text-xs font-black uppercase tracking-[0.18em] mb-6">
                <Sparkles size={14} className="text-accent" />
                Precio unico
              </div>

              <h3 className="text-3xl md:text-4xl font-extrabold mb-3">Kit completo HazloPorMi</h3>
              <p className="text-white/70 text-lg max-w-lg mb-8">
                Para personas que necesitan pasar de la confusion a una accion concreta con diagnostico, redaccion humana y ruta operativa.
              </p>

              <div className="flex items-end gap-3 mb-8">
                <span className="text-6xl md:text-7xl font-extrabold leading-none">$59.900</span>
                <span className="text-white/60 font-black text-lg pb-2">COP</span>
              </div>

              <div className="rounded-[2rem] bg-white/8 border border-white/10 p-5 mb-8">
                <div className="flex items-start gap-4">
                  <div className="rounded-2xl bg-accent text-brand p-3 shrink-0">
                    <Trophy size={20} />
                  </div>
                  <div>
                    <p className="font-extrabold text-white mb-1">Incluye codigo de participacion y codigo de expediente</p>
                    <p className="text-white/70 text-sm leading-relaxed">
                      Cada pago aprobado recibe identificadores unicos, no secuenciales, para seguimiento operativo y para la promocion vigente.
                    </p>
                  </div>
                </div>
              </div>

              <div className="flex flex-col sm:flex-row gap-4">
                <Link to="/diagnostico" className="btn-primary flex justify-center items-center gap-2 px-8 py-4 text-lg">
                  Revisar mi caso gratis <ArrowRight size={18} />
                </Link>
                <div className="rounded-2xl bg-white/8 border border-white/10 px-5 py-4 text-sm font-bold text-white/80">
                  Pago seguro con Wompi: PSE, Nequi, tarjetas y transferencias habilitadas.
                </div>
              </div>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 24 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.06 }}
            className="rounded-[2.8rem] bg-white p-8 md:p-10 border border-brand/10 shadow-[0_24px_60px_rgba(26,58,107,0.08)]"
          >
            <div className="flex items-center gap-3 mb-6">
              <div className="rounded-2xl bg-success/10 p-3">
                <ShieldCheck size={20} className="text-success" />
              </div>
              <div>
                <p className="text-sm uppercase tracking-[0.18em] font-black text-brand/45">Que recibes</p>
                <p className="text-2xl font-extrabold text-brand">No es solo un documento</p>
              </div>
            </div>

            <ul className="space-y-4">
              {features.map((item) => (
                <li key={item} className="flex items-start gap-3 text-brand/80 font-medium">
                  <div className="mt-0.5 rounded-full bg-success/10 p-1.5 shrink-0">
                    <Check size={16} className="text-success" />
                  </div>
                  <span>{item}</span>
                </li>
              ))}
            </ul>

            <div className="mt-8 rounded-[2rem] border border-brand/10 bg-brand/5 p-5">
              <p className="text-sm font-black text-brand mb-2">Promocion de mayo 2026</p>
              <p className="text-sm text-brand/65 leading-relaxed">
                Los usuarios de la app con pago aprobado hasta el <strong>30 de mayo de 2026</strong> participan por un bono de <strong>2.5 millones de pesos</strong>. El bono se entrega el <strong>30 de mayo de 2026</strong>.
              </p>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
};

export default Pricing;
