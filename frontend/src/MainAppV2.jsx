import React, { useEffect, useState } from "react";
import { AnimatePresence } from "framer-motion";

import { api, extractError, withAuth } from "./lib/api";
import AuthViewVision from "./views/AuthViewVision";
import DashboardV2 from "./views/DashboardV2";
import DocumentModal from "./views/DocumentModal";
import LandingVision from "./views/LandingVision";
import LegalPageView from "./views/LegalPageView";
import PaymentResultView from "./views/PaymentResultView";

const ROUTES = {
  landing: "/",
  login: "/login",
  register: "/register",
  dashboard: "/dashboard",
  payment_result: "/pago/resultado",
  terminos: "/terminos",
  privacidad: "/privacidad",
  contacto: "/contacto",
};

const pathToView = (pathname) => {
  if (pathname === ROUTES.login) return "login";
  if (pathname === ROUTES.register) return "register";
  if (pathname === ROUTES.dashboard) return "dashboard";
  if (pathname === ROUTES.payment_result) return "payment_result";
  if (pathname === ROUTES.terminos) return "terminos";
  if (pathname === ROUTES.privacidad) return "privacidad";
  if (pathname === ROUTES.contacto) return "contacto";
  return "landing";
};

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
  const [view, setView] = useState(() => pathToView(window.location.pathname));
  const [session, setSession] = useState(loadSession());
  const [cases, setCases] = useState([]);
  const [internalCases, setInternalCases] = useState([]);
  const [catalog, setCatalog] = useState([]);
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

  const navigate = (nextView, { replace = false } = {}) => {
    const target = ROUTES[nextView] || ROUTES.landing;
    if (window.location.pathname !== target) {
      const method = replace ? "replaceState" : "pushState";
      window.history[method]({}, "", target);
    }
    setView(nextView);
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
    const onPopState = () => setView(pathToView(window.location.pathname));
    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
  }, []);

  useEffect(() => {
    let cancelled = false;
    const loadCatalog = async () => {
      try {
        const response = await api.get("/catalog/products");
        if (!cancelled) {
          setCatalog(response.data || []);
        }
      } catch {
        if (!cancelled) {
          setCatalog([]);
        }
      }
    };
    loadCatalog();
    return () => {
      cancelled = true;
    };
  }, []);

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
          navigate("dashboard", { replace: true });
        }
      } catch {
        if (!cancelled) {
          syncSession(null);
          if (window.location.pathname === ROUTES.dashboard) {
            navigate("login", { replace: true });
          } else {
            setView(pathToView(window.location.pathname));
          }
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
      navigate("dashboard", { replace: true });
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

  const handleCreateWompiSession = (caseId, payload) =>
    withAction(async () => {
      const response = await api.post(`/cases/${caseId}/payments/wompi/session`, payload, withAuth(session.token));
      return response.data;
    }, "No fue posible iniciar el pago con Wompi.");

  const handleGetPayment = (reference) =>
    withAction(async () => {
      const response = await api.get(`/payments/${reference}`, withAuth(session.token));
      return response.data;
    }, "No fue posible consultar el estado del pago.");

  const handleReconcilePayment = (payload) =>
    withAction(async () => {
      const response = await api.post("/payments/wompi/reconcile", payload, withAuth(session.token));
      await refreshCollections(session.token, session.user.role);
      return response.data;
    }, "No fue posible reconciliar el pago con Wompi.");

  const handleRefreshCase = async (caseId, scope = "citizen") => {
    const endpoint = scope === "internal" ? `/internal/cases/${caseId}` : `/cases/${caseId}`;
    const response = await api.get(endpoint, withAuth(session.token));
    setActiveCaseDetail(response.data);
    await refreshCollections(session.token, session.user.role);
    return response.data;
  };

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
    navigate("landing", { replace: true });
  };

  return (
    <>
      <AnimatePresence mode="wait">
        {view === "landing" && (
          <div key="landing">
            <LandingVision
              onStart={() => navigate("register")}
              onLogin={() => navigate("login")}
              onLegalNavigate={(page) => navigate(page)}
            />
          </div>
        )}

        {view === "login" && (
          <div key="login">
            <AuthViewVision
              title="Iniciar sesión"
              subtitle="Accede a tu panel para gestionar expedientes, pagos y radicaciones."
              fields={[
                { name: "email", label: "Correo electrónico", type: "email", placeholder: "ejemplo@correo.com" },
                { name: "password", label: "Contraseña", type: "password", placeholder: "Mínimo 8 caracteres" },
              ]}
              onSubmit={(data) => handleAuth("/auth/login", data)}
              secondaryText="¿No tienes cuenta?"
              secondaryLabel="Regístrate aquí"
              secondaryAction={() => navigate("register")}
              onBack={() => navigate("landing")}
              loading={authLoading}
              error={authError}
            />
          </div>
        )}

        {view === "register" && (
          <div key="register">
            <AuthViewVision
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
              secondaryAction={() => navigate("login")}
              onBack={() => navigate("landing")}
              loading={authLoading}
              error={authError}
            />
          </div>
        )}

        {view === "payment_result" && (
          <div key="payment_result">
            <PaymentResultView
              session={session}
              onReconcilePayment={handleReconcilePayment}
              onOpenDashboard={() => navigate("dashboard", { replace: true })}
              onLogin={() => navigate("login", { replace: true })}
              onBackHome={() => navigate("landing", { replace: true })}
            />
          </div>
        )}

        {["terminos", "privacidad", "contacto"].includes(view) && (
          <div key={view}>
            <LegalPageView page={view} onBackHome={() => navigate("landing", { replace: true })} />
          </div>
        )}

        {view === "dashboard" && session && (
          <div key="dashboard">
            <DashboardV2
              session={session}
              cases={cases}
              internalCases={internalCases}
              catalog={catalog}
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
              onCreateWompiSession={handleCreateWompiSession}
              onGetPayment={handleGetPayment}
              onReconcilePayment={handleReconcilePayment}
              onRefreshCase={handleRefreshCase}
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
