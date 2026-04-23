import React from 'react';
import { motion } from 'framer-motion';
import { MessageSquare, Cpu, CreditCard, PenTool, Mail } from 'lucide-react';

const steps = [
  {
    icon: <MessageSquare className="w-8 h-8" />,
    title: "Describes tu problema",
    desc: "Cuéntanos qué pasó en lenguaje normal. Es gratis y anónimo."
  },
  {
    icon: <Cpu className="w-8 h-8" />,
    title: "IA hace el diagnóstico",
    desc: "Nuestra IA legal identifica el documento exacto y las leyes que te protegen."
  },
  {
    icon: <CreditCard className="w-8 h-8" />,
    title: "Pagas precio único",
    desc: "Sin suscripciones ni costos ocultos. Un solo pago seguro vía Wompi."
  },
  {
    icon: <PenTool className="w-8 h-8" />,
    title: "Redactamos y revisamos",
    desc: "Nuestro equipo prepara tu kit completo con rigor jurídico."
  },
  {
    icon: <Mail className="w-8 h-8" />,
    title: "Recibes en tu correo",
    desc: "En máximo 24 horas hábiles tienes todo listo para radicar."
  }
];

const Process = () => {
  return (
    <section id="proceso" className="py-24 bg-brand text-white">
      <div className="max-w-7xl mx-auto px-6">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-extrabold mb-4">¿Cómo funciona?</h2>
          <p className="text-white/70 text-lg">Un proceso simple, rápido y 100% digital.</p>
        </div>
        
        <div className="relative">
          {/* Connector Line */}
          <div className="absolute left-8 md:left-1/2 top-0 bottom-0 w-0.5 bg-accent/30 -translate-x-1/2 hidden md:block"></div>
          
          <div className="space-y-12">
            {steps.map((step, index) => (
              <motion.div 
                key={index}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                className={`flex flex-col md:flex-row items-center gap-8 ${index % 2 !== 0 ? 'md:flex-row-reverse' : ''}`}
              >
                <div className="flex-1 md:text-right w-full">
                  {index % 2 === 0 && (
                    <div className="md:pr-12">
                      <h3 className="text-2xl font-bold mb-2 text-accent">{step.title}</h3>
                      <p className="text-white/60">{step.desc}</p>
                    </div>
                  )}
                </div>
                
                <div className="relative z-10 bg-accent text-brand p-4 rounded-full shadow-[0_0_20px_rgba(245,166,35,0.4)]">
                  {step.icon}
                </div>
                
                <div className="flex-1 w-full">
                  {index % 2 !== 0 && (
                    <div className="md:pl-12">
                      <h3 className="text-2xl font-bold mb-2 text-accent">{step.title}</h3>
                      <p className="text-white/60">{step.desc}</p>
                    </div>
                  )}
                  {index % 2 === 0 && <div className="hidden md:block"></div>}
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
};

export default Process;
