import React, { useEffect, useState } from 'react';
import { Bot, Eye, Filter, LayoutDashboard, Search, TrendingUp } from 'lucide-react';
import { Link, useLocation } from 'react-router-dom';
import { api, extractError } from '../lib/api';
import { LAUNCH_PRICE_COP, RAFFLE_SHORT_LABEL } from '../lib/launchConfig';

const formatDateTime = (value) => {
  if (!value) return '';
  try {
    return new Date(value).toLocaleString('es-CO');
  } catch {
    return String(value);
  }
};

const escapeCsv = (value) => `"${String(value ?? '').replace(/"/g, '""')}"`;
const formatBogotaDateTime = (value) => {
  if (!value) return '-';
  try {
    return new Date(value).toLocaleString('es-CO', { timeZone: 'America/Bogota' });
  } catch {
    return String(value);
  }
};

const formatWaitingTime = (value, nowMs) => {
  if (!value) return '-';
  const createdMs = new Date(value).getTime();
  if (!Number.isFinite(createdMs)) return '-';
  const diffMs = Math.max(0, nowMs - createdMs);
  const totalMinutes = Math.floor(diffMs / 60000);
  const days = Math.floor(totalMinutes / 1440);
  const hours = Math.floor((totalMinutes % 1440) / 60);
  const minutes = totalMinutes % 60;
  if (days > 0) return `${days}d ${hours}h ${minutes}m`;
  if (hours > 0) return `${hours}h ${minutes}m`;
  return `${minutes}m`;
};

const AdminPanel = () => {
  const location = useLocation();
  const adminBasePath = location.pathname.startsWith('/equipo') ? '/equipo' : '/admin';
  const [casos, setCasos] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('todos');
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);
  const [checkingSession, setCheckingSession] = useState(true);
  const [loginForm, setLoginForm] = useState({ email: '', password: '', second_factor_code: '' });
  const [loginError, setLoginError] = useState('');
  const [requiresTwoFactor, setRequiresTwoFactor] = useState(false);
  const [panelError, setPanelError] = useState('');
  const [securityError, setSecurityError] = useState('');
  const [securityMessage, setSecurityMessage] = useState('');
  const [twoFactorSetup, setTwoFactorSetup] = useState(null);
  const [twoFactorCode, setTwoFactorCode] = useState('');
  const [recoveryCodes, setRecoveryCodes] = useState([]);
  const [recoveryCodesVisible, setRecoveryCodesVisible] = useState(false);
  const [twoFactorBusy, setTwoFactorBusy] = useState(false);
  const [marketing, setMarketing] = useState(null);
  const [configSaving, setConfigSaving] = useState(false);
  const [marketingConfigForm, setMarketingConfigForm] = useState({
    cta_variant: 'default',
    cta_label: '',
    raffle_label: '',
  });
  const [nowMs, setNowMs] = useState(Date.now());

  const handleLogout = async () => {
    try {
      await api.post('/auth/logout', {});
    } catch (_) {}
    setIsLoggedIn(false);
    setCurrentUser(null);
    setCasos([]);
    setPanelError('');
    setLoginError('');
    setLoginForm({ email: '', password: '', second_factor_code: '' });
    setRequiresTwoFactor(false);
    setTwoFactorSetup(null);
    setTwoFactorCode('');
    setRecoveryCodes([]);
    setRecoveryCodesVisible(false);
    setSecurityError('');
    setSecurityMessage('');
    setMarketing(null);
  };

  useEffect(() => {
    let alive = true;
    const bootstrapSession = async () => {
      try {
        const me = await api.get('/auth/me');
        if (alive && me?.data?.role === 'internal') {
          setIsLoggedIn(true);
          setCurrentUser(me.data);
        }
      } catch (_) {
        if (alive) {
          setIsLoggedIn(false);
          setCurrentUser(null);
        }
      } finally {
        if (alive) setCheckingSession(false);
      }
    };
    bootstrapSession();
    return () => {
      alive = false;
    };
  }, []);

  useEffect(() => {
    if (isLoggedIn) {
      fetchCasos();
      fetchMarketing();
    }
  }, [isLoggedIn]);

  useEffect(() => {
    if (!isLoggedIn) return;
    const interval = setInterval(() => {
      if (document.visibilityState === 'visible') {
        setNowMs(Date.now());
        fetchCasos();
        fetchMarketing();
      }
    }, 30 * 60 * 1000);
    return () => clearInterval(interval);
  }, [isLoggedIn]);

  useEffect(() => {
    if (!isLoggedIn) return;
    const timer = setInterval(() => setNowMs(Date.now()), 60 * 1000);
    return () => clearInterval(timer);
  }, [isLoggedIn]);

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setLoginError('');
    try {
      const payload = {
        email: loginForm.email,
        password: loginForm.password,
        otp_code: loginForm.second_factor_code || undefined,
        recovery_code: loginForm.second_factor_code || undefined,
      };
      const response = await api.post('/auth/login', payload);
      setIsLoggedIn(true);
      setCurrentUser(response.data.user);
      setRequiresTwoFactor(false);
      setLoginForm((current) => ({ ...current, second_factor_code: '' }));
    } catch (error) {
      const code = error?.response?.data?.detail?.code;
      if (code === '2fa_required' || code === '2fa_invalid') {
        setRequiresTwoFactor(true);
      }
      setLoginError(extractError(error, 'Credenciales invalidas o sin permisos de admin.'));
    } finally {
      setLoading(false);
    }
  };

  const fetchCasos = async () => {
    setLoading(true);
    setPanelError('');
    try {
      const response = await api.get('/internal/cases');
      setCasos(response.data);
    } catch (error) {
      if (error.response?.status === 401) {
        setIsLoggedIn(false);
        setCurrentUser(null);
        return;
      }
      if (error.response?.status === 403) {
        setPanelError('Tu usuario no tiene permisos internos para ver esta bandeja operativa.');
        setCasos([]);
        return;
      }
      setPanelError('No fue posible cargar los casos en este momento.');
    } finally {
      setLoading(false);
    }
  };

  const fetchMarketing = async () => {
    try {
      const response = await api.get('/internal/analytics/overview');
      setMarketing(response.data);
      const cfg = response.data?.marketing_config || {};
      setMarketingConfigForm({
        cta_variant: cfg.cta_variant || 'default',
        cta_label: cfg.cta_label || '',
        raffle_label: cfg.raffle_label || '',
      });
    } catch (error) {
      if (error.response?.status === 401) {
        setIsLoggedIn(false);
        setCurrentUser(null);
      }
    }
  };

  const saveMarketingConfig = async () => {
    setConfigSaving(true);
    try {
      await api.post('/internal/marketing/config', marketingConfigForm);
      await fetchMarketing();
    } finally {
      setConfigSaving(false);
    }
  };

  const handleQuickStatus = async (caseId, newStatus) => {
    try {
      await api.post(`/internal/cases/${caseId}/status`, { status: newStatus });
      await fetchCasos();
    } catch (error) {
      if (error.response?.status === 401) {
        setIsLoggedIn(false);
        setCurrentUser(null);
        return;
      }
      if (error.response?.status === 403) {
        setPanelError('Tu usuario no tiene permisos internos para actualizar estados.');
      }
    }
  };

  const startTwoFactorSetup = async () => {
    setTwoFactorBusy(true);
    setSecurityError('');
    setSecurityMessage('');
    setRecoveryCodes([]);
    try {
      const response = await api.post('/auth/2fa/setup', {});
      setTwoFactorSetup(response.data);
    } catch (error) {
      setSecurityError(extractError(error, 'No fue posible iniciar la configuracion de 2FA.'));
    } finally {
      setTwoFactorBusy(false);
    }
  };

  const confirmTwoFactorSetup = async () => {
    if (!twoFactorSetup?.secret) return;
    setTwoFactorBusy(true);
    setSecurityError('');
    setSecurityMessage('');
    try {
      const response = await api.post('/auth/2fa/enable', {
        secret: twoFactorSetup.secret,
        otp_code: twoFactorCode,
      });
      setCurrentUser(response.data.user);
      setRecoveryCodes(response.data.recovery_codes || []);
      setRecoveryCodesVisible((response.data.recovery_codes || []).length > 0);
      setTwoFactorSetup(null);
      setTwoFactorCode('');
      setSecurityMessage('Verificacion en 2 pasos activada. Guarda tus codigos de recuperacion.');
    } catch (error) {
      setSecurityError(extractError(error, 'No fue posible activar la verificacion en 2 pasos.'));
    } finally {
      setTwoFactorBusy(false);
    }
  };

  const disableTwoFactor = async () => {
    if (!twoFactorCode.trim()) {
      setSecurityError('Ingresa un codigo de Microsoft Authenticator o un codigo de recuperacion.');
      return;
    }
    setTwoFactorBusy(true);
    setSecurityError('');
    setSecurityMessage('');
    try {
      const response = await api.post('/auth/2fa/disable', {
        otp_code: twoFactorCode,
        recovery_code: twoFactorCode,
      });
      setCurrentUser(response.data);
      setTwoFactorSetup(null);
      setTwoFactorCode('');
      setRecoveryCodes([]);
      setRecoveryCodesVisible(false);
      setSecurityMessage('Verificacion en 2 pasos desactivada.');
    } catch (error) {
      setSecurityError(extractError(error, 'No fue posible desactivar 2FA.'));
    } finally {
      setTwoFactorBusy(false);
    }
  };

  const isReadyForHuman = (caso) =>
    caso.payment_status === 'pagado' && ['pagado_en_revision', 'en_revision'].includes(caso.status);

  useEffect(() => {
    if (!recoveryCodesVisible || recoveryCodes.length === 0) return;
    const timeout = setTimeout(() => {
      setRecoveryCodesVisible(false);
      setRecoveryCodes([]);
      setSecurityMessage('Codigos de recuperacion ocultos por seguridad.');
    }, 2 * 60 * 1000);
    return () => clearTimeout(timeout);
  }, [recoveryCodesVisible, recoveryCodes.length]);

  const filteredCasos = casos.filter((c) =>
    (c.user_name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
    (c.user_email || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
    (c.target_entity || '').toLowerCase().includes(searchTerm.toLowerCase())
  ).filter((c) => {
    if (statusFilter === 'todos') return true;
    if (statusFilter === 'cola') return c.payment_status === 'pagado' && c.status !== 'entregado';
    if (statusFilter === 'listos_humano') return isReadyForHuman(c);
    return c.status === statusFilter;
  });

  const stats = {
    total: casos.length,
    ventas: casos.filter((c) => c.payment_status === 'pagado').length,
    pendientes: casos.filter((c) => c.status !== 'entregado').length,
    listosHumano: casos.filter((c) => isReadyForHuman(c)).length,
    totalIngresos: casos.filter((c) => c.payment_status === 'pagado').length * LAUNCH_PRICE_COP,
  };
  const eventCounts = marketing?.event_counts || {};
  const funnel = marketing?.funnel || {};
  const topPages = marketing?.top_pages || [];
  const recommendations = marketing?.marketing_agent || [];
  const comparison = marketing?.comparison || {};
  const dropAlerts = marketing?.drop_alerts || [];
  const channels = marketing?.channels_7d || [];
  const campaigns = marketing?.campaigns_7d || [];
  const pct = (num, den) => (den > 0 ? `${Math.round((num / den) * 100)}%` : '0%');
  const deltaPct = (a, b) => (b > 0 ? `${Math.round(((a - b) / b) * 100)}%` : '0%');
  const readyCases = casos
    .filter((c) => isReadyForHuman(c))
    .sort((a, b) => new Date(a.updated_at || a.created_at || 0) - new Date(b.updated_at || b.created_at || 0));

  const paidCases = casos
    .filter((c) => c.payment_status === 'pagado')
    .map((c) => {
      const summary = c.submission_summary || {};
      return {
        caseId: c.id,
        name: c.user_name || '',
        email: c.user_email || '',
        phone: c.user_phone || '',
        category: c.category || '',
        action: c.recommended_action || '',
        paymentReference: c.payment_reference || '',
        expediente: summary?.customer_case?.code || '',
        raffleCode: summary?.raffle?.code || '',
        invoice: summary?.invoice?.number || '',
        paidAt: summary?.payment_summary?.approved_at || summary?.invoice?.issued_at || c.updated_at || c.created_at || '',
      };
    });

  const downloadPaidCasesCsv = () => {
    const headers = [
      'case_id',
      'nombre',
      'email',
      'telefono',
      'categoria',
      'documento_recomendado',
      'referencia_pago',
      'codigo_expediente',
      'codigo_rifa',
      'factura',
      'fecha_pago',
    ];
    const rows = paidCases.map((row) => [
      row.caseId,
      row.name,
      row.email,
      row.phone,
      row.category,
      row.action,
      row.paymentReference,
      row.expediente,
      row.raffleCode,
      row.invoice,
      formatDateTime(row.paidAt),
    ]);
    const csv = [headers, ...rows].map((line) => line.map(escapeCsv).join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    const today = new Date();
    const month = String(today.getMonth() + 1).padStart(2, '0');
    a.href = url;
    a.download = `participantes-rifa-${today.getFullYear()}-${month}.csv`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  };

  if (checkingSession) {
    return (
      <div className="min-h-screen bg-[#F5F7FB] flex items-center justify-center px-6">
        <div className="text-slate-500 font-semibold">Validando acceso...</div>
      </div>
    );
  }

  if (!isLoggedIn) {
    return (
      <div className="min-h-screen bg-[#F5F7FB] flex items-center justify-center px-6">
        <div className="w-full max-w-md rounded-[28px] border border-slate-200 bg-white p-8 shadow-[0_18px_55px_rgba(18,35,61,0.06)]">
          <div className="flex items-center gap-3 mb-8 justify-center">
            <div className="w-11 h-11 rounded-2xl bg-[linear-gradient(135deg,#0D68FF_0%,#19B7FF_100%)] grid place-items-center text-white">
              <LayoutDashboard className="w-5 h-5" />
            </div>
            <span className="text-2xl font-black text-slate-900">123tutela Admin</span>
          </div>
          <form onSubmit={handleLogin} className="grid gap-4">
            <label className="grid gap-2">
              <span className="text-xs font-black uppercase tracking-wide text-slate-400">Email</span>
              <input
                type="email"
                className="rounded-2xl border border-slate-200 px-4 py-4 outline-none"
                placeholder="admin@123tutelaapp.com"
                value={loginForm.email}
                onChange={(e) => setLoginForm({ ...loginForm, email: e.target.value })}
                required
              />
            </label>
            <label className="grid gap-2">
              <span className="text-xs font-black uppercase tracking-wide text-slate-400">Contraseña</span>
              <input
                type="password"
                className="rounded-2xl border border-slate-200 px-4 py-4 outline-none"
                value={loginForm.password}
                onChange={(e) => setLoginForm({ ...loginForm, password: e.target.value })}
                required
              />
            </label>
            {requiresTwoFactor && (
              <label className="grid gap-2">
                <span className="text-xs font-black uppercase tracking-wide text-slate-400">Codigo 2FA o recuperacion</span>
                <input
                  type="text"
                  className="rounded-2xl border border-slate-200 px-4 py-4 outline-none"
                  placeholder="123456 o ABCD-EF12"
                  value={loginForm.second_factor_code}
                  onChange={(e) => setLoginForm({ ...loginForm, second_factor_code: e.target.value })}
                  required
                />
              </label>
            )}
            {loginError && <p className="text-sm font-semibold text-red-600">{loginError}</p>}
            <button type="submit" disabled={loading} className="rounded-2xl bg-[#0D68FF] px-4 py-4 text-white font-black">
              {loading ? 'Entrando...' : requiresTwoFactor ? 'Validar y entrar' : 'Entrar al panel'}
            </button>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#F5F7FB] text-slate-900">
      <main className="max-w-7xl mx-auto px-6 py-10">
        <header className="flex justify-between items-start gap-6 flex-wrap mb-10">
          <div>
            <p className="text-xs font-black uppercase tracking-[0.2em] text-slate-400 mb-2">Panel operativo</p>
            <h1 className="text-4xl font-black">123tutela Admin</h1>
            <p className="text-slate-500 mt-3">Casos, pagos y seguimiento bajo el mismo lenguaje visual del producto.</p>
          </div>
          <div className="flex items-center gap-3 flex-wrap">
            <a
              href="#mercadeo"
              className="rounded-2xl bg-[#0D68FF] px-4 py-3 text-sm font-black text-white no-underline hover:bg-[#0B5BE0]"
            >
              Ir a Mercadeo
            </a>
            <div className="relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
              <input
                type="text"
                placeholder="Buscar cliente o entidad"
                className="rounded-2xl border border-slate-200 bg-white pl-11 pr-4 py-3 w-72 outline-none"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            <div className="rounded-2xl border border-slate-200 bg-white px-3 py-2 flex items-center gap-2">
              <Filter size={16} className="text-slate-500" />
              <select
                className="bg-transparent outline-none text-sm font-bold text-slate-600"
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
              >
                <option value="todos">Todos</option>
                <option value="cola">Cola operativa</option>
                <option value="listos_humano">Listos para humano</option>
                <option value="pagado_en_revision">Pagado en revision</option>
                <option value="en_revision">En revision</option>
                <option value="entregado">Entregado</option>
              </select>
            </div>
            <button
              onClick={handleLogout}
              className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-black text-slate-600 hover:bg-slate-50"
            >
              Cerrar sesion
            </button>
          </div>
        </header>

        <section className="grid md:grid-cols-5 gap-5 mb-10">
          {[
            { label: 'Total interacciones', value: stats.total, tone: 'text-slate-900' },
            { label: 'Pagos aprobados', value: stats.ventas, tone: 'text-[#0D68FF]' },
            { label: 'Ingresos brutos', value: `$${stats.totalIngresos.toLocaleString()}`, tone: 'text-[#0F766E]' },
            { label: 'Pendientes', value: stats.pendientes, tone: 'text-[#F97316]' },
            { label: 'Listos para humano', value: stats.listosHumano, tone: 'text-[#065F46]' },
          ].map((item) => (
            <div key={item.label} className="rounded-[24px] border border-slate-200 bg-white p-6 shadow-[0_18px_55px_rgba(18,35,61,0.04)]">
              <p className="text-xs font-black uppercase tracking-wide text-slate-400 mb-2">{item.label}</p>
              <p className={`text-3xl font-black ${item.tone}`}>{item.value}</p>
            </div>
          ))}
        </section>

        <section className="rounded-[24px] border border-slate-200 bg-white p-6 mb-8 shadow-[0_18px_55px_rgba(18,35,61,0.04)]">
          <div className="flex items-center justify-between gap-4 flex-wrap">
            <div>
              <p className="text-xs font-black uppercase tracking-wide text-slate-400 mb-1">Seguridad admin</p>
              <h2 className="text-xl font-black text-slate-900">Verificacion en 2 pasos</h2>
              <p className="text-sm text-slate-500 mt-1">
                Usuario actual: <strong>{currentUser?.email || 'sin correo'}</strong>
              </p>
            </div>
            <span className={`rounded-full px-4 py-2 text-xs font-black uppercase ${currentUser?.two_factor_enabled ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'}`}>
              {currentUser?.two_factor_enabled ? '2FA activo' : '2FA pendiente'}
            </span>
          </div>

          {!currentUser?.two_factor_enabled && !twoFactorSetup && (
            <div className="mt-4">
              <p className="text-sm text-slate-600 mb-4">
                Activalo con Microsoft Authenticator. En esta primera version puedes registrarlo con clave manual.
              </p>
              <button
                type="button"
                onClick={startTwoFactorSetup}
                disabled={twoFactorBusy}
                className="rounded-2xl bg-[#0D68FF] px-4 py-3 text-sm font-black text-white disabled:opacity-60"
              >
                {twoFactorBusy ? 'Preparando...' : 'Activar 2FA'}
              </button>
            </div>
          )}

          {!currentUser?.two_factor_enabled && twoFactorSetup && (
            <div className="mt-5 grid gap-4">
              <div className="rounded-2xl border border-slate-200 bg-[#F8FBFF] p-4">
                <p className="text-xs font-black uppercase tracking-wide text-slate-400 mb-2">Paso 1</p>
                <p className="text-sm text-slate-700">
                  En Microsoft Authenticator agrega una cuenta tipo <strong>Otro</strong> o <strong>Cuenta personal</strong> y usa esta clave:
                </p>
                <p className="mt-3 rounded-xl bg-white px-4 py-3 font-mono text-sm font-black text-[#0D68FF] break-all">
                  {twoFactorSetup.manual_entry_key}
                </p>
                <p className="mt-2 text-xs text-slate-500">Cuenta: {twoFactorSetup.account_label}</p>
              </div>
              <div className="rounded-2xl border border-slate-200 bg-white p-4">
                <p className="text-xs font-black uppercase tracking-wide text-slate-400 mb-2">Paso 2</p>
                <p className="text-sm text-slate-700 mb-3">Ingresa el codigo de 6 digitos para confirmar.</p>
                <div className="flex gap-3 flex-wrap">
                  <input
                    type="text"
                    className="rounded-2xl border border-slate-200 px-4 py-3 outline-none w-64"
                    placeholder="123456"
                    value={twoFactorCode}
                    onChange={(e) => setTwoFactorCode(e.target.value)}
                  />
                  <button
                    type="button"
                    onClick={confirmTwoFactorSetup}
                    disabled={twoFactorBusy}
                    className="rounded-2xl bg-emerald-600 px-4 py-3 text-sm font-black text-white disabled:opacity-60"
                  >
                    {twoFactorBusy ? 'Activando...' : 'Confirmar 2FA'}
                  </button>
                </div>
              </div>
            </div>
          )}

          {currentUser?.two_factor_enabled && (
            <div className="mt-5 grid gap-4">
              <p className="text-sm text-slate-600">
                Para desactivar 2FA, confirma con un codigo vigente de Microsoft Authenticator o con un codigo de recuperacion.
              </p>
              <div className="flex gap-3 flex-wrap">
                <input
                  type="text"
                  className="rounded-2xl border border-slate-200 px-4 py-3 outline-none w-72"
                  placeholder="123456 o ABCD-EF12"
                  value={twoFactorCode}
                  onChange={(e) => setTwoFactorCode(e.target.value)}
                />
                <button
                  type="button"
                  onClick={disableTwoFactor}
                  disabled={twoFactorBusy}
                  className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-black text-red-700 disabled:opacity-60"
                >
                  {twoFactorBusy ? 'Desactivando...' : 'Desactivar 2FA'}
                </button>
              </div>
            </div>
          )}

          {recoveryCodesVisible && recoveryCodes.length > 0 && (
            <div className="mt-5 rounded-2xl border border-amber-200 bg-amber-50 p-4">
              <div className="flex items-center justify-between gap-3 mb-2">
                <p className="text-sm font-black text-amber-800">Codigos de recuperacion</p>
                <button
                  type="button"
                  onClick={() => {
                    setRecoveryCodesVisible(false);
                    setRecoveryCodes([]);
                  }}
                  className="rounded-lg border border-amber-300 bg-white px-3 py-1 text-xs font-black uppercase text-amber-800"
                >
                  Ocultar
                </button>
              </div>
              <p className="text-sm text-amber-700 mb-3">Guardalos ahora. Se muestran una sola vez.</p>
              <div className="grid md:grid-cols-4 gap-2">
                {recoveryCodes.map((code) => (
                  <div key={code} className="rounded-xl bg-white px-3 py-2 font-mono text-sm font-black text-amber-800">
                    {code}
                  </div>
                ))}
              </div>
            </div>
          )}

          {securityError && <p className="mt-4 text-sm font-semibold text-red-600">{securityError}</p>}
          {securityMessage && <p className="mt-4 text-sm font-semibold text-emerald-700">{securityMessage}</p>}
        </section>

        <section className="rounded-[24px] border border-emerald-200 bg-emerald-50 p-6 mb-8 shadow-[0_18px_55px_rgba(18,35,61,0.04)]">
          <div className="flex items-center justify-between gap-4 flex-wrap mb-3">
            <div>
              <p className="text-xs font-black uppercase tracking-wide text-emerald-700 mb-1">Cola operativa humana</p>
              <h2 className="text-xl font-black text-emerald-900">Documentos listos para elaborar</h2>
            </div>
            <span className="rounded-full bg-emerald-600 px-4 py-2 text-xs font-black uppercase text-white">
              {readyCases.length} en cola
            </span>
          </div>
          <p className="text-sm text-emerald-800 mb-4">
            Estos casos ya tienen pago aprobado y están listos para realizar documento y enviarlo al usuario.
          </p>
          <div className="overflow-x-auto">
            <table className="w-full text-left min-w-[940px]">
              <thead>
                <tr className="border-b border-emerald-200">
                  <th className="py-2 text-xs font-black uppercase tracking-wide text-emerald-700">Cliente</th>
                  <th className="py-2 text-xs font-black uppercase tracking-wide text-emerald-700">Realizar documento</th>
                  <th className="py-2 text-xs font-black uppercase tracking-wide text-emerald-700">Codigo expediente</th>
                  <th className="py-2 text-xs font-black uppercase tracking-wide text-emerald-700">Estado</th>
                  <th className="py-2 text-xs font-black uppercase tracking-wide text-emerald-700">Tiempo esperando</th>
                  <th className="py-2 text-xs font-black uppercase tracking-wide text-emerald-700">Ultima actualizacion</th>
                  <th className="py-2 text-xs font-black uppercase tracking-wide text-emerald-700">Accion</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-emerald-100">
                {readyCases.length === 0 ? (
                  <tr>
                    <td colSpan="7" className="py-5 text-sm font-semibold text-emerald-700">
                      No hay casos listos para humano en este momento.
                    </td>
                  </tr>
                ) : readyCases.map((caso) => {
                  const summary = caso.submission_summary || {};
                  const expediente = summary?.customer_case?.code || caso.payment_reference || '-';
                  return (
                    <tr key={`ready-${caso.id}`}>
                      <td className="py-3">
                        <p className="font-black text-slate-900">{caso.user_name || 'Anonimo'}</p>
                        <p className="text-xs text-slate-500">{caso.user_email || '-'}</p>
                      </td>
                      <td className="py-3 text-sm font-semibold text-slate-700">{caso.recommended_action || '-'}</td>
                      <td className="py-3 text-sm font-black text-[#0D68FF]">{expediente}</td>
                      <td className="py-3">
                        <span className="rounded-full bg-emerald-600 px-3 py-1 text-[11px] font-black uppercase text-white">
                          Listo para realizar
                        </span>
                      </td>
                      <td className="py-3 text-sm font-black text-amber-700">{formatWaitingTime(caso.created_at, nowMs)}</td>
                      <td className="py-3 text-sm font-semibold text-slate-600">{formatBogotaDateTime(caso.updated_at || caso.created_at)}</td>
                      <td className="py-3">
                        <Link to={`${adminBasePath}/caso/${caso.id}`} className="inline-flex items-center gap-2 rounded-xl border border-emerald-300 bg-white px-3 py-2 text-emerald-700 no-underline">
                          <Eye size={16} />
                          Realizar / Enviar
                        </Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </section>

        <section id="mercadeo" className="rounded-[24px] border border-slate-200 bg-white p-6 mb-8 shadow-[0_18px_55px_rgba(18,35,61,0.04)]">
          <div className="flex items-center justify-between gap-4 flex-wrap mb-5">
            <div>
              <p className="text-xs font-black uppercase tracking-wide text-slate-400 mb-1">Inteligencia comercial</p>
              <h2 className="text-xl font-black text-slate-900">Analista de marketing</h2>
              <div className="mt-3 flex flex-wrap gap-2">
                <span className="rounded-full bg-slate-100 px-3 py-1 text-[11px] font-black uppercase text-slate-600">
                  Tarjetas de arriba: historico total de la app
                </span>
                <span className="rounded-full bg-blue-100 px-3 py-1 text-[11px] font-black uppercase text-blue-700">
                  Mercadeo: ultimos {marketing?.window_days || 30} dias
                </span>
                <span className="rounded-full bg-amber-100 px-3 py-1 text-[11px] font-black uppercase text-amber-700">
                  Actualizado: {formatBogotaDateTime(marketing?.updated_at)}
                </span>
              </div>
              <p className="text-sm text-slate-500 mt-1">
                Embudo real + recomendaciones automáticas para subir conversión.
              </p>
            </div>
            <button
              onClick={fetchMarketing}
              className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs font-black uppercase text-slate-600 hover:bg-slate-50"
            >
              Actualizar ahora
            </button>
          </div>

          <div className="grid md:grid-cols-5 gap-3 mb-5">
            {[
              ['Visitas', eventCounts.page_views || 0],
              ['Clicks CTA', eventCounts.cta_clicks || 0],
              ['Diagnósticos', eventCounts.diagnosis_starts || 0],
              ['Checkout', eventCounts.checkout_starts || 0],
              ['Intake enviado', eventCounts.intake_submissions || 0],
            ].map(([label, value]) => (
              <div key={label} className="rounded-xl border border-slate-200 bg-[#F8FBFF] p-3">
                <p className="text-[11px] font-black uppercase tracking-wide text-slate-400">{label}</p>
                <p className="text-2xl font-black text-slate-900 mt-1">{value}</p>
              </div>
            ))}
          </div>

          <div className="grid md:grid-cols-2 gap-3 mb-5">
            <div className="rounded-xl border border-slate-200 bg-[#F8FBFF] p-4">
              <p className="text-xs font-black uppercase tracking-wide text-slate-400 mb-2">Comparativo 7 días</p>
              <p className="text-sm text-slate-600">
                Diagnóstico: <strong>{comparison?.last_7d?.diagnosis_starts || 0}</strong> ({deltaPct(comparison?.last_7d?.diagnosis_starts || 0, comparison?.prev_7d?.diagnosis_starts || 0)} vs 7 días previos)
              </p>
              <p className="text-sm text-slate-600">
                Checkout: <strong>{comparison?.last_7d?.checkout_starts || 0}</strong> ({deltaPct(comparison?.last_7d?.checkout_starts || 0, comparison?.prev_7d?.checkout_starts || 0)} vs 7 días previos)
              </p>
            </div>
            <div className="rounded-xl border border-slate-200 bg-[#F8FBFF] p-4">
              <p className="text-xs font-black uppercase tracking-wide text-slate-400 mb-2">Comparativo 30 días</p>
              <p className="text-sm text-slate-600">
                Diagnóstico: <strong>{comparison?.last_30d?.diagnosis_starts || 0}</strong> ({deltaPct(comparison?.last_30d?.diagnosis_starts || 0, comparison?.prev_30d?.diagnosis_starts || 0)} vs 30 días previos)
              </p>
              <p className="text-sm text-slate-600">
                Intake enviado: <strong>{comparison?.last_30d?.intake_submissions || 0}</strong> ({deltaPct(comparison?.last_30d?.intake_submissions || 0, comparison?.prev_30d?.intake_submissions || 0)} vs 30 días previos)
              </p>
            </div>
          </div>

          <div className="grid lg:grid-cols-3 gap-4">
            <div className="rounded-xl border border-slate-200 p-4">
              <p className="text-sm font-black text-slate-900 mb-3 flex items-center gap-2"><TrendingUp size={16} /> Embudo operativo</p>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between"><span>Diagnóstico</span><strong>{funnel.diagnosed || 0}</strong></div>
                <div className="flex justify-between"><span>Checkout iniciado</span><strong>{funnel.checkout_started || 0} ({pct(funnel.checkout_started || 0, funnel.diagnosed || 0)})</strong></div>
                <div className="flex justify-between"><span>Pago aprobado</span><strong>{funnel.paid_cases || 0} ({pct(funnel.paid_cases || 0, funnel.checkout_started || 0)})</strong></div>
                <div className="flex justify-between"><span>Expediente enviado</span><strong>{funnel.intake_submitted || 0} ({pct(funnel.intake_submitted || 0, funnel.paid_cases || 0)})</strong></div>
                <div className="flex justify-between"><span>Documento entregado</span><strong>{funnel.delivered_cases || 0} ({pct(funnel.delivered_cases || 0, funnel.intake_submitted || 0)})</strong></div>
              </div>
            </div>

            <div className="rounded-xl border border-slate-200 p-4">
              <p className="text-sm font-black text-slate-900 mb-3">Páginas con más visitas</p>
              <div className="space-y-2">
                {topPages.length === 0 ? (
                  <p className="text-sm text-slate-400 font-semibold">Sin datos todavía.</p>
                ) : topPages.map((row) => (
                  <div key={row.page_path} className="flex justify-between text-sm">
                    <span className="text-slate-600 truncate max-w-[220px]">{row.page_path}</span>
                    <strong>{row.visits}</strong>
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-xl border border-slate-200 p-4 bg-[#08172E] text-white">
              <p className="text-sm font-black mb-3 flex items-center gap-2"><Bot size={16} /> Recomendaciones del agente</p>
              <div className="space-y-3">
                {recommendations.length === 0 ? (
                  <p className="text-sm text-white/70">Aún no hay suficientes señales para sugerencias.</p>
                ) : recommendations.map((item, idx) => (
                  <div key={`${item.title}-${idx}`} className="rounded-lg border border-white/15 bg-white/5 p-3">
                    <p className="text-xs font-black uppercase text-[#19B7FF]">{item.priority}</p>
                    <p className="font-bold mt-1">{item.title}</p>
                    <p className="text-sm text-white/80 mt-1">{item.action}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="grid lg:grid-cols-2 gap-4 mt-4">
            <div className="rounded-xl border border-slate-200 p-4">
              <p className="text-sm font-black text-slate-900 mb-3">Canales 7 días</p>
              <div className="space-y-2">
                {channels.length === 0 ? (
                  <p className="text-sm text-slate-400 font-semibold">Sin datos.</p>
                ) : channels.map((row) => (
                  <div key={row.key} className="flex justify-between text-sm">
                    <span className="text-slate-600">{row.key}</span>
                    <strong>D{row.diagnosis_starts} / C{row.checkout_starts}</strong>
                  </div>
                ))}
              </div>
            </div>
            <div className="rounded-xl border border-slate-200 p-4">
              <p className="text-sm font-black text-slate-900 mb-3">Campañas 7 días</p>
              <div className="space-y-2">
                {campaigns.length === 0 ? (
                  <p className="text-sm text-slate-400 font-semibold">Sin datos UTM todavía.</p>
                ) : campaigns.map((row) => (
                  <div key={row.key} className="flex justify-between text-sm">
                    <span className="text-slate-600">{row.key}</span>
                    <strong>D{row.diagnosis_starts} / C{row.checkout_starts}</strong>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {dropAlerts.length > 0 && (
            <div className="mt-4 rounded-xl border border-amber-200 bg-amber-50 p-4">
              <p className="text-sm font-black text-amber-800 mb-2">Alertas de caída detectadas</p>
              <div className="space-y-1 text-sm text-amber-700">
                {dropAlerts.map((alert, idx) => (
                  <p key={`${alert.label}-${idx}`}>• {alert.label}: {alert.stage} cayó {alert.drop_pct}%</p>
                ))}
              </div>
            </div>
          )}

          <div className="mt-4 rounded-xl border border-slate-200 p-4">
            <p className="text-sm font-black text-slate-900 mb-3">Acción semiautomática: copy/CTA</p>
            <div className="grid md:grid-cols-3 gap-3">
              <select
                className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-semibold"
                value={marketingConfigForm.cta_variant}
                onChange={(e) => setMarketingConfigForm({ ...marketingConfigForm, cta_variant: e.target.value })}
              >
                <option value="default">Default</option>
                <option value="urgencia">Urgencia</option>
                <option value="confianza">Confianza</option>
                <option value="sorteo">Sorteo</option>
              </select>
              <input
                type="text"
                className="rounded-xl border border-slate-200 px-3 py-2 text-sm"
                placeholder="Texto CTA principal"
                value={marketingConfigForm.cta_label}
                onChange={(e) => setMarketingConfigForm({ ...marketingConfigForm, cta_label: e.target.value })}
              />
              <input
                type="text"
                className="rounded-xl border border-slate-200 px-3 py-2 text-sm"
                placeholder="Texto franja rifa"
                value={marketingConfigForm.raffle_label}
                onChange={(e) => setMarketingConfigForm({ ...marketingConfigForm, raffle_label: e.target.value })}
              />
            </div>
            <p className="mt-3 text-xs font-semibold text-slate-500">
              Default actual: {RAFFLE_SHORT_LABEL}
            </p>
            <button
              onClick={saveMarketingConfig}
              disabled={configSaving}
              className="mt-3 rounded-xl bg-[#0D68FF] px-4 py-2 text-sm font-black text-white disabled:opacity-60"
            >
              {configSaving ? 'Guardando...' : 'Publicar variante'}
            </button>
          </div>
        </section>

        {panelError && (
          <div className="mb-6 rounded-2xl border border-amber-200 bg-amber-50 px-5 py-4 text-sm font-semibold text-amber-700">
            <div className="flex items-center justify-between gap-4 flex-wrap">
              <span>{panelError}</span>
              <button
                onClick={handleLogout}
                className="rounded-xl border border-amber-300 bg-white px-3 py-2 text-xs font-black uppercase text-amber-700 hover:bg-amber-100"
              >
                Ingresar con otro usuario
              </button>
            </div>
          </div>
        )}

        <section className="rounded-[28px] border border-slate-200 bg-white overflow-hidden shadow-[0_18px_55px_rgba(18,35,61,0.04)]">
          <table className="w-full text-left">
            <thead className="bg-[#F8FBFF] border-b border-slate-200">
              <tr>
                <th className="px-6 py-4 text-xs font-black uppercase tracking-wide text-slate-400">Cliente</th>
                <th className="px-6 py-4 text-xs font-black uppercase tracking-wide text-slate-400">Entidad</th>
                <th className="px-6 py-4 text-xs font-black uppercase tracking-wide text-slate-400">Categoria</th>
                <th className="px-6 py-4 text-xs font-black uppercase tracking-wide text-slate-400">Pago</th>
                <th className="px-6 py-4 text-xs font-black uppercase tracking-wide text-slate-400">Estado</th>
                <th className="px-6 py-4 text-xs font-black uppercase tracking-wide text-slate-400">Checklist</th>
                <th className="px-6 py-4 text-xs font-black uppercase tracking-wide text-slate-400">Accion</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr><td colSpan="7" className="px-6 py-16 text-center text-slate-400 font-semibold">Cargando base operativa...</td></tr>
              ) : filteredCasos.length === 0 ? (
                <tr><td colSpan="7" className="px-6 py-16 text-center text-slate-400 font-semibold">No se encontraron registros</td></tr>
              ) : filteredCasos.map((caso) => (
                <tr key={caso.id} className={`${isReadyForHuman(caso) ? 'bg-emerald-100/80 border-l-4 border-emerald-500' : ''} hover:bg-[#FCFDFF]`}>
                  <td className="px-6 py-5">
                    <p className="font-black text-slate-900">{caso.user_name || 'Anonimo'}</p>
                    <p className="text-xs text-slate-400 mt-1">{caso.user_email}</p>
                  </td>
                  <td className="px-6 py-5 text-sm text-slate-600 font-semibold">{caso.target_entity || 'N/A'}</td>
                  <td className="px-6 py-5">
                    <span className="rounded-full bg-slate-100 px-3 py-1 text-[11px] font-black uppercase text-slate-600">
                      {caso.category}
                    </span>
                  </td>
                  <td className="px-6 py-5">
                    <span className={`rounded-full px-3 py-1 text-[11px] font-black uppercase ${caso.payment_status === 'pagado' ? 'bg-emerald-50 text-emerald-600' : 'bg-slate-100 text-slate-500'}`}>
                      {caso.payment_status}
                    </span>
                  </td>
                  <td className="px-6 py-5">
                    <span className={`rounded-full px-3 py-1 text-[11px] font-black uppercase ${caso.status === 'entregado' ? 'bg-blue-50 text-blue-600' : 'bg-amber-50 text-amber-600'}`}>
                      {caso.status}
                    </span>
                    {isReadyForHuman(caso) && (
                      <span className="ml-2 rounded-full bg-emerald-600 px-3 py-1 text-[11px] font-black uppercase text-white">
                        Listo para humano
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-5">
                    <div className="flex flex-wrap gap-2">
                      <button
                        onClick={() => handleQuickStatus(caso.id, 'en_revision')}
                        className="rounded-lg border border-slate-200 px-2 py-1 text-[11px] font-black uppercase text-slate-600 hover:bg-slate-50"
                      >
                        Chulear revision
                      </button>
                      <button
                        onClick={() => handleQuickStatus(caso.id, 'entregado')}
                        className="rounded-lg border border-emerald-200 bg-emerald-50 px-2 py-1 text-[11px] font-black uppercase text-emerald-700 hover:bg-emerald-100"
                      >
                        Chulear enviado
                      </button>
                    </div>
                  </td>
                  <td className="px-6 py-5">
                    <Link to={`${adminBasePath}/caso/${caso.id}`} className="inline-flex items-center gap-2 rounded-xl border border-slate-200 px-3 py-2 text-slate-700 no-underline">
                      <Eye size={16} />
                      Ver
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        <section className="rounded-[24px] border border-slate-200 bg-white p-6 mt-8 mb-8 shadow-[0_18px_55px_rgba(18,35,61,0.04)]">
          <p className="text-xs font-black uppercase tracking-wide text-slate-400 mb-1">Estados operativos</p>
          <div className="grid md:grid-cols-4 gap-3 text-sm">
            <div className="rounded-xl bg-slate-50 p-3"><span className="font-black text-slate-700">Pagado en revisión:</span> pago confirmado, falta completar/validar expediente.</div>
            <div className="rounded-xl bg-slate-50 p-3"><span className="font-black text-slate-700">En revisión:</span> equipo interno redactando y preparando entrega.</div>
            <div className="rounded-xl bg-slate-50 p-3"><span className="font-black text-slate-700">Entregado:</span> documento final enviado al cliente.</div>
            <div className="rounded-xl bg-slate-50 p-3"><span className="font-black text-slate-700">Cola operativa:</span> todos los pagados que aún no están entregados.</div>
          </div>
        </section>

        <section className="rounded-[24px] border border-slate-200 bg-white p-6 mb-8 shadow-[0_18px_55px_rgba(18,35,61,0.04)]">
          <div className="flex items-center justify-between gap-4 flex-wrap">
            <div>
              <p className="text-xs font-black uppercase tracking-wide text-slate-400 mb-1">Rifa mensual</p>
              <h2 className="text-xl font-black text-slate-900">Participantes con pago aprobado</h2>
              <p className="text-sm text-slate-500 mt-1">
                {paidCases.length} registro(s) listo(s) para control interno y descarga mensual.
              </p>
            </div>
            <button
              type="button"
              onClick={downloadPaidCasesCsv}
              className="rounded-2xl bg-[#0D68FF] px-4 py-3 text-sm font-black text-white hover:bg-[#0B5BE0]"
              disabled={paidCases.length === 0}
            >
              Descargar base rifa (CSV)
            </button>
          </div>
          <div className="mt-5 overflow-x-auto">
            <table className="w-full text-left min-w-[860px]">
              <thead>
                <tr className="border-b border-slate-200">
                  <th className="py-3 text-xs font-black uppercase tracking-wide text-slate-400">Caso</th>
                  <th className="py-3 text-xs font-black uppercase tracking-wide text-slate-400">Nombre</th>
                  <th className="py-3 text-xs font-black uppercase tracking-wide text-slate-400">Documento</th>
                  <th className="py-3 text-xs font-black uppercase tracking-wide text-slate-400">Código rifa</th>
                  <th className="py-3 text-xs font-black uppercase tracking-wide text-slate-400">Pago</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {paidCases.length === 0 ? (
                  <tr>
                    <td colSpan="5" className="py-6 text-sm font-semibold text-slate-400">
                      Aún no hay pagos aprobados para rifa.
                    </td>
                  </tr>
                ) : paidCases.slice(0, 12).map((row) => (
                  <tr key={row.caseId}>
                    <td className="py-3 text-sm font-semibold text-slate-700">{row.caseId.slice(0, 8)}</td>
                    <td className="py-3 text-sm font-semibold text-slate-700">{row.name || '-'}</td>
                    <td className="py-3 text-sm font-semibold text-slate-700">{row.expediente || '-'}</td>
                    <td className="py-3 text-sm font-black text-[#0D68FF]">{row.raffleCode || '-'}</td>
                    <td className="py-3 text-sm font-semibold text-slate-700">{formatDateTime(row.paidAt) || '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </main>
    </div>
  );
};

export default AdminPanel;
