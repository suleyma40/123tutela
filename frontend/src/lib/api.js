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

export const extractError = (error, fallback) =>
  error?.response?.data?.detail || error?.message || fallback;
