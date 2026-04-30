const express = require("express");
const qrcode = require("qrcode");
const { Client, LocalAuth } = require("whatsapp-web.js");

const app = express();
app.use(express.json({ limit: "1mb" }));

const PORT = Number(process.env.PORT || 3000);
const API_KEY = String(process.env.WEBJS_API_KEY || "").trim();
const INSTANCE_NAME = String(process.env.WEBJS_INSTANCE || "123tutela").trim();

let qrText = "";
let ready = false;
let lastState = "booting";

const client = new Client({
  authStrategy: new LocalAuth({ clientId: INSTANCE_NAME }),
  puppeteer: {
    headless: true,
    args: ["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"],
    executablePath: process.env.PUPPETEER_EXECUTABLE_PATH || undefined,
  },
});

process.on("unhandledRejection", (reason) => {
  console.error("unhandledRejection", reason);
});

process.on("uncaughtException", (err) => {
  console.error("uncaughtException", err);
});

client.on("qr", (qr) => {
  qrText = qr;
  ready = false;
  lastState = "qr";
});

client.on("ready", () => {
  ready = true;
  lastState = "ready";
  qrText = "";
});

client.on("authenticated", () => {
  lastState = "authenticated";
});

client.on("auth_failure", () => {
  ready = false;
  lastState = "auth_failure";
});

client.on("disconnected", (reason) => {
  ready = false;
  lastState = `disconnected:${reason || "unknown"}`;
});

function normalizeNumber(raw) {
  const digits = String(raw || "").replace(/\D+/g, "");
  if (!digits) return "";
  if (digits.startsWith("57") && digits.length >= 12) return digits;
  if (digits.length === 10) return `57${digits}`;
  if (digits.startsWith("0") && digits.length === 11) return `57${digits.slice(1)}`;
  return digits;
}

function requireApiKey(req, res, next) {
  if (!API_KEY) return next();
  const incoming = String(req.header("x-api-key") || req.query.key || "");
  if (incoming !== API_KEY) {
    return res.status(401).json({ ok: false, error: "unauthorized" });
  }
  return next();
}

app.get("/health", (_req, res) => {
  res.json({ ok: true, state: lastState, ready });
});

app.get("/qr", requireApiKey, async (_req, res) => {
  if (!qrText) return res.json({ ok: true, state: lastState, qr_available: false });
  const dataUrl = await qrcode.toDataURL(qrText);
  return res.json({ ok: true, state: lastState, qr_available: true, qr_data_url: dataUrl });
});

app.post("/send", requireApiKey, async (req, res) => {
  try {
    if (!ready) {
      return res.status(409).json({ ok: false, error: "not_ready", state: lastState });
    }
    const number = normalizeNumber(req.body?.number);
    const text = String(req.body?.text || "").trim();
    if (!number || !text) {
      return res.status(400).json({ ok: false, error: "missing_number_or_text" });
    }
    const jid = `${number}@c.us`;
    const sent = await client.sendMessage(jid, text);
    return res.json({
      ok: true,
      to: number,
      message_id: sent?.id?._serialized || "",
      timestamp: sent?.timestamp || null,
      state: lastState,
    });
  } catch (error) {
    return res.status(500).json({ ok: false, error: String(error?.message || error) });
  }
});

app.post("/reconnect", requireApiKey, async (_req, res) => {
  try {
    await client.destroy();
  } catch (_) {}
  client.initialize().catch((error) => {
    console.error("initialize_error", error);
  });
  ready = false;
  lastState = "restarting";
  return res.json({ ok: true, state: lastState });
});

app.listen(PORT, () => {
  client.initialize().catch((error) => {
    console.error("initialize_error", error);
  });
});
