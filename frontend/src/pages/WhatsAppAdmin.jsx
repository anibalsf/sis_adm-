import React, { useState, useEffect } from 'react';
import { axiosInstance as axios } from '../services/api';
import '../css/WhatsApp.css';

const TIPO_LABELS = {
    payment_confirmation: '💳 Pago Confirmado',
    shift_reminder: '🕐 Recordatorio Turno',
    sanction_notice: '⚠️ Sanción',
    reservation_confirmation: '🎫 Reserva',
    meeting_reminder: '📅 Reunión',
    debt_reminder: '💸 Deuda Pendiente',
    cuota_payment: '✅ Cuota Mensual',
    hoja_ruta_emitted: '📄 Hoja de Ruta',
    general: '💬 General',
};

const STATUS_LABELS = {
    pending: { label: 'Pendiente', cls: 'st-pending' },
    sent: { label: 'Enviado', cls: 'st-sent' },
    delivered: { label: 'Entregado', cls: 'st-delivered' },
    read: { label: 'Leído', cls: 'st-read' },
    failed: { label: 'Fallido', cls: 'st-failed' },
};

export default function WhatsAppAdmin() {
    const [tab, setTab] = useState('historial'); // historial | config | plantillas | prueba
    const [mensajes, setMensajes] = useState([]);
    const [plantillas, setPlantillas] = useState([]);
    const [config, setConfig] = useState(null);
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);
    const [busqueda, setBusqueda] = useState('');
    const [filtroTipo, setFiltroTipo] = useState('');
    const [filtroEstado, setFiltroEstado] = useState('');

    // Prueba manual
    const [testPhone, setTestPhone] = useState('');
    const [testMsg, setTestMsg] = useState('');
    const [testResult, setTestResult] = useState(null);
    const [testLoading, setTestLoading] = useState(false);

    // Config
    const [cfgEdit, setCfgEdit] = useState(null);
    const [cfgSaving, setCfgSaving] = useState(false);

    // Plantilla edicion
    const [plantEditar, setPlantEditar] = useState(null);

    useEffect(() => { loadAll(); }, []);

    const loadAll = async () => {
        setLoading(true);
        try {
            const [msgRes, tplRes, cfgRes, stRes] = await Promise.all([
                axios.get('/api/whatsapp/messages/?ordering=-created_at&page_size=100'),
                axios.get('/api/whatsapp/templates/'),
                axios.get('/api/whatsapp/config/current/'),
                axios.get('/api/whatsapp/messages/stats/'),
            ]);
            setMensajes(msgRes.data?.results || (Array.isArray(msgRes.data) ? msgRes.data : []));
            setPlantillas(tplRes.data?.results || (Array.isArray(tplRes.data) ? tplRes.data : []));
            setConfig(cfgRes.data);
            setCfgEdit(cfgRes.data);
            setStats(stRes.data);
        } catch (err) {
            console.error('Error cargando whatsapp:', err);
        } finally {
            setLoading(false);
        }
    };

    const guardarConfig = async () => {
        setCfgSaving(true);
        try {
            await axios.put(`/api/whatsapp/config/${config.id}/`, cfgEdit);
            await loadAll();
            alert('✅ Configuración guardada correctamente');
        } catch (err) {
            alert('Error al guardar configuración');
        } finally {
            setCfgSaving(false);
        }
    };

    const probarConexion = async () => {
        if (!testPhone) { alert('Ingresa un número de teléfono'); return; }
        setTestLoading(true);
        setTestResult(null);
        try {
            const res = await axios.post('/api/whatsapp/config/test_connection/', { test_phone: testPhone });
            setTestResult({ ok: true, msg: res.data.message });
        } catch (err) {
            setTestResult({ ok: false, msg: err.response?.data?.error || 'Error al probar conexión' });
        } finally {
            setTestLoading(false);
        }
    };

    const enviarManual = async () => {
        if (!testPhone || !testMsg) { alert('Completa el número y el mensaje'); return; }
        setTestLoading(true);
        try {
            await axios.post('/api/whatsapp/messages/send_manual/', {
                phone: testPhone, message: testMsg, message_type: 'general', recipient_name: 'Prueba'
            });
            alert('✅ Mensaje enviado (revisa el historial)');
            await loadAll();
        } catch (err) {
            alert(err.response?.data?.error || 'Error al enviar');
        } finally {
            setTestLoading(false);
        }
    };

    const guardarPlantilla = async (pl) => {
        try {
            await axios.put(`/api/whatsapp/templates/${pl.id}/`, pl);
            alert('✅ Plantilla actualizada');
            setPlantEditar(null);
            await loadAll();
        } catch { alert('Error al guardar plantilla'); }
    };

    const msgFiltrados = (mensajes || []).filter(m => {
        const matchBus = !busqueda || 
            (typeof m.recipient_name === 'string' && m.recipient_name.toLowerCase().includes(busqueda.toLowerCase())) || 
            (typeof m.recipient_phone === 'string' && m.recipient_phone.includes(busqueda));
        const matchTipo = !filtroTipo || m.message_type === filtroTipo;
        const matchSt = !filtroEstado || m.status === filtroEstado;
        return matchBus && matchTipo && matchSt;
    });

    return (
        <div className="wa-page">
            <div className="wa-header">
                <div>
                    <h1>📱 WhatsApp Notificaciones</h1>
                    <p>Panel de control de mensajes automáticos</p>
                </div>
                <div 
                    className={`wa-status-pill ${config?.is_enabled ? 'enabled' : 'disabled'}`}
                    style={{ cursor: 'pointer' }}
                    onClick={() => setActiveTab('config')}
                    title="Click para configurar"
                >
                    {config?.is_enabled ? '🟢 HABILITADO' : '🔴 DESACTIVADO'}
                </div>
            </div>

            {/* Stats rápidas */}
            {stats && typeof stats === 'object' && (
                <div className="wa-stats">
                    <div className="wa-stat"><span>{String(stats.total || 0)}</span><label>Total Mensajes</label></div>
                    <div className="wa-stat green"><span>{String(stats.by_status?.sent || 0)}</span><label>✅ Enviados</label></div>
                    <div className="wa-stat blue"><span>{String(stats.by_status?.delivered || 0)}</span><label>📩 Entregados</label></div>
                    <div className="wa-stat red"><span>{String(stats.by_status?.failed || 0)}</span><label>❌ Fallidos</label></div>
                    <div className="wa-stat amber"><span>{String(stats.by_status?.pending || 0)}</span><label>⏳ Pendientes</label></div>
                </div>
            )}

            {/* Tabs */}
            <div className="wa-tabs">
                {[
                    { id: 'historial', label: '📋 Historial' },
                    { id: 'plantillas', label: '📝 Plantillas' },
                    { id: 'config', label: '⚙️ Configuración' },
                    { id: 'prueba', label: '🧪 Prueba' },
                ].map(t => (
                    <button key={t.id} className={`wa-tab ${tab === t.id ? 'active' : ''}`} onClick={() => setTab(t.id)}>
                        {t.label}
                    </button>
                ))}
            </div>

            {loading ? (
                <div className="wa-loading"><div className="spinner"></div><p>Cargando...</p></div>
            ) : (
                <>
                    {/* HISTORIAL */}
                    {tab === 'historial' && (
                        <div className="wa-section">
                            <div className="wa-filters">
                                <input className="wa-search" placeholder="🔍 Buscar por nombre o teléfono..." value={busqueda} onChange={e => setBusqueda(e.target.value)} />
                                <select className="wa-sel" value={filtroTipo} onChange={e => setFiltroTipo(e.target.value)}>
                                    <option value="">Todos los tipos</option>
                                    {Object.entries(TIPO_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                                </select>
                                <select className="wa-sel" value={filtroEstado} onChange={e => setFiltroEstado(e.target.value)}>
                                    <option value="">Todos los estados</option>
                                    {Object.entries(STATUS_LABELS).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
                                </select>
                            </div>

                            {msgFiltrados.length === 0 ? (
                                <div className="wa-empty">
                                    <span>📭</span>
                                    <p>No hay mensajes enviados todavía</p>
                                    <small>Los mensajes aparecerán aquí cuando se registren pagos, reservas o se apliquen sanciones</small>
                                </div>
                            ) : (
                                <div className="wa-table-wrap">
                                    <table className="wa-table">
                                        <thead>
                                            <tr>
                                                <th>Destinatario</th>
                                                <th>Tipo</th>
                                                <th>Mensaje</th>
                                                <th>Estado</th>
                                                <th>Fecha</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {msgFiltrados.map((m, idx) => (
                                                <tr key={m.id || idx}>
                                                    <td>
                                                        <strong>{typeof m.recipient_name === 'object' ? '' : (m.recipient_name || 'Sin nombre')}</strong>
                                                        <br /><small>📞 {String(m.recipient_phone || '')}</small>
                                                    </td>
                                                    <td><span className="wa-badge-tipo">{TIPO_LABELS[m.message_type] || String(m.message_type || '')}</span></td>
                                                    <td><div className="wa-msg-preview">{typeof m.message_content === 'string' ? m.message_content.substring(0, 80) : String(m.message_content || '')}...</div></td>
                                                    <td><span className={`wa-badge-st ${STATUS_LABELS[m.status]?.cls || ''}`}>{STATUS_LABELS[m.status]?.label || String(m.status || '')}</span></td>
                                                    <td><small>{new Date(m.created_at).toLocaleString('es-BO')}</small></td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            )}
                        </div>
                    )}

                    {/* PLANTILLAS */}
                    {tab === 'plantillas' && (
                        <div className="wa-section">
                            <div className="wa-info-box">
                                <strong>ℹ️ ¿Cómo funcionan?</strong> Cada plantilla es el texto que se enviará automáticamente. Puedes personalizar el mensaje. Las variables entre llaves <code>{'{nombre}'}</code> se reemplazan automáticamente.
                            </div>
                            <div className="plantillas-grid">
                                {plantillas.map((pl, idx) => (
                                    <div key={pl.id || idx} className="plantilla-card">
                                        <div className="plantilla-head">
                                            <span className="pl-tipo">{TIPO_LABELS[pl.message_type] || String(pl.message_type || '')}</span>
                                            <span className={`pl-badge ${pl.is_active ? 'active' : 'inactive'}`}>{pl.is_active ? '✅ Activa' : '⏸ Inactiva'}</span>
                                        </div>
                                        <code className="plantilla-nombre">{String(pl.name || '')}</code>
                                        <pre className="plantilla-preview">{String(pl.template_content || '')}</pre>
                                        <button className="btn-editar-pl" onClick={() => setPlantEditar({ ...pl })}>✏️ Editar</button>
                                    </div>
                                ))}
                            </div>

                            {plantEditar && (
                                <div className="wa-modal-overlay" onClick={() => setPlantEditar(null)}>
                                    <div className="wa-modal" onClick={e => e.stopPropagation()}>
                                        <h3>✏️ Editar Plantilla: <code>{plantEditar.name}</code></h3>
                                        <label>Tipo de mensaje</label>
                                        <select value={plantEditar.message_type} onChange={e => setPlantEditar({ ...plantEditar, message_type: e.target.value })}>
                                            {Object.entries(TIPO_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                                        </select>
                                        <label>Contenido del mensaje</label>
                                        <small>Variables disponibles: {'{nombre}'}, {'{monto}'}, {'{tipo}'}, {'{fecha}'}, {'{ruta}'}, {'{asiento}'}, {'{codigo}'}, etc.</small>
                                        <textarea rows={10} value={plantEditar.template_content} onChange={e => setPlantEditar({ ...plantEditar, template_content: e.target.value })} />
                                        <div className="wa-modal-actions">
                                            <input type="checkbox" id="pl-activa" checked={plantEditar.is_active} onChange={e => setPlantEditar({ ...plantEditar, is_active: e.target.checked })} />
                                            <label htmlFor="pl-activa">Plantilla activa</label>
                                            <button className="btn-cancel-wa" onClick={() => setPlantEditar(null)}>Cancelar</button>
                                            <button className="btn-save-wa" onClick={() => guardarPlantilla(plantEditar)}>💾 Guardar</button>
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>
                    )}

                    {/* CONFIGURACIÓN */}
                    {tab === 'config' && cfgEdit && (
                        <div className="wa-section">
                            <div className="wa-info-box warning">
                                <strong>⚙️ Requisitos para activar WhatsApp:</strong><br />
                                1. Tener cuenta en <strong>Twilio.com</strong> (gratuita para pruebas)<br />
                                2. Agregar al <strong>.env</strong> del backend:<br />
                                <code>TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxx</code><br />
                                <code>TWILIO_AUTH_TOKEN=tu_auth_token</code><br />
                                <code>TWILIO_WHATSAPP_FROM=whatsapp:+14155238886</code><br />
                                3. Activar el interruptor de abajo y guardar
                            </div>

                            <div className="cfg-grid">
                                <div className="cfg-field">
                                    <label>Estado del Sistema WhatsApp</label>
                                    <div className="toggle-wrap">
                                        <label className="toggle">
                                            <input type="checkbox" checked={cfgEdit.is_enabled} onChange={e => setCfgEdit({ ...cfgEdit, is_enabled: e.target.checked })} />
                                            <span className="toggle-slider"></span>
                                        </label>
                                        <span>{cfgEdit.is_enabled ? '🟢 Habilitado' : '🔴 Deshabilitado'}</span>
                                    </div>
                                </div>
                                <div className="cfg-field">
                                    <label>Proveedor</label>
                                    <select value={cfgEdit.provider} onChange={e => setCfgEdit({ ...cfgEdit, provider: e.target.value })}>
                                        <option value="twilio">Twilio (Recomendado)</option>
                                        <option value="baileys">Baileys (WhatsApp Web)</option>
                                        <option value="whatsapp_business">WhatsApp Business API</option>
                                    </select>
                                </div>
                                <div className="cfg-field">
                                    <label>Límite diario de mensajes</label>
                                    <input type="number" value={cfgEdit.daily_message_limit} onChange={e => setCfgEdit({ ...cfgEdit, daily_message_limit: parseInt(e.target.value) })} />
                                </div>
                                <div className="cfg-field">
                                    <label>Máximo reintentos</label>
                                    <input type="number" value={cfgEdit.max_retries} onChange={e => setCfgEdit({ ...cfgEdit, max_retries: parseInt(e.target.value) })} />
                                </div>
                            </div>

                            <div style={{ marginTop: '2rem', textAlign: 'right' }}>
                                <button className="btn-save-wa" onClick={guardarConfig} disabled={cfgSaving}>
                                    {cfgSaving ? 'Guardando...' : '💾 Guardar Configuración'}
                                </button>
                            </div>
                        </div>
                    )}

                    {/* PRUEBA */}
                    {tab === 'prueba' && (
                        <div className="wa-section">
                            <div className="prueba-grid">
                                <div className="prueba-card">
                                    <h3>🔌 Probar Conexión</h3>
                                    <p>Envía un mensaje de prueba para verificar que la integración funciona.</p>
                                    <label>Número de teléfono (sin +591)</label>
                                    <input value={testPhone} onChange={e => setTestPhone(e.target.value)} placeholder="76543210" />
                                    <button className="btn-test" onClick={probarConexion} disabled={testLoading}>
                                        {testLoading ? 'Enviando...' : '📡 Probar Conexión'}
                                    </button>
                                    {testResult && (
                                        <div className={`test-result ${testResult.ok ? 'ok' : 'err'}`}>
                                            {testResult.ok ? '✅' : '❌'} {testResult.msg}
                                        </div>
                                    )}
                                </div>

                                <div className="prueba-card">
                                    <h3>✉️ Enviar Mensaje Manual</h3>
                                    <p>Envía un mensaje personalizado a cualquier número.</p>
                                    <label>Número de teléfono</label>
                                    <input value={testPhone} onChange={e => setTestPhone(e.target.value)} placeholder="76543210" />
                                    <label>Mensaje</label>
                                    <textarea rows={4} value={testMsg} onChange={e => setTestMsg(e.target.value)} placeholder="Escribe el mensaje aquí..." />
                                    <button className="btn-test" onClick={enviarManual} disabled={testLoading}>
                                        {testLoading ? 'Enviando...' : '📤 Enviar Mensaje'}
                                    </button>
                                </div>

                                <div className="prueba-card info">
                                    <h3>❓ Cómo funciona</h3>
                                    <ul>
                                        <li>🔄 <strong>Automático:</strong> Cuando registras un pago → WhatsApp automático al afiliado</li>
                                        <li>🎫 <strong>Reservas:</strong> Al crear una reserva → Boleto por WhatsApp al pasajero</li>
                                        <li>⚠️ <strong>Sanciones:</strong> Al aplicar multa → Aviso inmediato al afiliado</li>
                                        <li>📅 <strong>Recordatorios:</strong> Automáticos cada día para turnos y reuniones</li>
                                        <li>💸 <strong>Morosos:</strong> Recordatorio semanal a afiliados con deuda</li>
                                    </ul>
                                </div>
                            </div>
                        </div>
                    )}
                </>
            )}
        </div>
    );
}
