import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import YapeQRModal from '../components/YapeQRModal';
import '../css/PagosYEgresos.css';
import { IconPrinter, IconPencil, IconTrash } from '../components/Icons';

function PagosYEgresos() {
    const navigate = useNavigate();
    const [pagos, setPagos] = useState([]);
    const [egresos, setEgresos] = useState([]);
    const [countPagos, setCountPagos] = useState(0);
    const [countEgresos, setCountEgresos] = useState(0);
    const [afiliados, setAfiliados] = useState([]);
    const [tiposPago, setTiposPago] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [vehiculos, setVehiculos] = useState([]);
    const [rutas, setRutas] = useState([]);
    const [activeTab, setActiveTab] = useState('ingresos');
    const [searchQuery, setSearchQuery] = useState('');
    const [showModal, setShowModal] = useState(false);
    const [modalMode, setModalMode] = useState('create');
    const [submitError, setSubmitError] = useState('');
    const [fieldErrors, setFieldErrors] = useState({});
    const [form, setForm] = useState({});
    const [editingId, setEditingId] = useState(null);
    const [multaInfo, setMultaInfo] = useState(null); // Info de multa calculada
    const [metodoPago, setMetodoPago] = useState('efectivo');
    const [qrData, setQrData] = useState(null);
    const [verificandoPago, setVerificandoPago] = useState(false);
    const [pageIngresos, setPageIngresos] = useState(1);
    const [pageEgresos, setPageEgresos] = useState(1);
    const [pageSize, setPageSize] = useState(10);
    const [aplicarMulta, setAplicarMulta] = useState(true);

    const loadTableData = useCallback(async () => {
        try {
            setLoading(true);
            const [pagosRes, egresosRes] = await Promise.all([
                api.getPagos({ page: pageIngresos, page_size: pageSize }),
                api.getEgresos({ page: pageEgresos, page_size: pageSize })
            ]);

            const pagosList = pagosRes.data?.results || pagosRes.data || [];
            const egresosList = egresosRes.data?.results || egresosRes.data || [];

            setPagos(pagosList);
            setEgresos(egresosList);
            setCountPagos(pagosRes.data?.count ?? (Array.isArray(pagosList) ? pagosList.length : 0));
            setCountEgresos(egresosRes.data?.count ?? (Array.isArray(egresosList) ? egresosList.length : 0));
            setError('');
        } catch (err) {
            setError('Error al cargar los datos');
            console.error(err);
        } finally {
            setLoading(false);
        }
    }, [pageIngresos, pageEgresos, pageSize]);

    // Cargar datos auxiliares en segundo plano
    useEffect(() => {
        const loadAuxData = async () => {
            try {
                const [afiRes, tiposRes, veRes, ruRes] = await Promise.all([
                    api.getAfiliados({ page_size: 1000, ordering: 'apellidos' }),
                    api.getTiposPago(),
                    api.getVehiculos({ page_size: 1000 }),
                    api.getRutas({ page_size: 1000 })
                ]);
                setAfiliados(afiRes.data?.results || afiRes.data || []);
                setTiposPago(tiposRes.data?.results || tiposRes.data || []);
                setVehiculos(veRes.data?.results || veRes.data || []);
                setRutas(ruRes.data?.results || ruRes.data || []);
            } catch (err) {
                console.error("Error cargando datos auxiliares:", err);
            }
        };
        loadAuxData();
    }, []);

    useEffect(() => {
        loadTableData();
    }, [loadTableData]);

    useEffect(() => {
        if (activeTab !== 'ingresos') return;
        const tp = tiposPago.find(t => String(t.id) === String(form.tipo_pago));
        const isHoja = tp && /hoja/i.test(tp?.nombre || '') && /ruta/i.test(tp?.nombre || '');
        if (!isHoja) return;

        // No forzar monto si el usuario ya eligió uno manualmente o si podemos calcular uno mejor
        if (form.monto && parseFloat(form.monto) > 0 && !form._autoSet) return;

        let targetMonto = '20'; // Default Caranavi
        const rutaSelected = rutas.find(r => String(r.id) === String(form.ruta_id));
        const vehiculoSelected = vehiculos.find(v => String(v.id) === String(form.vehiculo_id));

        if (rutaSelected) {
            const nom = (rutaSelected.nombre || rutaSelected.destino || '').toLowerCase();
            if (nom.includes('la paz')) {
                if (vehiculoSelected) {
                    const tipo = (vehiculoSelected.tipo || '').toLowerCase();
                    if (tipo.includes('ipsum')) targetMonto = '0.00';
                    else if (tipo.includes('minibus') || tipo.includes('minibús')) targetMonto = '0.00';
                    else targetMonto = '0.00';
                } else {
                    targetMonto = '0.00';
                }
            } else if (nom.includes('caranavi')) {
                targetMonto = '0.00';
            }
        }

        if (aplicarMulta && multaInfo && multaInfo.monto_total) {
            targetMonto = String(multaInfo.monto_total);
        }

        if (String(form.monto || '') !== String(targetMonto)) {
            setForm(prev => ({ ...prev, monto: targetMonto, _autoSet: true }));
        }
    }, [multaInfo, form.tipo_pago, form.monto, form.ruta_id, form.vehiculo_id, activeTab, tiposPago, aplicarMulta, rutas, vehiculos]);



    const openCreate = () => {
        console.log("➡️ Abriendo modal de creación...");
        setModalMode('create');
        if (activeTab === 'ingresos') {
            setForm({ fecha_pago: '', monto: '0.00', tipo_pago: '', afiliado: '', observaciones: '', saldo_anterior_gestion: '0.00', banco: '', nro_operacion: '' });
            setMetodoPago('efectivo');
        } else {
            setForm({ fecha: '', monto: '0.00', descripcion: '', tipo_pago: '', banco: '', nro_operacion: '' });
            setMetodoPago('efectivo');
        }
        setSubmitError('');
        setFieldErrors({});
        setAplicarMulta(true);
        setShowModal(true);
    };

    const openEdit = (item) => {
        setModalMode('edit');
        if (activeTab === 'ingresos') {
            setForm({
                fecha_pago: item.fecha_pago || '',
                monto: String(item.monto || ''),
                tipo_pago: item.tipo_pago || '',
                afiliado: item.afiliado || '',
                saldo_anterior_gestion: String(item.saldo_anterior_gestion || '0.00'),
                observaciones: item.observaciones || '',
                banco: item.banco || '',
                nro_operacion: item.nro_operacion || ''
            });
            setMetodoPago(item.metodo_pago || 'efectivo');
        } else {
            setForm({
                fecha: item.fecha || '',
                monto: String(item.monto || ''),
                descripcion: item.descripcion || '',
                tipo_pago: item.tipo_pago || '',
                banco: item.banco || '',
                nro_operacion: item.nro_operacion || ''
            });
            setMetodoPago(item.metodo_pago || 'efectivo');
        }
        setSubmitError('');
        setFieldErrors({});
        setShowModal(true);
        setEditingId(item.id);
    };

    const onChange = async (e) => {
        const { name, value } = e.target;
        let nextForm = { ...form, [name]: value };

        if (activeTab === 'ingresos' && name === 'tipo_pago') {
            const tp = tiposPago.find(t => String(t.id) === String(value));
            const isHojaRuta = tp && /hoja/i.test(tp.nombre || '') && /ruta/i.test(tp.nombre || '');
            if (isHojaRuta) {
                // Si es hoja de ruta, intentar inicializar campos extras
                if (!nextForm.ruta_id) {
                    const rLP = rutas.find(r => (r.nombre || '').toLowerCase().includes('la paz'));
                    if (rLP) nextForm.ruta_id = rLP.id;
                }
                nextForm.monto = '0.00'; // Default with leading zero for accounting
            }
        }

        if (activeTab === 'ingresos' && name === 'afiliado') {
            // Autofill vehiculo si solo tiene uno
            const vs = vehiculos.filter(v => String(v.afiliado) === String(value));
            if (vs.length > 0) {
                nextForm.vehiculo_id = vs[0].id;
            } else {
                nextForm.vehiculo_id = '';
            }
        }

        if (name === 'monto') {
            nextForm._autoSet = false; // El usuario editó manualmente
        }

        setForm(nextForm);

        if (activeTab === 'ingresos' && (name === 'monto' || name === 'tipo_pago' || name === 'aplicar_multa')) {
            const tpId = name === 'tipo_pago' ? value : nextForm.tipo_pago;
            const montoC = name === 'monto' ? parseFloat(value) : parseFloat(nextForm.monto);
            const aplMulta = name === 'aplicar_multa' ? (e.target.type === 'checkbox' ? e.target.checked : value === 'true') : aplicarMulta;

            if (tpId && montoC > 0) {
                try {
                    const res = await api.calcularMontoConMulta(tpId, montoC, aplMulta);
                    setMultaInfo(res.data);
                } catch (err) {
                    setMultaInfo(null);
                    console.error(err);
                }
            } else {
                setMultaInfo(null);
            }
        }
    };

    const handleToggleMulta = async (checked) => {
        setAplicarMulta(checked);
        if (form.tipo_pago && (form.monto || 20)) {
            try {
                const res = await api.calcularMontoConMulta(form.tipo_pago, parseFloat(form.monto || 20), checked);
                setMultaInfo(res.data);
            } catch (err) {
                console.error(err);
            }
        }
    };

    const save = async (e) => {
        e.preventDefault();
        try {
            setSubmitError('');
            setFieldErrors({});

            // Validación básica manual antes de enviar
            if (activeTab === 'ingresos') {
                if (!form.afiliado || !form.tipo_pago || !form.fecha_pago) {
                    setSubmitError('Por favor complete los campos obligatorios: Afiliado, Tipo de Pago y Fecha.');
                    return;
                }
            } else {
                if (!form.tipo_pago || !form.fecha || !form.descripcion) {
                    setSubmitError('Por favor complete los campos obligatorios: Fecha, Tipo de Egreso y Descripción.');
                    return;
                }
            }

            const tpSel = tiposPago.find(t => String(t.id) === String(form.tipo_pago));
            const isHoja = activeTab === 'ingresos' && tpSel && /hoja/i.test(tpSel?.nombre || '') && /ruta/i.test(tpSel?.nombre || '');
            let montoCalculado = parseFloat(form.monto || '0');
            if (isHoja) {
                if (multaInfo && typeof multaInfo.monto_total !== 'undefined') {
                    montoCalculado = parseFloat(multaInfo.monto_total);
                } else {
                    try {
                        const resCalc = await api.calcularMontoConMulta(form.tipo_pago, montoCalculado || 20, aplicarMulta);
                        montoCalculado = parseFloat(resCalc.data?.monto_total ?? 20);
                    } catch {
                        montoCalculado = 20;
                    }
                }
                if (!montoCalculado || (montoCalculado < 20 && aplicarMulta)) montoCalculado = 20;
                if (!aplicarMulta) montoCalculado = 20;
            }

            // Limpiar y preparar payload de forma segura
            console.log("Datos del formulario antes de procesar:", form);

            const saldoGestion = form.saldo_anterior_gestion == null || form.saldo_anterior_gestion === ''
                ? 0
                : parseFloat(form.saldo_anterior_gestion);

            // Asegurarnos de que el monto sea el calculado si existe
            const montoFinal = parseFloat(montoCalculado);

            if (metodoPago === 'transferencia') {
                if (!form.banco || !form.nro_operacion) {
                    setSubmitError('Para transferencias, debe ingresar el Banco y el Nro de Operación.');
                    return;
                }
            }

            const payload = {
                ...form,
                monto: isNaN(montoFinal) ? 0 : montoFinal,
                saldo_anterior_gestion: isNaN(saldoGestion) ? 0 : saldoGestion,
                metodo_pago: metodoPago
            };

            console.log("Payload a enviar:", payload);

            // Validar monto
            if (payload.monto <= 0) {
                setSubmitError('El monto debe ser un número mayor a 0');
                return;
            }

            if (modalMode === 'create') {
                if (activeTab === 'ingresos') {
                    console.log("Enviando createPago...");
                    const res = await api.createPago(payload);
                    console.log("Respuesta createPago:", res);

                    if (metodoPago === 'qr') {
                        // Generar cobro QR
                        try {
                            const qrRes = await api.generarPagoQrIngreso(res.data.id);
                            setQrData(qrRes.data);
                            setShowModal(false); // Cerramos el de creación pero mantenemos el QR
                            return; // No navegamos aún
                        } catch (err) {
                            console.error("Error generando QR:", err);
                            alert("Ingreso registrado pero hubo un error generando el QR.");
                        }
                    }
                    navigate(`/recibo/ingreso/${res.data.id}`);
                } else {
                    const res = await api.createEgreso(payload);
                    navigate(`/recibo/egreso/${res.data.id}`);
                }
            } else {
                if (activeTab === 'ingresos') {
                    await api.updatePago(editingId, payload);
                } else {
                    await api.updateEgreso(editingId, payload);
                }
            }
            setShowModal(false);
            await loadTableData();
        } catch (err) {
            const data = err.response?.data;
            console.error("Error detallado:", data); // Log para debugging

            if (data && typeof data === 'object') {
                setFieldErrors(data);
                // Construir mensaje de error legible
                let message = data.detail || data.non_field_errors?.[0];

                if (!message) {
                    // Si hay errores de campos, mostrar el primero
                    const firstError = Object.values(data)[0];
                    if (Array.isArray(firstError)) message = firstError[0];
                    else if (typeof firstError === 'string') message = firstError;
                    else message = 'Verifique los campos marcados en rojo';
                }

                setSubmitError(message || 'Error al guardar');
            } else {
                setSubmitError('Error al guardar. Verifique su conexión.');
            }
            console.error(err);
        }
    };

    const remove = async (id) => {
        if (!window.confirm('¿Eliminar registro?')) return;
        try {
            if (activeTab === 'ingresos') {
                await api.deletePago(id);
            } else {
                await api.deleteEgreso(id);
            }
            await loadTableData();
        } catch (err) {
            alert('Error al eliminar');
            console.error(err);
        }
    };

    const verificarPago = async () => {
        if (!qrData) return;
        setVerificandoPago(true);
        try {
            // Extraer el ID del pago de la glosa: "Pago [Tipo] - ID: [ID] - ..."
            const match = qrData.glosa.match(/ID: (\d+)/);
            const pagoId = match ? match[1] : null;

            await api.verify_payment ? await api.verify_payment(qrData.transaction_id) : alert('Simulación: Pago Verificado');

            alert('¡Pago verificado exitosamente!');
            setQrData(null);
            if (pagoId) {
                navigate(`/recibo/ingreso/${pagoId}`);
            }
            await loadTableData();
        } catch (err) {
            console.error(err);
            alert('Aún no se ha detectado el pago. Por favor intenta de nuevo en unos momentos.');
        } finally {
            setVerificandoPago(false);
        }
    };

    const handleDescargarRecibo = async (id) => {
        try {
            const response = await api.generarReciboPago(id);
            const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `recibo_NRO-${String(id).padStart(6, '0')}.pdf`);
            document.body.appendChild(link);
            link.click();
            link.remove();
            window.URL.revokeObjectURL(url);
        } catch (err) {
            alert('Error al descargar el recibo');
            console.error(err);
        }
    };

    // Filtrar tipos de pago según el tab activo
    const tiposPagoFiltrados = tiposPago.filter(tp =>
        activeTab === 'ingresos' ? tp.tipo === 'ingreso' : tp.tipo === 'egreso'
    );

    const filteredPagos = pagos.filter(item =>
        (item.afiliado_nombre && item.afiliado_nombre.toLowerCase().includes(searchQuery.toLowerCase())) ||
        (item.tipo_pago_nombre && item.tipo_pago_nombre.toLowerCase().includes(searchQuery.toLowerCase()))
    );

    const filteredEgresos = egresos.filter(item =>
        (item.descripcion && item.descripcion.toLowerCase().includes(searchQuery.toLowerCase())) ||
        (item.tipo_pago_nombre && item.tipo_pago_nombre.toLowerCase().includes(searchQuery.toLowerCase()))
    );

    return (
        <div className="pagos-y-egresos-container">
            <h1>Módulo de Pagos y Egresos</h1>
            <p>Aquí podrás gestionar todos los ingresos y egresos económicos del sindicato.</p>

            <div className="card">
                <div className="tabs">
                    <button className={activeTab === 'ingresos' ? 'active' : ''} onClick={() => setActiveTab('ingresos')}>
                        Ingresos
                    </button>
                    <button className={activeTab === 'egresos' ? 'active' : ''} onClick={() => setActiveTab('egresos')}>
                        Egresos
                    </button>
                </div>

                <div className="table-header">
                    <input
                        type="text"
                        placeholder="Buscar..."
                        className="search-input"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                    />
                    <select
                        value={pageSize}
                        onChange={(e) => {
                            const v = parseInt(e.target.value || '10', 10);
                            setPageSize(v);
                            setPageIngresos(1);
                            setPageEgresos(1);
                        }}
                        style={{ marginLeft: '10px' }}
                    >
                        <option value={10}>10</option>
                        <option value={20}>20</option>
                        <option value={50}>50</option>
                    </select>
                    <button className="btn btn-success" style={{ marginLeft: '10px' }} onClick={() => activeTab === 'ingresos' ? api.downloadPagosExcel() : api.downloadEgresosExcel()}>
                        📥 Descargar Excel
                    </button>
                    <button className="btn btn-primary" onClick={openCreate}>
                        <span>{activeTab === 'ingresos' ? '➕ Registrar Ingreso' : '➕ Registrar Egreso'}</span>
                    </button>

                </div>

                {loading ? (
                    <div className="loading">Cargando...</div>
                ) : error ? (
                    <div className="error">{error}</div>
                ) : (
                    <div className="table-wrapper">
                        {activeTab === 'ingresos' ? (
                            <table>
                                <thead>
                                    <tr>
                                        <th>ID</th>
                                        <th>Fecha</th>
                                        <th>Afiliado</th>
                                        <th>Tipo de Pago</th>
                                        <th>Monto (Bs.)</th>
                                        <th>Observaciones</th>
                                        <th>Acciones</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {filteredPagos.length > 0 ? (
                                        filteredPagos.map((pago) => (
                                            <tr key={pago.id}>
                                                <td>{pago.id}</td>
                                                <td>{pago.fecha_pago}</td>
                                                <td>{pago.afiliado_nombre}</td>
                                                <td>{pago.tipo_pago_nombre}</td>
                                                <td>{parseFloat(pago.monto).toFixed(2)}</td>
                                                <td>{pago.observaciones || '-'}</td>
                                                <td className="actions">
                                                    <button className="btn-icon btn-print" onClick={() => handleDescargarRecibo(pago.id)} title="Descargar Recibo"><IconPrinter /></button>
                                                    <button className="btn-icon btn-edit" onClick={() => openEdit(pago)} title="Editar"><IconPencil /></button>
                                                    <button className="btn-icon btn-delete" onClick={() => remove(pago.id)} title="Eliminar"><IconTrash /></button>
                                                </td>
                                            </tr>
                                        ))
                                    ) : (
                                        <tr>
                                            <td colSpan="7" style={{ textAlign: 'center' }}>No se encontraron ingresos</td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        ) : (
                            <table>
                                <thead>
                                    <tr>
                                        <th>ID</th>
                                        <th>Fecha</th>
                                        <th>Tipo de Egreso</th>
                                        <th>Descripción</th>
                                        <th>Monto (Bs.)</th>
                                        <th>Acciones</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {filteredEgresos.length > 0 ? (
                                        filteredEgresos.map((egreso) => (
                                            <tr key={egreso.id}>
                                                <td>{egreso.id}</td>
                                                <td>{egreso.fecha}</td>
                                                <td>{egreso.tipo_pago_nombre}</td>
                                                <td>{egreso.descripcion}</td>
                                                <td>{parseFloat(egreso.monto).toFixed(2)}</td>
                                                <td className="actions">
                                                    <button className="btn-icon btn-edit" onClick={() => openEdit(egreso)} title="Editar"><IconPencil /></button>
                                                    <button className="btn-icon btn-delete" onClick={() => remove(egreso.id)} title="Eliminar"><IconTrash /></button>
                                                </td>
                                            </tr>
                                        ))
                                    ) : (
                                        <tr>
                                            <td colSpan="6" style={{ textAlign: 'center' }}>No se encontraron egresos</td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        )}
                        <div className="pagination-wrapper" style={{ display: 'flex', gap: '15px', alignItems: 'center', marginTop: '2rem', justifyContent: 'center' }}>
                            <button
                                className="btn btn-secondary"
                                onClick={() => {
                                    if (activeTab === 'ingresos') setPageIngresos(p => Math.max(1, p - 1));
                                    else setPageEgresos(p => Math.max(1, p - 1));
                                }}
                                disabled={(activeTab === 'ingresos' ? pageIngresos : pageEgresos) <= 1}
                            >
                                ← Anterior
                            </button>
                            <span className="pagination-info">
                                Página {activeTab === 'ingresos' ? pageIngresos : pageEgresos} de {Math.ceil((activeTab === 'ingresos' ? countPagos : countEgresos) / pageSize)}
                            </span>
                            <button
                                className="btn btn-secondary"
                                onClick={() => {
                                    const count = activeTab === 'ingresos' ? countPagos : countEgresos;
                                    const page = activeTab === 'ingresos' ? pageIngresos : pageEgresos;
                                    if (page * pageSize < count) {
                                        if (activeTab === 'ingresos') setPageIngresos(p => p + 1);
                                        else setPageEgresos(p => p + 1);
                                    }
                                }}
                                disabled={(activeTab === 'ingresos' ? pageIngresos : pageEgresos) * pageSize >= (activeTab === 'ingresos' ? countPagos : countEgresos)}
                            >
                                Siguiente →
                            </button>
                            <span className="pagination-info" style={{ marginLeft: 'auto', opacity: 0.7 }}>
                                Total: {activeTab === 'ingresos' ? countPagos : countEgresos} registros
                            </span>
                        </div>
                    </div>
                )}
            </div>

            {showModal && (
                <div className="modal-overlay" onClick={() => setShowModal(false)}>
                    <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                        <div className="modal-header">
                            <h2>{modalMode === 'create' ? (activeTab === 'ingresos' ? 'Nuevo Ingreso' : 'Nuevo Egreso') : (activeTab === 'ingresos' ? 'Editar Ingreso' : 'Editar Egreso')}</h2>
                            <button className="modal-close" onClick={() => setShowModal(false)}>✕</button>
                        </div>
                        {submitError && <div className="error" style={{ marginBottom: '10px' }}>{submitError}</div>}
                        <form onSubmit={save} className="modal-form">
                            {activeTab === 'ingresos' ? (
                                <>
                                    <div className="form-group">
                                        <label htmlFor="fecha_pago">Fecha de Pago *</label>
                                        <input id="fecha_pago" name="fecha_pago" type="date" value={form.fecha_pago} onChange={onChange} required />
                                        {fieldErrors.fecha_pago && <div className="error">{fieldErrors.fecha_pago}</div>}
                                    </div>
                                    <div className="form-group">
                                        <label htmlFor="afiliado">Afiliado *</label>
                                        <select id="afiliado" name="afiliado" value={form.afiliado} onChange={onChange} required>
                                            <option value="">Selecciona un afiliado...</option>
                                            {Array.isArray(afiliados) && afiliados.map(a => (
                                                <option key={a.id} value={a.id}>{a.apellidos} {a.nombres}</option>
                                            ))}
                                        </select>
                                        {fieldErrors.afiliado && <div className="error">{fieldErrors.afiliado}</div>}
                                    </div>
                                    <div className="form-group">
                                        <label htmlFor="tipo_pago">Tipo de Pago *</label>
                                        <select id="tipo_pago" name="tipo_pago" value={form.tipo_pago} onChange={onChange} required>
                                            <option value="">Selecciona tipo de pago...</option>
                                            {tiposPagoFiltrados.map(tp => (
                                                <option key={tp.id} value={tp.id}>{tp.nombre}</option>
                                            ))}
                                        </select>
                                        {fieldErrors.tipo_pago && <div className="error">{fieldErrors.tipo_pago}</div>}
                                    </div>

                                    {(() => {
                                        const tpSel = tiposPago.find(t => String(t.id) === String(form.tipo_pago));
                                        const isHoja = tpSel && /hoja/i.test(tpSel?.nombre || '') && /ruta/i.test(tpSel?.nombre || '');
                                        if (!isHoja) return null;

                                        return (
                                            <>
                                                <div className="form-group">
                                                    <label htmlFor="ruta_id">Ruta / Destino</label>
                                                    <select id="ruta_id" name="ruta_id" value={form.ruta_id} onChange={onChange}>
                                                        <option value="">Selecciona ruta...</option>
                                                        {rutas.map(r => (
                                                            <option key={r.id} value={r.id}>{r.nombre}</option>
                                                        ))}
                                                    </select>
                                                </div>
                                                <div className="form-group">
                                                    <label htmlFor="vehiculo_id">Vehículo del Afiliado</label>
                                                    <select id="vehiculo_id" name="vehiculo_id" value={form.vehiculo_id} onChange={onChange}>
                                                        <option value="">Selecciona vehículo...</option>
                                                        {vehiculos.filter(v => String(v.afiliado) === String(form.afiliado)).map(v => (
                                                            <option key={v.id} value={v.id}>{v.placa} — {(v.tipo || '').toUpperCase()}</option>
                                                        ))}
                                                    </select>
                                                </div>
                                                <div className="form-group" style={{ background: 'rgba(99, 102, 241, 0.05)', padding: '15px', borderRadius: '12px', border: '1px dashed #6366f1', marginBottom: '15px' }}>
                                                <label style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: 'pointer', margin: 0 }}>
                                                    <span>🚨 ¿Aplicar multa de 50 Bs?</span>
                                                    <div className="toggle-switch" style={{ position: 'relative', width: '50px', height: '26px' }}>
                                                        <input
                                                            type="checkbox"
                                                            checked={aplicarMulta}
                                                            onChange={(e) => handleToggleMulta(e.target.checked)}
                                                            style={{ opacity: 0, width: 0, height: 0 }}
                                                        />
                                                        <span className="slider" style={{
                                                            position: 'absolute', cursor: 'pointer', top: 0, left: 0, right: 0, bottom: 0,
                                                            backgroundColor: aplicarMulta ? '#6366f1' : '#ccc', transition: '.4s', borderRadius: '34px'
                                                        }}>
                                                            <span style={{
                                                                position: 'absolute', height: '18px', width: '18px', left: aplicarMulta ? '28px' : '4px', bottom: '4px',
                                                                backgroundColor: 'white', transition: '.4s', borderRadius: '50%'
                                                            }}></span>
                                                        </span>
                                                    </div>
                                                </label>
                                                <small style={{ marginTop: '8px', display: 'block', opacity: 0.7 }}>
                                                    {aplicarMulta ? 'La multa se sumará al monto base del pasaje.' : 'Se cobrará solo el monto base (20 Bs).'}
                                                </small>
                                            </div>
                                            </>
                                        );
                                    })()}

                                    {/* Alerta de multa */}
                                    {multaInfo && multaInfo.tiene_multa && (
                                        <div className="alert-multa warning">
                                            <strong>⚠️ Pago fuera de plazo</strong>
                                            <p className="alert-message">
                                                {multaInfo.mensaje}
                                            </p>
                                            <div className="alert-details">
                                                <div>• Monto base: {multaInfo.monto_base} Bs</div>
                                                <div>• Multa: <strong className="text-danger">{multaInfo.multa} Bs</strong></div>
                                                <div>• <strong>Total a pagar: {multaInfo.monto_total} Bs</strong></div>
                                            </div>
                                        </div>
                                    )}

                                    {multaInfo && !multaInfo.tiene_multa && multaInfo.mensaje && (
                                        <div className="alert-multa success">
                                            ✅ {multaInfo.mensaje}
                                        </div>
                                    )}

                                    {activeTab === 'ingresos' && modalMode === 'create' && (
                                        <div className="form-group">
                                            <label>Método de Pago *</label>
                                            <div style={{ display: 'flex', gap: '20px', marginTop: '10px' }}>
                                                <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                                                    <input
                                                        type="radio"
                                                        name="metodoPago"
                                                        value="efectivo"
                                                        checked={metodoPago === 'efectivo'}
                                                        onChange={() => setMetodoPago('efectivo')}
                                                    />
                                                    💵 Efectivo
                                                </label>
                                                <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                                                    <input
                                                        type="radio"
                                                        name="metodoPago"
                                                        value="qr"
                                                        checked={metodoPago === 'qr'}
                                                        onChange={() => setMetodoPago('qr')}
                                                    />
                                                    📱 Yape (QR)
                                                </label>
                                                <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                                                    <input
                                                        type="radio"
                                                        name="metodoPago"
                                                        value="transferencia"
                                                        checked={metodoPago === 'transferencia'}
                                                        onChange={() => setMetodoPago('transferencia')}
                                                    />
                                                    🏦 Transferencia
                                                </label>
                                            </div>
                                        </div>
                                    )}

                                    <div className="form-group">
                                        <label htmlFor="monto">Monto (Bs.) *</label>
                                        {(() => {
                                            const tpSel = tiposPago.find(tp => String(tp.id) === String(form.tipo_pago));
                                            const isHojaRuta = tpSel && /hoja/i.test(tpSel?.nombre || '') && /ruta/i.test(tpSel?.nombre || '');
                                            return (
                                                <input
                                                    id="monto"
                                                    name="monto"
                                                    type="text"
                                                    inputMode="decimal"
                                                    placeholder="0.00"
                                                    value={form.monto}
                                                    onChange={(e) => {
                                                        const val = e.target.value;
                                                        if (val === '' || /^\d*\.?\d*$/.test(val)) {
                                                            onChange(e);
                                                        }
                                                    }}
                                                    onFocus={(e) => { if(e.target.value === '0' || e.target.value === '0.00') setForm(prev => ({...prev, monto: ''})) }}
                                                    onBlur={(e) => { if(e.target.value === '') setForm(prev => ({...prev, monto: '0.00'})) }}
                                                    required
                                                    title={isHojaRuta ? 'Ingrese el monto manualmente' : undefined}
                                                />
                                            );
                                        })()}
                                        {fieldErrors.monto && <div className="error">{fieldErrors.monto}</div>}
                                    </div>
                                    <div className="form-group">
                                        <label htmlFor="saldo_anterior_gestion">Saldo Anterior Gestión (Bs.)</label>
                                        <input
                                            id="saldo_anterior_gestion"
                                            name="saldo_anterior_gestion"
                                            type="text"
                                            inputMode="decimal"
                                            placeholder="0.00"
                                            value={form.saldo_anterior_gestion}
                                            onChange={(e) => {
                                                const val = e.target.value;
                                                if (val === '' || /^\d*\.?\d*$/.test(val)) {
                                                    onChange(e);
                                                }
                                            }}
                                            onFocus={(e) => { if(e.target.value === '0' || e.target.value === '0.00') setForm(prev => ({...prev, saldo_anterior_gestion: ''})) }}
                                            onBlur={(e) => { if(e.target.value === '') setForm(prev => ({...prev, saldo_anterior_gestion: '0.00'})) }}
                                        />
                                        {fieldErrors.saldo_anterior_gestion && <div className="error">{fieldErrors.saldo_anterior_gestion}</div>}
                                    </div>
                                    
                                    {metodoPago === 'transferencia' && (
                                        <div style={{ display: 'flex', gap: '15px' }}>
                                            <div className="form-group" style={{ flex: 1 }}>
                                                <label htmlFor="banco">Banco *</label>
                                                <input id="banco" name="banco" type="text" placeholder="Ej. BNB, BMSC..." value={form.banco} onChange={onChange} required={metodoPago === 'transferencia'} />
                                            </div>
                                            <div className="form-group" style={{ flex: 1 }}>
                                                <label htmlFor="nro_operacion">Nro Transacción / Operación *</label>
                                                <input id="nro_operacion" name="nro_operacion" type="text" placeholder="Ej. 12345678" value={form.nro_operacion} onChange={onChange} required={metodoPago === 'transferencia'} />
                                            </div>
                                        </div>
                                    )}

                                    <div className="form-group">
                                        <label htmlFor="observaciones">Observaciones</label>
                                        <textarea id="observaciones" name="observaciones" value={form.observaciones} onChange={onChange} rows="3"></textarea>
                                        {fieldErrors.observaciones && <div className="error">{fieldErrors.observaciones}</div>}
                                    </div>
                                </>
                            ) : (
                                <>
                                    <div className="form-group">
                                        <label htmlFor="fecha">Fecha *</label>
                                        <input id="fecha" name="fecha" type="date" value={form.fecha} onChange={onChange} required />
                                        {fieldErrors.fecha && <div className="error">{fieldErrors.fecha}</div>}
                                    </div>
                                    <div className="form-group">
                                        <label htmlFor="tipo_pago">Tipo de Egreso *</label>
                                        <select id="tipo_pago" name="tipo_pago" value={form.tipo_pago} onChange={onChange} required>
                                            <option value="">Selecciona tipo de egreso...</option>
                                            {tiposPagoFiltrados.map(tp => (
                                                <option key={tp.id} value={tp.id}>{tp.nombre}</option>
                                            ))}
                                        </select>
                                        {fieldErrors.tipo_pago && <div className="error">{fieldErrors.tipo_pago}</div>}
                                    </div>
                                    <div className="form-group">
                                        <label htmlFor="descripcion">Descripción *</label>
                                        <input id="descripcion" name="descripcion" type="text" value={form.descripcion} onChange={onChange} required />
                                        {fieldErrors.descripcion && <div className="error">{fieldErrors.descripcion}</div>}
                                    </div>

                                    {modalMode === 'create' && (
                                        <div className="form-group">
                                            <label>Método de Pago *</label>
                                            <div style={{ display: 'flex', gap: '20px', marginTop: '10px' }}>
                                                <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                                                    <input
                                                        type="radio"
                                                        name="metodoPago"
                                                        value="efectivo"
                                                        checked={metodoPago === 'efectivo'}
                                                        onChange={() => setMetodoPago('efectivo')}
                                                    />
                                                    💵 Efectivo
                                                </label>
                                                <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                                                    <input
                                                        type="radio"
                                                        name="metodoPago"
                                                        value="transferencia"
                                                        checked={metodoPago === 'transferencia'}
                                                        onChange={() => setMetodoPago('transferencia')}
                                                    />
                                                    🏦 Transferencia
                                                </label>
                                            </div>
                                        </div>
                                    )}

                                    {metodoPago === 'transferencia' && (
                                        <div style={{ display: 'flex', gap: '15px' }}>
                                            <div className="form-group" style={{ flex: 1 }}>
                                                <label htmlFor="banco">Banco *</label>
                                                <input id="banco" name="banco" type="text" placeholder="Ej. BNB, BMSC..." value={form.banco} onChange={onChange} required={metodoPago === 'transferencia'} />
                                            </div>
                                            <div className="form-group" style={{ flex: 1 }}>
                                                <label htmlFor="nro_operacion">Nro Transacción / Operación *</label>
                                                <input id="nro_operacion" name="nro_operacion" type="text" placeholder="Ej. 12345678" value={form.nro_operacion} onChange={onChange} required={metodoPago === 'transferencia'} />
                                            </div>
                                        </div>
                                    )}

                                    <div className="form-group">
                                        <label htmlFor="monto">Monto (Bs.) *</label>
                                        <input id="monto" name="monto" type="text" inputMode="decimal" placeholder="0.00" value={form.monto} 
                                            onChange={(e) => {
                                                const val = e.target.value;
                                                if (val === '' || /^\d*\.?\d*$/.test(val)) {
                                                    onChange(e);
                                                }
                                            }}
                                            onFocus={(e) => { if(e.target.value === '0' || e.target.value === '0.00') setForm(prev => ({...prev, monto: ''})) }}
                                            onBlur={(e) => { if(e.target.value === '') setForm(prev => ({...prev, monto: '0.00'})) }}
                                            required />
                                        {fieldErrors.monto && <div className="error">{fieldErrors.monto}</div>}
                                    </div>
                                </>
                            )}
                            <div className="form-actions">
                                <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>Cancelar</button>
                                <button type="submit" className="btn btn-primary">Guardar</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* Modal de Pago QR (Yape) Reutilizable */}
            <YapeQRModal
                qrData={qrData}
                onVerify={verificarPago}
                onClose={() => setQrData(null)}
                verifying={verificandoPago}
            />
        </div>
    );
}

export default PagosYEgresos;
