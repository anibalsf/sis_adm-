import { useState, useEffect } from 'react';
import { Bar, Line } from 'react-chartjs-2';
import api from '../services/api';
import './ReportesFinancieros.css';

function ReportesAvanzados() {
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState('kpis');

    // Estados para cada reporte
    const [kpis, setKpis] = useState(null);
    const [rentabilidad, setRentabilidad] = useState(null);
    const [tendencias, setTendencias] = useState(null);

    useEffect(() => {
        cargarDatos();
    }, [activeTab]);

    const cargarDatos = async () => {
        setLoading(true);
        try {
            if (activeTab === 'kpis') {
                const res = await api.getKPIsEjecutivos();
                setKpis(res.data);
            } else if (activeTab === 'rentabilidad') {
                const res = await api.getRentabilidadRutas({ meses: 3 });
                setRentabilidad(res.data);
            } else if (activeTab === 'tendencias') {
                const res = await api.getTendenciasMensualesView({ meses: 12 });
                setTendencias(res.data);
            }
        } catch (error) {
            console.error('Error cargando reportes avanzados:', error);
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

        return (
            <div className="kpis-dashboard">
                <div className="kpis-header">
                    <h2>Dashboard Ejecutivo</h2>
                    <p className="periodo">Período: {kpis.periodo}</p>
                </div>

                <div className="kpis-grid">
                    {Object.entries(kpis.kpis).map(([key, kpi]) => (
                        <div key={key} className="kpi-card" style={{ borderLeftColor: getEstadoColor(kpi.estado) }}>
                            <div className="kpi-header">
                                <span className="kpi-label">{kpi.descripcion}</span>
                                {kpi.estado && (
                                    <span className={`kpi-badge ${kpi.estado}`}>
                                        {kpi.estado === 'bueno' ? '✓' : kpi.estado === 'regular' ? '!' : '✗'}
                                    </span>
                                )}
                            </div>
                            <div className="kpi-value">
                                {kpi.valor.toLocaleString()} <span className="kpi-unit">{kpi.unidad}</span>
                            </div>
                            {kpi.objetivo && (
                                <div className="kpi-objetivo">
                                    Objetivo: {kpi.objetivo} {kpi.unidad}
                                </div>
                            )}
                        </div>
                    ))}
                </div>

                <div className="resumen-financiero">
                    <h3>Resumen Financiero del Mes</h3>
                    <div className="resumen-grid">
                        <div className="resumen-item">
                            <span className="resumen-label">Ingresos</span>
                            <span className="resumen-valor positivo">
                                Bs. {kpis.resumen_financiero.ingresos_mes.toLocaleString()}
                            </span>
                        </div>
                        <div className="resumen-item">
                            <span className="resumen-label">Egresos</span>
                            <span className="resumen-valor negativo">
                                Bs. {kpis.resumen_financiero.egresos_mes.toLocaleString()}
                            </span>
                        </div>
                        <div className="resumen-item">
                            <span className="resumen-label">Saldo</span>
                            <span className={`resumen-valor ${kpis.resumen_financiero.saldo_mes >= 0 ? 'positivo' : 'negativo'}`}>
                                Bs. {kpis.resumen_financiero.saldo_mes.toLocaleString()}
                            </span>
                        </div>
                    </div>
                </div>
            </div>
        );
    };

    // Renderizar Rentabilidad de Rutas
    const renderRentabilidad = () => {
        if (!rentabilidad) return null;

        const datosGrafico = {
            labels: rentabilidad.rutas.map(r => r.ruta_nombre),
            datasets: [
                {
                    label: 'Utilidad (Bs)',
                    data: rentabilidad.rutas.map(r => r.utilidad),
                    backgroundColor: rentabilidad.rutas.map(r =>
                        r.utilidad >= 0 ? 'rgba(16, 185, 129, 0.7)' : 'rgba(239, 68, 68, 0.7)'
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
                        callback: (value) => 'Bs. ' + value.toLocaleString()
                    }
                }
            }
        };

        return (
            <div className="rentabilidad-container">
                <div className="rentabilidad-header">
                    <h2>Rentabilidad por Ruta</h2>
                    <p className="periodo">{rentabilidad.periodo}</p>
                </div>

                <div className="chart-container" style={{ height: '400px', marginBottom: '2rem' }}>
                    <Bar data={datosGrafico} options={opciones} />
                </div>

                <div className="rentabilidad-resumen">
                    <div className="resumen-card">
                        <span className="resumen-label">Total Rutas Analizadas</span>
                        <span className="resumen-valor">{rentabilidad.resumen.total_rutas}</span>
                    </div>
                    <div className="resumen-card">
                        <span className="resumen-label">Ingresos Totales</span>
                        <span className="resumen-valor positivo">
                            Bs. {rentabilidad.resumen.ingresos_totales.toLocaleString()}
                        </span>
                    </div>
                    <div className="resumen-card">
                        <span className="resumen-label">Utilidad Total</span>
                        <span className="resumen-valor positivo">
                            Bs. {rentabilidad.resumen.utilidad_total.toLocaleString()}
                        </span>
                    </div>
                </div>

                <div className="table-section">
                    <h3>Detalle por Ruta</h3>
                    <div className="table-container">
                        <table>
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
                                {rentabilidad.rutas.map((ruta, idx) => (
                                    <tr key={idx}>
                                        <td><strong>{ruta.ruta_nombre}</strong></td>
                                        <td>{ruta.total_viajes}</td>
                                        <td className="positivo">Bs. {ruta.ingresos_totales.toLocaleString()}</td>
                                        <td className="negativo">Bs. {ruta.costos_estimados.toLocaleString()}</td>
                                        <td className={ruta.utilidad >= 0 ? 'positivo' : 'negativo'}>
                                            Bs. {ruta.utilidad.toLocaleString()}
                                        </td>
                                        <td>{ruta.margen_porcentaje}%</td>
                                        <td>{ruta.ocupacion_promedio}%</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        );
    };

    // Renderizar Tendencias Mensuales
    const renderTendencias = () => {
        if (!tendencias) return null;

        const datosGrafico = {
            labels: tendencias.tendencias.map(t => t.mes_nombre || t.mes),
            datasets: [
                {
                    label: 'Ingresos',
                    data: tendencias.tendencias.map(t => t.ingresos),
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    tension: 0.4,
                },
                {
                    label: 'Egresos',
                    data: tendencias.tendencias.map(t => t.egresos),
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
                        callback: (value) => 'Bs. ' + value.toLocaleString()
                    }
                }
            }
        };

        return (
            <div className="tendencias-container">
                <div className="tendencias-header">
                    <h2>Análisis de Tendencias</h2>
                    <p className="periodo">{tendencias.periodo}</p>
                </div>

                <div className="chart-container" style={{ height: '400px', marginBottom: '2rem' }}>
                    <Line data={datosGrafico} options={opciones} />
                </div>

                <div className="estadisticas-grid">
                    <div className="stat-card">
                        <span className="stat-label">Ingreso Promedio</span>
                        <span className="stat-valor">Bs. {tendencias.estadisticas.ingreso_promedio.toLocaleString()}</span>
                    </div>
                    <div className="stat-card">
                        <span className="stat-label">Egreso Promedio</span>
                        <span className="stat-valor">Bs. {tendencias.estadisticas.egreso_promedio.toLocaleString()}</span>
                    </div>
                    <div className="stat-card">
                        <span className="stat-label">Mejor Mes</span>
                        <span className="stat-valor">{tendencias.estadisticas.mejor_mes}</span>
                    </div>
                    <div className="stat-card">
                        <span className="stat-label">Peor Mes</span>
                        <span className="stat-valor">{tendencias.estadisticas.peor_mes}</span>
                    </div>
                </div>

                {tendencias.proyeccion_proximo_mes && (
                    <div className="proyeccion-card">
                        <h3>📊 Proyección Próximo Mes</h3>
                        <div className="proyeccion-grid">
                            <div className="proyeccion-item">
                                <span>Ingresos Proyectados:</span>
                                <strong>Bs. {tendencias.proyeccion_proximo_mes.ingresos_proyectados.toLocaleString()}</strong>
                            </div>
                            <div className="proyeccion-item">
                                <span>Egresos Proyectados:</span>
                                <strong>Bs. {tendencias.proyeccion_proximo_mes.egresos_proyectados.toLocaleString()}</strong>
                            </div>
                            <div className="proyeccion-item">
                                <span>Saldo Proyectado:</span>
                                <strong className={tendencias.proyeccion_proximo_mes.saldo_proyectado >= 0 ? 'positivo' : 'negativo'}>
                                    Bs. {tendencias.proyeccion_proximo_mes.saldo_proyectado.toLocaleString()}
                                </strong>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        );
    };

    return (
        <div className="reportes-avanzados">
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
                {loading ? (
                    <div style={{ padding: '2rem', textAlign: 'center' }}>
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
