import React from 'react';
import { motion } from 'framer-motion';
import { Check, Trophy, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';

const features = [
  "Documento legal personalizado",
  "Checklist de radicación paso a paso",
  "Cronograma legal con fechas límite",
  "Datos de contacto de la entidad",
  "Guía de seguimiento del caso",
  "Revisión por expertos humanos",
  "Entrega en menos de 24 horas hábiles",
  "Soporte vía correo"
];

const Pricing = () => {
  return (
    <section id="precio" className="py-24 px-6 bg-cream">
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-extrabold mb-4 text-brand">Precio único y transparente</h2>
          <p className="text-brand/60 text-lg">Todo lo que necesitas para actuar, sin letras chiquitas.</p>
        </div>
        
        <motion.div 
          initial={{ opacity: 0, scale: 0.95 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          className="bg-white rounded-[3rem] p-8 md:p-12 shadow-2xl border-4 border-brand relative overflow-hidden"
        >
          {/* Raffle Badge */}
          <div className="absolute top-8 right-[-50px] bg-accent text-brand font-bold py-2 px-16 rotate-45 shadow-lg flex items-center gap-2">
            <Trophy size={16} /> ¡INCLUYE RIFA!
          </div>
          
          <div className="grid md:grid-cols-2 gap-12 items-center">
            <div>
              <h3 className="text-3xl font-extrabold mb-2 text-brand">Kit completo de acción ciudadana</h3>
              <div className="flex items-baseline gap-2 mb-6">
                <span className="text-5xl font-extrabold text-brand">$59.900</span>
                <span className="text-brand/60 font-bold">COP</span>
              </div>
              
              <p className="text-brand/70 mb-8">
                Cada pago incluye un código para nuestra rifa mensual de un bono de <strong>$200.000 COP</strong>.
              </p>
              
              <Link to="/diagnostico" className="btn-primary w-full flex justify-center items-center gap-2 py-4 text-xl">
                Empezar ahora <ArrowRight />
              </Link>
              <p className="text-center mt-4 text-sm text-brand/50 font-medium">
                Pago seguro vía Wompi (PSE, Nequi, Tarjetas)
              </p>
            </div>
            
            <div className="bg-brand/5 p-8 rounded-3xl">
              <ul className="space-y-4">
                {features.map((item, i) => (
                  <li key={i} className="flex items-center gap-3 font-medium text-brand/80">
                    <div className="bg-success/10 p-1 rounded-full">
                      <Check size={18} className="text-success" />
                    </div>
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </motion.div>
        
        <div className="mt-12 text-center">
          <p className="text-brand/50 font-medium italic">
            "El diagnóstico inicial es gratis. Solo pagas si decides que redactemos tu documento."
          </p>
        </div>
      </div>
    </section>
  );
};

export default Pricing;
