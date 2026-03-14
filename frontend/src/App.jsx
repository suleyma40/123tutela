import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Scale, Heart, Shield, Landmark, ShoppingCart, Info, ArrowRight, CheckCircle2, AlertCircle, FileText, Send, Zap } from 'lucide-react';
import axios from 'axios';

const N8N_WEBHOOK_URL = "https://n8ntutela.123tutelaapp.com/webhook/webhook-casos";

const MODULES = [
  { id: 'health', icon: Heart, name: 'Salud / EPS', color: '#ff4b5c' },
  { id: 'habeas', icon: Shield, name: 'Habeas Data', color: '#00d2ff' },
  { id: 'services', icon: Zap, name: 'Servicios Públicos', color: '#ffcc00' },
  { id: 'banking', icon: Landmark, name: 'Bancos', color: '#4caf50' },
  { id: 'consumer', icon: ShoppingCart, name: 'Consumidor', color: '#ff9800' },
  { id: 'others', icon: Info, name: 'Otros Trámites', color: '#9c27b0' }
];

const App = () => {
  const [step, setStep] = useState('welcome');
  const [selectedModule, setSelectedModule] = useState(null);
  const [loading, setLoading] = useState(false);
  const [diagnosis, setDiagnosis] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    city: '',
    details: ''
  });

  const handleStart = () => setStep('selection');

  const handleSelectModule = (mod) => {
    setSelectedModule(mod);
    setStep('details');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const response = await axios.post(N8N_WEBHOOK_URL, {
        ...formData,
        module_id: selectedModule.id,
        problem_type: selectedModule.name
      });
      setDiagnosis(response.data);
      setStep('diagnosis');
    } catch (err) {
      console.error(err);
      // Mock for demo if webhook is not live yet
      setDiagnosis("Tu caso ha sido pre-analizado. Basado en la Ley 1755 de 2015, tienes derecho a una respuesta inmediata. Procederemos a generar tu documento.");
      setStep('diagnosis');
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen relative py-12 px-4 sm:px-6 lg:px-8">
      <div className="bg-blob blob-1"></div>
      <div className="bg-blob blob-2"></div>

      <nav className="max-w-7xl mx-auto flex justify-between items-center mb-16">
        <div className="flex items-center gap-2">
          <Scale className="text-primary h-8 w-8" />
          <span className="text-2xl font-bold">123<span className="text-primary">tutela</span></span>
        </div>
        <div className="hidden md:flex gap-8 text-muted font-medium">
          <a href="#" className="hover:text-white transition">Cómo funciona</a>
          <a href="#" className="hover:text-white transition">Precios</a>
        </div>
      </nav>

      <main className="max-w-4xl mx-auto">
        <AnimatePresence mode="wait">
          {step === 'welcome' && (
            <motion.div
              key="welcome"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="text-center"
            >
              <h1 className="text-5xl md:text-7xl font-bold mb-6">
                Tu justicia a solo <span className="text-gradient">un clic</span>
              </h1>
              <p className="text-xl text-muted mb-10 max-w-2xl mx-auto">
                Genera tutelas, derechos de petición y reclamaciones legales en minutos con inteligencia artificial. Sin abogados, sin complicaciones.
              </p>
              <button onClick={handleStart} className="btn-premium text-lg px-8 py-4">
                Empezar mi trámite <ArrowRight />
              </button>
            </motion.div>
          )}

          {step === 'selection' && (
            <motion.div
              key="selection"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
            >
              <div className="col-span-full mb-4">
                <h2 className="text-3xl font-bold mb-2">¿Cuál es tu problema?</h2>
                <p className="text-muted">Selecciona la categoría que mejor describa tu situación.</p>
              </div>
              {MODULES.map((mod) => (
                <button
                  key={mod.id}
                  onClick={() => handleSelectModule(mod)}
                  className="glass-card p-8 text-left hover:border-primary/50 transition-all group"
                >
                  <mod.icon className="h-10 w-10 mb-4 transition-transform group-hover:scale-110" style={{ color: mod.color }} />
                  <h3 className="text-xl font-bold mb-2">{mod.name}</h3>
                  <p className="text-sm text-muted">Protege tus derechos en {mod.name.toLowerCase()}.</p>
                </button>
              ))}
            </motion.div>
          )}

          {step === 'details' && (
            <motion.div
              key="details"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              className="glass-card p-8 md:p-12"
            >
              <button onClick={() => setStep('selection')} className="text-primary mb-6 flex items-center gap-1 hover:underline">
                Volver
              </button>
              <h2 className="text-3xl font-bold mb-8">Cuéntanos sobre tu caso de {selectedModule.name}</h2>
              <form onSubmit={handleSubmit} className="space-y-6">
                <div className="grid md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-muted mb-2">Nombre Completo</label>
                    <input 
                      required
                      type="text" 
                      className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 focus:outline-none focus:border-primary"
                      placeholder="Ej: Juan Pérez"
                      value={formData.name}
                      onChange={e => setFormData({...formData, name: e.target.value})}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-muted mb-2">Ciudad</label>
                    <input 
                      required
                      type="text" 
                      className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 focus:outline-none focus:border-primary"
                      placeholder="Ej: Bogotá"
                      value={formData.city}
                      onChange={e => setFormData({...formData, city: e.target.value})}
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-muted mb-2">Describe el problema detalladamente</label>
                  <textarea 
                    required
                    rows="4"
                    className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 focus:outline-none focus:border-primary"
                    placeholder="¿Qué sucedió? ¿Qué entidad está involucrada?"
                    value={formData.details}
                    onChange={e => setFormData({...formData, details: e.target.value})}
                  />
                </div>
                <button disabled={loading} type="submit" className="w-full btn-premium justify-center py-4 text-lg">
                  {loading ? 'Analizando con IA...' : 'Generar Diagnóstico Gratuito'} <Zap />
                </button>
              </form>
            </motion.div>
          )}

          {step === 'diagnosis' && (
            <motion.div
              key="diagnosis"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="glass-card p-8 md:p-12"
            >
              <div className="flex items-center gap-4 mb-8">
                <div className="bg-green-500/20 p-3 rounded-full">
                  <CheckCircle2 className="text-green-500 h-8 w-8" />
                </div>
                <div>
                  <h2 className="text-3xl font-bold">Diagnóstico Legal Listos</h2>
                  <p className="text-muted">Análisis realizado por nuestro motor jurídico 123tutela.</p>
                </div>
              </div>

              <div className="bg-white/5 rounded-2xl p-6 mb-8 border border-white/5">
                <p className="text-lg leading-relaxed">
                  {diagnosis}
                </p>
              </div>

              <div className="grid md:grid-cols-2 gap-6 mb-8">
                <div className="border border-primary/30 rounded-2xl p-6 flex flex-col items-center text-center">
                  <FileText className="text-primary h-10 w-10 mb-4" />
                  <h3 className="font-bold mb-2">Documento PDF</h3>
                  <p className="text-sm text-muted mb-4">Listo para radicar con todas las normas citadas.</p>
                  <button className="btn-premium w-full justify-center">Descargar Documento</button>
                </div>
                <div className="border border-accent/30 rounded-2xl p-6 flex flex-col items-center text-center">
                  <Send className="text-accent h-10 w-10 mb-4" />
                  <h3 className="font-bold mb-2">Envío Directo</h3>
                  <p className="text-sm text-muted mb-4">Nosotros lo enviamos a la entidad por ti.</p>
                  <button className="bg-white/10 border border-white/10 text-white font-bold py-3 px-6 rounded-xl w-full hover:bg-white/20 transition">Contratar Envío</button>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </main>

      <footer className="mt-20 text-center text-muted text-sm max-w-lg mx-auto">
        <p>© 2026 123tutela Colombia. Todos los derechos reservados. No reemplazamos asesoría legal personalizada para casos penales o de alta complejidad.</p>
      </footer>
    </div>
  );
};

export default App;
