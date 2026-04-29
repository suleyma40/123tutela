import React, { useEffect, useState } from 'react';
import { DollarSign, Eye, Filter, LayoutDashboard, Search } from 'lucide-react';
import { Link, useLocation } from 'react-router-dom';
import { api } from '../lib/api';

const AdminPanel = () => {
  const location = useLocation();
  const adminBasePath = location.pathname.startsWith('/equipo') ? '/equipo' : '/admin';
  const [casos, setCasos] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('todos');
  const [isLoggedIn, setIsLoggedIn] = useState(!!localStorage.getItem('admin-token'));
  const [loginForm, setLoginForm] = useState({ email: '', password: '' });
  const [loginError, setLoginError] = useState('');
  const [panelError, setPanelError] = useState('');

  useEffect(() => {
    if (isLoggedIn) fetchCasos();
  }, [isLoggedIn]);

  useEffect(() => {
    if (!isLoggedIn) return;
    const interval = setInterval(() => {
      if (document.visibilityState === 'visible') fetchCasos();
    }, 10000);
    return () => clearInterval(interval);
  }, [isLoggedIn]);

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setLoginError('');
    try {
      const response = await api.post('/auth/login', loginForm);
      localStorage.setItem('admin-token', response.data.token);
      setIsLoggedIn(true);
    } catch {
      setLoginError('Credenciales invalidas o sin permisos de admin.');
    } finally {
      setLoading(false);
    }
  };

  const fetchCasos = async () => {
    setLoading(true);
    setPanelError('');
    try {
      const token = localStorage.getItem('admin-token');
      const response = await api.get('/internal/cases', {
        headers: { Authorization: `Bearer ${token}` },
      });
      setCasos(response.data);
    } catch (error) {
      if (error.response?.status === 401) {
        setIsLoggedIn(false);
        localStorage.removeItem('admin-token');
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

  const handleQuickStatus = async (caseId, newStatus) => {
    try {
      const token = localStorage.getItem('admin-token');
      await api.post(`/internal/cases/${caseId}/status`, { status: newStatus }, {
        headers: { Authorization: `Bearer ${token}` },
      });
      await fetchCasos();
    } catch (error) {
      if (error.response?.status === 401) {
        setIsLoggedIn(false);
        localStorage.removeItem('admin-token');
        return;
      }
      if (error.response?.status === 403) {
        setPanelError('Tu usuario no tiene permisos internos para actualizar estados.');
      }
    }
  };

  const filteredCasos = casos.filter((c) =>
    (c.user_name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
    (c.user_email || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
    (c.target_entity || '').toLowerCase().includes(searchTerm.toLowerCase())
  ).filter((c) => {
    if (statusFilter === 'todos') return true;
    if (statusFilter === 'cola') return c.payment_status === 'pagado' && c.status !== 'entregado';
    return c.status === statusFilter;
  });

  const stats = {
    total: casos.length,
    ventas: casos.filter((c) => c.payment_status === 'pagado').length,
    pendientes: casos.filter((c) => c.status !== 'entregado').length,
    totalIngresos: casos.filter((c) => c.payment_status === 'pagado').length * 49900,
  };

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
            {loginError && <p className="text-sm font-semibold text-red-600">{loginError}</p>}
            <button type="submit" disabled={loading} className="rounded-2xl bg-[#0D68FF] px-4 py-4 text-white font-black">
              {loading ? 'Entrando...' : 'Entrar al panel'}
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
                <option value="pagado_en_revision">Pagado en revision</option>
                <option value="en_revision">En revision</option>
                <option value="entregado">Entregado</option>
              </select>
            </div>
          </div>
        </header>

        <section className="grid md:grid-cols-4 gap-5 mb-10">
          {[
            { label: 'Total interacciones', value: stats.total, tone: 'text-slate-900' },
            { label: 'Pagos aprobados', value: stats.ventas, tone: 'text-[#0D68FF]' },
            { label: 'Ingresos brutos', value: `$${stats.totalIngresos.toLocaleString()}`, tone: 'text-[#0F766E]' },
            { label: 'Pendientes', value: stats.pendientes, tone: 'text-[#F97316]' },
          ].map((item) => (
            <div key={item.label} className="rounded-[24px] border border-slate-200 bg-white p-6 shadow-[0_18px_55px_rgba(18,35,61,0.04)]">
              <p className="text-xs font-black uppercase tracking-wide text-slate-400 mb-2">{item.label}</p>
              <p className={`text-3xl font-black ${item.tone}`}>{item.value}</p>
            </div>
          ))}
        </section>

        {panelError && (
          <div className="mb-6 rounded-2xl border border-amber-200 bg-amber-50 px-5 py-4 text-sm font-semibold text-amber-700">
            {panelError}
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
                <tr key={caso.id} className="hover:bg-[#FCFDFF]">
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
      </main>
    </div>
  );
};

export default AdminPanel;
