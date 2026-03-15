import React, { useEffect, useState } from "react";
import { AnimatePresence } from "framer-motion";

import { api, extractError, withAuth } from "./lib/api";
import AuthView from "./views/AuthView";
import DashboardV2 from "./views/DashboardV2";
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

export default function MainAppV2() {
  const [view, setView] = useState("landing");
  const [session, setSession] = useState(loadSession());
  const [cases, setCases] = useState([]);
  const [internalCases, setInternalCases] = useState([]);
  const [activeTab, setActiveTab] = useState("inicio");
  const [loading, setLoading] = useState(false);
  const [authLoading, setAuthLoading] = useState(false);
  const [authError, setAuthError] = useState("");
  const [actionError, setActionError] = useState("");
  const [documentCase, setDocumentCase] = useState(null);
  const [activeCaseDetail, setActiveCaseDetail] = useState(null);

  const syncSession = (nextSession) => {
    setSession(nextSession);
    persistSession(nextSession);
  };

  const loadCases = async (token) => {
    const response = await api.get("/cases", withAuth(token));
    setCases(response.data);
    return response.data;
  };

  const loadInternalCases = async (token, role) => {
    if (role !== "internal") {
      setInternalCases([]);
      return [];
    }
    const response = await api.get("/internal/cases", withAuth(token));
    setInternalCases(response.data);
    return response.data;
  };

  const refreshCollections = async (token, role) => {
    await loadCases(token);
    await loadInternalCases(token, role);
  };

  useEffect(() => {
    if (!session?.token) {
      setCases([]);
      setInternalCases([]);
      return;
    }

    let cancelled = false;
    const bootstrap = async () => {
      try {
        const me = await api.get("/auth/me", withAuth(session.token));
        if (cancelled) return;
        const nextSession = { token: session.token, user: me.data };
        syncSession(nextSession);
        await refreshCollections(session.token, me.data.role);
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
      await refreshCollections(response.data.token, response.data.user.role);
      setView("dashboard");
    } catch (error) {
      setAuthError(extractError(error, "No fue posible procesar la sesión."));
    } finally {
      setAuthLoading(false);
    }
  };

  const withAction = async (fn, fallback) => {
    setLoading(true);
    setActionError("");
    try {
      return await fn();
    } catch (error) {
      setActionError(extractError(error, fallback));
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const handleSaveProfile = (payload) =>
    withAction(async () => {
      const response = await api.patch("/auth/me", payload, withAuth(session.token));
      const nextSession = { ...session, user: response.data };
      syncSession(nextSession);
      return response.data;
    }, "No fue posible actualizar el perfil.");

  const handlePreview = (payload) =>
    withAction(async () => {
      const response = await api.post("/analysis/preview", payload);
      return response.data;
    }, "No fue posible analizar el caso.");

  const handleTempUpload = (file, fileKind = "attachment") =>
    withAction(async () => {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("file_kind", fileKind);
      const response = await api.post("/uploads", formData, {
        ...withAuth(session.token),
        headers: {
          ...withAuth(session.token).headers,
          "Content-Type": "multipart/form-data",
        },
      });
      return response.data;
    }, "No fue posible subir el archivo.");

  const handleCreateCase = (payload) =>
    withAction(async () => {
      const response = await api.post("/cases", payload, withAuth(session.token));
      await refreshCollections(session.token, session.user.role);
      setActiveCaseDetail(response.data);
      return response.data;
    }, "No fue posible crear el expediente.");

  const handleOpenCase = (caseId, scope = "citizen") =>
    withAction(async () => {
      const endpoint = scope === "internal" ? `/internal/cases/${caseId}` : `/cases/${caseId}`;
      const response = await api.get(endpoint, withAuth(session.token));
      setActiveCaseDetail(response.data);
      return response.data;
    }, "No fue posible abrir el expediente.");

  const handleConfirmPayment = (caseId, reference) =>
    withAction(async () => {
      const response = await api.post(`/cases/${caseId}/payment`, { reference }, withAuth(session.token));
      await refreshCollections(session.token, session.user.role);
      const detail = await api.get(`/cases/${caseId}`, withAuth(session.token));
      setActiveCaseDetail(detail.data);
      return response.data;
    }, "No fue posible registrar el pago.");

  const handleGenerateDocument = (caseId) =>
    withAction(async () => {
      const response = await api.post(`/cases/${caseId}/document`, {}, withAuth(session.token));
      await refreshCollections(session.token, session.user.role);
      const detail = await api.get(`/cases/${caseId}`, withAuth(session.token));
      setActiveCaseDetail(detail.data);
      setDocumentCase(response.data.case);
      return response.data;
    }, "No fue posible generar el documento.");

  const handleSubmitCase = (caseId, payload) =>
    withAction(async () => {
      const response = await api.post(`/cases/${caseId}/submit`, payload, withAuth(session.token));
      await refreshCollections(session.token, session.user.role);
      setActiveCaseDetail(response.data);
      return response.data;
    }, "No fue posible ejecutar la radicación.");

  const handleManualRadicado = (caseId, payload) =>
    withAction(async () => {
      const response = await api.post(`/cases/${caseId}/manual-radicado`, payload, withAuth(session.token));
      await refreshCollections(session.token, session.user.role);
      setActiveCaseDetail(response.data);
      return response.data;
    }, "No fue posible registrar el radicado manual.");

  const handleUploadEvidence = (caseId, file, note = "") =>
    withAction(async () => {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("note", note);
      const response = await api.post(`/cases/${caseId}/evidence`, formData, {
        ...withAuth(session.token),
        headers: {
          ...withAuth(session.token).headers,
          "Content-Type": "multipart/form-data",
        },
      });
      const detail = await api.get(`/cases/${caseId}`, withAuth(session.token));
      setActiveCaseDetail(detail.data);
      await refreshCollections(session.token, session.user.role);
      return response.data;
    }, "No fue posible subir la evidencia.");

  const handleInternalStatus = (caseId, payload) =>
    withAction(async () => {
      const response = await api.post(`/internal/cases/${caseId}/status`, payload, withAuth(session.token));
      await refreshCollections(session.token, session.user.role);
      setActiveCaseDetail(response.data);
      return response.data;
    }, "No fue posible actualizar el estado interno.");

  const handleLogout = () => {
    syncSession(null);
    setCases([]);
    setInternalCases([]);
    setActiveCaseDetail(null);
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
              subtitle="Accede a tu panel para gestionar expedientes, pagos y radicaciones."
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
              subtitle="Primero activamos tu sesión. Luego completas el perfil jurídico obligatorio."
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
            <DashboardV2
              session={session}
              cases={cases}
              internalCases={internalCases}
              activeTab={activeTab}
              setActiveTab={setActiveTab}
              activeCaseDetail={activeCaseDetail}
              setDocumentCase={setDocumentCase}
              onLogout={handleLogout}
              onSaveProfile={handleSaveProfile}
              onPreview={handlePreview}
              onTempUpload={handleTempUpload}
              onCreateCase={handleCreateCase}
              onOpenCase={handleOpenCase}
              onConfirmPayment={handleConfirmPayment}
              onGenerateDocument={handleGenerateDocument}
              onSubmitCase={handleSubmitCase}
              onManualRadicado={handleManualRadicado}
              onUploadEvidence={handleUploadEvidence}
              onInternalStatus={handleInternalStatus}
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
