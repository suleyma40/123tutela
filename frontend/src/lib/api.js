import axios from "axios";

const API_URL =
  import.meta.env.VITE_API_URL ||
  (import.meta.env.PROD ? "https://api.123tutelaapp.com" : "http://localhost:8000");

export const api = axios.create({
  baseURL: API_URL,
});

export const withAuth = (token) => ({
  headers: {
    Authorization: `Bearer ${token}`,
  },
});

const normalizeDetail = (detail) => {
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === "string") return item;
        if (item?.msg) return item.msg;
        if (item?.detail) return item.detail;
        return JSON.stringify(item);
      })
      .filter(Boolean)
      .join(" | ");
  }
  if (detail && typeof detail === "object") {
    if (detail.detail) return normalizeDetail(detail.detail);
    if (detail.msg) return String(detail.msg);
    return JSON.stringify(detail);
  }
  return String(detail || "").trim();
};

const humanizePlatformError = (detail, fallback) => {
  const text = normalizeDetail(detail);
  const lowered = text.toLowerCase();
  if (!text) return fallback;
  if (lowered.includes("jurisprudencia") || lowered.includes("soporte oficial verificado")) {
    return "La IA esta reforzando internamente el sustento juridico del borrador para que quede listo para entrega.";
  }
  if (lowered.includes("string should have at most") || lowered.includes("at most 6000 characters")) {
    return "El relato consolidado quedo demasiado largo para el analisis inicial. Vamos a resumirlo mejor en el siguiente intento.";
  }
  return text;
};

export const extractError = (error, fallback) =>
  humanizePlatformError(error?.response?.data?.detail || error?.message, fallback);
