import { useState, useEffect } from 'react';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    BarElement,
    ArcElement,
    Title,
    Tooltip,
    Legend,
} from 'chart.js';
import { Line, Bar, Pie } from 'react-chartjs-2';
import ChartDataLabels from 'chartjs-plugin-datalabels';
import api from '../services/api';
import './ReportesFinancieros.css';

// Registrar componentes de Chart.js
ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    BarElement,
    ArcElement,
    Title,
    Tooltip,
    Legend,
    ChartDataLabels
);

function ReportesFinancieros() {
    const [datosMensuales, setDatosMensuales] = useState(null);
    const [datosPorTipo, setDatosPorTipo] = useState(null);
    const [transacciones, setTransacciones] = useState([]);
    const [resumen, setResumen] = useState(null);
    const [excluidos, setExcluidos] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [fechaInicio, setFechaInicio] = useState('');
    const [fechaFin, setFechaFin] = useState('');
    const [pagina, setPagina] = useState(1);
    const [totalItems, setTotalItems] = useState(0);
    const [paginasTotales, setPaginasTotales] = useState(1);

    useEffect(() => {
        loadDatos();
    }, [pagina]);

    const loadDatos = async () => {
        try {
            setLoading(true);
            const params = {};
            if (fechaInicio) params.fecha_inicio = fechaInicio;
            if (fechaFin) params.fecha_fin = fechaFin;

            // Cargar datos mensuales
            const mensualRes = await api.getReportesGraficos({ ...params, tipo: 'mensual' });
            setDatosMensuales(mensualRes.data);

            // Cargar datos por tipo
            const tipoRes = await api.getReportesGraficos({ ...params, tipo: 'por_tipo' });
            setDatosPorTipo(tipoRes.data);

            // Cargar transacciones
            const transacRes = await api.getTransacciones({ ...params, page: pagina });
            setTransacciones(transacRes.data.transacciones || []);
            setResumen(transacRes.data.resumen || null);
            setExcluidos(transacRes.data.excluidos_por_estado || null);
            setTotalItems(transacRes.data.count || 0);
            setPaginasTotales(transacRes.data.total_pages || 1);

            setError('');
        } catch (err) {
            const errorMsg = err.response?.data?.error || err.response?.data?.detail || err.message || 'Error desconocido';
            setError(`Error al cargar los reportes: ${errorMsg}`);
            console.error('Error cargando reportes:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleFiltrar = (e) => {
        e.preventDefault();
        setPagina(1);
        loadDatos();
    };

    const limpiarFiltros = () => {
        setFechaInicio('');
        setFechaFin('');
        setPagina(1);
        setTimeout(() => loadDatos(), 100);
    };

    // Preparar datos para gráfico de líneas (Tendencia Mensual)
    const prepararDatosLinea = () => {
        if (!datosMensuales) return null;

        // Obtener todos los meses únicos
        const mesesSet = new Set();
        datosMensuales.ingresos.forEach(item => mesesSet.add(item.mes));
        datosMensuales.egresos.forEach(item => mesesSet.add(item.mes));
        const meses = Array.from(mesesSet).sort();

        // Crear mapas para búsqueda rápida
        const ingresosMap = {};
        const egresosMap = {};
        datosMensuales.ingresos.forEach(item => ingresosMap[item.mes] = item.total);
        datosMensuales.egresos.forEach(item => egresosMap[item.mes] = item.total);

        return {
            labels: meses,
            datasets: [
                {
                    label: 'Ingresos',
                    data: meses.map(mes => ingresosMap[mes] || 0),
                    borderColor: 'rgb(75, 192, 192)',
                    backgroundColor: 'rgba(75, 192, 192, 0.5)',
                    tension: 0.3,
                },
                {
                    label: 'Egresos',
                    data: meses.map(mes => egresosMap[mes] || 0),
                    borderColor: 'rgb(255, 99, 132)',
                    backgroundColor: 'rgba(255, 99, 132, 0.5)',
                    tension: 0.3,
                },
            ],
        };
    };

    // Preparar datos para gráfico de barras (Comparación Mensual)
    const prepararDatosBarras = () => {
        if (!datosMensuales) return null;

        const mesesSet = new Set();
        datosMensuales.ingresos.forEach(item => mesesSet.add(item.mes));
        datosMensuales.egresos.forEach(item => mesesSet.add(item.mes));
        const meses = Array.from(mesesSet).sort();

        const ingresosMap = {};
        const egresosMap = {};
        datosMensuales.ingresos.forEach(item => ingresosMap[item.mes] = item.total);
        datosMensuales.egresos.forEach(item => egresosMap[item.mes] = item.total);

        return {
            labels: meses,
            datasets: [
                {
                    label: 'Ingresos',
                    data: meses.map(mes => ingresosMap[mes] || 0),
                    backgroundColor: 'rgba(54, 162, 235, 0.8)',
                },
                {
                    label: 'Egresos',
                    data: meses.map(mes => egresosMap[mes] || 0),
                    backgroundColor: 'rgba(255, 99, 132, 0.8)',
                },
            ],
        };
    };

    // Preparar datos para gráfico de pastel (Distribución por Tipo - Ingresos)
    const prepararDatosPieIngresos = () => {
        if (!datosPorTipo || !datosPorTipo.ingresos.length) return null;

        return {
            labels: datosPorTipo.ingresos.map(item => item.tipo),
            datasets: [
                {
                    label: 'Monto',
                    data: datosPorTipo.ingresos.map(item => item.total),
                    backgroundColor: [
                        'rgba(255, 99, 132, 0.8)',
                        'rgba(54, 162, 235, 0.8)',
                        'rgba(255, 206, 86, 0.8)',
                        'rgba(75, 192, 192, 0.8)',
                        'rgba(153, 102, 255, 0.8)',
                        'rgba(255, 159, 64, 0.8)',
                    ],
                },
            ],
        };
    };

    // Preparar datos para gráfico de pastel (Distribución por Tipo - Egresos)
    const prepararDatosPieEgresos = () => {
        if (!datosPorTipo || !datosPorTipo.egresos.length) return null;

        return {
            labels: datosPorTipo.egresos.map(item => item.tipo),
            datasets: [
                {
                    label: 'Monto',
                    data: datosPorTipo.egresos.map(item => item.total),
                    backgroundColor: [
                        'rgba(255, 99, 132, 0.8)',
                        'rgba(54, 162, 235, 0.8)',
                        'rgba(255, 206, 86, 0.8)',
                        'rgba(75, 192, 192, 0.8)',
                        'rgba(153, 102, 255, 0.8)',
                        'rgba(255, 159, 64, 0.8)',
                    ],
                },
            ],
        };
    };

    const opcionesLinea = {
        responsive: true,
        plugins: {
            legend: {
                position: 'top',
            },
            title: {
                display: true,
                text: 'Tendencia Mensual de Ingresos y Egresos',
            },
            datalabels: {
                display: false
            }
        },
        scales: {
            y: {
                beginAtZero: true,
            },
        }
    };

    const opcionesBarras = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'top',
            },
            title: {
                display: true,
                text: 'Comparación Mensual de Ingresos vs Egresos',
            },
            datalabels: {
                display: false
            }
        },
        scales: {
            y: {
                beginAtZero: true,
            },
        },
        maxBarThickness: 50,
        categoryPercentage: 0.8
    };

    const opcionesPie = {
        responsive: true,
        plugins: {
            legend: {
                position: 'bottom',
                labels: {
                    padding: 20,
                    usePointStyle: true,
                }
            },
            tooltip: {
                callbacks: {
                    label: function (context) {
                        const label = context.label || '';
                        const value = context.parsed || 0;
                        const total = context.dataset.data.reduce((acc, curr) => acc + curr, 0);
                        const percentage = ((value / total) * 100).toFixed(1);
                        return `${label}: Bs ${value.toLocaleString()} (${percentage}%)`;
                    }
                }
            }
        },
        datalabels: {
            formatter: (value, ctx) => {
                const total = ctx.dataset.data.reduce((acc, curr) => acc + curr, 0);
                const percentage = ((value / total) * 100).toFixed(1) + "%";
                return percentage;
            },
            color: '#fff',
            font: {
                weight: 'bold',
                size: 14
            },
            textShadowBlur: 4,
            textShadowColor: 'rgba(0,0,0,0.5)'
        }
    };

    const datosLinea = prepararDatosLinea();
    const datosBarras = prepararDatosBarras();
    const datosPieIngresos = prepararDatosPieIngresos();
    const datosPieEgresos = prepararDatosPieEgresos();

    return (
        <div className="reportes-container">
            <h1>Módulo de Reportes Financieros</h1>
            <p>Visualización de datos financieros con gráficos interactivos</p>

            {/* Filtros */}
            <div className="card filter-card">
                <form onSubmit={handleFiltrar} className="filter-form">
                    <div className="form-group">
                        <label htmlFor="fecha_inicio">Fecha Inicio</label>
                        <input
                            id="fecha_inicio"
                            type="date"
                            value={fechaInicio}
                            onChange={(e) => setFechaInicio(e.target.value)}
                        />
                    </div>
                    <div className="form-group">
                        <label htmlFor="fecha_fin">Fecha Fin</label>
                        <input
                            id="fecha_fin"
                            type="date"
                            value={fechaFin}
                            onChange={(e) => setFechaFin(e.target.value)}
                        />
                    </div>
                    <div className="form-actions">
                        <button type="submit" className="btn btn-primary">Filtrar</button>
                        <button type="button" className="btn btn-secondary" onClick={limpiarFiltros}>Limpiar</button>
                    </div>
                </form>
            </div>

            {loading ? (
                <div className="loading">Cargando gráficos...</div>
            ) : error ? (
                <div className="error">{error}</div>
            ) : (
                <div className="charts-grid">
                    {/* Gráfico de Líneas */}
                    {datosLinea && (
                        <div className="chart-card">
                            <Line options={opcionesLinea} data={datosLinea} />
                        </div>
                    )}

                    {/* Gráfico de Barras */}
                    {datosBarras && (
                        <div className="chart-card">
                            <Bar options={opcionesBarras} data={datosBarras} />
                        </div>
                    )}

                    {/* Gráficos de Pastel con Desglose por Categoría */}
                    <div className="pie-charts">
                        {datosPieIngresos && (
                            <div className="chart-card pie-chart">
                                <h3>Distribución de Ingresos por Tipo / Categoría</h3>
                                <Pie options={opcionesPie} data={datosPieIngresos} />
                                {datosPorTipo?.ingresos?.length > 0 && (
                                    <div style={{ marginTop: '1.25rem', width: '100%', overflowX: 'auto' }}>
                                        <table style={{ width: '100%', fontSize: '0.875rem', borderCollapse: 'collapse' }}>
                                            <thead>
                                                <tr style={{ borderBottom: '2px solid #e2e8f0', color: '#2d3748', background: '#f7fafc' }}>
                                                    <th style={{ textAlign: 'left', padding: '6px 8px' }}>Categoría</th>
                                                    <th style={{ textAlign: 'right', padding: '6px 8px' }}>Total (Bs)</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {datosPorTipo.ingresos.map((item, idx) => (
                                                    <tr key={idx} style={{ borderBottom: '1px solid #edf2f7' }}>
                                                        <td style={{ padding: '6px 8px', fontWeight: '500' }}>{item.tipo}</td>
                                                        <td style={{ textAlign: 'right', fontWeight: 'bold', color: '#2e7d32', padding: '6px 8px' }}>
                                                            Bs. {Number(item.total).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                                                        </td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                )}
                            </div>
                        )}

                        {datosPieEgresos && (
                            <div className="chart-card pie-chart">
                                <h3>Distribución de Egresos por Tipo / Categoría</h3>
                                <Pie options={opcionesPie} data={datosPieEgresos} />
                                {datosPorTipo?.egresos?.length > 0 && (
                                    <div style={{ marginTop: '1.25rem', width: '100%', overflowX: 'auto' }}>
                                        <table style={{ width: '100%', fontSize: '0.875rem', borderCollapse: 'collapse' }}>
                                            <thead>
                                                <tr style={{ borderBottom: '2px solid #e2e8f0', color: '#2d3748', background: '#f7fafc' }}>
                                                    <th style={{ textAlign: 'left', padding: '6px 8px' }}>Categoría</th>
                                                    <th style={{ textAlign: 'right', padding: '6px 8px' }}>Total (Bs)</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {datosPorTipo.egresos.map((item, idx) => (
                                                    <tr key={idx} style={{ borderBottom: '1px solid #edf2f7' }}>
                                                        <td style={{ padding: '6px 8px', fontWeight: '500' }}>{item.tipo}</td>
                                                        <td style={{ textAlign: 'right', fontWeight: 'bold', color: '#c62828', padding: '6px 8px' }}>
                                                            Bs. {Number(item.total).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                                                        </td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>

                    {/* Tabla de Transacciones */}
                    <div className="chart-card" style={{ marginTop: '2rem' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                            <h3>Informe de Transacciones (Ingresos y Egresos)</h3>
                            <div className="form-actions">
                                <button
                                    type="button"
                                    className="btn btn-primary"
                                    onClick={async () => {
                                        const result = await api.downloadTransaccionesPdf({ fecha_inicio: fechaInicio, fecha_fin: fechaFin });
                                        if (!result.success) {
                                            setError(result.error);
                                        }
                                    }}
                                >
                                    📄 Exportar PDF
                                </button>
                                <button
                                    type="button"
                                    className="btn btn-secondary"
                                    onClick={async () => {
                                        const result = await api.downloadTransaccionesCsv({ fecha_inicio: fechaInicio, fecha_fin: fechaFin });
                                        if (!result.success) {
                                            setError(result.error);
                                        }
                                    }}
                                >
                                    📊 Exportar Excel
                                </button>
                            </div>
                        </div>

                        {resumen && (
                            <div style={{
                                display: 'grid',
                                gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
                                gap: '1rem',
                                marginBottom: '1.25rem'
                            }}>
                                <div style={{ background: '#e8f5e9', borderLeft: '4px solid #2e7d32', padding: '0.75rem 1rem', borderRadius: '6px' }}>
                                    <div style={{ fontSize: '0.8rem', color: '#2d3748', fontWeight: '600' }}>Total Ingresos ({resumen.count_ingresos})</div>
                                    <div style={{ fontSize: '1.25rem', fontWeight: '700', color: '#2e7d32' }}>Bs. {Number(resumen.total_ingresos).toLocaleString(undefined, { minimumFractionDigits: 2 })}</div>
                                </div>
                                <div style={{ background: '#fed7d7', borderLeft: '4px solid #c62828', padding: '0.75rem 1rem', borderRadius: '6px' }}>
                                    <div style={{ fontSize: '0.8rem', color: '#2d3748', fontWeight: '600' }}>Total Egresos ({resumen.count_egresos})</div>
                                    <div style={{ fontSize: '1.25rem', fontWeight: '700', color: '#c62828' }}>Bs. {Number(resumen.total_egresos).toLocaleString(undefined, { minimumFractionDigits: 2 })}</div>
                                </div>
                                <div style={{ background: resumen.saldo >= 0 ? '#e3f2fd' : '#fff3e0', borderLeft: '4px solid ' + (resumen.saldo >= 0 ? '#1565c0' : '#ef6c00'), padding: '0.75rem 1rem', borderRadius: '6px' }}>
                                    <div style={{ fontSize: '0.8rem', color: '#2d3748', fontWeight: '600' }}>Saldo del Período</div>
                                    <div style={{ fontSize: '1.25rem', fontWeight: '700', color: resumen.saldo >= 0 ? '#1565c0' : '#ef6c00' }}>Bs. {Number(resumen.saldo).toLocaleString(undefined, { minimumFractionDigits: 2 })}</div>
                                </div>
                            </div>
                        )}

                        {excluidos && (excluidos.ingresos.count > 0 || excluidos.egresos.count > 0) && (
                            <div style={{
                                background: '#fff8e1',
                                borderLeft: '4px solid #f9a825',
                                padding: '0.6rem 1rem',
                                borderRadius: '6px',
                                marginBottom: '1rem',
                                fontSize: '0.875rem',
                                color: '#5d4037'
                            }}>
                                ⚠️ <strong>Excluidos del informe por estado no válido:</strong> {excluidos.ingresos.count} ingreso(s) (Bs. {Number(excluidos.ingresos.monto).toLocaleString(undefined, { minimumFractionDigits: 2 })}) y {excluidos.egresos.count} egreso(s) (Bs. {Number(excluidos.egresos.monto).toLocaleString(undefined, { minimumFractionDigits: 2 })}).
                            </div>
                        )}

                        <div style={{ overflowX: 'auto' }}>
                            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                                <thead>
                                    <tr style={{ backgroundColor: '#f7fafc', borderBottom: '2px solid #e2e8f0' }}>
                                        <th style={{ padding: '0.75rem', textAlign: 'left' }}>Fecha</th>
                                        <th style={{ padding: '0.75rem', textAlign: 'left' }}>Tipo</th>
                                        <th style={{ padding: '0.75rem', textAlign: 'left' }}>Afiliado</th>
                                        <th style={{ padding: '0.75rem', textAlign: 'left' }}>Tipo Pago</th>
                                        <th style={{ padding: '0.75rem', textAlign: 'left' }}>Descripción</th>
                                        <th style={{ padding: '0.75rem', textAlign: 'right' }}>Monto (Bs)</th>
                                        <th style={{ padding: '0.75rem', textAlign: 'left' }}>Estado</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {transacciones.length > 0 ? (
                                        transacciones.map((t, idx) => (
                                            <tr key={idx} style={{ borderBottom: '1px solid #e2e8f0' }}>
                                                <td style={{ padding: '0.75rem' }}>{t.fecha}</td>
                                                <td style={{ padding: '0.75rem' }}>
                                                    <span style={{
                                                        padding: '0.25rem 0.5rem',
                                                        borderRadius: '4px',
                                                        fontSize: '0.875rem',
                                                        fontWeight: '600',
                                                        backgroundColor: t.tipo === 'INGRESO' ? '#c6f6d5' : '#fed7d7',
                                                        color: t.tipo === 'INGRESO' ? '#22543d' : '#742a2a'
                                                    }}>
                                                        {t.tipo}
                                                    </span>
                                                </td>
                                                <td style={{ padding: '0.75rem' }}>{t.afiliado || '-'}</td>
                                                <td style={{ padding: '0.75rem' }}>{t.tipo_pago || '-'}</td>
                                                <td style={{ padding: '0.75rem' }}>{t.descripcion || '-'}</td>
                                                <td style={{
                                                    padding: '0.75rem',
                                                    textAlign: 'right',
                                                    fontWeight: '600',
                                                    color: t.tipo === 'INGRESO' ? '#38a169' : '#e53e3e'
                                                }}>
                                                    {t.tipo === 'INGRESO' ? '+' : '-'} {Number(t.monto).toFixed(2)}
                                                </td>
                                                <td style={{ padding: '0.75rem' }}>
                                                    {t.estado === 'VÁLIDO' || t.estado === 'completado' || t.estado === 'aprobado' ? (
                                                        <span style={{ padding: '0.2rem 0.5rem', borderRadius: '4px', fontSize: '0.75rem', fontWeight: '600', backgroundColor: '#e8f5e9', color: '#1b5e20' }}>
                                                            VÁLIDO
                                                        </span>
                                                    ) : (
                                                        <span style={{ padding: '0.2rem 0.5rem', borderRadius: '4px', fontSize: '0.75rem', fontWeight: '600', backgroundColor: '#ffebee', color: '#b71c1c' }}>
                                                            {t.estado || '—'}
                                                        </span>
                                                    )}
                                                </td>
                                            </tr>
                                        ))
                                    ) : (
                                        <tr>
                                            <td colSpan="7" style={{ padding: '2rem', textAlign: 'center', color: '#a0aec0' }}>
                                                No hay transacciones para mostrar
                                            </td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </div>

                        {/* Paginación */}
                        <div className="pagination" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '1rem', marginTop: '1.5rem', paddingBottom: '1rem' }}>
                            <button
                                onClick={() => setPagina(p => Math.max(1, p - 1))}
                                disabled={pagina === 1}
                                className="btn btn-secondary"
                            >
                                ◀
                            </button>
                            <span className="pagi-info" style={{ fontWeight: '600' }}>
                                {pagina} de {Math.max(1, paginasTotales)}
                            </span>
                            <button
                                onClick={() => setPagina(p => p + 1)}
                                disabled={pagina >= paginasTotales || paginasTotales === 0}
                                className="btn btn-secondary"
                            >
                                ▶
                            </button>
                            <span style={{ fontSize: '0.875rem', color: '#666' }}>
                                (Total: {totalItems})
                            </span>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

export default ReportesFinancieros;
