import React, { useMemo, useState } from "react";
import {
  Briefcase,
  CheckCircle2,
  ChevronRight,
  FileText,
  Heart,
  HelpCircle,
  Landmark,
  Layout,
  LogOut,
  Plus,
  Scale,
  Search,
  Send,
  Shield,
  ShoppingCart,
  Upload,
  Zap,
} from "lucide-react";

import { Badge, Button, Field, SessionCard, TextArea, TextInput } from "../ui";
import { C, CATEGORIES } from "../theme";

const iconMap = {
  Heart,
  Briefcase,
  Landmark,
  Zap,
  ShoppingCart,
  Shield,
};

function CaseCard({ item, onGenerateDocument, onOpenDocument }) {
  return (
    <div className="glass-card" style={{ padding: 22, display: "grid", gap: 14 }}>
      <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "start" }}>
        <div>
          <div style={{ fontSize: 18, fontWeight: 800, color: C.text }}>{item.category}</div>
          <div style={{ color: C.textMuted, marginTop: 4 }}>
            {item.user_city}, {item.user_department}
          </div>
        </div>
        <Badge color={item.status === "documento_generado" ? C.success : C.primary}>{item.status.replaceAll("_", " ")}</Badge>
      </div>
      <p style={{ color: C.textMuted, lineHeight: 1.6 }}>{item.description}</p>
      <div style={{ padding: 16, background: C.primaryLight, borderRadius: 14 }}>
        <div style={{ fontSize: 12, fontWeight: 800, color: C.primary, marginBottom: 6 }}>ACCIÓN RECOMENDADA</div>
        <div style={{ color: C.text, fontWeight: 700 }}>{item.recommended_action}</div>
      </div>
      <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
        <Button variant="secondary" onClick={() => onGenerateDocument(item.id)} icon={FileText}>
          {item.generated_document ? "Regenerar borrador" : "Generar borrador"}
        </Button>
        {item.generated_document && (
          <Button variant="outline" onClick={() => onOpenDocument(item)}>
            Ver documento
          </Button>
        )}
      </div>
    </div>
  );
}

export default function Dashboard({
  session,
  cases,
  activeTab,
  setActiveTab,
  onLogout,
  onPreview,
  onCreateCase,
  onGenerateDocument,
  onOpenDocument,
  loading,
  actionError,
}) {
  const [step, setStep] = useState(1);
  const [analysis, setAnalysis] = useState(null);
  const [files, setFiles] = useState([]);
  const [form, setForm] = useState({
    category: "",
    city: "Bogotá",
    department: "Cundinamarca",
    description: "",
  });

  const stats = useMemo(
    () => [
      { label: "Trámites creados", value: String(cases.length) },
      { label: "Borradores listos", value: String(cases.filter((item) => item.generated_document).length) },
      { label: "Última acción", value: cases[0]?.recommended_action || "Sin análisis" },
    ],
    [cases]
  );

  const sideItems = [
    { id: "inicio", label: "Inicio", icon: Layout },
    { id: "nuevo", label: "Nuevo trámite", icon: Plus },
    { id: "tramites", label: "Mis trámites", icon: Briefcase },
    { id: "documentos", label: "Documentos", icon: FileText },
    { id: "ayuda", label: "Ayuda", icon: HelpCircle },
  ];

  const canContinue =
    (step === 1 && form.category) ||
    (step === 2 && form.description.trim().length >= 20) ||
    step === 3 ||
    (step === 4 && form.city.trim() && form.department.trim()) ||
    step === 5;

  const resetFlow = () => {
    setStep(1);
    setAnalysis(null);
    setFiles([]);
    setForm({
      category: "",
      city: "Bogotá",
      department: "Cundinamarca",
      description: "",
    });
  };

  const submitPreview = async () => {
    try {
      const result = await onPreview({ ...form, attachments: files });
      setAnalysis(result);
      setStep(5);
    } catch {
      // The parent already exposes the user-facing error state.
    }
  };

  const submitCase = async () => {
    const created = await onCreateCase({ ...form, attachments: files });
    if (created) {
      resetFlow();
      setActiveTab("tramites");
    }
  };

  const renderHome = () => (
    <div style={{ display: "grid", gap: 28 }}>
      <div
        style={{
          background: "linear-gradient(135deg, #0B1628 0%, #111D32 100%)",
          borderRadius: 24,
          padding: "42px 38px",
          color: "#fff",
          border: "1px solid rgba(255,255,255,0.08)",
        }}
      >
        <Badge color={C.accent}>Panel operativo</Badge>
        <h2 style={{ fontSize: 38, margin: "16px 0 10px", fontWeight: 800, fontFamily: "'Playfair Display', serif" }}>
          Hola, {session.user.name}
        </h2>
        <p style={{ maxWidth: 560, color: "rgba(255,255,255,0.68)", lineHeight: 1.7 }}>
          Ya puedes analizar casos, guardarlos en la base de datos y generar borradores jurídicos con la ruta operativa sugerida.
        </p>
        <div style={{ display: "flex", gap: 12, marginTop: 24 }}>
          <Button onClick={() => setActiveTab("nuevo")}>Crear nuevo trámite</Button>
          <Button
            variant="ghost"
            style={{ color: "#fff", background: "rgba(255,255,255,0.08)", border: "1px solid rgba(255,255,255,0.1)" }}
            onClick={() => setActiveTab("tramites")}
          >
            Ver mis casos
          </Button>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 18 }}>
        {stats.map((item) => (
          <div key={item.label} className="glass-card" style={{ padding: 22 }}>
            <div style={{ color: C.textMuted, fontSize: 13, fontWeight: 700 }}>{item.label}</div>
            <div style={{ marginTop: 10, fontSize: 22, fontWeight: 800, color: C.text }}>{item.value}</div>
          </div>
        ))}
      </div>

      {cases.length ? (
        <div style={{ display: "grid", gap: 14 }}>
          {cases.slice(0, 3).map((item) => (
            <CaseCard key={item.id} item={item} onGenerateDocument={onGenerateDocument} onOpenDocument={onOpenDocument} />
          ))}
        </div>
      ) : (
        <div className="glass-card" style={{ padding: 24, color: C.textMuted }}>
          Aún no hay trámites guardados. Crea el primero desde “Nuevo trámite”.
        </div>
      )}
    </div>
  );

  const renderWizard = () => (
    <div style={{ display: "grid", gap: 24 }}>
      <div style={{ display: "flex", gap: 10, justifyContent: "center" }}>
        {[1, 2, 3, 4, 5].map((current) => (
          <div key={current} style={{ width: 54, height: 5, borderRadius: 99, background: current <= step ? C.primary : C.border }} />
        ))}
      </div>

      {step === 1 && (
        <SessionCard title="1. Selecciona la categoría" subtitle="Esto orienta la búsqueda normativa y el destino operativo.">
          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 16 }}>
            {CATEGORIES.map((item) => {
              const Icon = iconMap[item.icon];
              return (
                <button
                  key={item.label}
                  onClick={() => setForm((current) => ({ ...current, category: item.label }))}
                  style={{
                    textAlign: "left",
                    padding: 18,
                    borderRadius: 18,
                    background: form.category === item.label ? `${item.color}14` : C.card,
                    border: form.category === item.label ? `2px solid ${item.color}` : `1px solid ${C.border}`,
                    cursor: "pointer",
                  }}
                >
                  <div style={{ width: 46, height: 46, borderRadius: 14, background: `${item.color}18`, display: "grid", placeItems: "center", marginBottom: 14 }}>
                    <Icon size={20} style={{ color: item.color }} />
                  </div>
                  <div style={{ fontWeight: 800, color: C.text }}>{item.title}</div>
                  <p style={{ marginTop: 8, color: C.textMuted, lineHeight: 1.55, fontSize: 14 }}>{item.desc}</p>
                </button>
              );
            })}
          </div>
        </SessionCard>
      )}

      {step === 2 && (
        <SessionCard title="2. Cuéntanos qué pasó" subtitle="Incluye fechas, respuestas recibidas, urgencia y quién está afectando tus derechos.">
          <div style={{ display: "grid", gap: 16 }}>
            <TextArea
              value={form.description}
              onChange={(event) => setForm((current) => ({ ...current, description: event.target.value }))}
              placeholder="Ejemplo: Llevo tres meses solicitando una cita prioritaria con cardiología..."
            />
            <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "center" }}>
              <span style={{ color: C.textMuted, fontSize: 13 }}>{form.description.length} caracteres</span>
              <Button onClick={submitPreview} disabled={loading || form.description.trim().length < 20} icon={Search}>
                {loading ? "Analizando..." : "Analizar ahora"}
              </Button>
            </div>
            {analysis && (
              <div style={{ padding: 18, borderRadius: 16, background: C.primaryLight, border: `1px solid ${C.primary}22` }}>
                <div style={{ fontSize: 12, fontWeight: 800, color: C.primary, marginBottom: 6 }}>VISTA PREVIA</div>
                <div style={{ color: C.text, lineHeight: 1.65 }}>{analysis.strategy}</div>
              </div>
            )}
          </div>
        </SessionCard>
      )}

      {step === 3 && (
        <SessionCard title="3. Adjunta pruebas" subtitle="En este MVP guardaremos los nombres de los archivos para mantener el flujo completo.">
          <input
            id="evidence-upload"
            type="file"
            multiple
            style={{ display: "none" }}
            onChange={(event) => setFiles(Array.from(event.target.files || []).map((file) => file.name))}
          />
          <div style={{ display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
            <Button variant="secondary" onClick={() => document.getElementById("evidence-upload").click()} icon={Upload}>
              Seleccionar archivos
            </Button>
            {files.length ? files.map((name) => <Badge key={name} color={C.accent}>{name}</Badge>) : <span style={{ color: C.textMuted }}>Aún no has adjuntado archivos.</span>}
          </div>
        </SessionCard>
      )}

      {step === 4 && (
        <SessionCard title="4. Ubicación del trámite" subtitle="Usaremos ciudad y departamento para sugerir el juzgado o canal operativo.">
          <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 16 }}>
            <Field label="Departamento">
              <TextInput value={form.department} onChange={(event) => setForm((current) => ({ ...current, department: event.target.value }))} />
            </Field>
            <Field label="Ciudad o municipio">
              <TextInput value={form.city} onChange={(event) => setForm((current) => ({ ...current, city: event.target.value }))} />
            </Field>
          </div>
        </SessionCard>
      )}

      {step === 5 && (
        <SessionCard title="5. Confirmación final" subtitle="Aquí cerramos el análisis y dejamos guardado el trámite.">
          <div style={{ display: "grid", gap: 16 }}>
            <div style={{ padding: 18, borderRadius: 16, background: C.primaryLight }}>
              <div style={{ display: "flex", justifyContent: "space-between", gap: 12, marginBottom: 10 }}>
                <span style={{ color: C.textMuted, fontWeight: 700 }}>Categoría</span>
                <span style={{ fontWeight: 800, color: C.text }}>{form.category}</span>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", gap: 12, marginBottom: 10 }}>
                <span style={{ color: C.textMuted, fontWeight: 700 }}>Ubicación</span>
                <span style={{ fontWeight: 800, color: C.text }}>{form.city}, {form.department}</span>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", gap: 12 }}>
                <span style={{ color: C.textMuted, fontWeight: 700 }}>Archivos</span>
                <span style={{ fontWeight: 800, color: C.text }}>{files.length}</span>
              </div>
            </div>

            {analysis ? (
              <>
                <div style={{ padding: 18, borderRadius: 16, background: "#F0FDF4", border: "1px solid #BBF7D0" }}>
                  <div style={{ fontSize: 12, fontWeight: 800, color: C.success, marginBottom: 6 }}>ESTRATEGIA SUGERIDA</div>
                  <div style={{ color: C.text, fontWeight: 800, marginBottom: 8 }}>{analysis.recommended_action}</div>
                  <div style={{ color: C.textMuted, lineHeight: 1.65 }}>{analysis.strategy}</div>
                </div>
                {analysis.routing?.primary_target && (
                  <div style={{ padding: 18, borderRadius: 16, border: `1px solid ${C.border}` }}>
                    <div style={{ fontSize: 12, fontWeight: 800, color: C.primary, marginBottom: 6 }}>DESTINO SUGERIDO</div>
                    <div style={{ color: C.text, fontWeight: 800 }}>{analysis.routing.primary_target.name}</div>
                    <div style={{ color: C.textMuted, marginTop: 6 }}>{analysis.routing.primary_target.contact || "Sin contacto detectado todavía"}</div>
                  </div>
                )}
              </>
            ) : (
              <div className="glass-card" style={{ padding: 18, color: C.textMuted }}>
                Genera la vista previa desde el paso 2 antes de guardar el trámite.
              </div>
            )}
          </div>
        </SessionCard>
      )}

      {actionError && <p style={{ color: C.danger, marginTop: -8 }}>{actionError}</p>}

      <div style={{ display: "flex", justifyContent: "space-between", gap: 12 }}>
        <Button variant="ghost" onClick={() => setStep((current) => Math.max(1, current - 1))} disabled={step === 1}>
          Atrás
        </Button>
        <div style={{ display: "flex", gap: 12 }}>
          <Button variant="outline" onClick={resetFlow}>Reiniciar</Button>
          {step < 5 ? (
            <Button onClick={() => setStep((current) => Math.min(5, current + 1))} disabled={!canContinue}>
              Continuar <ChevronRight size={16} />
            </Button>
          ) : (
            <Button onClick={submitCase} disabled={loading || !analysis} icon={Send}>
              {loading ? "Guardando..." : "Guardar trámite"}
            </Button>
          )}
        </div>
      </div>
    </div>
  );

  const renderCases = () =>
    cases.length ? (
      <div style={{ display: "grid", gap: 16 }}>
        {cases.map((item) => (
          <CaseCard key={item.id} item={item} onGenerateDocument={onGenerateDocument} onOpenDocument={onOpenDocument} />
        ))}
      </div>
    ) : (
      <div className="glass-card" style={{ padding: 26, color: C.textMuted }}>
        Todavía no tienes trámites guardados.
      </div>
    );

  const renderDocuments = () => {
    const docs = cases.filter((item) => item.generated_document);
    return docs.length ? (
      <div style={{ display: "grid", gap: 16 }}>
        {docs.map((item) => (
          <div key={item.id} className="glass-card" style={{ padding: 22 }}>
            <div style={{ display: "flex", justifyContent: "space-between", gap: 12, marginBottom: 12 }}>
              <div>
                <div style={{ fontWeight: 800, color: C.text }}>{item.recommended_action}</div>
                <div style={{ color: C.textMuted, marginTop: 4 }}>{item.category}</div>
              </div>
              <Button variant="outline" onClick={() => onOpenDocument(item)}>Abrir</Button>
            </div>
            <p style={{ color: C.textMuted, lineHeight: 1.65 }}>{item.generated_document.slice(0, 220)}...</p>
          </div>
        ))}
      </div>
    ) : (
      <div className="glass-card" style={{ padding: 26, color: C.textMuted }}>
        Cuando generes borradores, aparecerán aquí.
      </div>
    );
  };

  const renderHelp = () => (
    <div style={{ display: "grid", gap: 16 }}>
      {[
        {
          title: "Qué hace el análisis",
          body: "Resume hechos, identifica normas aplicables, recomienda acción y sugiere destino operativo según la base de juzgados y entidades.",
        },
        {
          title: "Qué guarda el MVP",
          body: "Usuario, descripción del caso, ciudad, departamento, estrategia, acción sugerida, ruta operativa y borrador generado.",
        },
        {
          title: "Qué sigue después",
          body: "En la siguiente fase conectaremos radicación automática, correo y workflows reales en n8n.",
        },
      ].map((item) => (
        <div key={item.title} className="glass-card" style={{ padding: 22 }}>
          <div style={{ fontWeight: 800, color: C.text, marginBottom: 8 }}>{item.title}</div>
          <div style={{ color: C.textMuted, lineHeight: 1.65 }}>{item.body}</div>
        </div>
      ))}
    </div>
  );

  const content = {
    inicio: renderHome(),
    nuevo: renderWizard(),
    tramites: renderCases(),
    documentos: renderDocuments(),
    ayuda: renderHelp(),
  };

  return (
    <div style={{ minHeight: "100vh", background: "#111827", display: "flex", color: "#fff" }}>
      <aside style={{ width: 270, background: "#0F172A", borderRight: "1px solid rgba(255,255,255,0.08)", padding: 24, display: "flex", flexDirection: "column" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 34 }}>
          <div style={{ width: 38, height: 38, borderRadius: 10, background: C.primary, display: "grid", placeItems: "center" }}>
            <Scale size={20} />
          </div>
          <strong style={{ fontSize: 22 }}>123<span style={{ color: C.primary }}>tutela</span></strong>
        </div>

        <div style={{ display: "grid", gap: 8, flex: 1 }}>
          {sideItems.map((item) => (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              style={{
                border: "none",
                background: activeTab === item.id ? "#fff" : "transparent",
                color: activeTab === item.id ? C.primary : "rgba(255,255,255,0.65)",
                display: "flex",
                alignItems: "center",
                gap: 12,
                padding: "12px 14px",
                borderRadius: 14,
                fontSize: 14,
                fontWeight: 700,
                cursor: "pointer",
              }}
            >
              <item.icon size={18} />
              {item.label}
            </button>
          ))}
        </div>

        <div style={{ padding: 14, borderRadius: 16, background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <div style={{ width: 42, height: 42, borderRadius: 12, background: C.primary, display: "grid", placeItems: "center", fontWeight: 800 }}>
              {session.user.name.slice(0, 2).toUpperCase()}
            </div>
            <div style={{ flex: 1, overflow: "hidden" }}>
              <div style={{ fontWeight: 800, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{session.user.name}</div>
              <div style={{ fontSize: 12, color: "rgba(255,255,255,0.55)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                {session.user.email}
              </div>
            </div>
            <button onClick={onLogout} style={{ background: "transparent", border: "none", color: "rgba(255,255,255,0.5)", cursor: "pointer" }}>
              <LogOut size={16} />
            </button>
          </div>
        </div>
      </aside>

      <main style={{ flex: 1, padding: 34, background: C.bg, overflowY: "auto" }}>
        {content[activeTab]}
      </main>
    </div>
  );
}
