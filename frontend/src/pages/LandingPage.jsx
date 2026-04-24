import React from 'react';
import { ChevronDown, CheckCircle2, Scale, XCircle } from 'lucide-react';
import Navbar from '../components/Navbar';
import Hero from '../components/Hero';
import Process from '../components/Process';
import Pricing from '../components/Pricing';

const Entities = () => {
  const entities = [
    'EPS Sura', 'Sanitas', 'Compensar', 'Nueva EPS',
    'Bancolombia', 'Davivienda', 'Nu', 'Scotiabank',
    'Transito Bogota', 'Transito Medellin', 'DIAN', 'Colpensiones',
    'EPM', 'Alcaldias', 'Gobernaciones', 'Claro / Movistar',
  ];

  return (
    <section className="py-20 bg-white">
      <div className="max-w-7xl mx-auto px-6">
        <div className="text-center mb-12">
          <p className="text-accent uppercase tracking-[0.22em] text-xs font-black mb-4">Casos mixtos</p>
          <h2 className="text-3xl md:text-4xl font-extrabold mb-4 text-brand">
            Pensado para salud, bancos, transito y otros reclamos donde nadie te explica el siguiente paso
          </h2>
          <p className="text-brand/60 text-lg max-w-2xl mx-auto">
            HazloPorMi no te obliga a adivinar. Primero entiende tu caso, luego te dice que hacer y, si pagas, lo pasa a produccion humana.
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
      q: '¿HazloPorMi redacta automaticamente con IA?',
      a: 'No. La IA hace el diagnostico inicial y ayuda a ordenar la informacion. Cuando pagas, el caso pasa a produccion humana para que una persona prepare el documento final.',
    },
    {
      q: '¿Que pasa despues del pago?',
      a: 'Despues del pago te pedimos la informacion y los soportes necesarios. Con eso, el caso se consolida y se entrega al equipo humano para redaccion y seguimiento operativo.',
    },
    {
      q: '¿Cuanto demora el proceso?',
      a: 'El diagnostico inicial es inmediato. Despues del pago, el equipo humano entrega el kit en hasta 24 horas habiles desde que la informacion y los soportes esten completos.',
    },
    {
      q: '¿Que incluye el kit final?',
      a: 'Incluye el documento principal, el checklist de soportes, la ruta sugerida para presentarlo y los siguientes pasos para no perder trazabilidad.',
    },
    {
      q: '¿Como funciona el bono de mayo de 2026?',
      a: 'Cada pago aprobado en la app genera un codigo unico de participacion. Los usuarios con pago aprobado hasta el 30 de mayo de 2026 participan por un bono de 2.5 millones de pesos, que se entrega ese mismo 30 de mayo de 2026.',
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
        <h2 className="text-3xl md:text-4xl font-extrabold mb-4 text-brand">Asi se siente el flujo cuando ya no estas perdido</h2>
        <p className="text-brand/60 text-lg max-w-2xl mx-auto">
          No vendemos solo un archivo. Vendemos claridad, orden y una salida concreta para que una persona de produccion pueda ayudarte mejor.
        </p>
      </div>

      <div className="bg-white p-8 rounded-[3rem] shadow-2xl border border-brand/5 relative overflow-hidden max-w-3xl mx-auto">
        <div className="flex justify-between items-center mb-8 border-b border-brand/10 pb-6">
          <div>
            <h4 className="font-extrabold text-xl text-brand">Ruta del caso HazloPorMi</h4>
            <p className="text-xs font-bold text-brand/40 uppercase">Ejemplo de experiencia</p>
          </div>
          <div className="bg-success/10 text-success text-[10px] font-extrabold px-3 py-1 rounded-full uppercase">Listo para produccion</div>
        </div>

        <div className="space-y-6">
          <div className="flex gap-4">
            <div className="bg-brand text-white w-8 h-8 rounded-full flex items-center justify-center shrink-0 font-bold">1</div>
            <div>
              <p className="font-bold text-brand">Diagnostico inicial</p>
              <p className="text-sm text-brand/60">La app ordena tu situacion y te muestra la ruta recomendada antes del pago.</p>
            </div>
          </div>
          <div className="flex gap-4">
            <div className="bg-brand text-white w-8 h-8 rounded-full flex items-center justify-center shrink-0 font-bold">2</div>
            <div>
              <p className="font-bold text-brand">Cierre de datos y soportes</p>
              <p className="text-sm text-brand/60">Despues del pago te pedimos lo necesario para que el expediente quede claro y sin vacios.</p>
            </div>
          </div>
          <div className="flex gap-4">
            <div className="bg-brand text-white w-8 h-8 rounded-full flex items-center justify-center shrink-0 font-bold">3</div>
            <div>
              <p className="font-bold text-brand">Produccion humana</p>
              <p className="text-sm text-brand/60">Una persona redacta el documento final y deja trazabilidad para entrega y seguimiento.</p>
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
          <CheckCircle2 /> Lo que si hacemos
        </h3>
        <ul className="space-y-4 font-medium text-brand/80">
          <li>✓ Diagnostico inicial para ubicar el mejor camino.</li>
          <li>✓ Cierre de informacion y soportes despues del pago.</li>
          <li>✓ Redaccion humana del documento final.</li>
          <li>✓ Entrega comercial hasta en 24 horas habiles.</li>
          <li>✓ Seguimiento con codigo de expediente y referencia.</li>
        </ul>
      </div>
      <div className="bg-red-50 border border-red-100 p-8 rounded-[2rem]">
        <h3 className="text-2xl font-extrabold text-red-600 mb-6 flex items-center gap-2">
          <XCircle /> Lo que no hacemos
        </h3>
        <ul className="space-y-4 font-medium text-brand/80">
          <li>✕ No prometemos un resultado favorable.</li>
          <li>✕ No hacemos litigio presencial tradicional.</li>
          <li>✕ No reemplazamos la necesidad de soportes reales.</li>
          <li>✕ No entregamos el documento final solo con IA automatica.</li>
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
            <a href="#" className="hover:text-accent">Terminos</a>
            <a href="#" className="hover:text-accent">Privacidad</a>
            <a href="#" className="hover:text-accent">Contacto</a>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
