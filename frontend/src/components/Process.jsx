import React from 'react';
import { motion } from 'framer-motion';
import { CreditCard, Cpu, Mail, MessageSquare, PenTool } from 'lucide-react';

const steps = [
  {
    number: '01',
    icon: MessageSquare,
    title: 'Nos cuentas lo que paso',
    desc: 'Hablas en lenguaje normal. No necesitas saber de leyes ni escoger un documento por tu cuenta.',
  },
  {
    number: '02',
    icon: Cpu,
    title: 'La IA ordena el caso',
    desc: 'Detectamos la ruta mas probable, el tipo de escrito y lo que falta para dejar el expediente claro.',
  },
  {
    number: '03',
    icon: CreditCard,
    title: 'Pagas solo si te sirve',
    desc: 'Precio unico. Sin planes, sin sorpresas y con codigo propio para seguimiento y rifa.',
  },
  {
    number: '04',
    icon: PenTool,
    title: 'Produccion humana redacta',
    desc: 'Un humano revisa tu informacion, aterriza la narrativa y prepara el documento con criterio real.',
  },
  {
    number: '05',
    icon: Mail,
    title: 'Recibes kit y ruta de accion',
    desc: 'Te entregamos documento, checklist, anexos y forma de radicar para que actues con orden.',
  },
];

const Process = () => {
  return (
    <section id="proceso" className="py-24 px-6 bg-brand text-white overflow-hidden">
      <div className="max-w-7xl mx-auto grid lg:grid-cols-[0.85fr_1.15fr] gap-12 items-start">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="lg:sticky lg:top-28"
        >
          <p className="text-accent uppercase tracking-[0.22em] text-xs font-black mb-4">Como funciona</p>
          <h2 className="text-4xl md:text-5xl font-extrabold leading-tight mb-5">
            Un flujo corto para que tomes accion sin pelearte con el proceso.
          </h2>
          <p className="text-white/68 text-lg leading-relaxed max-w-xl">
            No te soltamos un PDF y ya. Primero diagnosticamos, luego cerramos la informacion correcta y despues entregamos un kit listo para mover el caso.
          </p>

          <div className="mt-8 rounded-[2rem] border border-white/12 bg-white/8 backdrop-blur-sm p-6">
            <p className="text-sm font-black uppercase tracking-wide text-white/55 mb-3">Promesa operativa</p>
            <div className="space-y-3 text-sm text-white/80 font-medium">
              <p>Diagnostico inicial gratis antes del pago.</p>
              <p>Codigo unico de expediente para seguimiento interno.</p>
              <p>Entrega comercial en hasta 24 horas habiles desde expediente completo.</p>
            </div>
          </div>
        </motion.div>

        <div className="grid gap-4">
          {steps.map((step, index) => {
            const Icon = step.icon;
            return (
              <motion.div
                key={step.number}
                initial={{ opacity: 0, x: 24 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.45, delay: index * 0.04 }}
                className="group grid md:grid-cols-[92px_1fr] gap-5 rounded-[2rem] border border-white/10 bg-white/6 hover:bg-white/10 transition-colors p-5 md:p-6"
              >
                <div className="flex md:flex-col md:items-start items-center gap-4">
                  <div className="h-14 w-14 rounded-2xl bg-accent text-brand flex items-center justify-center shadow-[0_12px_30px_rgba(245,166,35,0.22)]">
                    <Icon size={24} />
                  </div>
                  <span className="text-white/45 text-xs font-black tracking-[0.24em]">{step.number}</span>
                </div>

                <div className="pt-1">
                  <h3 className="text-2xl font-extrabold text-white mb-2">{step.title}</h3>
                  <p className="text-white/68 leading-relaxed max-w-2xl">{step.desc}</p>
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
};

export default Process;
