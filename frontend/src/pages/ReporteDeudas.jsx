import { useState, useEffect, useRef } from 'react';
import api from '../services/api';
import YapeQRModal from '../components/YapeQRModal';
import { Pie } from 'react-chartjs-2';
import ChartDataLabels from 'chartjs-plugin-datalabels';
import {
    Chart as ChartJS,
    ArcElement,
    Tooltip,
    Legend
} from 'chart.js';
import './ReportesFinancieros.css'; // Reutilizamos estilos
import '../css/Common.css'; // Modales

ChartJS.register(ArcElement, Tooltip, Legend, ChartDataLabels);

function ReporteDeudas() {
    const [subTab, setSubTab] = useState('deudores'); // 'deudores' | 'cancelaron'
    const [afiliados, setAfiliados] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [pagina, setPagina] = useState(1);
    const [paginasTotales, setPaginasTotales] = useState(1);
    const [totalItems, setTotalItems] = useState(0);
    const [searchTerm, setSearchTerm] = useState('');

    const [resumen, setResumen] = useState({
        total_activos: 0,
        total_deudores: 0,
        total_cancelaron: 0,
        porcentaje_al_dia: 0,
        monto_por_cobrar: 0,
        monto_cuotas: 0,
        monto_sanciones: 0,
        aportes_por_tipo: []
    });

    // QR States
    const [qrData, setQrData] = useState(null);
    const [verificandoPago, setVerificandoPago] = useState(false);

    // Detalle de deuda (aportes/cuotas y multas)
    const [detalleAfiliado, setDetalleAfiliado] = useState(null);

    // Identifica la última petición para descartar respuestas viejas al cambiar de pestaña
    const requestIdRef = useRef(0);

    useEffect(() => {
        loadData(pagina, subTab);
    }, [pagina, subTab]);

    const loadData = async (page = 1, currentSubTab = subTab) => {
        const requestId = ++requestIdRef.current;
        try {
            setLoading(true);
            const res = await api.getAfiliadosMorosos({
                page,
                page_size: 20,
                lista: currentSubTab,
                meses: 0, // Toda la deuda pendiente para Estado de Cuentas
                incluir_detalle: 'true'
            });

            if (requestId !== requestIdRef.current) return;

            if (res.data) {
                if (currentSubTab === 'cancelaron') {
                    setAfiliados(res.data.cancelaron || []);
                } else {
                    setAfiliados(res.data.morosos || []);
                }

                if (res.data.resumen) {
                    setResumen(prev => ({ ...prev, ...res.data.resumen }));
                }
                setPaginasTotales(res.data.total_pages || 1);
                setTotalItems(res.data.count || 0);
            }
            setError('');
        } catch (err) {
            if (requestId !== requestIdRef.current) return;
            setError('Error al cargar reporte de estado de cuentas');
            console.error(err);
        } finally {
            if (requestId === requestIdRef.current) setLoading(false);
        }
    };

    const handleTabChange = (newTab) => {
        if (newTab === subTab) return;
        setSubTab(newTab);
        setPagina(1);
        setSearchTerm('');
        setAfiliados([]);
    };

    const handlePagarTotal = async (afiliado) => {
        try {
            setLoading(true);
            const res = await api.generarPagoQrTotalAfiliado(afiliado.afiliado_id);
            setQrData(res.data);
        } catch (err) {
            console.error(err);
            alert('Error al generar QR de pago: ' + (err.response?.data?.error || 'Error desconocido'));
        } finally {
            setLoading(false);
        }
    };

    const verificarPagoQR = async () => {
        if (!qrData) return;
        setVerificandoPago(true);
        try {
            const res = await api.verifyPagoQr(qrData.transaction_id);
            if (res.data?.status !== 'ok') {
                throw new Error(res.data?.message || 'El pago aún no se ha confirmado');
            }
            alert('¡Pago verificado exitosamente!');
            setQrData(null);
            loadData(pagina, subTab);
        } catch (err) {
            console.error(err);
            alert('Aún no se ha detectado el pago. Por favor intenta de nuevo en unos momentos.');
        } finally {
            setVerificandoPago(false);
        }
    };

    const handleDownloadPdf = async () => {
        try {
            const res = await api.downloadAfiliadosMorososPdf({ meses: 0 });
            if (!res.success) {
                alert('Error al descargar PDF: ' + res.error);
            }
        } catch (e) {
            console.error(e);
            alert('Error al descargar PDF');
        }
    };

    const filteredAfiliados = afiliados.filter(a => {
        if (!searchTerm.trim()) return true;
        const term = searchTerm.toLowerCase();
        const nombre = (a.nombre_completo || '').toLowerCase();
        const ci = (a.ci || '').toLowerCase();
        const telf = (a.telefono || '').toLowerCase();
        return nombre.includes(term) || ci.includes(term) || telf.includes(term);
    });

    const detalleAportes = detalleAfiliado?.detalle_aportes || [];
    const detalleSanciones = detalleAfiliado?.detalle_sanciones || [];
    const totalDetalleAportes = detalleAportes.reduce((sum, a) => sum + a.monto, 0);
    const totalDetalleSanciones = detalleSanciones.reduce((sum, s) => sum + s.monto, 0);

    if (loading && afiliados.length === 0) {
        return <div className="loading">Cargando estado de cuentas...</div>;
    }
    if (error) return <div className="error">{error}</div>;

    return (
        <div className="reportes-container">
            {/* Header del Reporte */}
            <div className="report-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap', gap: '1rem' }}>
                <div>
                    <h1>Estado de Cuentas por Afiliado</h1>
                    <p>Quiénes cancelaron vs. deudores, con el detalle de todos sus aportes, cuotas y multas pendientes.</p>
                </div>
                <button className="btn btn-primary" onClick={handleDownloadPdf}>
                    📄 Descargar Reporte PDF
                </button>
            </div>

            {/* KPIs Grid + Gráfico de Torta */}
            <div className="metrics-grid" style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '20px', alignItems: 'stretch' }}>
                {/* 4 Tarjetas de Métricas */}
                <div className="deudas-kpis-grid">
                    <div className="metric-card" style={{ borderLeft: '4px solid #e53e3e' }}>
                        <h3>Monto por Cobrar</h3>
                        <div className="metric-value" style={{ color: '#e53e3e', fontSize: '1.45rem' }}>
                            Bs. {resumen.monto_por_cobrar.toFixed(2)}
                        </div>
                        <p style={{ fontSize: '0.85rem', color: '#718096' }}>
                            Aportes/Cuotas: Bs. {resumen.monto_cuotas.toFixed(2)} · Multas: Bs. {resumen.monto_sanciones.toFixed(2)}
                        </p>
                    </div>

                    <div className="metric-card" style={{ borderLeft: '4px solid #dd6b20' }}>
                        <h3>Deudores</h3>
                        <div className="metric-value" style={{ color: '#dd6b20', fontSize: '1.45rem' }}>
                            {resumen.total_deudores}
                        </div>
                        <p style={{ fontSize: '0.85rem', color: '#718096' }}>De {resumen.total_activos} afiliados activos</p>
                    </div>

                    <div className="metric-card" style={{ borderLeft: '4px solid #38a169' }}>
                        <h3>Que Cancelaron</h3>
                        <div className="metric-value" style={{ color: '#38a169', fontSize: '1.45rem' }}>
                            {resumen.total_cancelaron}
                        </div>
                        <p style={{ fontSize: '0.85rem', color: '#718096' }}>Afiliados activos al día</p>
                    </div>

                    <div className="metric-card" style={{ borderLeft: '4px solid #3182ce' }}>
                        <h3>% Al Día</h3>
                        <div className="metric-value" style={{ color: '#3182ce', fontSize: '1.45rem' }}>
                            {resumen.porcentaje_al_dia}%
                        </div>
                        <p style={{ fontSize: '0.85rem', color: '#718096' }}>Índice de cumplimiento</p>
                    </div>
                </div>

                {/* Gráfico Torta */}
                <div className="chart-card" style={{ padding: '15px', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                    <h3 style={{ marginBottom: '8px', fontSize: '0.95rem', textAlign: 'center' }}>Estado Global (%)</h3>
                    <div style={{ maxWidth: '200px', margin: '0 auto', width: '100%' }}>
                        <Pie
                            data={{
                                labels: ['Al Día', 'Con Deuda'],
                                datasets: [{
                                    data: [resumen.total_cancelaron, resumen.total_deudores],
                                    backgroundColor: ['#38a169', '#e53e3e'],
                                    hoverBackgroundColor: ['#2f855a', '#c53030'],
                                    borderWidth: 2,
                                    borderColor: '#ffffff'
                                }]
                            }}
                            options={{
                                plugins: {
                                    legend: { position: 'bottom', labels: { boxWidth: 12, font: { size: 11 } } },
                                    datalabels: {
                                        color: '#fff',
                                        font: { weight: 'bold', size: 11 },
                                        formatter: (value, ctx) => {
                                            const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
                                            return total > 0 ? ((value / total) * 100).toFixed(1) + "%" : "0%";
                                        }
                                    }
                                }
                            }}
                        />
                    </div>
                </div>
            </div>

            {/* Sub-pestañas: Deudores vs. Que Cancelaron */}
            <div className="tabs-container deudas-subtabs" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                    <button
                        className={`tab-button ${subTab === 'deudores' ? 'active' : ''}`}
                        onClick={() => handleTabChange('deudores')}
                    >
                        ❌ Deudores ({resumen.total_deudores})
                    </button>
                    <button
                        className={`tab-button ${subTab === 'cancelaron' ? 'active' : ''}`}
                        onClick={() => handleTabChange('cancelaron')}
                    >
                        ✅ Que Cancelaron ({resumen.total_cancelaron})
                    </button>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <input
                        type="text"
                        placeholder="Buscar por nombre, CI o telf..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        style={{
                            padding: '0.45rem 0.85rem',
                            borderRadius: '8px',
                            border: '1px solid #cbd5e0',
                            fontSize: '0.875rem',
                            minWidth: '240px'
                        }}
                    />
                    {searchTerm && (
                        <button
                            className="btn btn-secondary"
                            style={{ padding: '0.45rem 0.75rem', fontSize: '0.8rem' }}
                            onClick={() => setSearchTerm('')}
                        >
                            ✕
                        </button>
                    )}
                </div>
            </div>

            {/* Resumen de aportes/cuotas pendientes por tipo */}
            {subTab === 'deudores' && resumen.aportes_por_tipo.length > 0 && (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', margin: '0 0 0.5rem' }}>
                    {resumen.aportes_por_tipo.map(t => (
                        <div
                            key={t.tipo}
                            style={{
                                background: '#fff5f5',
                                border: '1px solid #feb2b2',
                                borderRadius: '8px',
                                padding: '0.4rem 0.75rem',
                                fontSize: '0.85rem',
                                color: '#742a2a'
                            }}
                        >
                            {t.etiqueta}: <strong>Bs. {t.monto.toFixed(2)}</strong>
                            <span style={{ color: '#975a5a' }}> ({t.cantidad} pend.)</span>
                        </div>
                    ))}
                </div>
            )}

            {/* Tabla de Resultados */}
            <div className="table-container" style={{ marginTop: '10px' }}>
                {subTab === 'deudores' ? (
                    <table className="vehiculos-table">
                        <thead>
                            <tr>
                                <th>Afiliado</th>
                                <th>Carnet (CI)</th>
                                <th>Faltas</th>
                                <th>Deuda Cuotas</th>
                                <th>Deuda Multas</th>
                                <th>Total Deuda</th>
                                <th>Nivel Morosidad</th>
                                <th>Acciones</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filteredAfiliados.length === 0 ? (
                                <tr>
                                    <td colSpan="8" className="no-data" style={{ padding: '2rem', textAlign: 'center' }}>
                                        {searchTerm ? 'No se encontraron deudores con ese criterio de búsqueda.' : '¡Excelente! Todos los afiliados están al día 🎉'}
                                    </td>
                                </tr>
                            ) : (
                                filteredAfiliados.map(a => (
                                    <tr key={a.afiliado_id}>
                                        <td>
                                            <div style={{ fontWeight: 'bold' }}>{a.nombre_completo}</div>
                                            <div style={{ fontSize: '0.8em', color: '#666' }}>{a.telefono || 'Sin telf.'}</div>
                                        </td>
                                        <td>{a.ci}</td>
                                        <td>
                                            {a.cantidad_faltas > 0 ? (
                                                <span className="badge badge-danger" style={{ backgroundColor: '#e53e3e' }}>{a.cantidad_faltas}</span>
                                            ) : (
                                                <span style={{ color: '#ccc' }}>0</span>
                                            )}
                                        </td>
                                        <td>
                                            {a.deuda_cuotas > 0 && <div style={{ fontSize: '0.85em', color: '#666' }}>{a.cantidad_cuotas_pendientes} pendientes</div>}
                                            Bs. {Number(a.deuda_cuotas || 0).toFixed(2)}
                                        </td>
                                        <td>
                                            {a.deuda_sanciones > 0 && <div style={{ fontSize: '0.85em', color: '#666' }}>{a.cantidad_sanciones_pendientes} pendientes</div>}
                                            Bs. {Number(a.deuda_sanciones || 0).toFixed(2)}
                                        </td>
                                        <td style={{ fontWeight: 'bold', color: a.deuda_total > 500 ? '#c53030' : 'inherit' }}>
                                            Bs. {Number(a.deuda_total || 0).toFixed(2)}
                                        </td>
                                        <td>
                                            <span className="badge" style={{
                                                backgroundColor:
                                                    a.nivel_morosidad === 'CRÍTICO' ? '#742a2a' :
                                                        a.nivel_morosidad === 'ALTO' ? '#c53030' :
                                                            a.nivel_morosidad === 'MODERADO' ? '#dd6b20' : '#4a5568',
                                                color: 'white'
                                            }}>
                                                {a.nivel_morosidad}
                                            </span>
                                        </td>
                                        <td>
                                            <div style={{ display: 'flex', gap: '4px', justifyContent: 'center' }}>
                                                <button
                                                    className="btn btn-action"
                                                    title="Ver detalle de aportes, cuotas y multas"
                                                    onClick={() => setDetalleAfiliado(a)}
                                                    style={{ fontSize: '1.2rem', padding: '5px' }}
                                                >
                                                    🔍
                                                </button>
                                                {a.deuda_total > 0 && (
                                                    <button
                                                        className="btn btn-action"
                                                        title="Pagar Todo con Yape (QR)"
                                                        onClick={() => handlePagarTotal(a)}
                                                        style={{ fontSize: '1.2rem', padding: '5px' }}
                                                    >
                                                        📱
                                                    </button>
                                                )}
                                            </div>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                        {/* Fila de Pie: Total Por Cobrar */}
                        <tfoot>
                            <tr style={{ background: '#fff5f5', borderTop: '2px solid #feb2b2' }}>
                                <td colSpan="5" style={{ textAlign: 'right', fontWeight: 'bold', color: '#742a2a', fontSize: '0.95rem' }}>
                                    TOTAL POR COBRAR:
                                </td>
                                <td style={{ fontWeight: '800', color: '#c53030', fontSize: '1.05rem' }}>
                                    Bs. {resumen.monto_por_cobrar.toFixed(2)}
                                </td>
                                <td colSpan="2"></td>
                            </tr>
                        </tfoot>
                    </table>
                ) : (
                    <table className="vehiculos-table">
                        <thead>
                            <tr>
                                <th>Afiliado</th>
                                <th>Carnet (CI)</th>
                                <th>Teléfono</th>
                                <th>Último Pago</th>
                                <th>Días desde Últ. Pago</th>
                                <th>Estado</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filteredAfiliados.length === 0 ? (
                                <tr>
                                    <td colSpan="6" className="no-data" style={{ padding: '2rem', textAlign: 'center' }}>
                                        {searchTerm ? 'No se encontraron afiliados que coincidan con la búsqueda.' : 'No hay afiliados al día para mostrar.'}
                                    </td>
                                </tr>
                            ) : (
                                filteredAfiliados.map(a => (
                                    <tr key={a.afiliado_id}>
                                        <td>
                                            <div style={{ fontWeight: 'bold' }}>{a.nombre_completo}</div>
                                        </td>
                                        <td>{a.ci || '-'}</td>
                                        <td>{a.telefono || 'Sin telf.'}</td>
                                        <td>
                                            <span style={{ fontWeight: '600', color: a.ultimo_pago === 'Nunca' ? '#a0aec0' : '#2d3748' }}>
                                                {a.ultimo_pago}
                                            </span>
                                        </td>
                                        <td>
                                            {a.dias_desde_ultimo_pago !== null && a.dias_desde_ultimo_pago !== undefined ? (
                                                <span style={{ color: '#4a5568', fontSize: '0.9rem' }}>
                                                    {a.dias_desde_ultimo_pago} días atrás
                                                </span>
                                            ) : (
                                                <span style={{ color: '#a0aec0' }}>-</span>
                                            )}
                                        </td>
                                        <td>
                                            <span className="badge badge-al-dia">
                                                Al día
                                            </span>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                )}
            </div>

            {/* Paginación */}
            <div className="pagination" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '1rem', marginTop: '1.5rem', paddingBottom: '1rem' }}>
                <button
                    className="btn btn-secondary"
                    disabled={pagina <= 1}
                    onClick={() => {
                        setPagina(p => Math.max(1, p - 1));
                        window.scrollTo(0, 0);
                    }}
                >
                    Anterior
                </button>
                <span style={{ fontWeight: '600' }}>
                    Página {pagina} de {paginasTotales}
                </span>
                <button
                    className="btn btn-secondary"
                    disabled={pagina >= paginasTotales}
                    onClick={() => {
                        setPagina(p => p + 1);
                        window.scrollTo(0, 0);
                    }}
                >
                    Siguiente
                </button>
                <span style={{ fontSize: '0.875rem', color: '#666' }}>
                    (Total: {totalItems})
                </span>
            </div>

            {/* Detalle de deuda del afiliado: aportes, cuotas y multas */}
            {detalleAfiliado && (
                <div className="modal-overlay" onClick={() => setDetalleAfiliado(null)}>
                    <div className="modal-content" style={{ maxWidth: '820px', width: '96%' }} onClick={(e) => e.stopPropagation()}>
                        <div className="modal-header">
                            <div>
                                <h2 style={{ margin: 0 }}>Estado de Cuenta</h2>
                                <div style={{ color: '#4a5568', fontSize: '0.95rem', marginTop: '4px' }}>
                                    {detalleAfiliado.nombre_completo} · CI {detalleAfiliado.ci || '-'}
                                </div>
                            </div>
                            <button className="modal-close" onClick={() => setDetalleAfiliado(null)}>✕</button>
                        </div>

                        <h3 style={{ fontSize: '1rem', color: '#2d3748', margin: '0 0 8px' }}>
                            Aportes y Cuotas Pendientes ({detalleAportes.length})
                        </h3>
                        <div className="table-container" style={{ marginBottom: '1.25rem' }}>
                            <table className="vehiculos-table">
                                <thead>
                                    <tr>
                                        <th>Concepto</th>
                                        <th>Período</th>
                                        <th style={{ textAlign: 'right' }}>Monto</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {detalleAportes.length === 0 ? (
                                        <tr><td colSpan="3" className="no-data">Sin aportes o cuotas pendientes</td></tr>
                                    ) : detalleAportes.map(a => (
                                        <tr key={`aporte-${a.id}`}>
                                            <td>{a.etiqueta}</td>
                                            <td>{a.periodo || '-'}</td>
                                            <td style={{ textAlign: 'right' }}>Bs. {a.monto.toFixed(2)}</td>
                                        </tr>
                                    ))}
                                </tbody>
                                {detalleAportes.length > 0 && (
                                    <tfoot>
                                        <tr style={{ background: '#fff5f5' }}>
                                            <td colSpan="2" style={{ textAlign: 'right', fontWeight: 'bold' }}>Total aportes/cuotas:</td>
                                            <td style={{ textAlign: 'right', fontWeight: 'bold', color: '#c53030' }}>Bs. {totalDetalleAportes.toFixed(2)}</td>
                                        </tr>
                                    </tfoot>
                                )}
                            </table>
                        </div>

                        <h3 style={{ fontSize: '1rem', color: '#2d3748', margin: '0 0 8px' }}>
                            Multas Pendientes ({detalleSanciones.length})
                        </h3>
                        <div className="table-container" style={{ marginBottom: '1.25rem' }}>
                            <table className="vehiculos-table">
                                <thead>
                                    <tr>
                                        <th>Tipo</th>
                                        <th>Motivo</th>
                                        <th>Fecha</th>
                                        <th style={{ textAlign: 'right' }}>Monto</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {detalleSanciones.length === 0 ? (
                                        <tr><td colSpan="4" className="no-data">Sin multas pendientes</td></tr>
                                    ) : detalleSanciones.map(s => (
                                        <tr key={`sancion-${s.id}`}>
                                            <td>{s.tipo}</td>
                                            <td>{s.motivo || '-'}</td>
                                            <td>{s.fecha ? s.fecha.split('-').reverse().join('/') : '-'}</td>
                                            <td style={{ textAlign: 'right' }}>Bs. {s.monto.toFixed(2)}</td>
                                        </tr>
                                    ))}
                                </tbody>
                                {detalleSanciones.length > 0 && (
                                    <tfoot>
                                        <tr style={{ background: '#fff5f5' }}>
                                            <td colSpan="3" style={{ textAlign: 'right', fontWeight: 'bold' }}>Total multas:</td>
                                            <td style={{ textAlign: 'right', fontWeight: 'bold', color: '#c53030' }}>Bs. {totalDetalleSanciones.toFixed(2)}</td>
                                        </tr>
                                    </tfoot>
                                )}
                            </table>
                        </div>

                        <div style={{
                            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                            padding: '0.9rem 1rem', background: '#fff5f5', borderRadius: '10px',
                            border: '1px solid #feb2b2', flexWrap: 'wrap', gap: '0.75rem'
                        }}>
                            <div style={{ fontSize: '1rem', fontWeight: '700', color: '#742a2a' }}>
                                DEUDA TOTAL: Bs. {(totalDetalleAportes + totalDetalleSanciones).toFixed(2)}
                            </div>
                            <div style={{ display: 'flex', gap: '0.5rem' }}>
                                <button className="btn btn-secondary" onClick={() => setDetalleAfiliado(null)}>
                                    Cerrar
                                </button>
                                {detalleAfiliado.deuda_total > 0 && (
                                    <button
                                        className="btn btn-primary"
                                        onClick={() => {
                                            const afiliado = detalleAfiliado;
                                            setDetalleAfiliado(null);
                                            handlePagarTotal(afiliado);
                                        }}
                                    >
                                        📱 Pagar todo con QR
                                    </button>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Modal de Pago QR (Yape) Reutilizable */}
            <YapeQRModal
                qrData={qrData}
                onVerify={verificarPagoQR}
                onClose={() => setQrData(null)}
                verifying={verificandoPago}
            />
        </div>
    );
}

export default ReporteDeudas;

