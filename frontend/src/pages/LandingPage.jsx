import React from 'react';
import { Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { ArrowRight, CheckCircle2, FileText, Gavel, Heart, Scale } from 'lucide-react';
import {
  BUSINESS_ADDRESS,
  BUSINESS_OPERATOR,
  CONTACT_PHONE,
  LAUNCH_PRICE_LABEL,
  NOTIFICATIONS_EMAIL,
  RAFFLE_DRAW_DATE_LABEL,
  RAFFLE_LONG_COPY,
  RAFFLE_MONTH_LABEL,
  RAFFLE_PRIZE_LABEL,
} from '../lib/launchConfig';

const palette = {
  bg: '#F5F7FB',
  ink: '#12233D',
  muted: '#667892',
  primary: '#0D68FF',
  accent: '#19B7FF',
  success: '#36D399',
  warm: '#F97316',
  teal: '#0F766E',
  purple: '#7C3AED',
  border: '#D8E0F0',
  surface: '#FCFDFF',
  dark: '#08172E',
};

const categories = [
  {
    title: 'Derecho de peticion',
    desc: 'Para pedir autorizacion, respuesta, medicamento, cita o explicacion formal a la EPS o IPS.',
    icon: FileText,
    color: palette.primary,
  },
  {
    title: 'Tutela en salud',
    desc: 'Para proteger el derecho a la salud cuando hay urgencia, barrera seria o riesgo actual.',
    icon: Heart,
    color: palette.warm,
  },
  {
    title: 'Impugnacion',
    desc: 'Para controvertir un fallo de tutela cuando fue negado o limito la proteccion.',
    icon: Gavel,
    color: palette.teal,
  },
  {
    title: 'Desacato',
    desc: 'Para exigir cumplimiento cuando ya existe un fallo favorable y la entidad no obedece.',
    icon: Scale,
    color: palette.purple,
  },
];

const steps = [
  {
    index: '01',
    title: 'Describe tu problema',
    description: 'Nos cuentas que paso y subes soportes si los tienes.',
  },
  {
    index: '02',
    title: 'La IA analiza tu caso',
    description: 'Identifica el derecho vulnerado y te muestra la mejor ruta antes de pagar.',
  },
  {
    index: '03',
    title: 'Activas tu documento',
    description: 'Pagas una sola vez y dejas tu expediente listo para avanzar desde el panel.',
  },
];

const highlights = [
  `Precio unico de ${LAUNCH_PRICE_LABEL} por documento.`,
  'Ruta clara antes de pagar, sin adivinar el tramite.',
  `Participas por la posibilidad de llevarse ${RAFFLE_PRIZE_LABEL} en ${RAFFLE_MONTH_LABEL}.`,
];

const faq = [
  {
    q: '¿123tutela redacta automaticamente con IA?',
    a: 'No. La IA hace el diagnostico inicial y ordena la informacion. Cuando pagas, el documento lo elabora un equipo experto antes de la entrega final.',
  },
  {
    q: '¿Que pasa despues del pago?',
    a: 'Se habilita tu documento, se consolida el expediente y ves el siguiente paso desde el panel.',
  },
  {
    q: '¿Cuanto demora?',
    a: 'El diagnostico inicial es inmediato. Luego activas tu documento con un precio unico visible antes del pago.',
  },
  {
    q: '¿Como funciona la rifa de lanzamiento?',
    a: RAFFLE_LONG_COPY,
  },
];

const Badge = ({ children, color = palette.primary }) => (
  <span
    style={{
      display: 'inline-flex',
      alignItems: 'center',
      gap: 8,
      padding: '6px 12px',
      borderRadius: 999,
      fontSize: 12,
      fontWeight: 800,
      background: `${color}18`,
      color,
    }}
  >
    {children}
  </span>
);

const landingStyles = `
  @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700;800&family=Playfair+Display:wght@700;800&display=swap');
  .landing-vision {
    background: ${palette.bg};
    color: ${palette.ink};
    min-height: 100vh;
    font-family: 'DM Sans', sans-serif;
  }
  .landing-vision * { box-sizing: border-box; }
  .landing-wrap { width: min(1200px, calc(100vw - 48px)); margin: 0 auto; }
  .landing-nav__row {
    min-height: 84px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 18px;
    flex-wrap: wrap;
  }
  .landing-logo {
    display: flex;
    align-items: center;
    gap: 12px;
    color: inherit;
    text-decoration: none;
  }
  .landing-logo__mark {
    width: 40px;
    height: 40px;
    border-radius: 14px;
    background: linear-gradient(135deg, ${palette.primary} 0%, ${palette.accent} 100%);
    display: grid;
    place-items: center;
    color: #fff;
  }
  .landing-logo__text { font-size: 30px; font-weight: 800; }
  .landing-logo__text span { color: ${palette.primary}; }
  .landing-nav__links {
    display: flex;
    align-items: center;
    gap: 18px;
    flex-wrap: wrap;
    color: ${palette.muted};
    font-weight: 700;
  }
  .landing-nav__links a { color: inherit; text-decoration: none; }
  .landing-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    border-radius: 14px;
    padding: 14px 22px;
    font-size: 15px;
    font-weight: 800;
    text-decoration: none;
    transition: transform 0.18s ease, opacity 0.18s ease;
  }
  .landing-btn:hover { transform: translateY(-1px); opacity: 0.96; }
  .landing-btn--primary { background: ${palette.primary}; color: #fff; }
  .landing-btn--outline { border: 1px solid ${palette.border}; color: ${palette.primary}; background: transparent; }
  .landing-btn--ghost { border: 1px solid rgba(255,255,255,0.1); color: #fff; background: rgba(255,255,255,0.08); }
  .landing-hero { padding: 130px 0 44px; }
  .landing-hero__grid {
    display: grid;
    grid-template-columns: 1.05fr 0.95fr;
    gap: 28px;
    align-items: stretch;
  }
  .landing-card {
    border: 1px solid ${palette.border};
    border-radius: 26px;
    background: ${palette.surface};
    box-shadow: 0 18px 55px rgba(18, 35, 61, 0.06);
  }
  .landing-card--hero {
    padding: 38px 34px;
    background: radial-gradient(circle at top left, rgba(13,104,255,0.14), transparent 36%), ${palette.dark};
    color: #fff;
    border: 1px solid rgba(255,255,255,0.08);
  }
  .landing-card--hero h1,
  .landing-section h2,
  .landing-process h2,
  .landing-pricing h2 {
    font-family: 'Playfair Display', serif;
    letter-spacing: 0;
  }
  .landing-card--hero h1 {
    margin: 22px 0 0;
    font-size: 64px;
    line-height: 0.98;
    font-weight: 700;
  }
  .landing-card--hero p {
    margin-top: 22px;
    max-width: 560px;
    color: rgba(255,255,255,0.76);
    font-size: 18px;
    line-height: 1.7;
  }
  .landing-chip-row {
    display: flex;
    gap: 20px;
    flex-wrap: wrap;
    margin-top: 24px;
    color: rgba(255,255,255,0.78);
    font-weight: 700;
  }
  .landing-preview { padding: 28px; }
  .landing-preview__top,
  .landing-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 18px;
    flex-wrap: wrap;
  }
  .landing-kpi-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
  }
  .landing-kpi {
    padding: 16px;
    border-radius: 16px;
    background: #F8FAFD;
    border: 1px solid ${palette.border};
  }
  .landing-section { padding: 8px 0 56px; }
  .landing-section__head {
    display: flex;
    justify-content: space-between;
    align-items: end;
    gap: 16px;
    flex-wrap: wrap;
    margin-bottom: 24px;
  }
  .landing-section__head h2,
  .landing-pricing h2 {
    margin: 12px 0 0;
    font-size: 44px;
    line-height: 1.05;
  }
  .landing-grid-4 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }
  .landing-grid-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 18px; }
  .landing-grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 28px; }
  .landing-category { padding: 20px; }
  .landing-process { background: ${palette.dark}; color: #fff; padding: 72px 0; }
  .landing-process h2 { margin-top: 16px; font-size: 54px; }
  .landing-process__step {
    padding: 28px;
    border-radius: 24px;
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
  }
  .landing-pricing { padding: 68px 0 96px; }
  .landing-pricing__panel { padding: 34px 32px; }
  .landing-faq { padding: 0 0 80px; }
  .landing-faq__list { display: grid; gap: 12px; }
  .landing-faq details {
    background: #fff;
    border: 1px solid ${palette.border};
    border-radius: 18px;
    padding: 18px 20px;
  }
  .landing-faq summary { cursor: pointer; font-weight: 800; list-style: none; }
  .landing-footer {
    padding: 26px 0 36px;
    border-top: 1px solid ${palette.border};
    color: ${palette.muted};
  }
  @media (max-width: 980px) {
    .landing-hero__grid,
    .landing-grid-2,
    .landing-grid-3,
    .landing-grid-4,
    .landing-kpi-grid { grid-template-columns: 1fr; }
    .landing-card--hero h1,
    .landing-process h2 { font-size: 46px; }
    .landing-section__head h2,
    .landing-pricing h2 { font-size: 36px; }
    .landing-nav__links { width: 100%; justify-content: flex-start; }
  }
`;

const LandingPage = () => {
  return (
    <div className="landing-vision">
      <style>{landingStyles}</style>

      <Navbar />

      <section className="landing-hero">
        <div className="landing-wrap landing-hero__grid">
          <div className="landing-card landing-card--hero">
            <Badge color={palette.success}>IA juridica colombiana + oferta de mayo</Badge>
            <h1>
              Tu documento legal en salud,
              <br />
              por {LAUNCH_PRICE_LABEL}.
            </h1>
            <p>
              123tutela analiza tu caso, te muestra la ruta correcta y te deja activar tu documento por un precio unico.
            </p>
            <p>
              {RAFFLE_LONG_COPY}
            </p>
            <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap', marginTop: 28 }}>
              <Link to="/diagnostico" className="landing-btn landing-btn--primary">
                Quiero mi documento <ArrowRight size={18} />
              </Link>
              <Link to="/admin" className="landing-btn landing-btn--ghost">
                Ya tengo cuenta
              </Link>
            </div>
            <div className="landing-chip-row">
              <span>Solo salud</span>
              <span>Precio unico</span>
              <span>Rifa en vivo el {RAFFLE_DRAW_DATE_LABEL}</span>
            </div>
          </div>

          <div className="landing-card landing-preview">
            <div className="landing-preview__top">
              <span style={{ color: palette.muted, fontWeight: 700 }}>Caso analizado hace 2 min</span>
              <Badge color={palette.accent}>En vivo</Badge>
            </div>

            <div style={{ display: 'grid', gap: 16, marginTop: 18 }}>
              <div style={{ padding: 18, borderRadius: 18, background: '#F0FDF4', border: '1px solid #BBF7D0' }}>
                <div style={{ fontSize: 12, fontWeight: 800, color: '#15803D', marginBottom: 6 }}>DERECHO VULNERADO IDENTIFICADO</div>
                <div style={{ fontSize: 28, fontWeight: 800, color: palette.ink }}>Salud</div>
                <div style={{ color: palette.muted }}>Acceso a tratamiento y continuidad del servicio.</div>
              </div>

              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                <Badge color="#DC2626">EPS nego tratamiento</Badge>
                <Badge color={palette.primary}>Ley 1751/2015</Badge>
                <Badge color={palette.purple}>T-760/2008</Badge>
              </div>

              <div style={{ padding: 20, borderRadius: 18, background: '#0F2C5F', color: '#fff' }}>
                <div style={{ fontSize: 12, fontWeight: 800, color: '#93C5FD', marginBottom: 6 }}>ACCION RECOMENDADA</div>
                <div style={{ fontSize: 30, fontWeight: 800 }}>Accion de tutela</div>
                <div style={{ marginTop: 8, color: 'rgba(255,255,255,0.76)' }}>
                  Documento listo para activar por {LAUNCH_PRICE_LABEL} desde la app.
                </div>
              </div>

              <div className="landing-kpi-grid">
                {[
                  { label: 'Analisis', value: 'Gratis' },
                  { label: 'Precio', value: LAUNCH_PRICE_LABEL },
                  { label: 'Bono', value: '2.5M' },
                ].map((item) => (
                  <div key={item.label} className="landing-kpi">
                    <div style={{ fontSize: 12, color: palette.muted, fontWeight: 700 }}>{item.label}</div>
                    <div style={{ marginTop: 8, fontSize: 24, fontWeight: 800 }}>{item.value}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      <section id="documentos-salud" className="landing-section">
        <div className="landing-wrap">
          <div className="landing-section__head">
            <div>
              <Badge color={palette.primary}>Solo salud</Badge>
              <h2>
                Documentos de salud
                <br />
                listos para activar.
              </h2>
            </div>
            <p style={{ maxWidth: 420, color: palette.muted }}>
              Por ahora no abrimos otras materias. El catalogo activo se limita a peticion, tutela, impugnacion y desacato en salud.
            </p>
          </div>

          <div className="landing-grid-4">
            {categories.map((item) => {
              const Icon = item.icon;
              return (
                <div key={item.title} className="landing-card landing-category">
                  <div
                    style={{
                      width: 50,
                      height: 50,
                      borderRadius: 16,
                      background: `${item.color}18`,
                      display: 'grid',
                      placeItems: 'center',
                      marginBottom: 16,
                    }}
                  >
                    <Icon size={22} style={{ color: item.color }} />
                  </div>
                  <h3 style={{ fontSize: 18, fontWeight: 800, margin: 0 }}>{item.title}</h3>
                  <p style={{ marginTop: 8, color: palette.muted, fontSize: 14, lineHeight: 1.65 }}>{item.desc}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      <section id="como-funciona" className="landing-process">
        <div className="landing-wrap">
          <div style={{ textAlign: 'center', marginBottom: 34 }}>
            <Badge color={palette.success}>Como funciona</Badge>
            <h2>Tres pasos. CTA directo.</h2>
          </div>

          <div className="landing-grid-3">
            {steps.map((step) => (
              <div key={step.index} className="landing-process__step">
                <div style={{ fontSize: 52, color: '#1D4ED8', fontWeight: 800, fontFamily: "'Playfair Display', serif" }}>{step.index}</div>
                <h3 style={{ marginTop: 18, fontSize: 34, lineHeight: 1.1 }}>{step.title}</h3>
                <p style={{ marginTop: 14, color: 'rgba(255,255,255,0.7)', lineHeight: 1.7 }}>{step.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section id="precios" className="landing-pricing">
        <div className="landing-wrap">
          <div className="landing-card landing-pricing__panel landing-grid-2">
            <div>
              <Badge color={palette.primary}>Oferta</Badge>
              <h2>
                Un precio claro.
                <br />
                Un gancho fuerte.
              </h2>
              <p style={{ marginTop: 16, color: palette.muted, lineHeight: 1.7, maxWidth: 520 }}>
                La promesa comercial es simple: diagnostico inicial, ruta clara y documento activable por un solo precio. {RAFFLE_LONG_COPY}
              </p>
              <div style={{ display: 'grid', gap: 12, marginTop: 22 }}>
                {highlights.map((item) => (
                  <div key={item} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <CheckCircle2 size={18} style={{ color: palette.accent }} />
                    <span>{item}</span>
                  </div>
                ))}
              </div>
            </div>

            <div
              style={{
                borderRadius: 26,
                padding: 24,
                background: 'linear-gradient(180deg, #F8FBFF 0%, #EEF4FF 100%)',
                border: `1px solid ${palette.border}`,
              }}
            >
              <div style={{ fontSize: 14, color: palette.muted, fontWeight: 700 }}>Precio visible para los tramites de salud habilitados</div>
              <div style={{ marginTop: 12, fontSize: 52, fontWeight: 800 }}>{LAUNCH_PRICE_LABEL}</div>
              <div style={{ color: palette.muted }}>Mismo precio para peticion, tutela, impugnacion y desacato en salud.</div>
              <div style={{ marginTop: 20, paddingTop: 20, borderTop: `1px solid ${palette.border}` }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 0' }}>
                  <span>Analisis inicial del caso</span>
                  <strong>Gratis</strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 0' }}>
                  <span>Cualquier documento</span>
                  <strong>{LAUNCH_PRICE_LABEL}</strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 0' }}>
                  <span>Rifa {RAFFLE_MONTH_LABEL}</span>
                  <strong>{RAFFLE_PRIZE_LABEL}</strong>
                </div>
              </div>
              <div style={{ marginTop: 18, padding: 18, borderRadius: 18, background: '#0F2C5F', color: '#fff' }}>
                <div style={{ fontSize: 12, fontWeight: 800, color: '#93C5FD', marginBottom: 6 }}>ENTREGA ESPECIAL</div>
                <div style={{ fontSize: 22, fontWeight: 800 }}>En vivo el {RAFFLE_DRAW_DATE_LABEL}</div>
                <div style={{ marginTop: 8, color: 'rgba(255,255,255,0.76)', lineHeight: 1.6 }}>
                  {RAFFLE_LONG_COPY}
                </div>
              </div>
              <div style={{ marginTop: 24 }}>
                <Link to="/diagnostico" className="landing-btn landing-btn--primary" style={{ width: '100%' }}>
                  Activar mi documento ahora
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="landing-faq">
        <div className="landing-wrap" style={{ maxWidth: 860 }}>
          <div style={{ textAlign: 'center', marginBottom: 24 }}>
            <Badge color={palette.primary}>FAQ</Badge>
            <h2 style={{ marginTop: 12, fontSize: 40, fontFamily: "'Playfair Display', serif" }}>Preguntas frecuentes</h2>
          </div>
          <div className="landing-faq__list">
            {faq.map((item) => (
              <details key={item.q}>
                <summary>{item.q}</summary>
                <div style={{ marginTop: 12, color: palette.muted, lineHeight: 1.7 }}>{item.a}</div>
              </details>
            ))}
          </div>
        </div>
      </section>

      <footer>
        <div className="landing-wrap landing-footer">
          <div>
            <div>© 2026 123tutela Colombia. {BUSINESS_OPERATOR}.</div>
            <div style={{ marginTop: 6 }}>
              Correo de notificaciones: {NOTIFICATIONS_EMAIL} · Telefono: {CONTACT_PHONE}
            </div>
            <div style={{ marginTop: 4 }}>
              Direccion: {BUSINESS_ADDRESS}
            </div>
            <div style={{ marginTop: 4 }}>
              Cumplimos politica de privacidad, tratamiento de datos personales y canales de soporte verificables.
            </div>
          </div>
          <div style={{ display: 'flex', gap: 18, flexWrap: 'wrap' }}>
            <Link to="/terminos" style={{ color: 'inherit', textDecoration: 'none', fontWeight: 700 }}>Terminos</Link>
            <Link to="/privacidad" style={{ color: 'inherit', textDecoration: 'none', fontWeight: 700 }}>Privacidad</Link>
            <Link to="/contacto" style={{ color: 'inherit', textDecoration: 'none', fontWeight: 700 }}>Contacto</Link>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
