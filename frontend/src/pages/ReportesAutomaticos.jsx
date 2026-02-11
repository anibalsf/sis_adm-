import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './ReportesAutomaticos.css';

const ReportesAutomaticos = () => {
    const [reportes, setReportes] = useState([]);
    const [configuraciones, setConfiguraciones] = useState([]);
    const [estadisticas, setEstadisticas] = useState(null);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState('historial');
    const [filtros, setFiltros] = useState({
        tipo: '',
        estado: '',
    });

    useEffect(() => {
        cargarDatos();
    }, [filtros]);

    const cargarDatos = async () => {
        setLoading(true);
        try {
            const token = localStorage.getItem('accessToken');
            const config = {
                headers: { Authorization: `Bearer ${token}` }
            };

            // Cargar reportes
            const params = new URLSearchParams();
            if (filtros.tipo) params.append('tipo', filtros.tipo);
            if (filtros.estado) params.append('estado', filtros.estado);

            const [reportesRes, configRes, statsRes] = await Promise.all([
                axios.get(`/reportes-auto/reportes/?${params}`, config),
                axios.get('/reportes-auto/configuracion/', config),
                axios.get('/reportes-auto/reportes/estadisticas/', config),
            ]);

            setReportes(reportesRes.data?.results || reportesRes.data || []);
            setConfiguraciones(configRes.data?.results || configRes.data || []);
            setEstadisticas(statsRes.data || {});
        } catch (error) {
            console.error('Error cargando datos:', error);
        } finally {
            setLoading(false);
        }
    };

    const generarReporteManual = async (tipo) => {
        try {
            const token = localStorage.getItem('accessToken');
            await axios.post(
                '/reportes-auto/reportes/generar-manual/',
                { tipo },
                { headers: { Authorization: `Bearer ${token}` } }
            );
            alert(`Reporte ${tipo} generado exitosamente`);
            cargarDatos();
        } catch (error) {
            console.error('Error generando reporte:', error);
            const serverError = error.response?.data?.error || error.response?.data?.detail || error.message;
            alert(`Error del servidor: ${serverError}`);
        }
    };

    const toggleConfiguracion = async (id, activo) => {
        try {
            const token = localStorage.getItem('accessToken');
            const config = configuraciones.find(c => c.id === id);

            await axios.patch(
                `/reportes-auto/configuracion/${id}/`,
                { ...config, activo: !activo },
                { headers: { Authorization: `Bearer ${token}` } }
            );

            cargarDatos();
        } catch (error) {
            console.error('Error actualizando configuración:', error);
        }
    };

    const getBadgeClass = (estado) => {
        const classes = {
            'generado': 'badge-info',
            'enviado': 'badge-success',
            'fallido': 'badge-danger',
        };
        return classes[estado] || 'badge-secondary';
    };

    if (loading) {
        return (
            <div className="reportes-auto-container">
                <div className="loading-spinner">
                    <div className="spinner"></div>
                    <p>Cargando reportes...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="reportes-auto-container">
            <div className="page-header">
                <h1>📊 Reportes Automáticos</h1>
                <p>Gestión de reportes programados y configuración</p>
            </div>

            {/* Estadísticas */}
            {estadisticas && (
                <div className="stats-grid">
                    <div className="stat-card">
                        <div className="stat-icon">📄</div>
                        <div className="stat-content">
                            <h3>{estadisticas.total}</h3>
                            <p>Total Reportes</p>
                        </div>
                    </div>
                    <div className="stat-card success">
                        <div className="stat-icon">✅</div>
                        <div className="stat-content">
                            <h3>{estadisticas.enviados}</h3>
                            <p>Enviados</p>
                        </div>
                    </div>
                    <div className="stat-card danger">
                        <div className="stat-icon">❌</div>
                        <div className="stat-content">
                            <h3>{estadisticas.fallidos}</h3>
                            <p>Fallidos</p>
                        </div>
                    </div>
                    <div className="stat-card info">
                        <div className="stat-icon">📅</div>
                        <div className="stat-content">
                            <h3>{estadisticas.por_tipo?.diario || 0}</h3>
                            <p>Diarios</p>
                        </div>
                    </div>
                </div>
            )}

            {/* Tabs */}
            <div className="tabs">
                <button
                    className={`tab ${activeTab === 'historial' ? 'active' : ''}`}
                    onClick={() => setActiveTab('historial')}
                >
                    📋 Historial
                </button>
                <button
                    className={`tab ${activeTab === 'configuracion' ? 'active' : ''}`}
                    onClick={() => setActiveTab('configuracion')}
                >
                    ⚙️ Configuración
                </button>
                <button
                    className={`tab ${activeTab === 'generar' ? 'active' : ''}`}
                    onClick={() => setActiveTab('generar')}
                >
                    ➕ Generar Manual
                </button>
            </div>

            {/* Contenido de Tabs */}
            <div className="tab-content">
                {activeTab === 'historial' && (
                    <div className="historial-section">
                        <div className="filters">
                            <select
                                value={filtros.tipo}
                                onChange={(e) => setFiltros({ ...filtros, tipo: e.target.value })}
                            >
                                <option value="">Todos los tipos</option>
                                <option value="diario">Diario</option>
                                <option value="semanal">Semanal</option>
                                <option value="mensual">Mensual</option>
                            </select>
                            <select
                                value={filtros.estado}
                                onChange={(e) => setFiltros({ ...filtros, estado: e.target.value })}
                            >
                                <option value="">Todos los estados</option>
                                <option value="generado">Generado</option>
                                <option value="enviado">Enviado</option>
                                <option value="fallido">Fallido</option>
                            </select>
                        </div>

                        <div className="reportes-list">
                            {(() => {
                                if (!Array.isArray(reportes) || reportes.length === 0) {
                                    return (
                                        <div className="empty-state">
                                            <p>No hay reportes generados</p>
                                        </div>
                                    );
                                }

                                // Agrupar reportes por mes y año
                                const grupos = reportes.reduce((acc, reporte) => {
                                    const fecha = new Date(reporte.fecha_generacion);
                                    const mesAnio = fecha.toLocaleString('es-BO', { month: 'long', year: 'numeric' });
                                    if (!acc[mesAnio]) acc[mesAnio] = [];
                                    acc[mesAnio].push(reporte);
                                    return acc;
                                }, {});

                                return Object.entries(grupos).map(([mesAnio, reportesGrupo]) => (
                                    <div key={mesAnio} className="reporte-grupo-mes">
                                        <h2 className="mes-titulo">{mesAnio.toUpperCase()}</h2>
                                        <div className="grupo-grid">
                                            {reportesGrupo.map((reporte) => (
                                                <div key={reporte.id} className="reporte-card">
                                                    <div className="reporte-header">
                                                        <div>
                                                            <h3>{reporte.tipo_display}</h3>
                                                            <p className="reporte-fecha">
                                                                {new Date(reporte.fecha_generacion).toLocaleString('es-BO')}
                                                            </p>
                                                        </div>
                                                        <span className={`badge ${getBadgeClass(reporte.estado)}`}>
                                                            {reporte.estado_display}
                                                        </span>
                                                    </div>
                                                    <div className="reporte-body">
                                                        <p><strong>Período:</strong> {new Date(reporte.fecha_periodo).toLocaleDateString('es-BO')}</p>
                                                        <p><strong>Mensajes enviados:</strong> {reporte.mensajes_enviados}</p>
                                                        {reporte.destinatarios_whatsapp && (
                                                            <p className="truncate"><strong>Destinatarios:</strong> {reporte.destinatarios_whatsapp}</p>
                                                        )}
                                                    </div>
                                                    <div className="reporte-actions">
                                                        <details className="reporte-content">
                                                            <summary>Ver contenido</summary>
                                                            <pre>{reporte.contenido}</pre>
                                                        </details>
                                                        <button
                                                            className="btn-download"
                                                            onClick={() => {
                                                                const blob = new Blob([reporte.contenido], { type: 'text/plain' });
                                                                const url = window.URL.createObjectURL(blob);
                                                                const a = document.createElement('a');
                                                                a.href = url;
                                                                a.download = `Reporte_${reporte.tipo}_${reporte.fecha_periodo}.txt`;
                                                                a.click();
                                                                window.URL.revokeObjectURL(url);
                                                            }}
                                                        >
                                                            📥 Descargar .txt
                                                        </button>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                ));
                            })()}
                        </div>
                    </div>
                )}

                {activeTab === 'configuracion' && (
                    <div className="configuracion-section">
                        <div className="config-list">
                            {Array.isArray(configuraciones) && configuraciones.map((config) => (
                                <div key={config.id} className="config-card">
                                    <div className="config-header">
                                        <h3>{config.nombre}</h3>
                                        <label className="toggle-switch">
                                            <input
                                                type="checkbox"
                                                checked={config.activo}
                                                onChange={() => toggleConfiguracion(config.id, config.activo)}
                                            />
                                            <span className="toggle-slider"></span>
                                        </label>
                                    </div>
                                    <div className="config-body">
                                        <p><strong>Tipo:</strong> {config.tipo_display}</p>
                                        <p><strong>Hora de envío:</strong> {config.hora_envio}</p>
                                        {config.destinatarios_whatsapp && (
                                            <p><strong>WhatsApp:</strong> {config.destinatarios_whatsapp}</p>
                                        )}
                                        {config.destinatarios_email && (
                                            <p><strong>Email:</strong> {config.destinatarios_email}</p>
                                        )}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {activeTab === 'generar' && (
                    <div className="generar-section">
                        <div className="generar-grid">
                            <div className="generar-card" onClick={() => generarReporteManual('diario')}>
                                <div className="generar-icon">📅</div>
                                <h3>Reporte Diario</h3>
                                <p>Generar reporte del día actual</p>
                                <button className="btn-generar">Generar</button>
                            </div>
                            <div className="generar-card" onClick={() => generarReporteManual('semanal')}>
                                <div className="generar-icon">📊</div>
                                <h3>Reporte Semanal</h3>
                                <p>Generar reporte de la semana</p>
                                <button className="btn-generar">Generar</button>
                            </div>
                            <div className="generar-card" onClick={() => generarReporteManual('mensual')}>
                                <div className="generar-icon">📈</div>
                                <h3>Reporte Mensual</h3>
                                <p>Generar reporte del mes</p>
                                <button className="btn-generar">Generar</button>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default ReportesAutomaticos;
