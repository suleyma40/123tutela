import React from 'react';
import { motion } from 'framer-motion';
import { ArrowRight, BadgeCheck, Clock3, FileText, Gift, ShieldCheck, Sparkles, Trophy, UploadCloud } from 'lucide-react';
import { Link } from 'react-router-dom';

const proofPoints = [
  'Diagnostico inicial inmediato',
  'Produccion humana despues del pago',
  'Checklist y siguiente paso claro',
];

const deliverables = [
  {
    icon: FileText,
    title: 'Documento listo para usar',
    text: 'Tutela, derecho de peticion o reclamo, segun lo que realmente aplique.',
  },
  {
    icon: UploadCloud,
    title: 'Lista exacta de soportes',
    text: 'Te decimos que anexos subir y cuales te faltan.',
  },
  {
    icon: ShieldCheck,
    title: 'Ruta clara para actuar',
    text: 'Que enviar, que pedir y como no perder trazabilidad.',
  },
  {
    icon: Clock3,
    title: 'Entrega comercial rapida',
    text: 'Hasta 24 horas habiles desde pago e informacion completa.',
  },
];

const Hero = () => {
  return (
    <section className="pt-32 pb-20 px-6 overflow-hidden relative">
      <div className="absolute inset-0 -z-10 bg-[radial-gradient(circle_at_top_left,rgba(245,166,35,0.18),transparent_28%),radial-gradient(circle_at_80%_20%,rgba(26,58,107,0.12),transparent_30%),linear-gradient(180deg,#f7f5f0_0%,#f5efe1_100%)]" />

      <div className="max-w-7xl mx-auto grid lg:grid-cols-[1.08fr_0.92fr] gap-14 items-center">
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <div className="inline-flex items-center gap-2 bg-white/90 border border-brand/10 px-4 py-2 rounded-full text-sm font-bold text-brand shadow-sm mb-7">
            <Sparkles size={16} className="text-accent" />
            Agente inicial + produccion humana + guia accionable
          </div>

          <div className="space-y-6">
            <h1 className="text-5xl md:text-6xl lg:text-7xl font-extrabold leading-[0.96] tracking-tight text-brand max-w-4xl">
              Si una <span className="text-accent">EPS, banco o entidad</span> te tiene dando vueltas, HazloPorMi te ayuda a entender el caso y a moverlo sin improvisar.
            </h1>

            <p className="text-xl md:text-2xl text-brand/72 max-w-2xl font-medium leading-relaxed">
              Empiezas con un diagnostico gratis. Si decides avanzar, te pedimos lo necesario y una persona de produccion prepara tu documento final y tu ruta paso a paso.
            </p>
          </div>

          <div className="flex flex-wrap gap-3 mt-8">
            {proofPoints.map((item) => (
              <div key={item} className="inline-flex items-center gap-2 rounded-full border border-brand/10 bg-white/85 px-4 py-2 text-sm font-bold text-brand shadow-sm">
                <BadgeCheck size={16} className="text-success" />
                {item}
              </div>
            ))}
          </div>

          <div className="flex flex-col sm:flex-row gap-4 mt-10">
            <Link to="/diagnostico" className="btn-primary text-center px-8 py-4 text-lg flex items-center justify-center gap-2">
              Quiero revisar mi caso <ArrowRight size={18} />
            </Link>
            <a href="#precio" className="btn-secondary text-center px-8 py-4 text-lg bg-white text-brand border border-brand/10 shadow-sm hover:bg-brand hover:text-white">
              Ver como funciona
            </a>
          </div>

          <div className="mt-6 flex flex-wrap items-center gap-x-6 gap-y-2 text-sm font-bold text-brand/60">
            <span>Sin abogado presencial</span>
            <span>Solo pagas si decides avanzar</span>
            <span>Pago seguro por Wompi</span>
          </div>

          <div className="mt-8 rounded-[2rem] border border-accent/25 bg-white/85 p-5 shadow-[0_16px_36px_rgba(26,58,107,0.08)]">
            <div className="flex items-start gap-4">
              <div className="rounded-2xl bg-accent text-brand p-3 shrink-0">
                <Gift size={22} />
              </div>
              <div>
                <p className="text-xs uppercase tracking-[0.18em] font-black text-brand/45 mb-2">Promocion vigente</p>
                <p className="text-brand font-extrabold text-lg leading-tight mb-2">
                  Los usuarios de la app participan por un bono de 2.5 millones de pesos.
                </p>
                <p className="text-sm text-brand/68 leading-relaxed">
                  La campaña aplica para pagos aprobados hechos hasta el <strong>30 de mayo de 2026</strong>. El bono se entrega ese mismo <strong>30 de mayo de 2026</strong>.
                </p>
              </div>
            </div>
          </div>

          <div className="grid sm:grid-cols-2 gap-4 mt-12">
            {deliverables.map((item) => {
              const Icon = item.icon;
              return (
                <div key={item.title} className="rounded-[1.75rem] border border-brand/10 bg-white/92 p-5 shadow-[0_18px_45px_rgba(26,58,107,0.08)]">
                  <div className="flex items-start gap-4">
                    <div className="rounded-2xl bg-brand text-white p-3 shrink-0">
                      <Icon size={20} />
                    </div>
                    <div>
                      <p className="text-lg font-extrabold text-brand">{item.title}</p>
                      <p className="text-sm text-brand/65 mt-1 leading-relaxed">{item.text}</p>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 30, scale: 0.97 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          transition={{ duration: 0.7 }}
          className="relative"
        >
          <div className="absolute -top-8 right-10 h-36 w-36 rounded-full bg-accent/25 blur-3xl" />
          <div className="absolute bottom-8 -left-4 h-32 w-32 rounded-full bg-brand/15 blur-3xl" />

          <div className="relative rounded-[2.75rem] bg-white p-3 shadow-[0_30px_80px_rgba(26,58,107,0.16)] border border-brand/10">
            <img
              src="https://images.unsplash.com/photo-1589829545856-d10d557cf95f?auto=format&fit=crop&q=80&w=1200"
              className="rounded-[2.1rem] object-cover h-[560px] w-full"
              alt="Escultura de justicia"
            />

            <div className="absolute left-6 top-6 right-6 flex justify-between gap-4">
              <div className="rounded-[1.5rem] bg-white/92 backdrop-blur px-4 py-3 shadow-lg border border-white/70 max-w-[240px]">
                <p className="text-[11px] uppercase tracking-[0.18em] font-black text-brand/45 mb-1">Promesa comercial</p>
                <p className="text-brand font-extrabold leading-tight">Diagnostico gratis. Documento final hecho por una persona si decides pagar.</p>
              </div>
              <div className="rounded-[1.5rem] bg-brand text-white px-4 py-3 shadow-lg max-w-[210px] hidden sm:block">
                <p className="text-[11px] uppercase tracking-[0.18em] font-black text-white/55 mb-1">Entrega</p>
                <p className="font-extrabold leading-tight">Hasta 24 horas habiles desde expediente completo.</p>
              </div>
            </div>

            <div className="absolute -bottom-7 left-6 right-6 grid sm:grid-cols-2 gap-4">
              <div className="rounded-[1.75rem] bg-white px-5 py-4 shadow-xl border border-brand/10">
                <div className="flex items-center gap-3 mb-2">
                  <div className="rounded-xl bg-success/10 p-2">
                    <ShieldCheck size={18} className="text-success" />
                  </div>
                  <p className="font-extrabold text-brand">No te dejamos adivinar</p>
                </div>
                <p className="text-sm text-brand/65 leading-relaxed">
                  Te mostramos la ruta recomendada, lo que falta y los siguientes pasos antes de pagar.
                </p>
              </div>

              <div className="rounded-[1.75rem] bg-accent text-brand px-5 py-4 shadow-xl">
                <div className="flex items-center gap-3 mb-2">
                  <div className="rounded-xl bg-white/55 p-2">
                    <Trophy size={18} />
                  </div>
                  <p className="font-extrabold">Cada pago aprobado participa en el bono</p>
                </div>
                <p className="text-sm font-medium leading-relaxed text-brand/85">
                  Recibes codigo unico de expediente y codigo unico de participacion. Nada de consecutivos publicos.
                </p>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
};

export default Hero;
