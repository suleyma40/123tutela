import React from 'react';
import { ChevronDown, Building2, CheckCircle2, Scale, XCircle } from 'lucide-react';
import Navbar from '../components/Navbar';
import Hero from '../components/Hero';
import Process from '../components/Process';
import Pricing from '../components/Pricing';

const Entities = () => {
  const entities = [
    'EPS Sura', 'Sanitas', 'Compensar', 'Nueva EPS',
    'Bancolombia', 'Davivienda', 'Nu', 'Scotiabank',
    'Transito Medellin', 'Transito Bogota', 'DIAN', 'Colpensiones',
    'EPM', 'Alcaldias', 'Gobernaciones', 'Claro / Movistar',
  ];

  return (
    <section className="py-20 bg-white">
      <div className="max-w-7xl mx-auto px-6">
        <div className="text-center mb-12">
          <p className="text-accent uppercase tracking-[0.22em] text-xs font-black mb-4">Casos mixtos</p>
          <h2 className="text-3xl md:text-4xl font-extrabold mb-4 text-brand">
            Ya ayudamos a ordenar reclamos frente a estas entidades y categorías
          </h2>
          <p className="text-brand/60 text-lg max-w-2xl mx-auto">
            Salud, bancos, tránsito y otros bloqueos administrativos donde lo más difícil suele ser saber por dónde empezar.
          </p>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {entities.map((item) => (
            <div
              key={item}
              className="p-4 border border-brand/10 rounded-2xl text-center font-bold text-brand/70 bg-brand/5 hover:bg-brand hover:text-white transition-colors cursor-default"
            >
              {item}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

const FAQ = () => {
  const questions = [
    {
      q: '¿Radican el documento por mí?',
      a: 'No. Te entregamos el kit completo para que tú radiques con más claridad y control. Incluye documento, checklist, anexos sugeridos y la ruta para presentarlo.',
    },
    {
      q: '¿Garantizan el resultado?',
      a: 'No garantizamos una decisión favorable. Lo que sí hacemos es ayudarte a actuar mejor: con un diagnóstico inicial, una redacción humana y una ruta mucho más clara que hacerlo solo.',
    },
    {
      q: '¿Cuánto demora el proceso?',
      a: 'El diagnóstico inicial es inmediato. Después del pago, el equipo humano entrega el kit en hasta 24 horas hábiles desde que la información y los soportes estén completos.',
    },
    {
      q: '¿Qué documentos incluye el kit?',
      a: 'Depende del caso, pero normalmente incluye el documento principal, checklist de radicación, cronograma, guía de soportes y siguientes pasos para seguimiento.',
    },
    {
      q: '¿Cómo funciona el bono de mayo de 2026?',
      a: 'Cada pago aprobado en la app genera un código único de participación. Los usuarios con pago aprobado hasta el 30 de mayo de 2026 participan por un bono de 2.5 millones de pesos, que se entrega el mismo 30 de mayo de 2026.',
    },
  ];

  return (
    <section id="faq" className="py-24 bg-cream">
      <div className="max-w-3xl mx-auto px-6">
        <h2 className="text-4xl font-extrabold text-center mb-12 text-brand">Preguntas frecuentes</h2>
        <div className="space-y-4">
          {questions.map((item) => (
            <details key={item.q} className="group bg-white rounded-2xl shadow-sm border border-brand/5 overflow-hidden">
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
    <div className="max-w-5xl mx-auto px-6">
      <div className="text-center mb-12">
        <p className="text-accent uppercase tracking-[0.22em] text-xs font-black mb-4">Entrega</p>
        <h2 className="text-3xl md:text-4xl font-extrabold mb-4 text-brand">Así se ve el kit que recibe el cliente</h2>
        <p className="text-brand/60 text-lg max-w-2xl mx-auto">
          Todo está pensado para que no tengas que traducir lenguaje legal ni adivinar qué sigue.
        </p>
      </div>

      <div className="bg-white p-8 rounded-[3rem] shadow-2xl border border-brand/5 relative overflow-hidden max-w-3xl mx-auto">
        <div className="flex justify-between items-center mb-8 border-b border-brand/10 pb-6">
          <div>
            <h4 className="font-extrabold text-xl text-brand">Checklist de radicación</h4>
            <p className="text-xs font-bold text-brand/40 uppercase">Ejemplo de entrega HazloPorMi</p>
          </div>
          <div className="bg-success/10 text-success text-[10px] font-extrabold px-3 py-1 rounded-full uppercase">Listo para usar</div>
        </div>

        <div className="space-y-6">
          <div className="flex gap-4">
            <div className="bg-brand text-white w-8 h-8 rounded-full flex items-center justify-center shrink-0 font-bold">1</div>
            <div>
              <p className="font-bold text-brand">Revisa y firma tu documento</p>
              <p className="text-sm text-brand/60">Te explicamos qué validar antes de enviarlo y cómo conservar una copia correcta.</p>
            </div>
          </div>
          <div className="flex gap-4">
            <div className="bg-brand text-white w-8 h-8 rounded-full flex items-center justify-center shrink-0 font-bold">2</div>
            <div>
              <p className="font-bold text-brand">Radica por el canal sugerido</p>
              <p className="text-sm text-brand/60">Te indicamos por dónde enviarlo y qué soporte guardar para demostrar que sí presentaste el caso.</p>
            </div>
          </div>
          <div className="flex gap-4">
            <div className="bg-brand text-white w-8 h-8 rounded-full flex items-center justify-center shrink-0 font-bold">3</div>
            <div>
              <p className="font-bold text-brand">Haz seguimiento con fechas claras</p>
              <p className="text-sm text-brand/60">Incluimos el siguiente paso recomendado si no responden o si la respuesta no resuelve el problema.</p>
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
          <CheckCircle2 /> Lo que sí hacemos
        </h3>
        <ul className="space-y-4 font-medium text-brand/80">
          <li>✓ Diagnóstico inicial para ubicar el mejor camino.</li>
          <li>✓ Redacción humana del documento final.</li>
          <li>✓ Checklist y guía para radicar con más orden.</li>
          <li>✓ Entrega comercial hasta en 24 horas hábiles.</li>
          <li>✓ Seguimiento usando código de expediente y referencia.</li>
        </ul>
      </div>
      <div className="bg-red-50 border border-red-100 p-8 rounded-[2rem]">
        <h3 className="text-2xl font-extrabold text-red-600 mb-6 flex items-center gap-2">
          <XCircle /> Lo que no hacemos
        </h3>
        <ul className="space-y-4 font-medium text-brand/80">
          <li>✕ No prometemos un resultado favorable.</li>
          <li>✕ No somos litigio tradicional con representación presencial.</li>
          <li>✕ No radicamos por ti ante la entidad.</li>
          <li>✕ No reemplazamos la necesidad de soportes reales del caso.</li>
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
