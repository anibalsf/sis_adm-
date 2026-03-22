import React, { useState, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../services/api';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    BarElement,
    Title,
    Tooltip,
    Legend,
    ArcElement,
    PointElement,
    LineElement,
    Filler,
} from 'chart.js';
import { Bar, Pie, Doughnut, Line } from 'react-chartjs-2';
import { useTheme } from '../context/ThemeContext';
import SkeletonLoader from '../components/SkeletonLoader';
import './Dashboard.css';
import './DashboardMejorado.css';

ChartJS.register(
    CategoryScale,
    LinearScale,
    BarElement,
    ArcElement,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
    Filler
);

const DashboardMejorado = () => {
    const [stats, setStats] = useState({
        afiliados: 0,
        vehiculos: 0,
        rutas: 0,
        operativos: null
    });
    const { darkMode } = useTheme();

    const chartTextColor = darkMode ? '#94a3b8' : '#64748b';
    const chartGridColor = darkMode ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.05)';

    const [graficosData, setGraficosData] = useState(null);
    const [salidasData, setSalidasData] = useState(null);
    const [semanalData, setSemanalData] = useState(null);
    const [egresosPorTipoData, setEgresosPorTipoData] = useState(null);
    const [rutasRentables, setRutasRentables] = useState([]);

    const [metricas, setMetricas] = useState({
        ingresos_mes: 0,
        egresos_mes: 0,
        balance_mes: 0,
        hojas_hoy: 0,
        reservas_activas: 0,
        total_afiliados: 0,
        afiliados_nuevos_mes: 0,
        porcentaje_cambio_ingresos: 0,
        sanciones_pendientes: 0,
        monto_sanciones_pendientes: 0,
        hojas_ruta_mes: 0,
        rutas_activas: 0,
    });

    const [alertas, setAlertas] = useState({
        sanciones_pendientes: [],
        pagos_vencidos: [],
        morosos_criticos: []
    });

    const [ocupacionData, setOcupacionData] = useState(null);
    const [hojasRecientes, setHojasRecientes] = useState([]);
    const [paginaHojas, setPaginaHojas] = useState(1);
    const [totalHojas, setTotalHojas] = useState(0);
    const [loadingHojas, setLoadingHojas] = useState(false);
    const [paginaSanciones, setPaginaSanciones] = useState(1);
    const [totalSanciones, setTotalSanciones] = useState(0);
    const [loadingSanciones, setLoadingSanciones] = useState(false);
    const [loading, setLoading] = useState(true);
    const [autoRefresh, setAutoRefresh] = useState(true);
    const [lastUpdate, setLastUpdate] = useState(new Date());
    const [isFetching, setIsFetching] = useState(false);
    const [periodo, setPeriodo] = useState(6);

    useEffect(() => {
        loadDashboardData();
        let interval;
        if (autoRefresh) {
            interval = setInterval(() => {
                loadDashboardData();
            }, 5 * 60 * 1000);
        }
        return () => {
            if (interval) clearInterval(interval);
        };
    }, [autoRefresh, periodo]);

    useEffect(() => {
        if (paginaHojas > 1) cargarHojasPaginadas();
    }, [paginaHojas]);

    useEffect(() => {
        if (paginaSanciones > 1) cargarSancionesPaginadas();
    }, [paginaSanciones]);

    const cargarHojasPaginadas = async () => {
        try {
            setLoadingHojas(true);
            const res = await api.getHojasRuta({
                page: paginaHojas,
                page_size: 5,
                ordering: '-fecha_emision'
            });
            const results = res?.data?.results || (Array.isArray(res?.data) ? res.data : []);
            const count = res?.data?.count || results.length;
            setHojasRecientes(results);
            setTotalHojas(count);
        } catch (error) {
            console.error('Error cargando hojas paginadas:', error);
        } finally {
            setLoadingHojas(false);
        }
    };

    const cargarSancionesPaginadas = async () => {
        try {
            setLoadingSanciones(true);
            const res = await api.getSanciones({
                estado: 'pendiente',
                page: paginaSanciones,
                page_size: 5
            });
            const results = res.data?.results || (Array.isArray(res.data) ? res.data : []);
            const count = res.data?.count || results.length;
            setAlertas(prev => ({ ...prev, sanciones_pendientes: results }));
            setTotalSanciones(count);
        } catch (error) {
            console.error('Error cargando sanciones paginadas:', error);
        } finally {
            setLoadingSanciones(false);
        }
    };

    const loadDashboardData = async () => {
        if (isFetching) return;
        try {
            setIsFetching(true);
            setLoading(true);
            const hoy = new Date();
            const fechaInicio = new Date(hoy.getFullYear(), hoy.getMonth() - (periodo - 1), 1).toISOString().split('T')[0];

            const [
                operativosRes,
                graficosRes,
                rutasRes,
                ocupacionRes,
                morososRes,
                hojasResponse,
                sancionesRes,
                salidasRes,
                semanalRes,
                egresosPorTipoRes
            ] = await Promise.all([
                api.getReportesOperativos().catch(e => ({ data: {} })),
                api.getReportesGraficos({ tipo: 'mensual', fecha_inicio: fechaInicio }).catch(e => ({ data: { ingresos: [], egresos: [] } })),
                api.getRutasRentables({ meses: periodo }).catch(e => ({ data: { rutas: [] } })),
                api.getOcupacionHistorica({ meses: periodo }).catch(e => ({ data: { meses: [] } })),
                api.getAfiliadosMorosos({ page_size: 5 }).catch(e => ({ data: { morosos: [] } })),
                api.getHojasRuta({ page: 1, page_size: 5, ordering: '-fecha_emision' }).catch(e => ({ data: { results: [] } })),
                api.getSanciones({ estado: 'pendiente', page: 1, page_size: 5 }).catch(e => ({ data: { results: [] } })),
                api.getReportesGraficos({ tipo: 'salidas' }).catch(e => ({ data: { salidas: [] } })),
                api.getReportesGraficos({ tipo: 'semanal' }).catch(e => ({ data: { semana: [] } })),
                api.getReportesGraficos({ tipo: 'por_tipo' }).catch(e => ({ data: { egresos: [] } }))
            ]);

            setStats({
                afiliados: operativosRes.data?.afiliados?.total || 0,
                vehiculos: operativosRes.data?.vehiculos?.total || 0,
                rutas: operativosRes.data?.hojas_ruta?.total || 0,
                operativos: operativosRes.data
            });
            setGraficosData(graficosRes.data || { ingresos: [], egresos: [] });
            setSalidasData(salidasRes?.data || { salidas: [] });
            setSemanalData(semanalRes?.data || { semana: [] });
            setEgresosPorTipoData(egresosPorTipoRes?.data || { egresos: [] });
            setRutasRentables(rutasRes.data?.rutas || []);
            setOcupacionData(ocupacionRes.data || { meses: [] });

            setAlertas(prev => ({
                ...prev,
                morosos_criticos: (morososRes.data?.morosos || []).filter(m => m && m.nivel_morosidad === 'CRÍTICO'),
                sanciones_pendientes: sancionesRes.data?.results || (Array.isArray(sancionesRes.data) ? sancionesRes.data : []),
            }));

            setTotalHojas(hojasResponse.data?.count || (Array.isArray(hojasResponse.data) ? hojasResponse.data.length : 0));
            setTotalSanciones(sancionesRes.data?.count || (Array.isArray(sancionesRes.data) ? sancionesRes.data.length : 0));
            setHojasRecientes(hojasResponse?.data?.results || hojasResponse?.data || []);

            setPaginaHojas(1);
            setPaginaSanciones(1);

            await cargarMetricasFinancieras();
            setLastUpdate(new Date());

        } catch (error) {
            console.error('Error loading dashboard:', error);
        } finally {
            setLoading(false);
            setIsFetching(false);
        }
    };

    const cargarMetricasFinancieras = async () => {
        try {
            const hoy = new Date();
            const res = await api.getReporteFinanzas().catch(e => ({ data: {} }));

            if (res && res.data) {
                setMetricas({
                    ingresos_mes: res.data.ingresos_mes || 0,
                    egresos_mes: res.data.egresos_mes || 0,
                    balance_mes: res.data.saldo_mes || 0,
                    hojas_hoy: res.data.hojas_hoy || 0,
                    reservas_activas: res.data.reservas_activas || 0,
                    total_afiliados: res.data.total_afiliados || 0,
                    afiliados_nuevos_mes: res.data.afiliados_nuevos_mes || 0,
                    porcentaje_cambio_ingresos: res.data.porcentaje_cambio_ingresos || 0,
                    sanciones_pendientes: res.data.sanciones_pendientes || 0,
                    monto_sanciones_pendientes: res.data.monto_sanciones_pendientes || 0,
                    hojas_ruta_mes: res.data.hojas_ruta_mes || 0,
                    rutas_activas: res.data.rutas_activas || 0,
                });
            }
        } catch (error) {
            console.error('Error cargando métricas financieras:', error);
        }
    };

    const barData = useMemo(() => {
        if (!graficosData) return null;
        return {
            labels: (graficosData?.ingresos || []).map(i => String(i?.mes || '')),
            datasets: [
                {
                    label: 'Ingresos',
                    data: (graficosData?.ingresos || []).map(i => parseFloat(i?.total || 0)),
                    backgroundColor: 'rgba(99, 102, 241, 0.7)',
                    borderRadius: 8,
                    borderSkipped: false,
                },
                {
                    label: 'Egresos',
                    data: (graficosData?.egresos || []).map(e => parseFloat(e?.total || 0)),
                    backgroundColor: 'rgba(239, 68, 68, 0.7)',
                    borderRadius: 8,
                    borderSkipped: false,
                }
            ]
        };
    }, [graficosData]);

    const pieData = useMemo(() => {
        if (!stats.operativos || !stats.operativos.afiliados) return null;
        const { activos = 0, pasivos = 0, sancionados = 0 } = stats.operativos.afiliados || {};
        return {
            labels: ['Activos', 'Pasivos', 'Sancionados'],
            datasets: [
                {
                    data: [activos, pasivos, sancionados],
                    backgroundColor: ['#10b981', '#f59e0b', '#ef4444'],
                    borderWidth: 0,
                    hoverOffset: 20
                }
            ]
        };
    }, [stats.operativos]);

    const lineOcupacionData = useMemo(() => {
        if (!ocupacionData || !Array.isArray(ocupacionData.meses) || ocupacionData.meses.length === 0) return null;
        return {
            labels: ocupacionData.meses.map(m => m?.mes || ''),
            datasets: [
                {
                    label: '% Ocupación',
                    data: ocupacionData.meses.map(m => parseFloat(m?.porcentaje_ocupacion || 0)),
                    borderColor: '#6366f1',
                    backgroundColor: 'rgba(99, 102, 241, 0.1)',
                    fill: true,
                    tension: 0.4,
                    pointRadius: 4,
                    pointBackgroundColor: '#6366f1'
                }
            ]
        };
    }, [ocupacionData]);

    const chartSalidasData = useMemo(() => {
        if (!salidasData || !salidasData.salidas) return null;
        return {
            labels: salidasData.salidas.map(s => s.fecha.split('-').slice(1).reverse().join('/')),
            datasets: [
                {
                    label: 'Canitdad de Salidas',
                    data: salidasData.salidas.map(s => s.total),
                    backgroundColor: 'rgba(52, 211, 153, 0.7)',
                    borderRadius: 6,
                }
            ]
        };
    }, [salidasData]);

    const chartSemanalData = useMemo(() => {
        if (!semanalData || !semanalData.semana) return null;
        return {
            labels: semanalData.semana.map(s => s.fecha.split('-').slice(1).reverse().join('/')),
            datasets: [
                {
                    label: 'Ingresos Diarios (Bs.)',
                    data: semanalData.semana.map(s => s.total),
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    fill: true,
                    tension: 0.4,
                    pointRadius: 4,
                }
            ]
        };
    }, [semanalData]);

    const chartEgresosPorTipoData = useMemo(() => {
        if (!egresosPorTipoData || !egresosPorTipoData.egresos) return null;
        return {
            labels: egresosPorTipoData.egresos.map(e => e.tipo),
            datasets: [
                {
                    label: 'Monto (Bs.)',
                    data: egresosPorTipoData.egresos.map(e => e.total),
                    backgroundColor: [
                        'rgba(99, 102, 241, 0.7)',
                        'rgba(244, 63, 94, 0.7)',
                        'rgba(16, 185, 129, 0.7)',
                        'rgba(245, 158, 11, 0.7)',
                        'rgba(139, 92, 246, 0.7)',
                        'rgba(14, 165, 233, 0.7)',
                    ],
                    borderWidth: 0,
                }
            ]
        };
    }, [egresosPorTipoData]);

    const rutaMasRentable = useMemo(() => {
        if (!rutasRentables || rutasRentables.length === 0) return null;
        return [...rutasRentables].sort((a, b) => b.ingresos_totales - a.ingresos_totales)[0];
    }, [rutasRentables]);

    const barRutasData = useMemo(() => {
        if (!rutasRentables || rutasRentables.length === 0) return null;
        return {
            labels: rutasRentables.map(r => r?.ruta_nombre || 'N/A'),
            datasets: [
                {
                    label: 'Ingresos (Bs.)',
                    data: rutasRentables.map(r => parseFloat(r?.ingresos_totales || 0)),
                    backgroundColor: 'rgba(236, 72, 153, 0.7)',
                    borderRadius: 10,
                }
            ]
        };
    }, [rutasRentables]);

    const formatLastUpdate = () => {
        if (!lastUpdate) return '';
        const now = new Date();
        const diff = Math.floor((now - lastUpdate) / 1000);
        if (diff < 60) return `Hace ${diff}s`;
        if (diff < 3600) return `Hace ${Math.floor(diff / 60)}m`;
        return lastUpdate.toLocaleTimeString();
    };

    const getGreeting = () => {
        const hour = new Date().getHours();
        if (hour < 12) return '¡Buenos días!';
        if (hour < 19) return '¡Buenas tardes!';
        return '¡Buenas noches!';
    };

    return (
        <div className="dashboard-mejorado">
            <div className="dashboard-header">
                <div>
                    <h1>{getGreeting()} 📊</h1>
                    <p>Bienvenido al Panel de Control Administrativo</p>
                </div>
                <div className="header-actions">
                    <div className="period-selector">
                        <select
                            value={periodo}
                            onChange={(e) => setPeriodo(Number(e.target.value))}
                            className="select-periodo"
                        >
                            <option value={3}>3 meses</option>
                            <option value={6}>6 meses</option>
                            <option value={12}>1 año</option>
                        </select>
                    </div>
                    <button
                        className={`btn-refresh ${autoRefresh ? 'active' : ''}`}
                        onClick={() => setAutoRefresh(!autoRefresh)}
                    >
                        {autoRefresh ? '🔄 Auto ON' : '🔄 Auto OFF'}
                    </button>
                    <button className="btn-refresh" onClick={loadDashboardData}>
                        Actualizar {formatLastUpdate()}
                    </button>
                </div>
            </div>

            {/* Nueva sección de Accesos Rápidos */}
            <div className="quick-access-bar" style={{
                display: 'flex',
                gap: '1rem',
                marginBottom: '1.5rem',
                overflowX: 'auto',
                paddingBottom: '0.5rem'
            }}>
                <Link to="/pizarra" className="quick-card-link" style={{
                    background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                    color: 'white',
                    padding: '1rem 1.5rem',
                    borderRadius: '12px',
                    textDecoration: 'none',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.75rem',
                    boxShadow: '0 4px 15px rgba(16, 185, 129, 0.2)',
                    minWidth: '220px'
                }}>
                    <span style={{ fontSize: '1.5rem' }}>🚌</span>
                    <div>
                        <div style={{ fontWeight: 'bold', fontSize: '0.9rem' }}>Pizarra Pública</div>
                        <div style={{ fontSize: '0.75rem', opacity: 0.9 }}>Ver salidas y reservas online</div>
                    </div>
                </Link>
                <Link to="/reservas" className="quick-card-link" style={{
                    background: 'white',
                    border: '1px solid #e2e8f0',
                    color: '#1e293b',
                    padding: '1rem 1.5rem',
                    borderRadius: '12px',
                    textDecoration: 'none',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.75rem',
                    minWidth: '220px'
                }}>
                    <span style={{ fontSize: '1.5rem' }}>📅</span>
                    <div>
                        <div style={{ fontWeight: 'bold', fontSize: '0.9rem' }}>Gestión Reservas</div>
                        <div style={{ fontSize: '0.75rem', color: '#64748b' }}>Admin. reservas internas</div>
                    </div>
                </Link>
                <a 
                    href="/QR_RESERVAS_TAIPIPLAYA.png" 
                    download="QR_RESERVAS_TAIPIPLAYA.png"
                    className="quick-card-link" 
                    style={{
                        background: 'linear-gradient(135deg, #7c3aed 0%, #6d28d9 100%)',
                        color: 'white',
                        padding: '1rem 1.5rem',
                        borderRadius: '12px',
                        textDecoration: 'none',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.75rem',
                        boxShadow: '0 4px 15px rgba(124, 58, 237, 0.2)',
                        minWidth: '220px',
                        border: 'none',
                        cursor: 'pointer'
                    }}
                >
                    <span style={{ fontSize: '1.5rem' }}>⬇️</span>
                    <div>
                        <div style={{ fontWeight: 'bold', fontSize: '0.9rem' }}>Descargar QR Reservas</div>
                        <div style={{ fontSize: '0.75rem', opacity: 0.9 }}>Para imprimir y colocar en oficina</div>
                    </div>
                </a>
                <a 
                    href="/volante_reservas.png" 
                    download="volante_reservas.png"
                    className="quick-card-link" 
                    style={{
                        background: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
                        color: 'white',
                        padding: '1rem 1.5rem',
                        borderRadius: '12px',
                        textDecoration: 'none',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.75rem',
                        boxShadow: '0 4px 15px rgba(245, 158, 11, 0.2)',
                        minWidth: '220px',
                        border: 'none',
                        cursor: 'pointer'
                    }}
                >
                    <span style={{ fontSize: '1.5rem' }}>📄</span>
                    <div>
                        <div style={{ fontWeight: 'bold', fontSize: '0.9rem' }}>Descargar Volante</div>
                        <div style={{ fontSize: '0.75rem', opacity: 0.9 }}>Diseño con QR para publicidad</div>
                    </div>
                </a>
            </div>

            <div className="metricas-grid">
                <div className="metrica-cards-grid">
                    {loading ? (
                        <SkeletonLoader type="card" count={4} />
                    ) : (
                        <>
                            <div className="metrica-card total-afiliados">
                                <div className="metrica-icon">👥</div>
                                <div className="metrica-info">
                                    <div className="metrica-label">Afiliados</div>
                                    <div className="metrica-valor">{metricas.total_afiliados.toLocaleString()}</div>
                                    <div className="metrica-trend upward">↑ {metricas.afiliados_nuevos_mes} este mes</div>
                                </div>
                            </div>

                            <div className="metrica-card ingresos-mes">
                                <div className="metrica-icon">💰</div>
                                <div className="metrica-info">
                                    <div className="metrica-label">Ingresos del Mes</div>
                                    <div className="metrica-valor">Bs. {metricas.ingresos_mes.toLocaleString()}</div>
                                    <div className="metrica-trend upward">↑ {metricas.porcentaje_cambio_ingresos}% vs ant.</div>
                                </div>
                            </div>

                            <div className="metrica-card sanciones-mes">
                                <div className="metrica-icon">⚠️</div>
                                <div className="metrica-info">
                                    <div className="metrica-label">Sanciones</div>
                                    <div className="metrica-valor">{metricas.sanciones_pendientes.toLocaleString()}</div>
                                    <div className="metrica-trend downward">Bs. {metricas.monto_sanciones_pendientes.toLocaleString()}</div>
                                </div>
                            </div>

                            <div className="metrica-card rutas-activas">
                                <div className="metrica-icon">🗺️</div>
                                <div className="metrica-info">
                                    <div className="metrica-label">Hojas Mes</div>
                                    <div className="metrica-valor">{metricas.hojas_ruta_mes.toLocaleString()}</div>
                                    <div className="metrica-trend upward">{metricas.rutas_activas} rutas</div>
                                </div>
                            </div>
                        </>
                    )}
                </div>
                {!loading && rutaMasRentable && (
                    <div className="metrica-card insight">
                        <div className="metrica-icon">🚀</div>
                        <div className="metrica-info">
                            <div className="metrica-label">Ruta Estrella</div>
                            <div className="metrica-valor">{rutaMasRentable.ruta_nombre}</div>
                            <div className="metrica-trend">Ganancia: Bs. {rutaMasRentable.ingresos_totales.toLocaleString()}</div>
                        </div>
                    </div>
                )}
            </div>

            <div className="dashboard-charts">
                <div className="chart-card">
                    <h3>📈 Rendimiento Financiero</h3>
                    {barData ? (
                        <Bar
                            data={barData}
                            options={{
                                responsive: true,
                                maintainAspectRatio: false,
                                plugins: { legend: { labels: { color: chartTextColor, font: { weight: 'bold' } } } },
                                scales: {
                                    y: { grid: { color: chartGridColor }, ticks: { color: chartTextColor } },
                                    x: { grid: { display: false }, ticks: { color: chartTextColor } }
                                },
                                maxBarThickness: 50,
                                categoryPercentage: 0.8,
                                barPercentage: 0.9
                            }}
                        />
                    ) : <p>Cargando...</p>}
                </div>
                <div className="chart-card">
                    <h3>📊 Ocupación de Vehículos</h3>
                    {lineOcupacionData ? (
                        <Line
                            data={lineOcupacionData}
                            options={{
                                responsive: true,
                                maintainAspectRatio: false,
                                plugins: { legend: { display: false } },
                                scales: {
                                    y: { beginAtZero: true, max: 100, grid: { color: chartGridColor }, ticks: { color: chartTextColor } },
                                    x: { grid: { display: false }, ticks: { color: chartTextColor } }
                                }
                            }}
                        />
                    ) : <p>Cargando...</p>}
                </div>
            </div>

            <div className="dashboard-charts second-row" style={{ marginTop: '1.5rem', gridTemplateColumns: 'minmax(0, 1fr) minmax(0, 1.5fr)' }}>
                <div className="chart-card">
                    <h3>👥 Estado de Afiliados</h3>
                    {pieData ? (
                        <Doughnut
                            data={pieData}
                            options={{
                                responsive: true,
                                maintainAspectRatio: false,
                                plugins: { legend: { position: 'right', labels: { color: chartTextColor, padding: 20 } } },
                                cutout: '70%'
                            }}
                        />
                    ) : <p>Cargando...</p>}
                </div>
                <div className="chart-card">
                    <h3>📍 Ingresos por Ruta</h3>
                    {barRutasData ? (
                        <Bar
                            data={barRutasData}
                            options={{
                                indexAxis: 'y',
                                responsive: true,
                                maintainAspectRatio: false,
                                plugins: { legend: { display: false } },
                                scales: {
                                    x: { grid: { color: chartGridColor }, ticks: { color: chartTextColor } },
                                    y: { grid: { display: false }, ticks: { color: chartTextColor } }
                                },
                                maxBarThickness: 40,
                                categoryPercentage: 0.8,
                                barPercentage: 0.9
                            }}
                        />
                    ) : <p>Cargando...</p>}
                </div>
            </div>

            <div className="dashboard-charts third-row" style={{ marginTop: '1.5rem', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '1.5rem', marginBottom: '1.5rem' }}>
                <div className="chart-card">
                    <h3>🚌 Salidas por Día (14 días)</h3>
                    {chartSalidasData ? (
                        <Bar
                            data={chartSalidasData}
                            options={{
                                responsive: true,
                                maintainAspectRatio: false,
                                plugins: { legend: { display: false } },
                                scales: {
                                    y: { beginAtZero: true, grid: { color: chartGridColor }, ticks: { color: chartTextColor, stepSize: 1 } },
                                    x: { grid: { display: false }, ticks: { color: chartTextColor } }
                                }
                            }}
                        />
                    ) : <p>Cargando salidas...</p>}
                </div>
                <div className="chart-card">
                    <h3>📅 Ingresos de la Semana Actual</h3>
                    {chartSemanalData ? (
                        <Line
                            data={chartSemanalData}
                            options={{
                                responsive: true,
                                maintainAspectRatio: false,
                                plugins: { legend: { display: false } },
                                scales: {
                                    y: { beginAtZero: true, grid: { color: chartGridColor }, ticks: { color: chartTextColor } },
                                    x: { grid: { display: false }, ticks: { color: chartTextColor } }
                                }
                            }}
                        />
                    ) : <p>Cargando ingresos...</p>}
                </div>
            </div>

            <div className="dashboard-charts fourth-row" style={{ marginTop: '1.5rem', display: 'grid', gridTemplateColumns: '1fr', gap: '1.5rem', marginBottom: '1.5rem' }}>
                <div className="chart-card" style={{ height: '350px' }}>
                    <h3>💰 Gastos Detallados por Categoría</h3>
                    <div style={{ height: '280px', position: 'relative' }}>
                        {chartEgresosPorTipoData ? (
                            <Doughnut
                                data={chartEgresosPorTipoData}
                                options={{
                                    maintainAspectRatio: false,
                                    responsive: true,
                                    plugins: {
                                        legend: {
                                            position: 'right',
                                            labels: {
                                                color: chartTextColor,
                                                font: { size: 12, weight: 'bold' },
                                                padding: 20
                                            }
                                        },
                                        tooltip: {
                                            callbacks: {
                                                label: function (context) {
                                                    let label = context.label || '';
                                                    if (label) label += ': ';
                                                    if (context.parsed !== null) {
                                                        label += 'Bs. ' + context.parsed.toLocaleString();
                                                    }
                                                    return label;
                                                }
                                            }
                                        }
                                    },
                                    cutout: '60%'
                                }}
                            />
                        ) : <p>Cargando gastos...</p>}
                    </div>
                </div>
            </div>

            <div className="dashboard-bottom-grid">
                <div className="alerts-column">
                    <div className="recent-header">
                        <h2>⚠️ Alertas Críticas</h2>
                        {totalSanciones > 5 && (
                            <div className="hojas-pagination">
                                <button disabled={paginaSanciones === 1} onClick={() => setPaginaSanciones(p => p - 1)} className="pagi-btn">◀</button>
                                <span className="pagi-info">{paginaSanciones} / {Math.max(1, Math.ceil(totalSanciones / 5))}</span>
                                <button disabled={paginaSanciones >= Math.ceil(totalSanciones / 5) || totalSanciones === 0} onClick={() => setPaginaSanciones(p => p + 1)} className="pagi-btn">▶</button>
                            </div>
                        )}
                    </div>
                    <div className="alerts-list">
                        {alertas.sanciones_pendientes.map(sancion => (
                            <div key={sancion.id} className="alert-item hazard">
                                <div className="alert-icon">💰</div>
                                <div className="alert-content">
                                    <div className="alert-title">{sancion.afiliado_nombre}</div>
                                    <div className="alert-desc">{sancion.tipo_sancion_nombre} - Bs. {sancion.monto}</div>
                                </div>
                            </div>
                        ))}
                        {alertas.morosos_criticos.map(moroso => (
                            <div key={moroso.id} className="alert-item critical">
                                <div className="alert-icon">🚨</div>
                                <div className="alert-content">
                                    <div className="alert-title">{moroso.afiliado}</div>
                                    <div className="alert-desc">Deuda Crítica: Bs. {moroso.total_deuda}</div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                <div className="recent-column">
                    <div className="recent-header">
                        <h2>📋 Hojas Recientes</h2>
                        {totalHojas > 5 && (
                            <div className="hojas-pagination">
                                <button disabled={paginaHojas === 1} onClick={() => setPaginaHojas(p => p - 1)} className="pagi-btn">◀</button>
                                <span className="pagi-info">{paginaHojas} / {Math.max(1, Math.ceil(totalHojas / 5))}</span>
                                <button disabled={paginaHojas >= Math.ceil(totalHojas / 5) || totalHojas === 0} onClick={() => setPaginaHojas(p => p + 1)} className="pagi-btn">▶</button>
                            </div>
                        )}
                    </div>
                    <div className="recent-list">
                        {hojasRecientes.map(hoja => (
                            <div key={hoja.id} className="recent-item">
                                <div className="hoja-id">#{hoja.nro || hoja.id}</div>
                                <div className="hoja-details">
                                    <div className="hoja-main">{hoja.afiliado_nombre || 'N/A'}</div>
                                    <div className="hoja-sub">{hoja.ruta_nombre} - {hoja.fecha_emision}</div>
                                </div>
                                <div className="hoja-amount">Bs. {parseFloat(hoja.precio || 0).toFixed(2)}</div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            <footer className="dashboard-footer">
                <p>© 2026 Sindicato Mixto Integración Taipiplaya • Panel Administrativo v2.0</p>
            </footer>
        </div>
    );
};

export default DashboardMejorado;
