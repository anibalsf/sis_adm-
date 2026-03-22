import React, { useState, useEffect, useRef } from 'react';
import { api, axiosInstance } from '../services/api';
import '../css/Encomiendas.css';

const ESTADOS = {
    registrado: { label: 'En Oficina', icon: '📦', color: 'estado-registrado' },
    en_transito: { label: 'En Tránsito', icon: '🚌', color: 'estado-transito' },
    entregado: { label: 'Entregado', icon: '✅', color: 'estado-entregado' },
};

const FORM_INIT = {
    remitente_nombre: '', remitente_ci: '', remitente_telefono: '',
    destinatario_nombre: '', destinatario_ci: '', destinatario_telefono: '',
    descripcion: '', peso_kg: '', precio: '', pagado: false, hoja_ruta: '',
};

export default function Encomiendas() {
    const [encomiendas, setEncomiendas] = useState([]);
    const [hojas, setHojas] = useState([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState('');
    const [filtroEstado, setFiltroEstado] = useState('');
    const [modalOpen, setModalOpen] = useState(false);
    const [editando, setEditando] = useState(null);
    const [form, setForm] = useState(FORM_INIT);
    const [saving, setSaving] = useState(false);
    const [detalle, setDetalle] = useState(null);
    const printRef = useRef();

    useEffect(() => { loadData(); }, []);

    const loadData = async () => {
        try {
            setLoading(true);
            const [encRes, hojasRes] = await Promise.all([
                api.getEncomiendas(),
                api.getHojasRuta({ page_size: 50 }),
            ]);
            setEncomiendas(encRes.data.results || encRes.data);
            setHojas(hojasRes.data.results || hojasRes.data);
        } catch (err) {
            console.error('Error cargando datos:', err);
        } finally {
            setLoading(false);
        }
    };

    const abrirNueva = () => {
        setEditando(null);
        setForm(FORM_INIT);
        setModalOpen(true);
    };

    const abrirEditar = (enc) => {
        setEditando(enc);
        setForm({
            ...enc,
            hoja_ruta: enc.hoja_ruta || '',
        });
        setModalOpen(true);
    };

    const cerrarModal = () => { setModalOpen(false); setEditando(null); };

    const handleChange = (e) => {
        const { name, value, type, checked } = e.target;
        setForm(f => ({ ...f, [name]: type === 'checkbox' ? checked : value }));
    };

    const guardar = async (e) => {
        e.preventDefault();
        setSaving(true);
        try {
            const payload = { ...form, hoja_ruta: form.hoja_ruta || null };
            if (editando) {
                await api.updateEncomienda(editando.id, payload);
            } else {
                await api.createEncomienda(payload);
            }
            await loadData();
            cerrarModal();
        } catch (err) {
            alert(err.response?.data?.detail || JSON.stringify(err.response?.data) || 'Error al guardar');
        } finally {
            setSaving(false);
        }
    };

    const cambiarEstado = async (id, estado) => {
        try {
            await api.cambiarEstadoEncomienda(id, estado);
            loadData();
        } catch (err) { alert('Error al cambiar estado'); }
    };

    const eliminar = async (id) => {
        if (!window.confirm('¿Eliminar esta encomienda?')) return;
        try {
            await api.deleteEncomienda(id);
            loadData();
        } catch { alert('Error al eliminar'); }
    };

    const imprimirTicket = async (enc) => {
        try {
            const res = await api.generarQrEncomienda(enc.id);
            setDetalle({ ...enc, qr_base64: res.data.qr_base64 });
            setTimeout(() => window.print(), 300);
        } catch (err) {
            alert('Error al generar QR para el ticket');
            setDetalle(enc);
            setTimeout(() => window.print(), 300);
        }
    };

    const notificarWsp = async (id, tipo) => {
        try {
            await api.notificarWhatsappEncomienda(id, tipo);
            alert('📱 Notificación de WhatsApp enviada con éxito');
        } catch (err) {
            alert('Error al enviar notificación: ' + (err.response?.data?.detail || err.message));
        }
    };

    const filtradas = encomiendas.filter(e => {
        const matchSearch = !search ||
            e.codigo_tracking.toLowerCase().includes(search.toLowerCase()) ||
            e.remitente_nombre.toLowerCase().includes(search.toLowerCase()) ||
            e.destinatario_nombre.toLowerCase().includes(search.toLowerCase());
        const matchEstado = !filtroEstado || e.estado === filtroEstado;
        return matchSearch && matchEstado;
    });

    const stats = {
        total: encomiendas.length,
        registrado: encomiendas.filter(e => e.estado === 'registrado').length,
        en_transito: encomiendas.filter(e => e.estado === 'en_transito').length,
        entregado: encomiendas.filter(e => e.estado === 'entregado').length,
    };

    return (
        <div className="enc-page">
            {/* Header */}
            <div className="enc-header">
                <div>
                    <h1>📦 Encomiendas y Paquetería</h1>
                    <p>Registro, seguimiento y entrega de paquetes</p>
                </div>
                <button className="btn-nueva" onClick={abrirNueva}>
                    + Nueva Encomienda
                </button>
            </div>

            {/* Stats Cards */}
            <div className="enc-stats">
                <div className="stat-card total"><span className="stat-num">{stats.total}</span><span className="stat-label">Total Hoy</span></div>
                <div className="stat-card registrado"><span className="stat-num">{stats.registrado}</span><span className="stat-label">📦 En Oficina</span></div>
                <div className="stat-card transito"><span className="stat-num">{stats.en_transito}</span><span className="stat-label">🚌 En Tránsito</span></div>
                <div className="stat-card entregado"><span className="stat-num">{stats.entregado}</span><span className="stat-label">✅ Entregados</span></div>
            </div>

            {/* Filtros */}
            <div className="enc-filters">
                <input
                    className="enc-search"
                    placeholder="🔍 Buscar por código, remitente o destinatario..."
                    value={search}
                    onChange={e => setSearch(e.target.value)}
                />
                <select className="enc-select" value={filtroEstado} onChange={e => setFiltroEstado(e.target.value)}>
                    <option value="">Todos los estados</option>
                    {Object.entries(ESTADOS).map(([k, v]) => (
                        <option key={k} value={k}>{v.icon} {v.label}</option>
                    ))}
                </select>
            </div>

            {/* Tabla */}
            <div className="enc-table-wrapper">
                {loading ? (
                    <div className="enc-loading"><div className="spinner"></div><p>Cargando encomiendas...</p></div>
                ) : filtradas.length === 0 ? (
                    <div className="enc-empty">
                        <span>📭</span>
                        <p>No hay encomiendas registradas</p>
                        <button className="btn-nueva" onClick={abrirNueva}>Registrar Primera Encomienda</button>
                    </div>
                ) : (
                    <table className="enc-table">
                        <thead>
                            <tr>
                                <th>Código</th>
                                <th>Remitente</th>
                                <th>Destinatario</th>
                                <th>Descripción</th>
                                <th>Precio</th>
                                <th>Pago</th>
                                <th>Estado</th>
                                <th>Vehículo</th>
                                <th>Acciones</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filtradas.map(enc => (
                                <tr key={enc.id}>
                                    <td><span className="tracking-code">{enc.codigo_tracking}</span></td>
                                    <td>
                                        <strong>{enc.remitente_nombre}</strong>
                                        <br /><small>📞 {enc.remitente_telefono}</small>
                                    </td>
                                    <td>
                                        <strong>{enc.destinatario_nombre}</strong>
                                        <br /><small>📞 {enc.destinatario_telefono}</small>
                                    </td>
                                    <td>{enc.descripcion}<br /><small>{enc.peso_kg} kg</small></td>
                                    <td><strong>Bs. {parseFloat(enc.precio).toFixed(2)}</strong></td>
                                    <td>
                                        <span className={`badge-pago ${enc.pagado ? 'pagado' : 'pendiente'}`}>
                                            {enc.pagado ? '✅ Pagado' : '⏳ Pendiente'}
                                        </span>
                                    </td>
                                    <td>
                                        <span className={`badge-estado ${ESTADOS[enc.estado]?.color}`}>
                                            {ESTADOS[enc.estado]?.icon} {ESTADOS[enc.estado]?.label}
                                        </span>
                                    </td>
                                    <td>
                                        {enc.hoja_ruta_detalle ? (
                                            <small>
                                                🚌 {enc.hoja_ruta_detalle.vehiculo_placa}<br />
                                                {enc.hoja_ruta_detalle.ruta_nombre}
                                            </small>
                                        ) : <span className="text-muted">Sin asignar</span>}
                                    </td>
                                    <td>
                                        <div className="action-btns">
                                            <button className="btn-act edit" title="Editar" onClick={() => abrirEditar(enc)}>✏️</button>
                                            <button className="btn-act print" title="Imprimir Ticket" onClick={() => imprimirTicket(enc)}>🖨️</button>
                                            
                                            {/* Notificaciones WhatsApp */}
                                            <div className="dropdown-wsp">
                                                <button className="btn-act wsp" title="Notificar WhatsApp">📱</button>
                                                <div className="dropdown-content">
                                                    <button onClick={() => notificarWsp(enc.id, 'registro')}>📝 Registro (Remitente)</button>
                                                    {enc.estado === 'en_transito' && <button onClick={() => notificarWsp(enc.id, 'llegada')}>🏠 Llegada (Destinatario)</button>}
                                                    {enc.estado === 'entregado' && <button onClick={() => notificarWsp(enc.id, 'entrega')}>✅ Entrega (Remitente)</button>}
                                                </div>
                                            </div>

                                            {enc.estado === 'registrado' && (
                                                <button className="btn-act transit" title="Marcar En Tránsito" onClick={() => cambiarEstado(enc.id, 'en_transito')}>🚌</button>
                                            )}
                                            {enc.estado === 'en_transito' && (
                                                <button className="btn-act deliver" title="Marcar Entregado" onClick={() => cambiarEstado(enc.id, 'entregado')}>✅</button>
                                            )}
                                            <button className="btn-act del" title="Eliminar" onClick={() => eliminar(enc.id)}>🗑️</button>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>

            {/* Modal Formulario */}
            {modalOpen && (
                <div className="enc-modal-overlay" onClick={cerrarModal}>
                    <div className="enc-modal" onClick={e => e.stopPropagation()}>
                        <div className="modal-head">
                            <h2>{editando ? '✏️ Editar Encomienda' : '📦 Nueva Encomienda'}</h2>
                            <button className="close-btn" onClick={cerrarModal}>×</button>
                        </div>
                        <form className="enc-form" onSubmit={guardar}>
                            <div className="form-section">
                                <h3>👤 Remitente</h3>
                                <div className="form-grid">
                                    <div className="field">
                                        <label>Nombre *</label>
                                        <input name="remitente_nombre" value={form.remitente_nombre} onChange={handleChange} required placeholder="Nombre completo" />
                                    </div>
                                    <div className="field">
                                        <label>CI</label>
                                        <input name="remitente_ci" value={form.remitente_ci} onChange={handleChange} placeholder="Cédula identidad" />
                                    </div>
                                    <div className="field">
                                        <label>Teléfono *</label>
                                        <input name="remitente_telefono" value={form.remitente_telefono} onChange={handleChange} required placeholder="Nro de celular" />
                                    </div>
                                </div>
                            </div>
                            <div className="form-section">
                                <h3>📍 Destinatario</h3>
                                <div className="form-grid">
                                    <div className="field">
                                        <label>Nombre *</label>
                                        <input name="destinatario_nombre" value={form.destinatario_nombre} onChange={handleChange} required placeholder="Nombre completo" />
                                    </div>
                                    <div className="field">
                                        <label>CI</label>
                                        <input name="destinatario_ci" value={form.destinatario_ci} onChange={handleChange} placeholder="Cédula identidad" />
                                    </div>
                                    <div className="field">
                                        <label>Teléfono *</label>
                                        <input name="destinatario_telefono" value={form.destinatario_telefono} onChange={handleChange} required placeholder="Nro de celular" />
                                    </div>
                                </div>
                            </div>
                            <div className="form-section">
                                <h3>📋 Detalle del Paquete</h3>
                                <div className="form-grid">
                                    <div className="field wide">
                                        <label>Descripción *</label>
                                        <input name="descripcion" value={form.descripcion} onChange={handleChange} required placeholder="Ej: Caja de ropa, Sobre documentos, Repuestos..." />
                                    </div>
                                    <div className="field">
                                        <label>Peso (kg)</label>
                                        <input name="peso_kg" type="number" step="0.1" value={form.peso_kg} onChange={handleChange} placeholder="0.5" />
                                    </div>
                                    <div className="field">
                                        <label>Precio (Bs.) *</label>
                                        <input name="precio" type="number" step="0.5" value={form.precio} onChange={handleChange} required placeholder="25.00" />
                                    </div>
                                    <div className="field">
                                        <label>Asignar Vehículo/Viaje</label>
                                        <select name="hoja_ruta" value={form.hoja_ruta} onChange={handleChange}>
                                            <option value="">Sin asignar aún</option>
                                            {hojas.map(h => (
                                                <option key={h.id} value={h.id}>
                                                    {h.vehiculo?.placa} - {h.ruta?.nombre} ({new Date(h.fecha_salida).toLocaleDateString()})
                                                </option>
                                            ))}
                                        </select>
                                    </div>
                                    <div className="field check-field">
                                        <label>
                                            <input name="pagado" type="checkbox" checked={form.pagado} onChange={handleChange} />
                                            &nbsp;Pago recibido
                                        </label>
                                    </div>
                                </div>
                            </div>
                            <div className="form-actions">
                                <button type="button" className="btn-cancel" onClick={cerrarModal}>Cancelar</button>
                                <button type="submit" className="btn-save" disabled={saving}>
                                    {saving ? 'Guardando...' : editando ? '💾 Actualizar' : '📦 Registrar Encomienda'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* Ticket de impresión (oculto, solo se activa al imprimir) */}
            {detalle && (
                <div className="print-only" ref={printRef}>
                    <div className="ticket">
                        <div className="ticket-header">
                            <img src="/logo-taipiplaya.png" alt="Logo" style={{ width: '50px', marginBottom: '5px' }} />
                            <h2>SINDICATO INTEGRACIÓN TAIPIPLAYA</h2>
                            <h3>🏷️ TICKET DE ENCOMIENDA</h3>
                        </div>
                        
                        <div className="ticket-body">
                            <div className="ticket-main-info">
                                <div className="ticket-code">{detalle.codigo_tracking}</div>
                                {detalle.qr_base64 && (
                                    <div className="ticket-qr">
                                        <img src={`data:image/png;base64,${detalle.qr_base64}`} alt="QR" style={{ width: '100px', height: '100px' }} />
                                    </div>
                                )}
                            </div>
                            
                            <hr />
                            <div className="ticket-row"><strong>REMITENTE:</strong> {detalle.remitente_nombre}<br />Tel: {detalle.remitente_telefono}</div>
                            <div className="ticket-row"><strong>DESTINATARIO:</strong> {detalle.destinatario_nombre}<br />Tel: {detalle.destinatario_telefono}</div>
                            <hr />
                            <div className="ticket-row"><strong>CONTENIDO:</strong> {detalle.descripcion}</div>
                            <div className="ticket-row"><strong>PESO:</strong> {detalle.peso_kg} kg &nbsp;&nbsp; <strong>PRECIO:</strong> Bs. {parseFloat(detalle.precio).toFixed(2)}</div>
                            <div className="ticket-row"><strong>PAGO:</strong> {detalle.pagado ? 'PAGADO' : 'POR PAGAR'}</div>
                            
                            {detalle.hoja_ruta_detalle && (
                                <div className="ticket-row"><strong>VEHÍCULO:</strong> {detalle.hoja_ruta_detalle.vehiculo_placa}</div>
                            )}
                        </div>

                        <div className="ticket-footer">
                            <p>Fecha: {new Date(detalle.fecha_registro).toLocaleString()}</p>
                            <p>¡Gracias por su preferencia!</p>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
