import React, { useEffect, useState } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { ArrowLeft, ExternalLink, Paperclip, Send } from 'lucide-react';
import { api } from '../lib/api';

const AdminCaseDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const adminBasePath = location.pathname.startsWith('/equipo') ? '/equipo' : '/admin';
  const [caso, setCaso] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isUpdating, setIsUpdating] = useState(false);
  const [deliveryFiles, setDeliveryFiles] = useState([]);
  const [deliveryNote, setDeliveryNote] = useState('');
  const [isSendingDelivery, setIsSendingDelivery] = useState(false);
  const [deliveryMessage, setDeliveryMessage] = useState('');
  const [transcribingByFile, setTranscribingByFile] = useState({});
  const [transcriptByFile, setTranscriptByFile] = useState({});

  useEffect(() => {
    fetchCaso();
  }, [id]);

  const fetchCaso = async () => {
    try {
      const response = await api.get(`/internal/cases/${id}`);
      setCaso(response.data);
    } catch (error) {
      if (error.response?.status === 401) navigate(adminBasePath);
    } finally {
      setLoading(false);
    }
  };

  const handleStatusUpdate = async (newStatus) => {
    setIsUpdating(true);
    try {
      await api.post(`/internal/cases/${id}/status`, { status: newStatus });
      fetchCaso();
    } finally {
      setIsUpdating(false);
    }
  };

  const handleUploadAndDeliver = async () => {
    if (!deliveryFiles.length) {
      setDeliveryMessage('Selecciona al menos un documento final (PDF o DOCX).');
      return;
    }
    setIsSendingDelivery(true);
    setDeliveryMessage('');
    try {
      const formData = new FormData();
      deliveryFiles.forEach((file) => {
        formData.append('files', file);
      });
      formData.append('delivery_note', deliveryNote || '');
      formData.append('send_whatsapp', 'false');
      const response = await api.post(`/internal/cases/${id}/deliver-upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      setCaso(response.data);
      setDeliveryFiles([]);
      setDeliveryNote('');
      setDeliveryMessage('Documentos enviados al cliente y caso marcado como entregado.');
    } catch (error) {
      const detail = error?.response?.data?.detail;
      let readable = 'No fue posible enviar el documento final.';
      if (typeof detail === 'string' && detail.trim()) {
        readable = detail;
      } else if (Array.isArray(detail) && detail.length) {
        readable = detail
          .map((item) => {
            if (typeof item === 'string') return item;
            if (item && typeof item === 'object') {
              const loc = Array.isArray(item.loc) ? item.loc.join('.') : '';
              const msg = item.msg ? String(item.msg) : JSON.stringify(item);
              return loc ? `${loc}: ${msg}` : msg;
            }
            return String(item);
          })
          .join(' | ');
      }
      setDeliveryMessage(readable);
    } finally {
      setIsSendingDelivery(false);
    }
  };

  if (loading) return <div className="min-h-screen bg-[#F5F7FB] p-20 text-center font-black text-slate-900">Cargando detalle del caso...</div>;
  if (!caso) return <div className="min-h-screen bg-[#F5F7FB] p-20 text-center font-black text-red-600">Caso no encontrado</div>;

  const c = caso.case;
  const intake = c.facts?.intake_form || {};
  const survey = c.facts?.survey_test || null;
  const trackingCode =
    caso.latest_payment?.raffle?.code ||
    caso.customer_summary?.raffle?.code ||
    caso.latest_payment?.reference ||
    c.payment_reference ||
    `EXP-${String(c.id || '').slice(0, 8).toUpperCase()}`;
  const audioFiles = (caso.files || []).filter((file) => {
    const name = String(file?.original_name || '').toLowerCase();
    const kind = String(file?.mime_type || '').toLowerCase();
    return kind.startsWith('audio/') || /\.(mp3|wav|m4a|aac|webm|ogg)$/i.test(name);
  });
  const deliveredFiles = (caso.files || []).filter((file) => String(file?.file_kind || '').toLowerCase() === 'delivery_document');

  const handleTranscribeAudio = async (fileId) => {
    setTranscribingByFile((current) => ({ ...current, [fileId]: true }));
    try {
      const response = await api.post(`/internal/cases/${id}/files/${fileId}/transcribe`);
      const transcript = String(response?.data?.transcript_text || '').trim();
      setTranscriptByFile((current) => ({ ...current, [fileId]: transcript }));
      await fetchCaso();
    } catch (error) {
      setTranscriptByFile((current) => ({
        ...current,
        [fileId]: `Error de transcripción: ${error?.response?.data?.detail || 'No fue posible transcribir.'}`,
      }));
    } finally {
      setTranscribingByFile((current) => ({ ...current, [fileId]: false }));
    }
  };

  return (
    <div className="min-h-screen bg-[#F5F7FB] text-slate-900">
      <main className="max-w-7xl mx-auto px-6 py-10">
        <header className="flex justify-between items-start gap-6 flex-wrap mb-10">
          <div className="flex items-start gap-4">
            <button onClick={() => navigate(adminBasePath)} className="rounded-2xl border border-slate-200 bg-white p-3">
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
                <p><strong className="text-slate-500">Tipo de documento:</strong> {c.recommended_action || c.workflow_type || 'N/A'}</p>
                <p><strong className="text-slate-500">Codigo de seguimiento:</strong> {trackingCode}</p>
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

            {survey && (
              <div className="rounded-[24px] border border-blue-200 bg-blue-50 p-6">
                <p className="text-xs font-black uppercase tracking-wide text-blue-700 mb-4">Analisis de encuesta</p>
                <div className="grid md:grid-cols-3 gap-3 text-sm">
                  <div className="rounded-xl bg-white p-3"><strong>Promedio:</strong> {survey.average_rating || '-'} / 5</div>
                  <div className="rounded-xl bg-white p-3"><strong>Uso:</strong> {survey.usage_probability || '-'} / 5</div>
                  <div className="rounded-xl bg-white p-3"><strong>Pago:</strong> {survey.would_pay || '-'}</div>
                  <div className="rounded-xl bg-white p-3"><strong>Lanzamiento:</strong> {String(survey.launch_readiness || '-').replaceAll('_', ' ')}</div>
                  <div className="rounded-xl bg-white p-3"><strong>Publicidad:</strong> {String(survey.advertising_confidence || '-').replaceAll('_', ' ')}</div>
                  <div className="rounded-xl bg-white p-3"><strong>Confianza:</strong> {survey.trust_rating || '-'} / 5</div>
                </div>
                <div className="mt-4 grid gap-3 text-sm">
                  <p className="rounded-xl bg-white p-3"><strong>Fallas:</strong> {survey.failures || 'No reportado'}</p>
                  <p className="rounded-xl bg-white p-3"><strong>Bloqueadores:</strong> {survey.blockers || 'No reportado'}</p>
                  <p className="rounded-xl bg-white p-3"><strong>Mejoras:</strong> {survey.improvement || 'No reportado'}</p>
                </div>
              </div>
            )}

            <div className="rounded-[24px] border border-slate-200 bg-white p-6">
              <p className="text-xs font-black uppercase tracking-wide text-slate-400 mb-4">Archivos adjuntos</p>
              {caso.files && caso.files.length > 0 ? (
                <div className="grid md:grid-cols-2 gap-4">
                  {caso.files.map((file) => {
                    const hasPath = Boolean(file?.relative_path);
                    return (
                      <div
                        key={file.id}
                        className="flex items-center gap-3 rounded-2xl border border-slate-200 bg-[#FCFDFF] px-4 py-4 text-slate-700"
                      >
                        <Paperclip size={16} />
                        <div className="overflow-hidden">
                          <p className="font-bold truncate">{file.original_name}</p>
                          <p className="text-[11px] uppercase text-slate-400 font-black">{file.file_kind}</p>
                          {!hasPath && <p className="text-[11px] text-red-500 font-semibold">Archivo sin ruta (revisar carga)</p>}
                        </div>
                        {hasPath && (
                          <a
                            href={`/public/files/${file.relative_path}`}
                            target="_blank"
                            rel="noreferrer"
                            className="ml-auto shrink-0 text-slate-600"
                            title="Abrir archivo"
                          >
                            <ExternalLink size={14} />
                          </a>
                        )}
                      </div>
                    );
                  })}
                </div>
              ) : (
                <p className="text-sm text-slate-400 font-semibold">No hay archivos cargados para este caso.</p>
              )}
            </div>

            {!!audioFiles.length && (
              <div className="rounded-[24px] border border-emerald-200 bg-emerald-50 p-6">
                <p className="text-xs font-black uppercase tracking-wide text-emerald-700 mb-3">Narracion en audio</p>
                <p className="text-sm text-emerald-800 mb-3">El equipo debe escuchar el audio completo. La transcripcion literal puede venir en formulario si el cliente la adjunto.</p>
                <div className="grid gap-2">
                  {audioFiles.map((file) => (
                    <div key={`audio-${file.id}`} className="rounded-xl border border-emerald-200 bg-white p-3">
                      <div className="flex items-center justify-between gap-3">
                        <a
                          href={file?.relative_path ? `/public/files/${file.relative_path}` : '#'}
                          target="_blank"
                          rel="noreferrer"
                          className="text-sm font-bold text-emerald-800 underline"
                        >
                          Escuchar/descargar: {file.original_name}
                        </a>
                        <button
                          type="button"
                          onClick={() => handleTranscribeAudio(file.id)}
                          disabled={Boolean(transcribingByFile[file.id])}
                          className="rounded-lg bg-emerald-600 px-3 py-2 text-xs font-black text-white disabled:opacity-60"
                        >
                          {transcribingByFile[file.id] ? 'Transcribiendo...' : 'Transcribir audio'}
                        </button>
                      </div>
                      {((file?.metadata || {}).transcript_text || transcriptByFile[file.id]) && (
                        <div className="mt-3 rounded-lg border border-emerald-100 bg-emerald-50 p-3">
                          <p className="text-[11px] font-black uppercase tracking-wide text-emerald-700 mb-1">Transcripción</p>
                          <p className="text-sm text-emerald-900 whitespace-pre-wrap">
                            {transcriptByFile[file.id] || (file?.metadata || {}).transcript_text}
                          </p>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

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

            <div className="rounded-[24px] border border-slate-200 bg-white p-6">
              <p className="text-xs font-black uppercase tracking-wide text-slate-400 mb-4">Ficha para redaccion humana</p>
              <div className="grid md:grid-cols-2 gap-4 text-sm">
                <p><strong className="text-slate-500">Nombre:</strong> {c.user_name || 'N/A'}</p>
                <p><strong className="text-slate-500">Documento:</strong> {c.user_document || intake.document_number || 'N/A'}</p>
                <p><strong className="text-slate-500">Codigo:</strong> {trackingCode}</p>
                <p><strong className="text-slate-500">Tipo:</strong> {c.recommended_action || c.workflow_type || 'N/A'}</p>
                <p><strong className="text-slate-500">Entidad:</strong> {c.target_entity || intake.target_entity || 'N/A'}</p>
                <p><strong className="text-slate-500">Ciudad:</strong> {c.user_city || intake.city || 'N/A'}</p>
              </div>
              <div className="mt-5 grid gap-4 text-sm">
                <div>
                  <p className="text-xs font-black uppercase tracking-wide text-slate-400 mb-1">Peticion concreta</p>
                  <p className="text-slate-700">{intake.concrete_request || 'N/A'}</p>
                </div>
                <div>
                  <p className="text-xs font-black uppercase tracking-wide text-slate-400 mb-1">Hechos del caso</p>
                  <p className="text-slate-700 whitespace-pre-wrap">{intake.case_story || c.description || 'N/A'}</p>
                </div>
                <div>
                  <p className="text-xs font-black uppercase tracking-wide text-slate-400 mb-1">Antecedentes clave</p>
                  <p className="text-slate-700 whitespace-pre-wrap">
                    {[
                      intake.prior_petition_same_cause ? `Peticion previa misma causa: ${intake.prior_petition_same_cause}` : '',
                      intake.prior_petition_date ? `Fecha peticion previa: ${intake.prior_petition_date}` : '',
                      intake.prior_petition_response ? `Respuesta entidad: ${intake.prior_petition_response}` : '',
                      intake.urgency_detail ? `Urgencia: ${intake.urgency_detail}` : '',
                    ].filter(Boolean).join('\n') || 'N/A'}
                  </p>
                </div>
              </div>
            </div>

            <div className="rounded-[24px] border border-emerald-200 bg-emerald-50 p-6">
              <p className="text-xs font-black uppercase tracking-wide text-emerald-700 mb-3">Entrega al usuario</p>
              <h3 className="text-xl font-black text-emerald-900 mb-3">Subir documento final y enviar</h3>
              <div className="grid gap-4">
                <input
                  type="file"
                  multiple
                  accept=".pdf,.doc,.docx,application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                  className="rounded-xl border border-emerald-200 bg-white px-3 py-3 text-sm"
                  onChange={(e) => {
                    const selected = Array.from(e.target.files || []);
                    if (!selected.length) return;
                    setDeliveryFiles((current) => {
                      const merged = [...current];
                      selected.forEach((file) => {
                        const key = `${file.name}::${file.size}::${file.lastModified}`;
                        const exists = merged.some(
                          (item) => `${item.name}::${item.size}::${item.lastModified}` === key,
                        );
                        if (!exists) merged.push(file);
                      });
                      return merged;
                    });
                    e.target.value = '';
                  }}
                />
                {!!deliveryFiles.length && (
                  <div className="rounded-xl border border-emerald-200 bg-white p-3">
                    <p className="text-xs font-bold text-emerald-800 mb-2">{deliveryFiles.length} archivo(s) listo(s) para envio:</p>
                    <div className="grid gap-2">
                      {deliveryFiles.map((file, index) => (
                        <div key={`${file.name}-${file.size}-${file.lastModified}`} className="flex items-center justify-between gap-3 rounded-lg border border-emerald-100 bg-emerald-50 px-3 py-2">
                          <p className="text-xs font-semibold text-emerald-900 truncate">{file.name}</p>
                          <button
                            type="button"
                            className="text-xs font-black text-red-600"
                            onClick={() => {
                              setDeliveryFiles((current) => current.filter((_, fileIndex) => fileIndex !== index));
                            }}
                          >
                            Quitar
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                <textarea
                  rows={3}
                  className="rounded-xl border border-emerald-200 bg-white px-3 py-3 text-sm outline-none"
                  placeholder="Nota opcional para el cliente"
                  value={deliveryNote}
                  onChange={(e) => setDeliveryNote(e.target.value)}
                />
                <button
                  type="button"
                  disabled={isSendingDelivery}
                  onClick={handleUploadAndDeliver}
                  className="inline-flex items-center justify-center gap-2 rounded-xl bg-emerald-600 px-4 py-3 text-sm font-black text-white disabled:opacity-60"
                >
                  <Send size={16} />
                  {isSendingDelivery ? 'Enviando...' : 'Enviar documento al cliente'}
                </button>
                {!!deliveryMessage && (
                  <p className="text-sm font-semibold text-emerald-800">{deliveryMessage}</p>
                )}
                {!!deliveredFiles.length && (
                  <div className="rounded-xl border border-emerald-200 bg-white p-3">
                    <p className="text-xs font-black uppercase tracking-wide text-emerald-700 mb-2">Documentos ya cargados en este caso</p>
                    <div className="grid gap-2">
                      {deliveredFiles.map((file) => (
                        <a
                          key={`delivered-${file.id}`}
                          href={file?.relative_path ? `/public/files/${file.relative_path}` : '#'}
                          target="_blank"
                          rel="noreferrer"
                          className="text-xs font-semibold text-emerald-900 underline truncate"
                        >
                          {file.original_name}
                        </a>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default AdminCaseDetail;
