import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Save, Send, FileDown, Sparkles, User, Mail, MapPin, Building, Calendar, Shield, ExternalLink, Paperclip } from 'lucide-react';
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
        headers: { Authorization: `Bearer ${token}` }
      });
      setCaso(response.data);
    } catch (error) {
      console.error(error);
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
        headers: { Authorization: `Bearer ${token}` }
      });
      alert(`Estado actualizado a: ${newStatus}`);
      fetchCaso();
    } catch (error) {
      alert("Error actualizando estado");
    } finally {
      setIsUpdating(false);
    }
  };

  if (loading) return <div className="p-20 text-center font-bold text-brand">Cargando detalle del caso...</div>;
  if (!caso) return <div className="p-20 text-center text-red-500 font-bold">Caso no encontrado</div>;

  const c = caso.case;

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        <header className="flex justify-between items-center mb-8">
          <div className="flex items-center gap-4">
            <button onClick={() => navigate('/admin')} className="p-2 hover:bg-white rounded-xl transition-colors">
              <ArrowLeft size={24} />
            </button>
            <h1 className="text-2xl font-extrabold text-brand">Detalle del Caso</h1>
            <span className={`text-[10px] font-black px-3 py-1 rounded-full uppercase ${
              c.status === 'entregado' ? 'bg-success/10 text-success' : 'bg-orange-100 text-orange-600'
            }`}>
              {c.status}
            </span>
          </div>
          <div className="flex gap-3">
             <select 
               className="bg-white border border-gray-200 px-4 py-2 rounded-xl font-bold text-sm focus:outline-none"
               value={c.status}
               onChange={(e) => handleStatusUpdate(e.target.value)}
             >
                <option value="checkout_pendiente">Pendiente Checkout</option>
                <option value="pagado_pendiente_intake">Pagado (Sin Formulario)</option>
                <option value="en_revision">En Revisión Humana</option>
                <option value="entregado">Entregado</option>
             </select>
          </div>
        </header>

        <div className="grid lg:grid-cols-3 gap-8">
          {/* Info Column */}
          <div className="space-y-6">
            <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
              <h3 className="font-bold text-brand mb-4 flex items-center gap-2 border-b pb-2"><User size={18} className="text-accent"/> Información Cliente</h3>
              <div className="space-y-3 text-sm">
                <p><strong className="text-brand/40 uppercase text-[10px]">Nombre:</strong><br/> {c.user_name || 'No suministrado'}</p>
                <p><strong className="text-brand/40 uppercase text-[10px]">Correo:</strong><br/> {c.user_email}</p>
                <p><strong className="text-brand/40 uppercase text-[10px]">Teléfono:</strong><br/> {c.user_phone || 'N/A'}</p>
                <p><strong className="text-brand/40 uppercase text-[10px]">Cédula:</strong><br/> {c.user_document || 'N/A'}</p>
              </div>
            </div>

            <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
              <h3 className="font-bold text-brand mb-4 flex items-center gap-2 border-b pb-2"><Shield size={18} className="text-accent"/> Diagnóstico IA</h3>
              <div className="space-y-3 text-sm">
                <p><strong className="text-brand/40 uppercase text-[10px]">Acción Sugerida:</strong><br/> {c.recommended_action}</p>
                <p><strong className="text-brand/40 uppercase text-[10px]">Categoría:</strong><br/> {c.category}</p>
                <p><strong className="text-brand/40 uppercase text-[10px]">Entidad:</strong><br/> {c.target_entity}</p>
              </div>
            </div>

            {caso.latest_payment && (
              <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
                <h3 className="font-bold text-brand mb-4 flex items-center gap-2 border-b pb-2 text-success"><ExternalLink size={18}/> Pago Wompi</h3>
                <div className="space-y-3 text-sm">
                  <p><strong className="text-brand/40 uppercase text-[10px]">Referencia:</strong><br/> {caso.latest_payment.reference}</p>
                  <p><strong className="text-brand/40 uppercase text-[10px]">Monto:</strong><br/> ${caso.latest_payment.amount_in_cents / 100}</p>
                  <p><strong className="text-brand/40 uppercase text-[10px]">Estado:</strong><br/> {caso.latest_payment.status}</p>
                  {caso.latest_payment.raffle && (
                    <p className="bg-accent/10 p-2 rounded-lg font-bold text-accent">Rifa: {caso.latest_payment.raffle.code}</p>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Main Content Column */}
          <div className="lg:col-span-2 space-y-6">
            <div className="bg-white p-8 rounded-2xl shadow-sm border border-gray-100">
              <h3 className="font-bold text-brand mb-4 flex items-center gap-2">Descripción del Problema</h3>
              <p className="text-sm text-brand/70 leading-relaxed italic bg-gray-50 p-6 rounded-xl border border-gray-100">
                "{c.description}"
              </p>
            </div>

            <div className="bg-white p-8 rounded-2xl shadow-sm border border-gray-100">
              <h3 className="font-bold text-brand mb-6 flex items-center gap-2 border-b pb-4">Archivos Adjuntos</h3>
              {caso.files && caso.files.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {caso.files.map(file => (
                    <a 
                      key={file.id} 
                      href={`/public/files/${file.relative_path}`} 
                      target="_blank" 
                      rel="noreferrer"
                      className="flex items-center gap-3 p-4 border border-gray-100 rounded-xl hover:bg-brand/5 transition-colors group"
                    >
                      <Paperclip size={18} className="text-brand/30 group-hover:text-brand" />
                      <div className="overflow-hidden">
                        <p className="text-sm font-bold text-brand truncate">{file.original_name}</p>
                        <p className="text-[10px] text-brand/40 uppercase font-black">{file.file_kind}</p>
                      </div>
                    </a>
                  ))}
                </div>
              ) : (
                <p className="text-center py-8 text-brand/30 font-medium">No hay archivos cargados para este caso.</p>
              )}
            </div>

            {/* Facts and Intake Data */}
            {c.facts?.intake_form && (
               <div className="bg-brand text-white p-8 rounded-2xl shadow-sm">
                  <h3 className="font-bold mb-6 text-accent">Datos del Formulario Completo</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm">
                     <div>
                        <strong className="text-white/40 uppercase text-[10px]">Petición Concreta:</strong>
                        <p className="mt-1">{c.facts.intake_form.concrete_request}</p>
                     </div>
                     <div>
                        <strong className="text-white/40 uppercase text-[10px]">Detalles Extra:</strong>
                        <p className="mt-1">{c.facts.intake_form.extra_details}</p>
                     </div>
                  </div>
               </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminCaseDetail;
