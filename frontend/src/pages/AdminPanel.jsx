import React, { useEffect, useState } from 'react';
import { LayoutDashboard, Users, FileText, CheckCircle, Clock, Search, Filter, Eye, DollarSign, Activity } from 'lucide-react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { api } from '../lib/api';

const AdminPanel = () => {
  const [casos, setCasos] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [isLoggedIn, setIsLoggedIn] = useState(!!localStorage.getItem('admin-token'));
  const [loginForm, setLoginForm] = useState({ email: '', password: '' });
  const [loginError, setLoginError] = useState('');

  useEffect(() => {
    if (isLoggedIn) {
      fetchCasos();
    }
  }, [isLoggedIn]);

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setLoginError('');
    try {
      const response = await api.post('/auth/login', loginForm);
      localStorage.setItem('admin-token', response.data.token);
      setIsLoggedIn(true);
    } catch (err) {
      setLoginError("Credenciales inválidas o no tienes permisos de admin.");
    } finally {
      setLoading(false);
    }
  };

  const fetchCasos = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('admin-token');
      const response = await api.get('/internal/cases', {
        headers: { Authorization: `Bearer ${token}` }
      });
      setCasos(response.data);
    } catch (error) {
      console.error("Error fetching cases:", error);
      if (error.response?.status === 401) {
        setIsLoggedIn(false);
        localStorage.removeItem('admin-token');
      }
    } finally {
      setLoading(false);
    }
  };

  const filteredCasos = casos.filter(c => 
    (c.user_name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
    (c.user_email || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
    (c.target_entity || '').toLowerCase().includes(searchTerm.toLowerCase())
  );

  const stats = {
    total: casos.length,
    ventas: casos.filter(c => c.payment_status === 'pagado').length,
    pendientes: casos.filter(c => c.status !== 'entregado').length,
    totalIngresos: casos.filter(c => c.payment_status === 'pagado').length * 59900
  };

  if (!isLoggedIn) {
    return (
      <div className="min-h-screen bg-brand flex items-center justify-center px-6">
        <motion.div initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} className="bg-white p-8 md:p-12 rounded-[2.5rem] shadow-2xl max-w-md w-full">
          <div className="flex items-center gap-3 mb-8 justify-center">
            <div className="bg-brand p-2 rounded-lg">
              <LayoutDashboard className="text-accent w-6 h-6" />
            </div>
            <span className="font-headings text-2xl font-extrabold text-brand tracking-tight">Admin Login</span>
          </div>
          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="text-xs font-bold text-brand/40 uppercase ml-1">Email</label>
              <input 
                type="email" 
                className="input-field mt-1" 
                placeholder="admin@hazlopormi.com"
                value={loginForm.email}
                onChange={e => setLoginForm({...loginForm, email: e.target.value})}
                required
              />
            </div>
            <div>
              <label className="text-xs font-bold text-brand/40 uppercase ml-1">Contraseña</label>
              <input 
                type="password" 
                className="input-field mt-1" 
                placeholder="••••••••"
                value={loginForm.password}
                onChange={e => setLoginForm({...loginForm, password: e.target.value})}
                required
              />
            </div>
            {loginError && <p className="text-red-600 text-xs font-bold text-center">{loginError}</p>}
            <button type="submit" disabled={loading} className="btn-primary w-full py-4 text-lg">
              {loading ? "Entrando..." : "Entrar al Panel"}
            </button>
          </form>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Sidebar */}
      <aside className="w-64 bg-brand text-white p-6 hidden md:block shrink-0">
        <div className="flex items-center gap-2 mb-12">
          <div className="bg-accent p-1.5 rounded">
            <LayoutDashboard className="text-brand w-5 h-5" />
          </div>
          <span className="font-headings font-bold text-lg">123tutela Admin</span>
        </div>
        
        <nav className="space-y-2">
          <Link to="/admin" className="flex items-center gap-3 bg-white/10 p-3 rounded-xl font-bold">
            <FileText size={20} /> Casos
          </Link>
          <button className="w-full flex items-center gap-3 hover:bg-white/5 p-3 rounded-xl font-medium transition-colors">
            <Users size={20} /> Clientes
          </button>
          <button className="w-full flex items-center gap-3 hover:bg-white/5 p-3 rounded-xl font-medium transition-colors">
            <DollarSign size={20} /> Ventas
          </button>
        </nav>
      </aside>

      {/* Main Content */}
      <main className="flex-1 p-8 overflow-auto">
        <header className="flex justify-between items-center mb-12">
          <h1 className="text-3xl font-extrabold text-brand">Panel de Gestión</h1>
          <div className="flex items-center gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
              <input 
                type="text" 
                placeholder="Buscar por cliente o entidad..." 
                className="bg-white border border-gray-200 rounded-xl pl-10 pr-4 py-2 w-64 focus:outline-none focus:ring-2 focus:ring-accent"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            <button className="bg-white p-2 rounded-xl border border-gray-200 hover:bg-gray-50">
              <Filter size={20} className="text-gray-600" />
            </button>
          </div>
        </header>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-12">
          <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
            <p className="text-gray-500 font-bold text-xs uppercase mb-1">Total Interacciones</p>
            <p className="text-3xl font-extrabold text-brand">{stats.total}</p>
          </div>
          <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
            <p className="text-gray-500 font-bold text-xs uppercase mb-1">Ventas (Pagos)</p>
            <p className="text-3xl font-extrabold text-accent">{stats.ventas}</p>
          </div>
          <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
            <p className="text-gray-500 font-bold text-xs uppercase mb-1">Ingresos Brutos</p>
            <p className="text-3xl font-extrabold text-success">
              ${stats.totalIngresos.toLocaleString()}
            </p>
          </div>
          <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
            <p className="text-gray-500 font-bold text-xs uppercase mb-1">Pendientes</p>
            <p className="text-3xl font-extrabold text-orange-500">{stats.pendientes}</p>
          </div>
        </div>

        {/* Table */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
          <table className="w-full text-left">
            <thead className="bg-gray-50 border-b border-gray-100">
              <tr>
                <th className="px-6 py-4 font-bold text-gray-600 text-xs uppercase">Cliente</th>
                <th className="px-6 py-4 font-bold text-gray-600 text-xs uppercase">Entidad</th>
                <th className="px-6 py-4 font-bold text-gray-600 text-xs uppercase">Categoría</th>
                <th className="px-6 py-4 font-bold text-gray-600 text-xs uppercase">Pago</th>
                <th className="px-6 py-4 font-bold text-gray-600 text-xs uppercase">Estado</th>
                <th className="px-6 py-4 font-bold text-gray-600 text-xs uppercase">Acción</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {loading ? (
                <tr><td colSpan="6" className="px-6 py-12 text-center text-gray-400 font-medium">Cargando base de datos...</td></tr>
              ) : filteredCasos.length === 0 ? (
                <tr><td colSpan="6" className="px-6 py-12 text-center text-gray-400 font-medium">No se encontraron registros</td></tr>
              ) : filteredCasos.map(caso => (
                <tr key={caso.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-6 py-4">
                    <p className="font-bold text-brand">{caso.user_name || 'Anónimo'}</p>
                    <p className="text-xs text-gray-400">{caso.user_email}</p>
                  </td>
                  <td className="px-6 py-4 font-medium text-sm text-brand/80">
                    {caso.target_entity || 'N/A'}
                  </td>
                  <td className="px-6 py-4">
                    <span className="text-[10px] font-black bg-brand/5 text-brand px-2 py-1 rounded-full uppercase">
                      {caso.category}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`text-[10px] font-black px-2 py-1 rounded-full uppercase ${
                      caso.payment_status === 'pagado' ? 'bg-success/10 text-success' : 'bg-gray-100 text-gray-400'
                    }`}>
                      {caso.payment_status}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`text-[10px] font-black px-2 py-1 rounded-full uppercase ${
                      caso.status === 'entregado' ? 'bg-blue-100 text-blue-600' : 'bg-orange-100 text-orange-600'
                    }`}>
                      {caso.status}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <Link to={`/admin/caso/${caso.id}`} className="text-brand hover:text-accent p-2 rounded-lg hover:bg-brand/5 transition-colors inline-block">
                      <Eye size={20} />
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </main>
    </div>
  );
};

export default AdminPanel;
