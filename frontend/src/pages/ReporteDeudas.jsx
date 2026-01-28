import { useState, useEffect } from 'react';
import api from '../services/api';
import YapeQRModal from '../components/YapeQRModal';
import './ReportesFinancieros.css'; // Reutilizamos estilos

function ReporteDeudas() {
    const [afiliados, setAfiliados] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [totales, setTotales] = useState({ deuda: 0, morosos: 0 });
    const [pagina, setPagina] = useState(1);
    const [paginasTotales, setPaginasTotales] = useState(1);

    // QR States
    const [qrData, setQrData] = useState(null);
    const [verificandoPago, setVerificandoPago] = useState(false);

    useEffect(() => {
        loadData();
    }, [pagina]);

    const loadData = async () => {
        try {
            setLoading(true);
            const res = await api.getAfiliadosMorosos({ page: pagina });
            // La API devuelve: { total_morosos, deuda_total_sistema, morosos: [], resumen_por_nivel }
            // morosos list item: { afiliado_id, nombre_completo, ci, deuda_cuotas, deuda_sanciones, deuda_total, cantidad_faltas, ... }
            if (res.data) {
                setAfiliados(res.data.morosos || []);
                setTotales({
                    deuda: res.data.deuda_total_sistema || 0,
                    morosos: res.data.count || 0
                });
                setPaginasTotales(res.data.total_pages || 1);
            }
            setError('');
        } catch (err) {
            setError('Error al cargar reporte de deudas');
            console.error(err);
        } finally {
            setLoading(false);
        }
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
            alert('¡Pago verificado exitosamente!');
            setQrData(null);
            loadData();
        } catch (err) {
            console.error(err);
            alert('Error al verificar pago');
        } finally {
            setVerificandoPago(false);
        }
    };

    const handleDownloadPdf = async () => {
        try {
            const res = await api.downloadAfiliadosMorososPdf();
            if (!res.success) {
                alert('Error al descargar PDF: ' + res.error);
            }
        } catch (e) {
            console.error(e);
            alert('Error al descargar PDF');
        }
    };

    if (loading) return <div className="loading">Cargando reporte de estado de cuentas...</div>;
    if (error) return <div className="error">{error}</div>;

    return (
        <div className="reportes-container">
            <div className="report-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                <div>
                    <h1>Estado de Cuentas por Afiliado</h1>
                    <p>Resumen de cuotas pendientes, multas y faltas.</p>
                </div>
                <button className="btn btn-primary" onClick={handleDownloadPdf}>
                    📄 Descargar Reporte PDF
                </button>
            </div>

            <div className="metrics-grid">
                <div className="metric-card">
                    <h3>Total Deuda Sistema</h3>
                    <div className="metric-value" style={{ color: '#e53e3e' }}>Bs. {totales.deuda.toFixed(2)}</div>
                </div>
                <div className="metric-card">
                    <h3>Afiliados con Deuda/Falta</h3>
                    <div className="metric-value">{totales.morosos}</div>
                </div>
            </div>

            <div className="table-container" style={{ marginTop: '20px' }}>
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
                        {afiliados.length === 0 ? (
                            <tr><td colSpan="8" className="no-data">Todos los afiliados están al día 🎉</td></tr>
                        ) : (
                            afiliados.map(a => (
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
                                        Bs. {a.deuda_cuotas.toFixed(2)}
                                    </td>
                                    <td>
                                        {a.deuda_sanciones > 0 && <div style={{ fontSize: '0.85em', color: '#666' }}>{a.cantidad_sanciones_pendientes} pendientes</div>}
                                        Bs. {a.deuda_sanciones.toFixed(2)}
                                    </td>
                                    <td style={{ fontWeight: 'bold', color: a.deuda_total > 500 ? '#c53030' : 'inherit' }}>
                                        Bs. {a.deuda_total.toFixed(2)}
                                    </td>
                                    <td>
                                        <span className={`badge`} style={{
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
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>

            {/* Paginación */}
            <div className="pagination" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '1rem', marginTop: '1.5rem', paddingBottom: '1rem' }}>
                <button
                    className="btn btn-secondary"
                    disabled={pagina <= 1}
                    onClick={() => {
                        setPagina(p => p - 1);
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
                    (Total: {totales.morosos})
                </span>
            </div>

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
