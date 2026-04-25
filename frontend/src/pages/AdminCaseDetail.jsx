import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, ExternalLink, Paperclip } from 'lucide-react';
import { api } from '../lib/api';

const AdminCaseDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [caso, setCaso] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isUpdating, setIsUpdating] = useState(false);

  useEffect(() => {
    fetchCaso();
  }, [id]);

  const fetchCaso = async () => {
    try {
      const token = localStorage.getItem('admin-token');
      const response = await api.get(`/internal/cases/${id}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setCaso(response.data);
    } catch (error) {
      if (error.response?.status === 401) navigate('/admin');
    } finally {
      setLoading(false);
    }
  };

  const handleStatusUpdate = async (newStatus) => {
    setIsUpdating(true);
    try {
      const token = localStorage.getItem('admin-token');
      await api.post(`/internal/cases/${id}/status`, { status: newStatus }, {
        headers: { Authorization: `Bearer ${token}` },
      });
      fetchCaso();
    } finally {
      setIsUpdating(false);
    }
  };

  if (loading) return <div className="min-h-screen bg-[#F5F7FB] p-20 text-center font-black text-slate-900">Cargando detalle del caso...</div>;
  if (!caso) return <div className="min-h-screen bg-[#F5F7FB] p-20 text-center font-black text-red-600">Caso no encontrado</div>;

  const c = caso.case;

  return (
    <div className="min-h-screen bg-[#F5F7FB] text-slate-900">
      <main className="max-w-7xl mx-auto px-6 py-10">
        <header className="flex justify-between items-start gap-6 flex-wrap mb-10">
          <div className="flex items-start gap-4">
            <button onClick={() => navigate('/admin')} className="rounded-2xl border border-slate-200 bg-white p-3">
              <ArrowLeft size={20} />
            </button>
            <div>
              <p className="text-xs font-black uppercase tracking-[0.18em] text-slate-400 mb-2">Expediente</p>
              <h1 className="text-4xl font-black">Detalle del caso</h1>
              <div className="flex items-center gap-3 mt-3 flex-wrap">
                <span className="rounded-full bg-slate-100 px-3 py-1 text-[11px] font-black uppercase text-slate-600">{c.category}</span>
                <span className={`rounded-full px-3 py-1 text-[11px] font-black uppercase ${c.status === 'entregado' ? 'bg-emerald-50 text-emerald-600' : 'bg-amber-50 text-amber-600'}`}>{c.status}</span>
              </div>
            </div>
          </div>

          <select
            className="rounded-2xl border border-slate-200 bg-white px-4 py-3 font-bold outline-none"
            value={c.status}
            disabled={isUpdating}
            onChange={(e) => handleStatusUpdate(e.target.value)}
          >
            <option value="checkout_pendiente">Pendiente checkout</option>
            <option value="pagado_pendiente_intake">Pagado sin formulario</option>
            <option value="en_revision">En revision humana</option>
            <option value="entregado">Entregado</option>
          </select>
        </header>

        <div className="grid lg:grid-cols-[0.9fr_1.1fr] gap-8">
          <div className="grid gap-6">
            <div className="rounded-[24px] border border-slate-200 bg-white p-6">
              <p className="text-xs font-black uppercase tracking-wide text-slate-400 mb-4">Cliente</p>
              <div className="grid gap-3 text-sm">
                <p><strong className="text-slate-500">Nombre:</strong> {c.user_name || 'No suministrado'}</p>
                <p><strong className="text-slate-500">Correo:</strong> {c.user_email}</p>
                <p><strong className="text-slate-500">Telefono:</strong> {c.user_phone || 'N/A'}</p>
                <p><strong className="text-slate-500">Documento:</strong> {c.user_document || 'N/A'}</p>
              </div>
            </div>

            <div className="rounded-[24px] border border-slate-200 bg-white p-6">
              <p className="text-xs font-black uppercase tracking-wide text-slate-400 mb-4">Diagnostico</p>
              <div className="grid gap-3 text-sm">
                <p><strong className="text-slate-500">Accion sugerida:</strong> {c.recommended_action}</p>
                <p><strong className="text-slate-500">Entidad:</strong> {c.target_entity}</p>
                <p><strong className="text-slate-500">Pago:</strong> {c.payment_status}</p>
              </div>
            </div>

            {caso.latest_payment && (
              <div className="rounded-[24px] border border-slate-200 bg-white p-6">
                <p className="text-xs font-black uppercase tracking-wide text-slate-400 mb-4">Pago Wompi</p>
                <div className="grid gap-3 text-sm">
                  <p><strong className="text-slate-500">Referencia:</strong> {caso.latest_payment.reference}</p>
                  <p><strong className="text-slate-500">Monto:</strong> ${caso.latest_payment.amount_in_cents / 100}</p>
                  <p><strong className="text-slate-500">Estado:</strong> {caso.latest_payment.status}</p>
                </div>
              </div>
            )}
          </div>

          <div className="grid gap-6">
            <div className="rounded-[24px] border border-slate-200 bg-white p-6">
              <p className="text-xs font-black uppercase tracking-wide text-slate-400 mb-4">Relato del caso</p>
              <p className="rounded-[20px] border border-slate-200 bg-[#FCFDFF] p-5 text-sm leading-7 text-slate-600">
                {c.description}
              </p>
            </div>

            <div className="rounded-[24px] border border-slate-200 bg-white p-6">
              <p className="text-xs font-black uppercase tracking-wide text-slate-400 mb-4">Archivos adjuntos</p>
              {caso.files && caso.files.length > 0 ? (
                <div className="grid md:grid-cols-2 gap-4">
                  {caso.files.map((file) => (
                    <a
                      key={file.id}
                      href={`/public/files/${file.relative_path}`}
                      target="_blank"
                      rel="noreferrer"
                      className="flex items-center gap-3 rounded-2xl border border-slate-200 bg-[#FCFDFF] px-4 py-4 text-slate-700 no-underline"
                    >
                      <Paperclip size={16} />
                      <div className="overflow-hidden">
                        <p className="font-bold truncate">{file.original_name}</p>
                        <p className="text-[11px] uppercase text-slate-400 font-black">{file.file_kind}</p>
                      </div>
                      <ExternalLink size={14} className="ml-auto shrink-0" />
                    </a>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-slate-400 font-semibold">No hay archivos cargados para este caso.</p>
              )}
            </div>

            {c.facts?.intake_form && (
              <div className="rounded-[24px] border border-white/10 bg-[#08172E] p-6 text-white">
                <p className="text-xs font-black uppercase tracking-wide text-white/45 mb-4">Formulario completo</p>
                <div className="grid md:grid-cols-2 gap-6 text-sm">
                  <div>
                    <p className="text-white/45 font-black uppercase text-[11px] mb-2">Peticion concreta</p>
                    <p className="text-white/80 leading-6">{c.facts.intake_form.concrete_request}</p>
                  </div>
                  <div>
                    <p className="text-white/45 font-black uppercase text-[11px] mb-2">Detalles extra</p>
                    <p className="text-white/80 leading-6">{c.facts.intake_form.extra_details}</p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};

export default AdminCaseDetail;
