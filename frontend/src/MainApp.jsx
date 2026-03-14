import React, { useEffect, useState } from "react";
import { AnimatePresence } from "framer-motion";

import { api, extractError, withAuth } from "./lib/api";
import AuthView from "./views/AuthView";
import Dashboard from "./views/Dashboard";
import DocumentModal from "./views/DocumentModal";
import Landing from "./views/Landing";

const loadSession = () => {
  try {
    const raw = localStorage.getItem("tutela-session");
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
};

const persistSession = (session) => {
  if (!session) {
    localStorage.removeItem("tutela-session");
    return;
  }
  localStorage.setItem("tutela-session", JSON.stringify(session));
};

export default function MainApp() {
  const [view, setView] = useState("landing");
  const [session, setSession] = useState(loadSession());
  const [cases, setCases] = useState([]);
  const [activeTab, setActiveTab] = useState("inicio");
  const [loading, setLoading] = useState(false);
  const [authLoading, setAuthLoading] = useState(false);
  const [authError, setAuthError] = useState("");
  const [actionError, setActionError] = useState("");
  const [documentCase, setDocumentCase] = useState(null);

  const syncSession = (nextSession) => {
    setSession(nextSession);
    persistSession(nextSession);
  };

  const loadCases = async (token) => {
    const response = await api.get("/cases", withAuth(token));
    setCases(response.data);
    return response.data;
  };

  useEffect(() => {
    if (!session?.token) {
      setCases([]);
      return;
    }

    let cancelled = false;
    const bootstrap = async () => {
      try {
        const me = await api.get("/auth/me", withAuth(session.token));
        if (cancelled) return;
        syncSession({ token: session.token, user: me.data });
        await loadCases(session.token);
        if (!cancelled) {
          setView("dashboard");
        }
      } catch {
        if (!cancelled) {
          syncSession(null);
          setView("landing");
        }
      }
    };

    bootstrap();
    return () => {
      cancelled = true;
    };
  }, [session?.token]);

  const handleAuth = async (endpoint, payload) => {
    setAuthLoading(true);
    setAuthError("");
    try {
      const response = await api.post(endpoint, payload);
      syncSession(response.data);
      await loadCases(response.data.token);
      setView("dashboard");
    } catch (error) {
      setAuthError(extractError(error, "No fue posible procesar la sesión."));
    } finally {
      setAuthLoading(false);
    }
  };

  const handlePreview = async (payload) => {
    setLoading(true);
    setActionError("");
    try {
      const response = await api.post("/analysis/preview", payload);
      return response.data;
    } catch (error) {
      setActionError(extractError(error, "No fue posible analizar el caso."));
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const handleCreateCase = async (payload) => {
    setLoading(true);
    setActionError("");
    try {
      const response = await api.post("/cases", payload, withAuth(session.token));
      await loadCases(session.token);
      return response.data;
    } catch (error) {
      setActionError(extractError(error, "No fue posible guardar el trámite."));
      return null;
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateDocument = async (caseId) => {
    setLoading(true);
    setActionError("");
    try {
      const response = await api.post(`/cases/${caseId}/document`, {}, withAuth(session.token));
      await loadCases(session.token);
      setDocumentCase(response.data.case);
    } catch (error) {
      setActionError(extractError(error, "No fue posible generar el documento."));
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    syncSession(null);
    setCases([]);
    setDocumentCase(null);
    setView("landing");
  };

  return (
    <>
      <AnimatePresence mode="wait">
        {view === "landing" && (
          <div key="landing">
            <Landing onStart={() => setView("register")} onLogin={() => setView("login")} />
          </div>
        )}

        {view === "login" && (
          <div key="login">
            <AuthView
              title="Iniciar sesión"
              subtitle="Accede a tu panel para revisar trámites y documentos."
              fields={[
                { name: "email", label: "Correo electrónico", type: "email", placeholder: "ejemplo@correo.com" },
                { name: "password", label: "Contraseña", type: "password", placeholder: "Mínimo 8 caracteres" },
              ]}
              onSubmit={(data) => handleAuth("/auth/login", data)}
              secondaryText="¿No tienes cuenta?"
              secondaryLabel="Regístrate aquí"
              secondaryAction={() => setView("register")}
              onBack={() => setView("landing")}
              loading={authLoading}
              error={authError}
            />
          </div>
        )}

        {view === "register" && (
          <div key="register">
            <AuthView
              title="Crear cuenta"
              subtitle="Te dejaremos listo el espacio para guardar tus análisis y borradores."
              fields={[
                { name: "name", label: "Nombre completo", type: "text", placeholder: "Tu nombre" },
                { name: "email", label: "Correo electrónico", type: "email", placeholder: "ejemplo@correo.com" },
                { name: "password", label: "Contraseña", type: "password", placeholder: "Mínimo 8 caracteres" },
              ]}
              onSubmit={(data) => handleAuth("/auth/register", data)}
              secondaryText="¿Ya tienes cuenta?"
              secondaryLabel="Inicia sesión"
              secondaryAction={() => setView("login")}
              onBack={() => setView("landing")}
              loading={authLoading}
              error={authError}
            />
          </div>
        )}

        {view === "dashboard" && session && (
          <div key="dashboard">
            <Dashboard
              session={session}
              cases={cases}
              activeTab={activeTab}
              setActiveTab={setActiveTab}
              onLogout={handleLogout}
              onPreview={handlePreview}
              onCreateCase={handleCreateCase}
              onGenerateDocument={handleGenerateDocument}
              onOpenDocument={setDocumentCase}
              loading={loading}
              actionError={actionError}
            />
          </div>
        )}
      </AnimatePresence>

      <DocumentModal caseItem={documentCase} onClose={() => setDocumentCase(null)} />
    </>
  );
}
