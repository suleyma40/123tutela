import axios from "axios";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL: API_URL,
});

export const withAuth = (token) => ({
  headers: {
    Authorization: `Bearer ${token}`,
  },
});

const humanizePlatformError = (detail, fallback) => {
  const text = String(detail || "").trim();
  const lowered = text.toLowerCase();
  if (!text) return fallback;
  if (lowered.includes("jurisprudencia") || lowered.includes("soporte oficial verificado")) {
    return "La IA esta reforzando internamente el sustento juridico del borrador para que quede listo para entrega.";
  }
  return text;
};

export const extractError = (error, fallback) =>
  humanizePlatformError(error?.response?.data?.detail || error?.message, fallback);
