import { useState, useEffect } from 'react';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    BarElement,
    ArcElement,
    Title,
    Tooltip,
    Legend,
} from 'chart.js';
import { Bar, Pie } from 'react-chartjs-2';
import api from '../services/api';
import { useTheme } from '../context/ThemeContext';
import './ReportesFinancieros.css';

// Registrar componentes de Chart.js
ChartJS.register(
    CategoryScale,
    LinearScale,
    BarElement,
    ArcElement,
    Title,
    Tooltip,
    Legend
);

function ReportesOperativos() {
    const [datos, setDatos] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const { darkMode } = useTheme();

    const chartTextColor = darkMode ? '#e2e8f0' : '#475569';
    const chartGridColor = darkMode ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)';

    useEffect(() => {
        loadDatos();
    }, []);

    const loadDatos = async () => {
        try {
            setLoading(true);
            const res = await api.getReportesOperativos();
            setDatos(res.data);
            setError('');
        } catch (err) {
            setError('Error al cargar los reportes operativos');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const handleExportPDF = async () => {
        const result = await api.downloadOperativosPdf({});
        if (!result.success) {
            setError(result.error);
        }
    };

    const handleExportCSV = async () => {
        const result = await api.downloadOperativosCsv({});
        if (!result.success) {
            setError(result.error);
        }
    };

    // Preparar datos para gráfico de barras - Afiliados por Estado
    const prepararDatosAfiliados = () => {
        if (!datos) return null;

        return {
            labels: ['Activos', 'Pasivos', 'Sancionados'],
            datasets: [
                {
                    label: 'Cantidad de Afiliados',
                    data: [
                        datos.afiliados?.activos || 0,
                        datos.afiliados?.pasivos || 0,
                        datos.afiliados?.sancionados || 0,
                    ],
                    backgroundColor: [
                        'rgba(75, 192, 192, 0.8)',
                        'rgba(255, 206, 86, 0.8)',
                        'rgba(255, 99, 132, 0.8)',
                    ],
                },
            ],
        };
    };

    // Preparar datos para gráfico de barras - Vehículos por Tipo
    const prepararDatosVehiculos = () => {
        if (!datos || !datos.vehiculos?.por_tipo?.length) return null;

        return {
            labels: datos.vehiculos.por_tipo.map(v => v.tipo),
            datasets: [
                {
                    label: 'Cantidad de Vehículos',
                    data: datos.vehiculos.por_tipo.map(v => v.total),
                    backgroundColor: 'rgba(54, 162, 235, 0.8)',
                },
            ],
        };
    };

    // Preparar datos para gráfico de pastel - Top Rutas
    const prepararDatosTopRutas = () => {
        if (!datos || !datos.hojas_ruta?.top_rutas?.length) return null;

        return {
            labels: datos.hojas_ruta.top_rutas.map(r => r.nombre),
            datasets: [
                {
                    label: 'Cantidad',
                    data: datos.hojas_ruta.top_rutas.map(r => r.total),
                    backgroundColor: [
                        'rgba(255, 99, 132, 0.8)',
                        'rgba(54, 162, 235, 0.8)',
                        'rgba(255, 206, 86, 0.8)',
                        'rgba(75, 192, 192, 0.8)',
                        'rgba(153, 102, 255, 0.8)',
                    ],
                },
            ],
        };
    };

    // Preparar datos para gráfico de barras - Reservas por Estado
    const prepararDatosReservas = () => {
        if (!datos || !datos.reservas?.por_estado?.length) return null;

        return {
            labels: datos.reservas.por_estado.map(r => r.estado),
            datasets: [
                {
                    label: 'Cantidad de Reservas',
                    data: datos.reservas.por_estado.map(r => r.total),
                    backgroundColor: 'rgba(153, 102, 255, 0.8)',
                },
            ],
        };
    };

    const opcionesBarras = {
        responsive: true,
        plugins: {
            legend: {
                position: 'top',
                labels: { color: chartTextColor }
            },
        },
        scales: {
            y: {
                beginAtZero: true,
                grid: { color: chartGridColor },
                ticks: { color: chartTextColor }
            },
            x: {
                grid: { color: chartGridColor },
                ticks: { color: chartTextColor }
            }
        },
    };

    const opcionesPie = {
        responsive: true,
        plugins: {
            legend: {
                position: 'right',
                labels: { color: chartTextColor }
            },
        },
    };

    const datosAfiliados = prepararDatosAfiliados();
    const datosVehiculos = prepararDatosVehiculos();
    const datosTopRutas = prepararDatosTopRutas();
    const datosReservas = prepararDatosReservas();

    return (
        <div className="reportes-container">
            <h1>Reportes Operativos</h1>
            <p>Estadísticas y métricas operativas del sindicato</p>

            {/* Botones de exportación */}
            <div className="card filter-card">
                <div className="form-actions">
                    <button type="button" className="btn btn-primary" onClick={handleExportPDF}>
                        📄 Exportar PDF
                    </button>
                    <button type="button" className="btn btn-secondary" onClick={handleExportCSV}>
                        📊 Exportar Excel
                    </button>
                </div>
            </div>

            {loading ? (
                <div className="loading">Cargando reportes...</div>
            ) : error ? (
                <div className="error">{error}</div>
            ) : datos ? (
                <>
                    {/* Tarjetas de resumen */}
                    <div className="stats-grid">
                        <div className="stat-card">
                            <h3>Afiliados</h3>
                            <div className="stat-value">{datos.afiliados.total}</div>
                            <div className="stat-detail">
                                Activos: {datos.afiliados.activos} | Pasivos: {datos.afiliados.pasivos}
                            </div>
                        </div>
                        <div className="stat-card">
                            <h3>Vehículos</h3>
                            <div className="stat-value">{datos.vehiculos.total}</div>
                        </div>
                        <div className="stat-card">
                            <h3>Hojas de Ruta</h3>
                            <div className="stat-value">{datos.hojas_ruta.total}</div>
                        </div>
                        <div className="stat-card">
                            <h3>Reservas</h3>
                            <div className="stat-value">{datos.reservas.total}</div>
                        </div>
                        <div className="stat-card">
                            <h3>Sanciones</h3>
                            <div className="stat-value">{datos.sanciones.total}</div>
                            <div className="stat-detail">
                                Pendientes: {datos.sanciones.pendientes}
                            </div>
                        </div>
                    </div>

                    {/* Gráficos */}
                    <div className="charts-grid">
                        {/* Gráfico de Afiliados */}
                        {datosAfiliados && (
                            <div className="chart-card">
                                <h3>Afiliados por Estado</h3>
                                <Bar options={opcionesBarras} data={datosAfiliados} />
                            </div>
                        )}

                        {/* Gráfico de Vehículos */}
                        {datosVehiculos && (
                            <div className="chart-card">
                                <h3>Vehículos por Tipo</h3>
                                <Bar options={opcionesBarras} data={datosVehiculos} />
                            </div>
                        )}

                        {/* Gráfico de Top Rutas */}
                        {datosTopRutas && (
                            <div className="chart-card pie-chart">
                                <h3>Top 5 Rutas Más Usadas</h3>
                                <Pie options={opcionesPie} data={datosTopRutas} />
                            </div>
                        )}

                        {/* Gráfico de Reservas */}
                        {datosReservas && (
                            <div className="chart-card">
                                <h3>Reservas por Estado</h3>
                                <Bar options={opcionesBarras} data={datosReservas} />
                            </div>
                        )}
                    </div>
                </>
            ) : null}
        </div>
    );
}

export default ReportesOperativos;
