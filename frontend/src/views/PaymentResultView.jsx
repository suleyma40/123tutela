import React, { useEffect, useMemo, useState } from "react";
import { ArrowRight, CheckCircle2, Clock3, Scale, ShieldAlert, XCircle } from "lucide-react";

import { Badge, Button } from "../ui";
import { C } from "../theme";

const STATUS_COPY = {
  APPROVED: {
    label: "Pago aprobado",
    color: C.success,
    icon: CheckCircle2,
    description: "Tu pago fue confirmado. Ahora puedes volver al panel y continuar con el documento o la radicacion.",
  },
  DECLINED: {
    label: "Pago rechazado",
    color: C.danger,
    icon: XCircle,
    description: "La transaccion no fue aprobada. Puedes volver al panel e intentar con otro medio de pago.",
  },
  ERROR: {
    label: "Pago con error",
    color: C.warning,
    icon: ShieldAlert,
    description: "Wompi reporto un error procesando la transaccion. Te conviene revisar el estado final desde tu panel.",
  },
  PENDING: {
    label: "Pago en validacion",
    color: C.warning,
    icon: Clock3,
    description: "La transaccion sigue en revision. El estado final aparecera en tu expediente cuando Wompi confirme el resultado.",
  },
  VOIDED: {
    label: "Pago anulado",
    color: C.textMuted,
    icon: XCircle,
    description: "La transaccion fue anulada. Puedes volver al panel si deseas generar un nuevo intento de pago.",
  },
};

const formatMoney = (value) => {
  const amount = Number(value || 0);
  if (!Number.isFinite(amount) || amount <= 0) return null;
  return amount.toLocaleString("es-CO", { style: "currency", currency: "COP", maximumFractionDigits: 0 });
};

export default function PaymentResultView({ session, onReconcilePayment, onOpenDashboard, onLogin, onBackHome }) {
  const params = useMemo(() => new URLSearchParams(window.location.search), []);
  const [syncMessage, setSyncMessage] = useState("");
  const status = (params.get("status") || "PENDING").toUpperCase();
  const reference = params.get("reference");
  const transactionId = params.get("id") || params.get("transaction-id") || params.get("transaction_id");
  const amount = formatMoney(params.get("amount-in-cents") ? Number(params.get("amount-in-cents")) / 100 : null);
  const merchant = params.get("merchant_name") || "123tutela";
  const detail = STATUS_COPY[status] || STATUS_COPY.PENDING;
  const Icon = detail.icon;

  useEffect(() => {
    let cancelled = false;
    const reconcile = async () => {
      if (!session?.token || !transactionId || !onReconcilePayment) return;
      try {
        const result = await onReconcilePayment({ transaction_id: transactionId, reference });
        if (!cancelled && result?.status === "approved") {
          setSyncMessage("El pago ya fue sincronizado con tu expediente.");
        }
      } catch {
        if (!cancelled) {
          setSyncMessage("No fue posible sincronizar el pago automaticamente todavia. Revisa tu panel en unos segundos.");
        }
      }
    };
    reconcile();
    return () => {
      cancelled = true;
    };
  }, [session, transactionId, reference, onReconcilePayment]);

  return (
    <div style={{ minHeight: "100vh", background: "linear-gradient(180deg, #F4F7FB 0%, #EAF0F9 100%)", padding: 24 }}>
      <div style={{ maxWidth: 1100, margin: "0 auto" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12, padding: "8px 0 28px" }}>
          <div style={{ width: 40, height: 40, borderRadius: 12, background: C.primary, display: "grid", placeItems: "center", color: "#fff" }}>
            <Scale size={20} />
          </div>
          <strong style={{ fontSize: 24, color: C.text }}>123<span style={{ color: C.primary }}>tutela</span></strong>
        </div>

        <div className="glass-card" style={{ padding: 0, overflow: "hidden" }}>
          <div style={{ display: "grid", gridTemplateColumns: "0.95fr 1.05fr" }}>
            <div style={{ background: C.bgDark, color: "#fff", padding: "54px 44px", position: "relative" }}>
              <Badge color={detail.color}>{detail.label}</Badge>
              <h1 style={{ fontSize: 42, lineHeight: 1.05, margin: "22px 0 18px", fontWeight: 800, fontFamily: "'Playfair Display', serif" }}>
                Resultado del
                <br />
                pago en linea
              </h1>
              <p style={{ color: "rgba(255,255,255,0.72)", lineHeight: 1.8, maxWidth: 420 }}>
                {detail.description}
              </p>

              <div style={{ marginTop: 34, display: "grid", gap: 12 }}>
                <div style={{ padding: 18, borderRadius: 18, background: "rgba(255,255,255,0.06)", border: "1px solid rgba(255,255,255,0.08)" }}>
                  <div style={{ fontSize: 12, color: "rgba(255,255,255,0.62)", textTransform: "uppercase", letterSpacing: 0.8 }}>Comercio</div>
                  <div style={{ fontSize: 24, fontWeight: 800, marginTop: 6 }}>{merchant}</div>
                </div>
                {amount && (
                  <div style={{ padding: 18, borderRadius: 18, background: "rgba(255,255,255,0.06)", border: "1px solid rgba(255,255,255,0.08)" }}>
                    <div style={{ fontSize: 12, color: "rgba(255,255,255,0.62)", textTransform: "uppercase", letterSpacing: 0.8 }}>Valor</div>
                    <div style={{ fontSize: 34, fontWeight: 800, marginTop: 4 }}>{amount}</div>
                  </div>
                )}
              </div>
            </div>

            <div style={{ padding: "54px 44px" }}>
              <div style={{ width: 76, height: 76, borderRadius: 24, display: "grid", placeItems: "center", background: `${detail.color}18`, color: detail.color }}>
                <Icon size={42} />
              </div>
              <h2 style={{ fontSize: 32, fontWeight: 800, color: C.text, marginTop: 20 }}>Estado de la transaccion</h2>
              <p style={{ color: C.textMuted, marginTop: 10, lineHeight: 1.8 }}>
                Wompi devolvio este resultado para tu expediente. Si el pago ya fue aprobado, el panel te mostrara la activacion del caso y los siguientes pasos.
              </p>

              <div style={{ marginTop: 28, border: `1px solid ${C.border}`, borderRadius: 20, overflow: "hidden" }}>
                <div style={{ padding: "16px 20px", background: "#F8FBFF", borderBottom: `1px solid ${C.border}` }}>
                  <strong style={{ color: C.text }}>Resumen de la operacion</strong>
                </div>
                <div style={{ display: "grid", gap: 0 }}>
                  <div style={{ display: "grid", gridTemplateColumns: "180px 1fr", padding: "15px 20px", borderBottom: `1px solid ${C.border}` }}>
                    <span style={{ color: C.textMuted, fontWeight: 700 }}>Estado</span>
                    <span style={{ color: detail.color, fontWeight: 800 }}>{detail.label}</span>
                  </div>
                  <div style={{ display: "grid", gridTemplateColumns: "180px 1fr", padding: "15px 20px", borderBottom: `1px solid ${C.border}` }}>
                    <span style={{ color: C.textMuted, fontWeight: 700 }}>Referencia</span>
                    <span style={{ color: C.text }}>{reference || "Pendiente de sincronizar"}</span>
                  </div>
                  {amount && (
                    <div style={{ display: "grid", gridTemplateColumns: "180px 1fr", padding: "15px 20px" }}>
                      <span style={{ color: C.textMuted, fontWeight: 700 }}>Valor</span>
                      <span style={{ color: C.text }}>{amount}</span>
                    </div>
                  )}
                </div>
              </div>

              <div style={{ display: "flex", gap: 12, marginTop: 30, flexWrap: "wrap" }}>
                <Button size="lg" onClick={onOpenDashboard} icon={ArrowRight}>
                  Ir a mi panel
                </Button>
                <Button variant="outline" size="lg" onClick={onLogin}>
                  Iniciar sesion
                </Button>
                <Button variant="ghost" size="lg" onClick={onBackHome}>
                  Volver al inicio
                </Button>
              </div>

              <p style={{ marginTop: 16, color: C.textMuted, fontSize: 13 }}>
                Si acabas de pagar, el estado del expediente puede tardar unos segundos en reflejarse mientras llega la confirmacion segura del webhook.
              </p>
              {syncMessage && <p style={{ marginTop: 10, color: C.primary, fontSize: 13 }}>{syncMessage}</p>}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
