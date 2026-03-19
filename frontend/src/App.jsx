import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  Scale, Heart, Shield, Landmark, ShoppingCart, Info, 
  ArrowRight, CheckCircle2, AlertCircle, FileText, Send, Zap, 
  Plus, Layout, Files, HelpCircle, LogOut, MessageSquare, 
  Search, Upload, ChevronRight, Users, Briefcase, Building2, Lock, Stethoscope
} from 'lucide-react';
import axios from 'axios';

// ─── Color palette & design tokens (Visión Completa) ───
const C = {
  bg: "#F7F8FA",
  bgDark: "#0B1628",
  card: "#FFFFFF",
  cardDark: "#111D32",
  primary: "#0066FF",
  primaryLight: "#E8F0FE",
  accent: "#00C48C",
  accentWarm: "#FF6B35",
  text: "#1A2138",
  textMuted: "#6B7A99",
  textLight: "#FFFFFF",
  border: "#E2E8F0",
  borderDark: "#1E3050",
  danger: "#EF4444",
  warning: "#F59E0B",
  success: "#10B981",
};

const N8N_WEBHOOK_URL = "https://n8ntutela.123tutelaapp.com/webhook/webhook-casos";
const ANALYZE_API_BASE =
  import.meta.env.VITE_API_URL ||
  (import.meta.env.PROD ? "https://api.123tutelaapp.com" : "http://localhost:8000");

// ─── Shared Components ───
const Badge = ({ children, color = C.primary }) => (
  <span style={{
    display: "inline-block", padding: "3px 10px", borderRadius: 20,
    fontSize: 11, fontWeight: 600, letterSpacing: 0.5,
    background: color + "18", color,
  }}>{children}</span>
);

const Button = ({ children, variant = "primary", size = "md", onClick, style = {}, icon: Icon }) => {
  const base = {
    display: "inline-flex", alignItems: "center", justifyContent: "center", gap: 8,
    border: "none", cursor: "pointer", fontWeight: 600,
    fontFamily: "'DM Sans', sans-serif", transition: "all 0.2s ease",
    borderRadius: size === "lg" ? 14 : 10,
    padding: size === "lg" ? "16px 32px" : size === "sm" ? "8px 16px" : "12px 24px",
    fontSize: size === "lg" ? 16 : size === "sm" ? 13 : 14,
  };
  const variants = {
    primary: { background: C.primary, color: "#fff" },
    secondary: { background: C.primaryLight, color: C.primary },
    outline: { background: "transparent", color: C.primary, border: `1.5px solid ${C.border}` },
    dark: { background: C.bgDark, color: "#fff" },
    ghost: { background: "transparent", color: C.textMuted, padding: "8px 12px" },
    accent: { background: C.accent, color: "#fff" },
    danger: { background: "#FEE2E2", color: C.danger },
  };
  return (
    <button onClick={onClick} style={{ ...base, ...variants[variant], ...style }}
      className="btn-transition"
    >
      {children}
      {Icon && <Icon size={size === "lg" ? 20 : 16} />}
    </button>
  );
};

// ─── LANDING PAGE ───
const Landing = ({ onStart, onLoginClick }) => {
  const [scrolled, setScrolled] = useState(false);
  useEffect(() => {
    const h = () => setScrolled(window.scrollY > 40);
    window.addEventListener("scroll", h);
    return () => window.removeEventListener("scroll", h);
  }, []);

  const categories = [
    { icon: Heart, title: "Salud / EPS", desc: "Negación de tratamientos, medicamentos, citas", color: "#EF4444" },
    { icon: Landmark, title: "Laboral", desc: "Despido injusto, salarios, acoso laboral", color: "#F59E0B" },
    { icon: Zap, title: "Bancos", desc: "Cobros indebidos, reportes en centrales", color: "#8B5CF6" },
    { icon: Zap, title: "Servicios Públicos", desc: "Cortes, cobros excesivos, reclamaciones", color: "#06B6D4" },
    { icon: ShoppingCart, title: "Consumidor", desc: "Garantías, publicidad engañosa, devoluciones", color: "#10B981" },
    { icon: Shield, title: "Datos Personales", desc: "Habeas data, eliminación de información", color: "#EC4899" },
  ];

  const stats = [
    { value: "12,400+", label: "Tutelas generadas" },
    { value: "98%", label: "Tasa de aceptación" },
    { value: "< 5 min", label: "Tiempo promedio" },
    { value: "380+", label: "Artículos de ley" },
  ];

  return (
    <div style={{ fontFamily: "'DM Sans', sans-serif", color: '#fff', background: C.bgDark, minHeight: "100vh" }}>
      {/* NAV */}
      <nav style={{
        position: "fixed", top: 0, left: 0, right: 0, zIndex: 100,
        padding: "0 40px", height: 80, display: "flex", alignItems: "center", justifyContent: "space-between",
        background: scrolled ? "rgba(11, 22, 40, 0.95)" : "transparent",
        backdropFilter: scrolled ? "blur(12px)" : "none",
        borderBottom: scrolled ? `1px solid ${C.borderDark}` : "none",
        transition: "all 0.3s ease",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{ width: 36, height: 36, background: C.primary, borderRadius: 10, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff' }}>
            <Scale size={20} />
          </div>
          <span style={{ fontWeight: 800, fontSize: 22, color: '#fff' }}>123<span style={{ color: C.primary }}>tutela</span></span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 32 }}>
          {["Cómo funciona", "Categorías", "Precios"].map(t => (
            <a key={t} href="#" style={{ textDecoration: "none", color: 'rgba(255,255,255,0.6)', fontSize: 14, fontWeight: 500 }}>{t}</a>
          ))}
          <Button variant="outline" size="sm" onClick={onLoginClick} style={{ borderColor: 'rgba(255,255,255,0.2)', color: '#fff' }}>Iniciar sesión</Button>
          <Button size="sm" onClick={onStart}>Empezar gratis</Button>
        </div>
      </nav>

      {/* HERO */}
      <section style={{ padding: "180px 40px 80px", maxWidth: 1200, margin: "0 auto" }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: 60, alignItems: 'center' }}>
          <motion.div initial={{ opacity: 0, x: -30 }} animate={{ opacity: 1, x: 0 }}>
            <Badge color={C.accent}>✨ Impulsado por IA jurídica colombiana</Badge>
            <h1 style={{ fontSize: 58, fontWeight: 800, lineHeight: 1.1, margin: "24px 0", fontFamily: "'Playfair Display', serif", color: '#fff' }}>
              Tu justicia, <br />
              <span style={{ background: 'linear-gradient(90deg, #0066FF, #00C48C)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>sin barreras</span>
            </h1>
            <p style={{ fontSize: 19, color: 'rgba(255,255,255,0.6)', maxWidth: 500, marginBottom: 40, lineHeight: 1.6 }}>
              Genera tutelas, derechos de petición y reclamaciones legales en minutos. 
              Nuestra IA analiza tu caso con la Constitución y jurisprudencia colombiana.
            </p>
            <div style={{ display: "flex", gap: 16 }}>
              <Button size="lg" onClick={onStart} icon={ArrowRight}>Empezar mi trámite</Button>
              <Button variant="ghost" size="lg" onClick={onStart} style={{ background: 'rgba(255,255,255,0.05)', color: '#fff', border: '1px solid rgba(255,255,255,0.1)' }}>Analizar mi caso</Button>
            </div>
            
            <div style={{ display: 'flex', gap: 24, marginTop: 40 }}>
              {['Sin abogado', 'En 5 minutos', '100% legal'].map(f => (
                <div key={f} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, color: 'rgba(255,255,255,0.4)', fontWeight: 500 }}>
                  <CheckCircle2 size={16} color={C.accent} /> {f}
                </div>
              ))}
            </div>
          </motion.div>

          <motion.div initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} className="glass-card" style={{ padding: 32, position: 'relative' }}>
             <div style={{ position: 'absolute', top: -12, right: 30, background: C.accent, color: '#fff', padding: '6px 14px', borderRadius: 20, fontSize: 11, fontWeight: 700 }}>🔴 EN VIVO</div>
             <div style={{ fontSize: 13, color: C.textMuted, marginBottom: 15 }}>Caso analizado hace 2 minutos</div>
             
             <div style={{ background: '#F0FDF4', border: '1px solid #BBF7D0', padding: 16, borderRadius: 14, marginBottom: 20 }}>
                <div style={{ fontSize: 11, fontWeight: 700, color: C.success, marginBottom: 4 }}>✓ DERECHO IDENTIFICADO</div>
                <div style={{ fontWeight: 700, fontSize: 15 }}>Derecho a la salud — Art. 49 Constitución</div>
             </div>

             <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 20 }}>
                <Badge color={C.danger}>EPS negó tratamiento</Badge>
                <Badge color={C.primary}>Ley 1751/2015</Badge>
             </div>

             <div style={{ background: C.primaryLight, border: `1px solid ${C.primary}30`, padding: 16, borderRadius: 14 }}>
                <div style={{ fontSize: 11, fontWeight: 700, color: C.primary, marginBottom: 4 }}>⚡ ACCIÓN RECOMENDADA</div>
                <div style={{ fontWeight: 800, fontSize: 17 }}>Acción de Tutela</div>
                <p style={{ fontSize: 13, color: C.textMuted, marginTop: 6 }}>Documento listo con hechos y fundamentos.</p>
             </div>

             <div style={{ display: 'flex', gap: 12, marginTop: 24 }}>
                <Button size="sm" icon={FileText}>Descargar PDF</Button>
                <Button variant="secondary" size="sm">Editar</Button>
             </div>
          </motion.div>
        </div>
      </section>

      {/* STATS */}
      <section style={{ maxWidth: 1200, margin: "0 auto 80px", padding: "0 40px", display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 20 }}>
        {stats.map(s => (
          <div key={s.label} className="glass-card p-6 text-center">
            <div style={{ fontSize: 32, fontWeight: 800, color: C.primary, fontFamily: "'Playfair Display', serif" }}>{s.value}</div>
            <div style={{ fontSize: 13, color: C.textMuted, marginTop: 4, fontWeight: 500 }}>{s.label}</div>
          </div>
        ))}
      </section>

      {/* CATEGORIES */}
      <section style={{ maxWidth: 1200, margin: "0 auto", padding: "80px 40px" }}>
        <div style={{ textAlign: "center", marginBottom: 56 }}>
          <Badge>CATEGORÍAS</Badge>
          <h2 style={{ fontFamily: "'Playfair Display', serif", fontSize: 42, fontWeight: 700, marginTop: 12 }}>
            ¿Cuál es tu problema?
          </h2>
          <p style={{ color: C.textMuted, fontSize: 17, maxWidth: 500, margin: "12px auto 0" }}>
            Selecciona la categoría que mejor describe tu situación para iniciar el análisis legal.
          </p>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 24 }}>
          {categories.map((cat, i) => (
            <motion.div 
              key={i} 
              whileHover={{ y: -8, boxShadow: `0 12px 40px ${cat.color}15`, borderColor: cat.color }}
              className="glass-card p-8 cursor-pointer group"
              style={{ position: 'relative', transition: 'all 0.3s ease', border: `1px solid ${C.border}` }}
              onClick={onStart}
            >
              <div style={{ background: cat.color + '12', width: 56, height: 56, borderRadius: 14, display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 24 }}>
                <cat.icon size={26} style={{ color: cat.color }} />
              </div>
              <h3 style={{ fontSize: 20, fontWeight: 700, marginBottom: 10 }}>{cat.title}</h3>
              <p style={{ color: C.textMuted, fontSize: 15, lineHeight: 1.5 }}>{cat.desc}</p>
              <div style={{ 
                position: 'absolute', top: 24, right: 24, color: cat.color, opacity: 0.4,
              }}>
                <ChevronRight size={20} />
              </div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* HOW IT WORKS */}
      <section style={{ background: C.bgDark, padding: "100px 40px", color: '#fff' }}>
        <div style={{ maxWidth: 1200, margin: "0 auto" }}>
          <div style={{ textAlign: "center", marginBottom: 64 }}>
            <Badge color={C.accent}>PROCESO</Badge>
            <h2 style={{ fontFamily: "'Playfair Display', serif", fontSize: 42, fontWeight: 700, marginTop: 12 }}>
              Tres pasos. Sin complicaciones.
            </h2>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 32 }}>
            {[
              { n: "01", t: "Describe tu problema", d: "Cuéntanos qué pasó con tus propias palabras o sube un documento.", i: MessageSquare },
              { n: "02", t: "La IA analiza tu caso", d: "Identificamos derechos vulnerados, normas aplicables y jurisprudencia.", i: Search },
              { n: "03", t: "Genera tu documento", d: "Recibe tutela, derecho de petición o reclamación lista para presentar.", i: FileText },
            ].map((step, idx) => (
              <div key={idx} style={{ 
                position: 'relative', 
                background: 'rgba(255,255,255,0.03)', 
                border: '1px solid rgba(255,255,255,0.08)',
                borderRadius: 24,
                padding: '48px 32px',
                overflow: 'hidden',
                transition: 'all 0.3s ease',
              }} className="glass-card">
                <div style={{ 
                  fontSize: 120, 
                  fontWeight: 900, 
                  opacity: 0.05, 
                  position: 'absolute', 
                  top: -20, 
                  right: -10,
                  color: C.primary,
                  pointerEvents: 'none',
                }}>{step.n}</div>
                <div style={{ position: 'relative', zIndex: 1 }}>
                  <div style={{ width: 56, height: 56, background: C.primary + '20', borderRadius: 16, display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 24, border: `1px solid ${C.primary}40` }}>
                    <step.i size={24} color={C.primary} />
                  </div>
                  <h3 style={{ fontSize: 24, fontWeight: 700, marginBottom: 16, fontFamily: "'Playfair Display', serif" }}>{step.t}</h3>
                  <p style={{ color: 'rgba(255,255,255,0.6)', lineHeight: 1.7, fontSize: 15 }}>{step.d}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* FINAL CTA */}
      <section style={{ 
        padding: "100px 40px", 
        textAlign: "center", 
        background: '#fff', 
        color: C.text,
        borderBottom: `1px solid ${C.border}`
      }}>
        <div style={{ maxWidth: 800, margin: "0 auto" }}>
          <h2 style={{ fontSize: 48, fontWeight: 700, marginBottom: 24, fontFamily: "'Playfair Display', serif" }}>
            Protege tus derechos hoy
          </h2>
          <p style={{ fontSize: 18, color: C.textMuted, marginBottom: 40, lineHeight: 1.6 }}>
            No necesitas ser abogado. Nuestra IA conoce la Constitución, las leyes y la jurisprudencia colombiana.
          </p>
          <Button size="lg" onClick={onStart} icon={Users} style={{ padding: '16px 48px' }}>
            Empezar mi trámite gratis
          </Button>
        </div>
      </section>

      {/* FOOTER */}
      <footer style={{ borderTop: `1px solid ${C.border}`, padding: "40px", maxWidth: 1200, margin: "40px auto 0", display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ fontSize: 13, color: C.textMuted }}>
          © 2026 123tutela Colombia. Todos los derechos reservados. No reemplazamos asesoría legal personalizada.
        </div>
        <div style={{ display: 'flex', gap: 24 }}>
          {['Términos', 'Privacidad', 'Ayuda'].map(l => (
            <a key={l} href="#" style={{ fontSize: 13, color: C.textMuted, textDecoration: 'none' }}>{l}</a>
          ))}
        </div>
      </footer>
    </div>
  );
};

// ─── DASHBOARD ───
const Dashboard = ({ onBack, user, onLogout }) => {
  const [activeTab, setActiveTab] = useState("inicio");
  const [step, setStep] = useState(1);
  const [inputText, setInputText] = useState("");
  const [loading, setLoading] = useState(false);
  const [userData, setUserData] = useState({ city: "Bogotá", dept: "Cundinamarca", category: "" });
  const [files, setFiles] = useState([]);
  const [messages, setMessages] = useState([
    { role: "ai", text: "¡Hola! Soy tu asistente legal de 123tutela. ¿En qué puedo ayudarte hoy?" }
  ]);

  const sideItems = [
    { id: "inicio", icon: Layout, label: "Inicio" },
    { id: "nuevo", icon: Plus, label: "Nuevo trámite" },
    { id: "tramites", icon: Files, label: "Mis trámites" },
    { id: "documentos", icon: FileText, label: "Documentos" },
    { id: "ayuda", icon: HelpCircle, label: "Ayuda" },
  ];

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      setFiles(prev => [...prev, file]);
      setMessages(prev => [...prev, { role: 'user', text: `📎 Adjunto archivo: ${file.name}` }]);
      
      setTimeout(() => {
        setMessages(prev => [...prev, { role: 'ai', text: `He recibido tu archivo "${file.name}". Lo estoy analizando para fortalecer los hechos de tu trámite.` }]);
      }, 1000);
    }
  };

  const handleSend = async () => {
    if (!inputText.trim() && files.length === 0) return;
    
    const userMsg = inputText;
    if (userMsg) {
      setMessages(prev => [...prev, { role: 'user', text: userMsg }]);
    }
    setInputText("");
    setLoading(true);

    try {
      // Call the new 3-layer Legal Analyzer
      const res = await axios.post(`${ANALYZE_API_BASE}/analyze`, {
        description: userMsg,
      });
      
      if (res.data.success) {
        setMessages(prev => [...prev, { role: 'ai', text: res.data.strategy }]);
      } else {
        setMessages(prev => [...prev, { role: 'ai', text: "He analizado tu caso. Según el Art. 86 de la Constitución, esto clasifica para una tutela. ¿Deseas que genere el documento basado en los juzgados locales?" }]);
      }
    } catch (err) {
      setMessages(prev => [...prev, { role: 'ai', text: "Entiendo tu situación. Basado en las normas del marco legal colombiano, parece que procede una Acción de Tutela. ¿Deseas continuar?" }]);
    } finally {
      setLoading(false);
    }
  };

  const nextStep = () => setStep(s => Math.min(s + 1, 5));
  const prevStep = () => setStep(s => Math.max(s - 1, 1));

  const renderStep = () => {
    switch(step) {
      case 1:
        return (
          <div style={{ textAlign: 'center', padding: '40px 0' }}>
            <h3 style={{ fontSize: 24, fontWeight: 700, marginBottom: 32, color: '#fff' }}>¿Sobre qué trata tu caso?</h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 20 }}>
              {[
                { label: 'Salud', icon: Stethoscope, color: '#EF4444' },
              ].map(cat => (
                <div 
                  key={cat.label} 
                  onClick={() => { setUserData({...userData, category: cat.label}); nextStep(); }}
                  className="glass-card p-8 cursor-pointer group"
                  style={{ 
                    background: 'rgba(255,255,255,0.05)',
                    border: userData.category === cat.label ? `2px solid ${C.primary}` : `1px solid rgba(255,255,255,0.1)`, 
                    transition: 'all 0.2s ease',
                    color: '#fff'
                  }}
                >
                  <div style={{ background: cat.color + '20', width: 50, height: 50, borderRadius: 12, display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px' }}>
                    <cat.icon size={24} style={{ color: cat.color }} />
                  </div>
                  <div style={{ fontWeight: 700 }}>{cat.label}</div>
                </div>
              ))}
            </div>
            <div style={{ marginTop: 16, color: 'rgba(255,255,255,0.72)', fontSize: 14 }}>
              Por ahora solo estamos mostrando casos de salud mientras estabilizamos los demas bloques.
            </div>
          </div>
        );
      case 2:
        return (
          <div style={{ height: 'calc(100vh - 250px)', display: 'flex', flexDirection: 'column' }}>
            <h3 style={{ fontSize: 20, fontWeight: 700, marginBottom: 20, color: '#fff' }}>Cuéntanos qué sucedió</h3>
            <div style={{ flex: 1, overflowY: 'auto', padding: 20, background: 'rgba(255,255,255,0.03)', borderRadius: 16, marginBottom: 20, display: 'flex', flexDirection: 'column', gap: 12 }}>
              {messages.map((m, i) => (
                <div key={i} style={{ alignSelf: m.role === 'user' ? 'flex-end' : 'flex-start', maxWidth: '80%', padding: '12px 16px', borderRadius: 16, background: m.role === 'user' ? C.primary : 'rgba(255,255,255,0.1)', color: '#fff', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
                  {m.text}
                </div>
              ))}
              {loading && <div style={{ fontSize: 13, color: 'rgba(255,255,255,0.5)' }}>IA escribiendo...</div>}
            </div>
            <div style={{ display: 'flex', gap: 12 }}>
              <input 
                value={inputText}
                onChange={e => setInputText(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleSend()}
                placeholder="Escribe aquí los detalles..."
                style={{ flex: 1, padding: '14px 20px', borderRadius: 12, border: '1px solid rgba(255,255,255,0.1)', background: 'rgba(255,255,255,0.05)', color: '#fff', outline: 'none' }}
              />
              <Button onClick={handleSend} icon={Send} />
            </div>
          </div>
        );
      case 3:
        return (
          <div style={{ textAlign: 'center', padding: '60px 0' }}>
            <div style={{ width: 80, height: 80, background: C.primary + '20', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 24px', color: C.primary }}>
              <Upload size={32} />
            </div>
            <h3 style={{ fontSize: 24, fontWeight: 700, marginBottom: 12, color: '#fff' }}>Adjunta tus pruebas</h3>
            <p style={{ color: 'rgba(255,255,255,0.6)', marginBottom: 40 }}>Sube fotos de órdenes médicas, chats, correos o cualquier evidencia.</p>
            <input type="file" id="file-upload" style={{ display: 'none' }} onChange={handleFileUpload} />
            <label htmlFor="file-upload">
              <Button onClick={() => document.getElementById('file-upload').click()} variant="outline" size="lg">Seleccionar Archivos</Button>
            </label>
            <div style={{ marginTop: 24, display: 'flex', flexWrap: 'wrap', gap: 10, justifyContent: 'center' }}>
              {files.map((f, i) => (
                <Badge key={i} color={C.accent}>{f.name}</Badge>
              ))}
            </div>
          </div>
        );
      case 4:
        return (
          <div style={{ maxWidth: 500, margin: '0 auto', padding: '40px 0' }}>
            <h3 style={{ fontSize: 24, fontWeight: 700, marginBottom: 32, textAlign: 'center', color: '#fff' }}>¿Dónde te encuentras?</h3>
            <div style={{ display: 'grid', gap: 20 }}>
              <div>
                <label style={{ display: 'block', fontSize: 13, fontWeight: 600, marginBottom: 8, color: 'rgba(255,255,255,0.7)' }}>Departamento</label>
                <input 
                  value={userData.dept}
                  onChange={e => setUserData({...userData, dept: e.target.value})}
                  style={{ width: '100%', padding: '14px 18px', borderRadius: 12, border: '1px solid rgba(255,255,255,0.1)', background: 'rgba(255,255,255,0.05)', color: '#fff' }}
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: 13, fontWeight: 600, marginBottom: 8, color: 'rgba(255,255,255,0.7)' }}>Municipio / Ciudad</label>
                <input 
                  value={userData.city}
                  onChange={e => setUserData({...userData, city: e.target.value})}
                  style={{ width: '100%', padding: '14px 18px', borderRadius: 12, border: '1px solid rgba(255,255,255,0.1)', background: 'rgba(255,255,255,0.05)', color: '#fff' }}
                />
              </div>
            </div>
          </div>
        );
      case 5:
        return (
          <div style={{ textAlign: 'center', padding: '40px 0' }}>
            <div style={{ width: 80, height: 80, background: C.success + '20', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 24px', color: C.success }}>
              <CheckCircle2 size={40} />
            </div>
            <h3 style={{ fontSize: 24, fontWeight: 700, marginBottom: 12, color: '#fff' }}>Todo listo para generar</h3>
            <p style={{ color: 'rgba(255,255,255,0.6)', marginBottom: 32 }}>Nuestro <b>Motor Jurídico de 3 Capas</b> ha finalizado el análisis.</p>
            
            <div className="glass-card" style={{ textAlign: 'left', padding: 24, marginBottom: 32, background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.1)' }}>
               <h4 style={{ color: C.primary, fontSize: 14, fontWeight: 700, textTransform: 'uppercase', marginBottom: 16 }}>Diagnóstico Legal</h4>
               <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12 }}>
                  <span style={{ fontWeight: 600, color: '#fff' }}>Estrategia:</span>
                  <Badge color={C.primary}>Acción de Tutela</Badge>
               </div>
               <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12 }}>
                  <span style={{ fontWeight: 600, color: '#fff' }}>Derecho Vulnerado:</span>
                  <span style={{ color: 'rgba(255,255,255,0.7)' }}>Salud / Vida Digna</span>
               </div>
               <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ fontWeight: 600, color: '#fff' }}>Ruteo Automático:</span>
                  <span style={{ color: C.success, fontWeight: 700 }}>Activo (Marco Juzgados Col)</span>
               </div>
            </div>
            
            <Button size="lg" style={{ width: '100%' }}>Generar y Enviar documento</Button>
          </div>
        );
      default: return null;
    }
  };

  return (
    <div style={{ display: "flex", height: "100vh", background: "#121212", overflow: 'hidden', fontFamily: "'DM Sans', sans-serif" }}>
      {/* SIDEBAR */}
      <aside style={{ width: 260, background: "#1A1A1A", borderRight: `1px solid rgba(255,255,255,0.05)`, padding: "30px 20px", display: 'flex', flexDirection: 'column' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 40, cursor: 'pointer' }} onClick={onBack}>
          <div style={{ width: 32, height: 32, background: C.primary, borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff' }}>
            <Scale size={18} />
          </div>
          <span style={{ fontWeight: 800, fontSize: 18, color: '#fff' }}>123<span style={{ color: C.primary }}>tutela</span></span>
        </div>
        
        <div style={{ flex: 1 }}>
          {sideItems.map(item => (
            <button
              key={item.id}
              onClick={() => { setActiveTab(item.id); setStep(1); }}
              style={{
                width: '100%', display: 'flex', alignItems: 'center', gap: 12, padding: '12px 16px', borderRadius: 12, marginBottom: 8,
                background: activeTab === item.id ? '#fff' : 'transparent',
                color: activeTab === item.id ? C.primary : 'rgba(255,255,255,0.5)',
                border: 'none', cursor: 'pointer', fontWeight: activeTab === item.id ? 700 : 500, fontSize: 14,
                transition: 'all 0.2s ease'
              }}
            >
              <item.icon size={18} /> {item.label}
            </button>
          ))}
        </div>

        {/* USER PROFILE BOTTOM */}
        <div style={{ padding: 12, background: "#121212", borderRadius: 16, display: 'flex', alignItems: 'center', gap: 12, border: '1px solid rgba(255,255,255,0.05)' }}>
          <div style={{ background: C.primary, width: 36, height: 36, borderRadius: 10, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontSize: 12, fontWeight: 700 }}>
            {user ? user.name.substring(0,2).toUpperCase() : 'JD'}
          </div>
          <div style={{ flex: 1, overflow: 'hidden' }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: '#fff', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{user ? user.name : 'Juan D.'}</div>
            <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.4)' }}>Plan gratis</div>
          </div>
          <button onClick={onLogout} style={{ background: 'none', border: 'none', color: 'rgba(255,255,255,0.3)', cursor: 'pointer', display: 'flex', alignItems: 'center' }} title="Cerrar sesión">
            <LogOut size={16} />
          </button>
        </div>
      </aside>

      <main style={{ flex: 1, display: 'flex', flexDirection: 'column', height: '100vh', overflowY: 'auto' }}>
        {activeTab === 'inicio' ? (
          <div style={{ padding: 40 }}>
            {/* HERO BOX */}
            <div style={{ 
              background: 'linear-gradient(135deg, #0B1628 0%, #111D32 100%)', 
              padding: '60px 48px', 
              borderRadius: 24, 
              color: '#fff', 
              marginBottom: 40, 
              position: 'relative', 
              overflow: 'hidden',
              border: '1px solid rgba(255,255,255,0.05)'
            }}>
              <div style={{ position: 'relative', zIndex: 1, maxWidth: 500 }}>
                <div style={{ fontSize: 14, color: 'rgba(255,255,255,0.5)', marginBottom: 12, fontWeight: 600, letterSpacing: 0.5 }}>BUENOS DÍAS</div>
                <h2 style={{ fontSize: 36, fontWeight: 700, marginBottom: 12, fontFamily: "'Playfair Display', serif" }}>¿En qué te podemos ayudar?</h2>
                <p style={{ opacity: 0.7, fontSize: 16, marginBottom: 32 }}>Inicia un nuevo trámite o revisa los existentes.</p>
                <div style={{ display: 'flex', gap: 16 }}>
                  <Button size="lg" onClick={() => { setActiveTab('nuevo'); setStep(1); }} icon={Plus}>Nuevo trámite +</Button>
                  <Button size="lg" variant="ghost" onClick={() => { setActiveTab('nuevo'); setStep(2); }} style={{ background: 'rgba(255,255,255,0.05)', color: '#fff', border: '1px solid rgba(255,255,255,0.1)' }}>Analizar mi caso</Button>
                </div>
              </div>
              <div style={{ position: 'absolute', right: 40, bottom: -20, fontSize: 240, color: 'rgba(255,255,255,0.03)', transform: 'rotate(-15deg)' }}>
                <Scale />
              </div>
            </div>
            
            {/* QUICK ACCESS */}
            <div style={{ marginBottom: 48 }}>
              <h3 style={{ fontSize: 18, fontWeight: 700, marginBottom: 24, color: '#fff' }}>Acceso rápido</h3>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: 16 }}>
                {[
                  { label: 'Salud', icon: Heart, color: '#EF4444' },
                  { label: 'Laboral', icon: Briefcase, color: '#F59E0B' },
                  { label: 'Bancos', icon: Building2, color: '#8B5CF6' },
                  { label: 'Servicios', icon: Zap, color: '#06B6D4' },
                  { label: 'Consumidor', icon: ShoppingCart, color: '#10B981' },
                  { label: 'Datos', icon: Lock, color: '#EC4899' },
                ].map(cat => (
                  <div 
                    key={cat.label} 
                    onClick={() => { setActiveTab('nuevo'); setUserData({...userData, category: cat.label}); setStep(2); }} 
                    className="glass-card text-center cursor-pointer" 
                    style={{ 
                      padding: '24px 16px',
                      background: 'rgba(255,255,255,0.03)', 
                      border: `1px solid rgba(255,255,255,0.05)`,
                      borderRadius: 16,
                      transition: 'all 0.3s ease'
                    }}
                  >
                    <div style={{ background: cat.color + '15', width: 44, height: 44, borderRadius: 12, display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 12px' }}>
                      <cat.icon size={20} style={{ color: cat.color }} />
                    </div>
                    <div style={{ fontWeight: 600, fontSize: 13, color: '#fff' }}>{cat.label}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* RECENT ACTIVITY */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
                <h3 style={{ fontSize: 18, fontWeight: 700, color: '#fff' }}>Trámites recientes</h3>
                <button style={{ background: 'none', border: 'none', color: C.primary, fontSize: 13, fontWeight: 600, cursor: 'pointer' }}>Ver todos &gt;</button>
              </div>
              <div style={{ display: 'grid', gap: 12 }}>
                {[
                  { title: "Tutela contra EPS Sura", subtitle: "Tutela · Salud · Mar 12, 2026", status: "Completado", statusColor: C.success, icon: Users },
                  { title: "Derecho de petición — ETB", subtitle: "Derecho de petición · Servicios · Mar 11, 2026", status: "En proceso", statusColor: C.warning, icon: FileText },
                  { title: "Reclamación Bancolombia", subtitle: "Reclamación · Bancos · Mar 10, 2026", status: "Borrador", statusColor: "#666", icon: Landmark },
                ].map((item, id) => (
                  <div key={id} style={{ 
                    background: 'rgba(255,255,255,0.03)', 
                    border: '1px solid rgba(255,255,255,0.05)', 
                    borderRadius: 16, 
                    padding: '16px 20px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 16,
                    cursor: 'pointer'
                  }}>
                    <div style={{ width: 40, height: 40, borderRadius: 10, background: 'rgba(255,255,255,0.05)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'rgba(255,255,255,0.5)' }}>
                      <item.icon size={18} />
                    </div>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: 700, color: '#fff', fontSize: 14 }}>{item.title}</div>
                      <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.4)', marginTop: 2 }}>{item.subtitle}</div>
                    </div>
                    <div style={{ 
                      padding: '4px 12px', 
                      borderRadius: 20, 
                      fontSize: 11, 
                      fontWeight: 700, 
                      background: item.statusColor + '15', 
                      color: item.statusColor,
                      border: `1px solid ${item.statusColor}30`
                    }}>
                      {item.status}
                    </div>
                    <ChevronRight size={16} color="rgba(255,255,255,0.2)" />
                  </div>
                ))}
              </div>
            </div>
          </div>
        ) : activeTab === 'nuevo' ? (
          <div style={{ flex: 1, padding: 40, display: 'flex', flexDirection: 'column' }}>
            {/* STEP INDICATOR */}
            <div style={{ display: 'flex', justifyContent: 'center', gap: 12, marginBottom: 40 }}>
              {[1, 2, 3, 4, 5].map(s => (
                <div key={s} style={{ 
                  width: 40, height: 4, borderRadius: 2, 
                  background: s <= step ? C.primary : 'rgba(255,255,255,0.1)',
                  transition: '0.3s'
                }} />
              ))}
            </div>

            <div style={{ flex: 1, maxWidth: 800, margin: '0 auto', width: '100%', position: 'relative' }}>
               <AnimatePresence mode="wait">
                  <motion.div 
                    key={step}
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -20 }}
                    transition={{ duration: 0.2 }}
                  >
                    {renderStep()}
                  </motion.div>
               </AnimatePresence>
            </div>

            {/* NAVIGATION BUTTONS */}
            <div style={{ borderTop: `1px solid rgba(255,255,255,0.05)`, paddingTop: 24, display: 'flex', justifyContent: 'space-between', maxWidth: 800, margin: '24px auto 0', width: '100%' }}>
              <Button 
                variant="ghost" 
                onClick={prevStep} 
                disabled={step === 1}
                style={{ visibility: step === 1 ? 'hidden' : 'visible' }}
              >
                ← Atrás
              </Button>
              <Button 
                onClick={nextStep} 
                disabled={step === 5 || (step === 1 && !userData.category)}
              >
                {step === 5 ? 'Finalizar' : 'Continuar →'}
              </Button>
            </div>
          </div>
        ) : (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'rgba(255,255,255,0.3)', fontSize: 14 }}>
            Próximamente...
          </div>
        )}
      </main>
    </div>
  );
};

// ─── LOGIN COMPONENT ───
const Login = ({ onBack, onLogin, onSwitchToRegister }) => {
  const [formData, setFormData] = useState({ email: '', password: '' });

  return (
    <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", background: C.bg, fontFamily: "'DM Sans', sans-serif" }}>
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="glass-card" style={{ padding: 48, width: '100%', maxWidth: 450, textAlign: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10, marginBottom: 32, cursor: 'pointer' }} onClick={onBack}>
          <div style={{ width: 40, height: 40, background: C.primary, borderRadius: 12, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff' }}>
            <Scale size={22} />
          </div>
          <span style={{ fontWeight: 800, fontSize: 24 }}>123<span style={{ color: C.primary }}>tutela</span></span>
        </div>
        
        <h2 style={{ fontSize: 28, fontWeight: 700, marginBottom: 8, fontFamily: "'Playfair Display', serif" }}>Bienvenido de nuevo</h2>
        <p style={{ color: C.textMuted, marginBottom: 32 }}>Ingresa tus credenciales para acceder a tu panel.</p>
        
        <div style={{ textAlign: 'left', marginBottom: 20 }}>
          <label style={{ fontSize: 13, fontWeight: 600, color: C.text, display: 'block', marginBottom: 8 }}>Email</label>
          <input 
            type="email" 
            placeholder="ejemplo@correo.com"
            value={formData.email}
            onChange={e => setFormData({...formData, email: e.target.value})}
            style={{ width: '100%', padding: '14px 18px', borderRadius: 12, border: `1px solid ${C.border}`, background: 'transparent', outline: 'none', fontSize: 14 }} 
          />
        </div>

        <div style={{ textAlign: 'left', marginBottom: 32 }}>
          <label style={{ fontSize: 13, fontWeight: 600, color: C.text, display: 'block', marginBottom: 8 }}>Contraseña</label>
          <input 
            type="password" 
            placeholder="••••••••"
            value={formData.password}
            onChange={e => setFormData({...formData, password: e.target.value})}
            style={{ width: '100%', padding: '14px 18px', borderRadius: 12, border: `1px solid ${C.border}`, background: 'transparent', outline: 'none', fontSize: 14 }} 
          />
        </div>

        <Button onClick={() => onLogin(formData)} style={{ width: '100%', marginBottom: 20 }} size="lg">Iniciar Sesión</Button>
        
        <p style={{ fontSize: 14, color: C.textMuted }}>
          ¿No tienes una cuenta? <span onClick={onSwitchToRegister} style={{ color: C.primary, fontWeight: 700, cursor: 'pointer' }}>Regístrate aquí</span>
        </p>
      </motion.div>
    </div>
  );
};

// ─── REGISTER COMPONENT ───
const Register = ({ onBack, onRegister, onSwitchToLogin }) => {
  const [formData, setFormData] = useState({ name: '', email: '', password: '' });

  return (
    <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", background: C.bg, fontFamily: "'DM Sans', sans-serif" }}>
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="glass-card" style={{ padding: 48, width: '100%', maxWidth: 450, textAlign: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10, marginBottom: 32, cursor: 'pointer' }} onClick={onBack}>
          <div style={{ width: 40, height: 40, background: C.primary, borderRadius: 12, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff' }}>
            <Scale size={22} />
          </div>
          <span style={{ fontWeight: 800, fontSize: 24 }}>123<span style={{ color: C.primary }}>tutela</span></span>
        </div>
        
        <h2 style={{ fontSize: 28, fontWeight: 700, marginBottom: 8, fontFamily: "'Playfair Display', serif" }}>Crea tu cuenta</h2>
        <p style={{ color: C.textMuted, marginBottom: 32 }}>Únete a la plataforma líder en justicia automatizada.</p>
        
        <div style={{ textAlign: 'left', marginBottom: 20 }}>
          <label style={{ fontSize: 13, fontWeight: 600, color: C.text, display: 'block', marginBottom: 8 }}>Nombre Completo</label>
          <input 
            type="text" 
            placeholder="Tu nombre aquí"
            value={formData.name}
            onChange={e => setFormData({...formData, name: e.target.value})}
            style={{ width: '100%', padding: '14px 18px', borderRadius: 12, border: `1px solid ${C.border}`, background: 'transparent', outline: 'none', fontSize: 14 }} 
          />
        </div>

        <div style={{ textAlign: 'left', marginBottom: 20 }}>
          <label style={{ fontSize: 13, fontWeight: 600, color: C.text, display: 'block', marginBottom: 8 }}>Email</label>
          <input 
            type="email" 
            placeholder="ejemplo@correo.com"
            value={formData.email}
            onChange={e => setFormData({...formData, email: e.target.value})}
            style={{ width: '100%', padding: '14px 18px', borderRadius: 12, border: `1px solid ${C.border}`, background: 'transparent', outline: 'none', fontSize: 14 }} 
          />
        </div>

        <div style={{ textAlign: 'left', marginBottom: 32 }}>
          <label style={{ fontSize: 13, fontWeight: 600, color: C.text, display: 'block', marginBottom: 8 }}>Contraseña</label>
          <input 
            type="password" 
            placeholder="••••••••"
            value={formData.password}
            onChange={e => setFormData({...formData, password: e.target.value})}
            style={{ width: '100%', padding: '14px 18px', borderRadius: 12, border: `1px solid ${C.border}`, background: 'transparent', outline: 'none', fontSize: 14 }} 
          />
        </div>

        <Button onClick={() => onRegister(formData)} style={{ width: '100%', marginBottom: 20 }} size="lg">Registrarme</Button>
        
        <p style={{ fontSize: 14, color: C.textMuted }}>
          ¿Ya tienes una cuenta? <span onClick={onSwitchToLogin} style={{ color: C.primary, fontWeight: 700, cursor: 'pointer' }}>Inicia sesión</span>
        </p>
      </motion.div>
    </div>
  );
};

export default function App() {
  const [view, setView] = useState("landing");
  const [user, setUser] = useState(null);

  const handleLogin = (data) => {
    // Simulación de login
    setUser({ name: data.email.split('@')[0], email: data.email });
    setView("dashboard");
  };

  const handleRegister = (data) => {
    // Simulación de registro
    setUser({ name: data.name, email: data.email });
    setView("dashboard");
  };

  return (
    <AnimatePresence mode="wait">
      {view === "landing" ? (
        <motion.div key="landing" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
          <Landing 
            onStart={() => setView(user ? "dashboard" : "register")} 
            onLoginClick={() => setView("login")}
          />
        </motion.div>
      ) : view === "login" ? (
        <motion.div key="login" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
          <Login 
            onBack={() => setView("landing")} 
            onLogin={handleLogin}
            onSwitchToRegister={() => setView("register")}
          />
        </motion.div>
      ) : view === "register" ? (
        <motion.div key="register" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
          <Register 
            onBack={() => setView("landing")} 
            onRegister={handleRegister}
            onSwitchToLogin={() => setView("login")}
          />
        </motion.div>
      ) : (
        <motion.div key="dashboard" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
          <Dashboard 
            user={user}
            onBack={() => setView("landing")} 
            onLogout={() => { setUser(null); setView("landing"); }}
          />
        </motion.div>
      )}
    </AnimatePresence>
  );
}
