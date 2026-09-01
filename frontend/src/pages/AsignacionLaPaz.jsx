import { useState, useEffect, useCallback } from 'react';
import api from '../services/api';
import '../css/Common.css';

function AsignacionLaPaz() {
    const [items, setItems] = useState([]);
    const [afiliados, setAfiliados] = useState([]);
    const [vehiculos, setVehiculos] = useState([]);
    const [rutas, setRutas] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [showModal, setShowModal] = useState(false);
    const [showQrModal, setShowQrModal] = useState(false);
    const [qrUrl, setQrUrl] = useState('');
    const [qrLoading, setQrLoading] = useState(false);
    const [submitError, setSubmitError] = useState('');
    const [fieldErrors, setFieldErrors] = useState({});
    const [form, setForm] = useState({
        nro: '',
        fecha_emision: '',
        fecha_salida: '',
        hora_salida: '',
        afiliado: '',
        vehiculo: '',
        ruta: '',  // Pre-seleccionada La Paz
        agente_parada: '',
        precio: ''
    });

    const findRutaLaPaz = (lista) => {
        const lower = (s) => String(s || '').toLowerCase().trim();
        return (lista || []).find(r =>
            lower(r?.destino) === 'la paz' ||
            lower(r?.nombre).includes('la paz')
        );
    };

    const loadData = useCallback(async () => {
        try {
            setLoading(true);
            const [hojasRes, afiliadosRes, vehiculosRes, rutasRes] = await Promise.all([
                api.getHojasRuta({ ruta_id: '', destino: 'La Paz' }),
                api.getAfiliados({ estado: 'activo', page_size: 1000 }),
                api.getVehiculos({ page_size: 1000 }),
                api.getRutas({ page_size: 100 })
            ]);

            setItems(hojasRes.data.results || hojasRes.data || []);
            setAfiliados(afiliadosRes.data.results || afiliadosRes.data || []);

            const vehiculosDocumentados = (vehiculosRes.data.results || vehiculosRes.data || [])
                .filter(v => !v.indocumentado && v.estado === 'activo');
            setVehiculos(vehiculosDocumentados);

            setRutas(rutasRes.data.results || rutasRes.data || []);

            const rutaLaPaz = findRutaLaPaz(rutasRes.data.results || rutasRes.data || []);
            if (rutaLaPaz) {
                setForm(prev => ({ ...prev, ruta: rutaLaPaz.id, precio: rutaLaPaz.tarifa_base || '' }));
            }

            setError('');
        } catch (err) {
            setError('Error al cargar datos');
            console.error(err);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        loadData();
    }, [loadData]);

    useEffect(() => {
        const rutaLaPaz = findRutaLaPaz(rutas);
        if (rutaLaPaz && !form.ruta) {
            setForm(prev => ({
                ...prev,
                ruta: rutaLaPaz.id,
                precio: rutaLaPaz.tarifa_base || prev.precio || ''
            }));
        }
    }, [rutas, form.ruta]);


    const openCreate = () => {
        setShowModal(true);
        setSubmitError('');
        const rutaLaPaz = findRutaLaPaz(rutas);
        if (rutaLaPaz) {
            setForm(prev => ({ ...prev, ruta: rutaLaPaz.id, precio: rutaLaPaz.tarifa_base || '' }));
        }
    };

    const closeModal = () => {
        setShowModal(false);
        setForm({ nro: '', fecha_emision: '', fecha_salida: '', hora_salida: '', afiliado: '', vehiculo: '', ruta: '', agente_parada: '', precio: '' });
        setSubmitError('');

        // Volver a pre-seleccionar La Paz
        const rutaLaPaz = findRutaLaPaz(rutas);
        if (rutaLaPaz) {
            setForm(prev => ({ ...prev, ruta: rutaLaPaz.id, precio: rutaLaPaz.tarifa_base || '' }));
        }
    };

    const onChange = (e) => {
        const { name, value } = e.target;
        setForm(prev => {
            const next = { ...prev, [name]: value };

            // Actualizar precio si cambia la ruta
            if (name === 'ruta') {
                const rutaSeleccionada = rutas.find(r => r.id === parseInt(value));
                if (rutaSeleccionada) {
                    next.precio = rutaSeleccionada.tarifa_base || '';
                }
            }
            if (name === 'afiliado') {
                const af = afiliados.find(a => String(a.id) === String(value));
                if (af) {
                    next.agente_parada = af.telefono || af.ci || '';
                    const vehiculosAptos = vehiculos.filter(v =>
                        String(v.afiliado) === String(value) &&
                        ['minibus', 'ipsum'].includes(String(v.tipo || '').toLowerCase())
                    );
                    next.vehiculo = vehiculosAptos.length > 0 ? vehiculosAptos[0].id : '';
                } else {
                    next.agente_parada = '';
                    next.vehiculo = '';
                }
            }
            return next;
        });
    };

    const validateForm = () => {
        const errs = {};
        if (!form.fecha_emision) errs.fecha_emision = 'Requerido';
        if (!form.fecha_salida) errs.fecha_salida = 'Requerido';
        if (!form.hora_salida) errs.hora_salida = 'Requerido';
        if (!form.afiliado) errs.afiliado = 'Requerido';
        if (!form.vehiculo) errs.vehiculo = 'Requerido';
        if (!form.ruta) errs.ruta = 'Requerido';
        const precioNum = parseFloat(String(form.precio || '0'));
        if (isNaN(precioNum) || precioNum <= 0) errs.precio = 'Monto inválido';
        if (form.fecha_emision && form.fecha_salida && form.fecha_salida < form.fecha_emision) errs.fecha_salida = 'Debe ser igual o posterior a emisión';
        const rutaSel = rutas.find(r => r.id === parseInt(form.ruta));
        const vehSel = vehiculos.find(v => v.id === parseInt(form.vehiculo));
        if (rutaSel && (
            (rutaSel.nombre || '').toLowerCase().includes('la paz') ||
            (rutaSel.destino || '').toLowerCase() === 'la paz'
        )) {
            const tipo = (vehSel?.tipo || '').toLowerCase();
            if (tipo && !['minibus', 'ipsum'].includes(tipo)) errs.vehiculo = 'Solo Minibus/Ipsum para La Paz';
        }
        setFieldErrors(errs);
        setSubmitError(Object.values(errs)[0] || '');
        return Object.keys(errs).length === 0;
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            if (!validateForm()) return;
            const payload = { ...form };
            await api.createHojaRuta(payload);
            closeModal();
            loadData();
            alert('✅ Asignación de ruta La Paz creada exitosamente');
        } catch (err) {
            setSubmitError(err.response?.data?.detail || 'Error al crear asignación');
        }
    };

    const handleImprimirPlanilla = async (id) => {
        try {
            const res = await api.generarPlanillaLaPaz(id);
            if (res.data?.archivo_url) {
                window.open(res.data.archivo_url, '_blank');
            } else {
                alert('No se pudo obtener la URL de la planilla');
            }
        } catch (err) {
            console.error(err);
            alert('Error al generar la planilla');
        }
    };

    const handleAbrirQr = async () => {
        setShowQrModal(true);
        setQrLoading(true);
        try {
            const res = await api.getQrReservasLaPaz();
            const blobUrl = URL.createObjectURL(res.data);
            setQrUrl(blobUrl);
        } catch (err) {
            console.error(err);
            alert('Error al generar el QR');
        } finally {
            setQrLoading(false);
        }
    };

    const handleImprimirQr = () => {
        if (!qrUrl) return;
        const w = window.open('', '_blank');
        if (!w) {
            alert('Permita ventanas emergentes para imprimir el QR');
            return;
        }
        w.document.write(`<!DOCTYPE html><html><head><title>QR Reservas La Paz</title><style>body{display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:90vh;font-family:sans-serif;text-align:center}img{width:320px;height:320px}h2{margin-bottom:4px}.sub{color:#555;margin-top:8px}</style></head><body><h2>Sindicato Mixto "Integración Taipiplaya"</h2><p style="color:#555">RESERVA DE PASAJES — RUTA LA PAZ</p><img src="${qrUrl}" /><p class="sub">Escanee con su celular para ver el nombre del afiliado,<br/>la placa, celular y hora de salida de cada movilidad</p></body></html>`);
        w.document.close();
        w.focus();
        w.print();
    };

    const closeQrModal = () => {
        setShowQrModal(false);
        if (qrUrl) {
            URL.revokeObjectURL(qrUrl);
            setQrUrl('');
        }
    };

    if (loading) return <div className="loading">Cargando...</div>;
    if (error) return <div className="error">{error}</div>;

    return (
        <div className="page-container">
            <div className="page-header">
                <h2>🚌 Asignación Ruta La Paz</h2>
                <div style={{ display: 'flex', gap: '10px' }}>
                    <button className="btn btn-secondary" onClick={handleAbrirQr}>
                        <span className="icon">📱</span> QR Reservas Pasajeros
                    </button>
                    <button className="btn btn-primary" onClick={openCreate}>
                        <span className="icon">+</span> Designar Agente La Paz
                    </button>
                </div>
            </div>

            <p style={{ color: '#666', marginBottom: '20px', fontSize: '14px', lineHeight: '1.6' }}>
                Gestiona las asignaciones de vehículos <strong>documentados (con placa)</strong> para la ruta a La Paz.
                Solo se muestran vehículos Ipsum y Minibus aptos para esta ruta.
            </p>

            <div className="table-container">
                <table className="vehiculos-table">
                    <thead>
                        <tr>
                            <th>Número</th>
                            <th>Afiliado</th>
                            <th>Vehículo</th>
                            <th>Fecha Salida</th>
                            <th>Hora Salida</th>
                            <th>Placa de la Movilidad</th>
                            <th>Precio</th>
                            <th>Estado</th>
                            <th>Acciones</th>
                        </tr>
                    </thead>
                    <tbody>
                        {items.length === 0 ? (
                            <tr><td colSpan="9" style={{ textAlign: 'center', color: '#999' }}>
                                No hay asignaciones para La Paz
                            </td></tr>
                        ) : (
                            items.map(item => (
                                <tr key={item.id}>
                                    <td>{item.nro}</td>
                                    <td>
                                        {(() => {
                                            const aid = item.afiliado?.id || item.afiliado;
                                            const af = afiliados.find(a => String(a.id) === String(aid));
                                            if (!af) return <span style={{ color: '#999' }}>Sin datos</span>;
                                            return (
                                                <div style={{ display: 'flex', flexDirection: 'column' }}>
                                                    <span style={{ fontWeight: 600 }}>{af.apellidos} {af.nombres}</span>
                                                    <span style={{ fontSize: '12px', color: '#555' }}>
                                                        CI: {af.ci || '-'} {af.telefono ? `• Tel: ${af.telefono}` : ''}
                                                    </span>
                                                </div>
                                            );
                                        })()}
                                    </td>
                                    <td>
                                        {vehiculos.find(v => v.id === (item.vehiculo?.id || item.vehiculo))?.tipo || '-'}
                                    </td>
                                    <td>{item.fecha_salida || item.fecha_emision}</td>
                                    <td>{item.hora_salida || '-'}</td>
                                    <td>{vehiculos.find(v => v.id === (item.vehiculo?.id || item.vehiculo))?.placa || '-'}</td>
                                    <td>Bs. {Number(item.precio || 0).toFixed(2)}</td>
                                    <td>
                                        <span className={`badge badge-${item.estado}`}>{item.estado}</span>
                                    </td>
                                    <td>
                                        <button
                                            className="btn btn-secondary btn-sm"
                                            onClick={() => handleImprimirPlanilla(item.id)}
                                            style={{ padding: '0.4rem 0.8rem', fontSize: '13px' }}
                                        >
                                            🖨️ Planilla
                                        </button>
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>

            {/* Modal QR Reservas */}
            {showQrModal && (
                <div className="modal-overlay" onClick={closeQrModal}>
                    <div className="modal-content" onClick={e => e.stopPropagation()} style={{ maxWidth: '420px', textAlign: 'center' }}>
                        <h3>📱 QR Reservas Pasajeros — La Paz</h3>
                        <p style={{ color: '#666', fontSize: '13px', marginBottom: '15px' }}>
                            Imprima este código y colóquelo en la parada/oficina. Al escanearlo,
                             el pasajero verá las asignaciones con el nombre del afiliado,
                             la placa, celular y hora de salida para reservar su pasaje.
                        </p>
                        {qrLoading ? (
                            <div className="loading" style={{ padding: '60px 0' }}>Generando QR...</div>
                        ) : qrUrl ? (
                            <img
                                src={qrUrl}
                                alt="QR Reservas La Paz"
                                style={{ width: '260px', height: '260px', border: '1px solid #ddd', borderRadius: '8px', padding: '8px', background: '#fff' }}
                            />
                        ) : null}
                        <div className="modal-actions" style={{ justifyContent: 'center', marginTop: '20px' }}>
                            <button type="button" className="btn btn-secondary" onClick={closeQrModal}>
                                Cerrar
                            </button>
                            <button type="button" className="btn btn-primary" onClick={handleImprimirQr} disabled={!qrUrl}>
                                🖨️ Imprimir QR
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Modal */}
            {showModal && (
                <div className="modal-overlay" onClick={closeModal}>
                    <div className="modal-content" onClick={e => e.stopPropagation()}>
                        <h3>Nueva Asignación - Ruta La Paz</h3>
                        {submitError && <div className="error-message">{submitError}</div>}

                        <form onSubmit={handleSubmit}>
                            <div className="form-row">
                                <div className="form-group">
                                    <label>Número *</label>
                                    <input
                                        type="text"
                                        name="nro"
                                        value={form.nro}
                                        onChange={onChange}
                                        placeholder="Automático"
                                        readOnly
                                        style={{ backgroundColor: '#f5f5f5' }}
                                    />
                                    <small style={{ color: '#666', fontSize: '11px' }}>Se generará automáticamente al guardar si se deja vacío</small>
                                </div>
                                <div className="form-group">
                                    <label>Monto *</label>
                                    <input
                                        type="number"
                                        step="0.01"
                                        name="precio"
                                        value={form.precio}
                                        onChange={onChange}
                                        required
                                    />
                                    {!!fieldErrors.precio && <div className="error-message">{fieldErrors.precio}</div>}
                                </div>
                            </div>

                            <div className="form-row">
                                <div className="form-group">
                                    <label>Hora de Salida *</label>
                                    <input type="time" name="hora_salida" value={form.hora_salida} onChange={onChange} required />
                                    {!!fieldErrors.hora_salida && <div className="error-message">{fieldErrors.hora_salida}</div>}
                                </div>
                            </div>

                            <div className="form-row">
                                <div className="form-group">
                                    <label>Fecha Emisión *</label>
                                    <input type="date" name="fecha_emision" value={form.fecha_emision} onChange={onChange} required />
                                    {!!fieldErrors.fecha_emision && <div className="error-message">{fieldErrors.fecha_emision}</div>}
                                </div>
                                <div className="form-group">
                                    <label>Fecha Salida *</label>
                                    <input type="date" name="fecha_salida" value={form.fecha_salida} onChange={onChange} required />
                                    {!!fieldErrors.fecha_salida && <div className="error-message">{fieldErrors.fecha_salida}</div>}
                                </div>
                            </div>

                            <div className="form-row">
                                <div className="form-group">
                                    <label>Afiliado *</label>
                                    <select name="afiliado" value={form.afiliado} onChange={onChange} required>
                                        <option value="">Selecciona...</option>
                                        {afiliados.map(a => (
                                            <option key={a.id} value={a.id}>
                                                {a.apellidos} {a.nombres}
                                            </option>
                                        ))}
                                    </select>
                                    {!!fieldErrors.afiliado && <div className="error-message">{fieldErrors.afiliado}</div>}
                                    {(() => {
                                        const af = afiliados.find(a => String(a.id) === String(form.afiliado));
                                        if (!af) return null;
                                        return (
                                            <div style={{
                                                marginTop: '8px',
                                                padding: '8px',
                                                border: '1px solid #e0e0e0',
                                                borderRadius: '4px',
                                                background: '#fafafa'
                                            }}>
                                                <div style={{ fontWeight: 600 }}>{af.apellidos} {af.nombres}</div>
                                                <div style={{ fontSize: '12px', color: '#555' }}>
                                                    CI: {af.ci || '-'} {af.telefono ? `• Tel: ${af.telefono}` : ''}
                                                </div>
                                                {af.direccion && (
                                                    <div style={{ fontSize: '12px', color: '#555' }}>
                                                        Dirección: {af.direccion}
                                                    </div>
                                                )}
                                            </div>
                                        );
                                    })()}
                                </div>
                                <div className="form-group">
                                    <label>Vehículo *</label>
                                    <select name="vehiculo" value={form.vehiculo} onChange={onChange} required>
                                        <option value="">Selecciona...</option>
                                        {vehiculos.map(v => (
                                            <option key={v.id} value={v.id}>
                                                {v.placa} - {v.tipo}
                                            </option>
                                        ))}
                                    </select>
                                    {!!fieldErrors.vehiculo && <div className="error-message">{fieldErrors.vehiculo}</div>}
                                </div>
                            </div>

                            <div className="form-group">
                                <label>Ruta / Destino</label>
                                <select name="ruta" value={form.ruta} onChange={onChange} required>
                                    {rutas.map(r => (
                                        <option key={r.id} value={r.id}>
                                            {r.nombre} ({r.origen} → {r.destino})
                                        </option>
                                    ))}
                                </select>
                                {!!fieldErrors.ruta && <div className="error-message">{fieldErrors.ruta}</div>}
                            </div>

                            <div className="modal-actions">
                                <button type="button" className="btn btn-secondary" onClick={closeModal}>
                                    Cancelar
                                </button>
                                <button type="submit" className="btn btn-primary">
                                    Guardar Asignación
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}

export default AsignacionLaPaz;
