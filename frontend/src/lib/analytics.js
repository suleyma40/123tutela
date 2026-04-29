import { api } from "./api";

const SESSION_KEY = "marketing-session-id";
const FIRST_TOUCH_KEY = "marketing-first-touch";

const getSessionId = () => {
  let sessionId = localStorage.getItem(SESSION_KEY);
  if (!sessionId) {
    sessionId = `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
    localStorage.setItem(SESSION_KEY, sessionId);
  }
  return sessionId;
};

export const trackEvent = async (eventName, payload = {}) => {
  try {
    const params = new URLSearchParams(window.location.search || "");
    const currentTouch = {
      utm_source: params.get("utm_source") || "",
      utm_medium: params.get("utm_medium") || "",
      utm_campaign: params.get("utm_campaign") || "",
      utm_content: params.get("utm_content") || "",
      utm_term: params.get("utm_term") || "",
    };
    const hasCurrentUtm = Object.values(currentTouch).some(Boolean);
    if (hasCurrentUtm) {
      localStorage.setItem(FIRST_TOUCH_KEY, JSON.stringify(currentTouch));
    }
    const firstTouch = JSON.parse(localStorage.getItem(FIRST_TOUCH_KEY) || "{}");
    await api.post("/public/analytics/event", {
      session_id: getSessionId(),
      event_name: eventName,
      page_path: window.location.pathname,
      source: document.referrer || "",
      metadata: {
        ...firstTouch,
        ...currentTouch,
        ...payload,
      },
    });
  } catch {
    // Silent by design.
  }
};
