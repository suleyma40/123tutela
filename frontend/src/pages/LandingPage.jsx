import React from 'react';
import Navbar from '../components/Navbar';
import Hero from '../components/Hero';
import Process from '../components/Process';
import Pricing from '../components/Pricing';
import { motion } from 'framer-motion';
import { Scale, CheckCircle2, XCircle, Building2, ChevronDown } from 'lucide-react';

const Entities = () => {
  const entities = [
    "EPS Sura", "Sanitas", "Compensar", "Nueva EPS", 
    "Bancolombia", "Davivienda", "Nubank", "Scotiabank",
    "Tránsito Medellín", "Tránsito Bogotá", "DIAN", "Colpensiones",
    "EPM", "Alcaldías", "Gobernaciones", "Movistar/Claro"
  ];

  return (
    <section className="py-20 bg-white">
      <div className="max-w-7xl mx-auto px-6">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-extrabold mb-4 flex items-center justify-center gap-3 text-brand">
            <Building2 className="text-accent" /> Resolvemos problemas con:
          </h2>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {entities.map((e, i) => (
            <div key={i} className="p-4 border border-brand/10 rounded-xl text-center font-bold text-brand/60 hover:bg-brand hover:text-white transition-colors cursor-default">
              {e}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

const FAQ = () => {
  const questions = [
    { q: "¿Radican el documento por mí?", a: "No. Nosotros te entregamos el kit completo (documento legal, checklist y guía) para que tú lo radiques fácilmente por correo electrónico o de forma física. Esto garantiza que tú mantienes el control de tu caso." },
    { q: "¿Garantizan el resultado?", a: "Prometemos entregarte la herramienta legal correcta y redactada profesionalmente en menos de 24h hábiles. El resultado final depende de la entidad y la ley, pero con nuestro documento tus posibilidades aumentan drásticamente." },
    { q: "¿Cuánto demora el proceso?", a: "El diagnóstico es inmediato. Una vez realizas el pago, nuestro equipo redacta y envía tu kit en un máximo de 24 horas hábiles." },
    { q: "¿Qué documentos incluye el kit?", a: "Incluye el documento legal principal (Derecho de Petición, Tutela, etc.), un checklist paso a paso de radicación, un cronograma con fechas límite de respuesta y datos de contacto de la entidad." },
    { q: "¿Cómo funciona la rifa?", a: "Por cada pago realizado, el sistema genera un código único (HPM-XXXXXX). Al final de cada mes realizamos un sorteo aleatorio entre todos los códigos y el ganador recibe un bono de $200.000 COP." }
  ];

  return (
    <section id="faq" className="py-24 bg-cream">
      <div className="max-w-3xl mx-auto px-6">
        <h2 className="text-4xl font-extrabold text-center mb-12 text-brand">Preguntas frecuentes</h2>
        <div className="space-y-4">
          {questions.map((item, i) => (
            <details key={i} className="group bg-white rounded-2xl shadow-sm border border-brand/5 overflow-hidden">
              <summary className="list-none p-6 font-bold text-lg flex justify-between items-center cursor-pointer hover:bg-brand/5 transition-colors text-brand">
                {item.q}
                <ChevronDown className="group-open:rotate-180 transition-transform text-accent" />
              </summary>
              <div className="px-6 pb-6 text-brand/70 leading-relaxed">
                {item.a}
              </div>
            </details>
          ))}
        </div>
      </div>
    </section>
  );
};

const ChecklistPreview = () => (
  <section className="py-24 bg-brand/5">
    <div className="max-w-4xl mx-auto px-6">
      <div className="text-center mb-12">
        <h2 className="text-3xl font-extrabold mb-4 text-brand">Así recibirás tu Checklist</h2>
        <p className="text-brand/60">Una guía paso a paso diseñada específicamente para tu caso.</p>
      </div>
      
      <div className="bg-white p-8 rounded-[3rem] shadow-2xl border border-brand/5 relative overflow-hidden max-w-2xl mx-auto">
        <div className="flex justify-between items-center mb-8 border-b pb-6">
          <div>
            <h4 className="font-extrabold text-xl text-brand">Checklist de Radicación</h4>
            <p className="text-xs font-bold text-brand/40 uppercase">Caso: Derecho de Petición - EPS Sura</p>
          </div>
          <div className="bg-success/10 text-success text-[10px] font-extrabold px-3 py-1 rounded-full uppercase">Listo para radicar</div>
        </div>

        <div className="space-y-6">
          <div className="flex gap-4">
            <div className="bg-brand text-white w-8 h-8 rounded-full flex items-center justify-center shrink-0 font-bold">1</div>
            <div>
              <p className="font-bold text-brand">Firma y escanea el documento</p>
              <p className="text-sm text-brand/60">Imprime el PDF adjunto, fírmalo con bolígrafo negro y escanéalo en formato PDF.</p>
            </div>
          </div>
          <div className="flex gap-4">
            <div className="bg-brand text-white w-8 h-8 rounded-full flex items-center justify-center shrink-0 font-bold">2</div>
            <div>
              <p className="font-bold text-brand">Envía correo a la entidad</p>
              <p className="text-sm text-brand/60">Envía el archivo a: <span className="text-brand font-bold">notificaciones@epssura.com</span></p>
              <p className="text-[10px] mt-1 font-bold text-accent uppercase">📍 Sede Principal: Calle 50 # 45-23, Medellín</p>
            </div>
          </div>
          <div className="flex gap-4 opacity-50">
            <div className="bg-brand text-white w-8 h-8 rounded-full flex items-center justify-center shrink-0 font-bold">3</div>
            <div>
              <p className="font-bold text-brand">Espera respuesta legal</p>
              <p className="text-sm text-brand/60">Fecha límite calculada: <span className="font-bold">15 de mayo, 2026</span></p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
);

const Honesty = () => (
  <section className="py-20 px-6">
    <div className="max-w-5xl mx-auto grid md:grid-cols-2 gap-8">
      <div className="bg-success/5 border border-success/20 p-8 rounded-[2rem]">
        <h3 className="text-2xl font-extrabold text-success mb-6 flex items-center gap-2">
          <CheckCircle2 /> Lo que SÍ hacemos
        </h3>
        <ul className="space-y-4 font-medium text-brand/80">
          <li>✓ Diagnóstico legal con IA experta.</li>
          <li>✓ Redacción profesional de documentos legales.</li>
          <li>✓ Guía paso a paso para que radiques tú mismo.</li>
          <li>✓ Entrega garantizada en menos de 24 horas hábiles.</li>
          <li>✓ Soporte si tienes dudas sobre el kit.</li>
        </ul>
      </div>
      <div className="bg-red-50 border border-red-100 p-8 rounded-[2rem]">
        <h3 className="text-2xl font-extrabold text-red-600 mb-6 flex items-center gap-2">
          <XCircle /> Lo que NO hacemos
        </h3>
        <ul className="space-y-4 font-medium text-brand/80">
          <li>✗ No garantizamos que la entidad falle a tu favor.</li>
          <li>✗ No somos una oficina de abogados con representación física.</li>
          <li>✗ No radicamos los documentos por ti.</li>
          <li>✗ No hacemos seguimiento telefónico a las entidades.</li>
        </ul>
      </div>
    </div>
  </section>
);

const LandingPage = () => {
  return (
    <div className="min-h-screen">
      <Navbar />
      <Hero />
      <Entities />
      <Process />
      <ChecklistPreview />
      <Honesty />
      <Pricing />
      <FAQ />
      <footer className="bg-brand text-white py-12 px-6">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-8">
          <div className="flex items-center gap-2">
            <div className="bg-white p-2 rounded-lg">
              <Scale className="text-brand w-6 h-6" />
            </div>
            <span className="font-headings text-xl font-extrabold tracking-tight">
              HazloPorMi
            </span>
          </div>
          <div className="text-white/50 text-sm font-medium">
            © 2026 HazloPorMi. Todos los derechos reservados. Colombia.
          </div>
          <div className="flex gap-6 font-bold text-sm">
            <a href="#" className="hover:text-accent">Términos</a>
            <a href="#" className="hover:text-accent">Privacidad</a>
            <a href="#" className="hover:text-accent">Contacto</a>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
