import { useState, useEffect } from 'react';
import { Bar, Line } from 'react-chartjs-2';
import { Chart as ChartJS, registerables } from 'chart.js';
import api from '../services/api';
import './ReportesFinancieros.css';

ChartJS.register(...registerables);

function ReportesAvanzados() {
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState('kpis');

    // Estados para cada reporte
    const [kpis, setKpis] = useState(null);
    const [rentabilidad, setRentabilidad] = useState(null);
    const [tendencias, setTendencias] = useState(null);
    const [error, setError] = useState('');

    useEffect(() => {
        cargarDatos();
    }, [activeTab]);

    const cargarDatos = async () => {
        setLoading(true);
        setError('');
        try {
            if (activeTab === 'kpis') {
                const res = await api.getKPIsEjecutivos();
                setKpis(res.data);
            } else if (activeTab === 'rentabilidad') {
                const res = await api.getRentabilidadRutas({ meses: 3 });
                setRentabilidad(res.data);
            } else if (activeTab === 'tendencias') {
                const res = await api.getTendenciasMensuales({ meses: 12 });
                setTendencias(res.data);
            }
        } catch (err) {
            console.error('Error cargando reportes avanzados:', err);
            setError('No se pudieron cargar los datos del reporte seleccionado.');
        } finally {
            setLoading(false);
        }
    };

    // Renderizar KPIs Ejecutivos
    const renderKPIs = () => {
        if (!kpis) return null;

        const getEstadoColor = (estado) => {
            switch (estado) {
                case 'bueno': return '#10b981';
                case 'regular': return '#f59e0b';
                case 'malo': return '#ef4444';
                default: return '#6366f1';
            }
        };

        const kpiEntries = kpis.kpis ? Object.entries(kpis.kpis) : [];

        return (
            <div className="kpis-dashboard">
                <div className="kpis-header" style={{ marginBottom: '1.5rem' }}>
                    <h2>Dashboard Ejecutivo</h2>
                    <p className="periodo">Período: {kpis.periodo || 'Mes actual'}</p>
                </div>

                <div className="kpis-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1.5rem', marginBottom: '2rem' }}>
                    {kpiEntries.map(([key, kpi]) => (
                        <div key={key} className="kpi-card" style={{ background: 'white', borderRadius: '12px', padding: '1.5rem', boxShadow: '0 4px 6px rgba(0,0,0,0.08)', borderLeft: `6px solid ${getEstadoColor(kpi?.estado)}` }}>
                            <div className="kpi-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                                <span className="kpi-label" style={{ fontWeight: '600', color: '#4b5563', fontSize: '0.9rem' }}>{kpi?.descripcion}</span>
                                {kpi?.estado && (
                                    <span className={`kpi-badge ${kpi.estado}`} style={{ fontSize: '0.8rem', padding: '2px 8px', borderRadius: '12px', color: 'white', background: getEstadoColor(kpi.estado) }}>
                                        {kpi.estado === 'bueno' ? '✓' : kpi.estado === 'regular' ? '!' : '✗'}
                                    </span>
                                )}
                            </div>
                            <div className="kpi-value" style={{ fontSize: '1.8rem', fontWeight: '800', color: '#1f2937' }}>
                                {Number(kpi?.valor || 0).toLocaleString()} <span className="kpi-unit" style={{ fontSize: '1rem', color: '#6b7280', fontWeight: '500' }}>{kpi?.unidad}</span>
                            </div>
                            {kpi?.objetivo && (
                                <div className="kpi-objetivo" style={{ marginTop: '0.5rem', fontSize: '0.8rem', color: '#6b7280' }}>
                                    Objetivo: {kpi.objetivo} {kpi.unidad}
                                </div>
                            )}
                        </div>
                    ))}
                </div>

                {kpis.resumen_financiero && (
                    <div className="resumen-financiero" style={{ background: 'white', borderRadius: '12px', padding: '1.5rem', boxShadow: '0 4px 6px rgba(0,0,0,0.08)' }}>
                        <h3 style={{ marginBottom: '1rem', color: '#1f2937' }}>Resumen Financiero del Mes</h3>
                        <div className="resumen-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1.5rem' }}>
                            <div className="resumen-item" style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                                <span className="resumen-label" style={{ color: '#6b7280', fontSize: '0.875rem' }}>Ingresos</span>
                                <span className="resumen-valor positivo" style={{ fontSize: '1.5rem', fontWeight: '700', color: '#10b981' }}>
                                    Bs. {Number(kpis.resumen_financiero.ingresos_mes || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                                </span>
                            </div>
                            <div className="resumen-item" style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                                <span className="resumen-label" style={{ color: '#6b7280', fontSize: '0.875rem' }}>Egresos</span>
                                <span className="resumen-valor negativo" style={{ fontSize: '1.5rem', fontWeight: '700', color: '#ef4444' }}>
                                    Bs. {Number(kpis.resumen_financiero.egresos_mes || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                                </span>
                            </div>
                            <div className="resumen-item" style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                                <span className="resumen-label" style={{ color: '#6b7280', fontSize: '0.875rem' }}>Saldo</span>
                                <span className={`resumen-valor ${(kpis.resumen_financiero.saldo_mes || 0) >= 0 ? 'positivo' : 'negativo'}`} style={{ fontSize: '1.5rem', fontWeight: '700', color: (kpis.resumen_financiero.saldo_mes || 0) >= 0 ? '#10b981' : '#ef4444' }}>
                                    Bs. {Number(kpis.resumen_financiero.saldo_mes || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                                </span>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        );
    };

    // Renderizar Rentabilidad de Rutas
    const renderRentabilidad = () => {
        if (!rentabilidad) return null;

        const rutasLista = rentabilidad.rutas || [];

        const datosGrafico = {
            labels: rutasLista.map(r => r.ruta_nombre || 'Sin nombre'),
            datasets: [
                {
                    label: 'Utilidad (Bs)',
                    data: rutasLista.map(r => r.utilidad || 0),
                    backgroundColor: rutasLista.map(r =>
                        (r.utilidad || 0) >= 0 ? 'rgba(16, 185, 129, 0.7)' : 'rgba(239, 68, 68, 0.7)'
                    ),
                    borderRadius: 8,
                }
            ]
        };

        const opciones = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                title: {
                    display: true,
                    text: 'Utilidad por Ruta'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: (value) => 'Bs. ' + Number(value).toLocaleString()
                    }
                }
            }
        };

        return (
            <div className="rentabilidad-container">
                <div className="rentabilidad-header" style={{ marginBottom: '1.5rem' }}>
                    <h2>Rentabilidad por Ruta</h2>
                    <p className="periodo">{rentabilidad.periodo}</p>
                </div>

                {rutasLista.length > 0 ? (
                    <>
                        <div className="chart-card" style={{ height: '400px', marginBottom: '2rem' }}>
                            <Bar data={datosGrafico} options={opciones} />
                        </div>

                        {rentabilidad.resumen && (
                            <div className="stats-grid" style={{ marginBottom: '2rem' }}>
                                <div className="stat-card">
                                    <h3>Total Rutas Analizadas</h3>
                                    <p className="stat-value">{rentabilidad.resumen.total_rutas || 0}</p>
                                </div>
                                <div className="stat-card">
                                    <h3>Ingresos Totales</h3>
                                    <p className="stat-value" style={{ color: '#10b981' }}>
                                        Bs. {Number(rentabilidad.resumen.ingresos_totales || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                                    </p>
                                </div>
                                <div className="stat-card">
                                    <h3>Utilidad Total</h3>
                                    <p className="stat-value" style={{ color: (rentabilidad.resumen.utilidad_total || 0) >= 0 ? '#10b981' : '#ef4444' }}>
                                        Bs. {Number(rentabilidad.resumen.utilidad_total || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                                    </p>
                                </div>
                            </div>
                        )}

                        <div className="chart-card list-section">
                            <h3>Detalle por Ruta</h3>
                            <div className="table-container">
                                <table className="data-table">
                                    <thead>
                                        <tr>
                                            <th>Ruta</th>
                                            <th>Viajes</th>
                                            <th>Ingresos</th>
                                            <th>Costos</th>
                                            <th>Utilidad</th>
                                            <th>Margen %</th>
                                            <th>Ocupación %</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {rutasLista.map((ruta, idx) => (
                                            <tr key={idx}>
                                                <td><strong>{ruta.ruta_nombre}</strong></td>
                                                <td>{ruta.total_viajes}</td>
                                                <td style={{ color: '#10b981', fontWeight: 'bold' }}>Bs. {Number(ruta.ingresos_totales || 0).toFixed(2)}</td>
                                                <td style={{ color: '#ef4444' }}>Bs. {Number(ruta.costos_estimados || 0).toFixed(2)}</td>
                                                <td style={{ color: (ruta.utilidad || 0) >= 0 ? '#10b981' : '#ef4444', fontWeight: 'bold' }}>
                                                    Bs. {Number(ruta.utilidad || 0).toFixed(2)}
                                                </td>
                                                <td>{ruta.margen_porcentaje}%</td>
                                                <td>{ruta.ocupacion_promedio}%</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </>
                ) : (
                    <div className="chart-card" style={{ padding: '2rem', textAlign: 'center' }}>
                        <p>No hay datos de rutas registradas en el período seleccionado.</p>
                    </div>
                )}
            </div>
        );
    };

    // Renderizar Tendencias Mensuales
    const renderTendencias = () => {
        if (!tendencias) return null;

        const tendenciasLista = tendencias.tendencias || [];

        const datosGrafico = {
            labels: tendenciasLista.map(t => t.mes_nombre || t.mes),
            datasets: [
                {
                    label: 'Ingresos',
                    data: tendenciasLista.map(t => t.ingresos || 0),
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    tension: 0.4,
                },
                {
                    label: 'Egresos',
                    data: tendenciasLista.map(t => t.egresos || 0),
                    borderColor: '#ef4444',
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    tension: 0.4,
                }
            ]
        };

        const opciones = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'top' },
                title: {
                    display: true,
                    text: 'Tendencias Mensuales - Ingresos vs Egresos'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: (value) => 'Bs. ' + Number(value).toLocaleString()
                    }
                }
            }
        };

        return (
            <div className="tendencias-container">
                <div className="tendencias-header" style={{ marginBottom: '1.5rem' }}>
                    <h2>Análisis de Tendencias</h2>
                    <p className="periodo">{tendencias.periodo}</p>
                </div>

                <div className="chart-card" style={{ height: '400px', marginBottom: '2rem' }}>
                    <Line data={datosGrafico} options={opciones} />
                </div>

                {tendencias.estadisticas && (
                    <div className="stats-grid" style={{ marginBottom: '2rem' }}>
                        <div className="stat-card">
                            <h3>Ingreso Promedio</h3>
                            <p className="stat-value">Bs. {Number(tendencias.estadisticas.ingreso_promedio || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}</p>
                        </div>
                        <div className="stat-card">
                            <h3>Egreso Promedio</h3>
                            <p className="stat-value">Bs. {Number(tendencias.estadisticas.egreso_promedio || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}</p>
                        </div>
                        <div className="stat-card">
                            <h3>Mejor Mes</h3>
                            <p className="stat-value">{tendencias.estadisticas.mejor_mes || 'N/A'}</p>
                        </div>
                        <div className="stat-card">
                            <h3>Peor Mes</h3>
                            <p className="stat-value">{tendencias.estadisticas.peor_mes || 'N/A'}</p>
                        </div>
                    </div>
                )}

                {tendencias.proyeccion_proximo_mes && (
                    <div className="chart-card list-section">
                        <h3>📊 Proyección Próximo Mes</h3>
                        <div className="resumen-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1.5rem', marginTop: '1rem' }}>
                            <div className="resumen-item">
                                <span>Ingresos Proyectados:</span>
                                <strong>Bs. {Number(tendencias.proyeccion_proximo_mes.ingresos_proyectados || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}</strong>
                            </div>
                            <div className="resumen-item">
                                <span>Egresos Proyectados:</span>
                                <strong>Bs. {Number(tendencias.proyeccion_proximo_mes.egresos_proyectados || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}</strong>
                            </div>
                            <div className="resumen-item">
                                <span>Saldo Proyectado:</span>
                                <strong style={{ color: (tendencias.proyeccion_proximo_mes.saldo_proyectado || 0) >= 0 ? '#10b981' : '#ef4444' }}>
                                    Bs. {Number(tendencias.proyeccion_proximo_mes.saldo_proyectado || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                                </strong>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        );
    };

    return (
        <div className="reportes-avanzados" style={{ padding: '1rem' }}>
            <div className="tabs-container">
                <button
                    className={`tab-button ${activeTab === 'kpis' ? 'active' : ''}`}
                    onClick={() => setActiveTab('kpis')}
                >
                    📊 KPIs Ejecutivos
                </button>
                <button
                    className={`tab-button ${activeTab === 'rentabilidad' ? 'active' : ''}`}
                    onClick={() => setActiveTab('rentabilidad')}
                >
                    💰 Rentabilidad de Rutas
                </button>
                <button
                    className={`tab-button ${activeTab === 'tendencias' ? 'active' : ''}`}
                    onClick={() => setActiveTab('tendencias')}
                >
                    📈 Tendencias Mensuales
                </button>
            </div>

            <div className="tab-content">
                {error && (
                    <div className="error-message" style={{ padding: '1rem', background: '#ffebee', color: '#c62828', borderRadius: '8px', marginBottom: '1rem' }}>
                        {error}
                    </div>
                )}
                {loading ? (
                    <div style={{ padding: '3rem', textAlign: 'center' }}>
                        <p>Cargando datos...</p>
                    </div>
                ) : (
                    <>
                        {activeTab === 'kpis' && renderKPIs()}
                        {activeTab === 'rentabilidad' && renderRentabilidad()}
                        {activeTab === 'tendencias' && renderTendencias()}
                    </>
                )}
            </div>
        </div>
    );
}

export default ReportesAvanzados;
