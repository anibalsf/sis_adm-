import { useState, useEffect } from 'react';
import api from '../services/api';
import './ReportesFinancieros.css';
import './ReportePorCategoria.css';

function ReportePorCategoria() {
    const [tiposPago, setTiposPago] = useState([]);
    const [filtros, setFiltros] = useState({
        tipo_pago_id: 'todos',
        fecha_inicio: '',
        fecha_fin: '',
        monto_esperado: ''
    });
    
    const [reporte, setReporte] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    useEffect(() => {
        cargarTiposPago();
    }, []);

    const cargarTiposPago = async () => {
        try {
            const res = await api.getReporteCategoria({});
            if (res.data && res.data.tipos_pago) {
                setTiposPago(res.data.tipos_pago);
            }
        } catch (err) {
            console.error("Error al cargar categorías de ingreso:", err);
            setError("Error al cargar categorías de ingreso");
        }
    };

    const handleFilterChange = (e) => {
        const { name, value } = e.target;
        setFiltros(prev => ({
            ...prev,
            [name]: value
        }));
    };

    const cargarReporte = async () => {
        if (!filtros.tipo_pago_id) {
            setError("Debe seleccionar una categoría");
            return;
        }
        
        try {
            setLoading(true);
            setError('');
            const params = filtros.tipo_pago_id === 'todos'
                ? { todas: '1' }
                : { tipo_pago_id: filtros.tipo_pago_id };
            if (filtros.fecha_inicio) params.fecha_inicio = filtros.fecha_inicio;
            if (filtros.fecha_fin) params.fecha_fin = filtros.fecha_fin;
            if (filtros.monto_esperado) params.monto_esperado = filtros.monto_esperado;

            const res = await api.getReporteCategoria(params);
            if (res.data && (res.data.resumen || res.data.categorias)) {
                setReporte(res.data);
            } else {
                setError(res.data?.error || "Error al generar reporte");
            }
        } catch (err) {
            console.error("Error al cargar el reporte:", err);
            setError(err.response?.data?.error || "Error al cargar el reporte");
            setReporte(null);
        } finally {
            setLoading(false);
        }
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        cargarReporte();
    };

    const handleDownloadPdf = async () => {
        if (!filtros.tipo_pago_id) return;
        try {
            const categoriaSeleccionada = tiposPago.find(t => t.id.toString() === filtros.tipo_pago_id.toString());
            const nombreCat = categoriaSeleccionada ? categoriaSeleccionada.nombre : '';
            
            const params = filtros.tipo_pago_id === 'todos'
                ? { todas: '1', nombre_categoria: 'todas_las_categorias' }
                : { tipo_pago_id: filtros.tipo_pago_id, nombre_categoria: nombreCat };
            if (filtros.fecha_inicio) params.fecha_inicio = filtros.fecha_inicio;
            if (filtros.fecha_fin) params.fecha_fin = filtros.fecha_fin;
            if (filtros.monto_esperado) params.monto_esperado = filtros.monto_esperado;

            const res = await api.downloadReporteCategoriaPdf(params);
            if (!res.success) {
                alert('Error al descargar PDF: ' + res.error);
            }
        } catch (err) {
            console.error("Error al descargar PDF:", err);
            alert("Error al descargar PDF");
        }
    };

    const handleDownloadExcel = async () => {
        if (!filtros.tipo_pago_id) return;
        try {
            const categoriaSeleccionada = tiposPago.find(t => t.id.toString() === filtros.tipo_pago_id.toString());
            const nombreCat = categoriaSeleccionada ? categoriaSeleccionada.nombre : '';
            
            const params = filtros.tipo_pago_id === 'todos'
                ? { todas: '1', nombre_categoria: 'todas_las_categorias' }
                : { tipo_pago_id: filtros.tipo_pago_id, nombre_categoria: nombreCat };
            if (filtros.fecha_inicio) params.fecha_inicio = filtros.fecha_inicio;
            if (filtros.fecha_fin) params.fecha_fin = filtros.fecha_fin;
            if (filtros.monto_esperado) params.monto_esperado = filtros.monto_esperado;

            const res = await api.downloadReporteCategoriaExcel(params);
            if (!res.success) {
                alert('Error al descargar Excel: ' + res.error);
            }
        } catch (err) {
            console.error("Error al descargar Excel:", err);
            alert("Error al descargar Excel");
        }
    };

    return (
        <div className="reporte-categoria-wrapper">
            {/* Hero Header */}
            <div className="categoria-hero">
                <div className="hero-title-group">
                    <span className="hero-icon">🎯</span>
                    <div>
                        <h1>Reporte de Cobertura por Categoría</h1>
                        <p>Analiza el estado de cumplimiento y pagos de afiliados por concepto de ingreso</p>
                    </div>
                </div>
            </div>

            {/* Panel de Filtros */}
            <div className="filtros-card">
                <div className="filtros-card-header">
                    <span>⚡ Parámetros del Reporte</span>
                </div>
                <form className="filtros-grid" onSubmit={handleSubmit}>
                    <div className="filtro-field">
                        <label>🏷️ Categoría de Ingreso:</label>
                        <select 
                            className="filtro-control"
                            name="tipo_pago_id" 
                            value={filtros.tipo_pago_id} 
                            onChange={handleFilterChange}
                            required
                        >
                            <option value="todos">Todas las categorías</option>
                            {tiposPago.map(tipo => (
                                <option key={tipo.id} value={tipo.id}>
                                    {tipo.nombre}
                                </option>
                            ))}
                        </select>
                    </div>
                    <div className="filtro-field">
                        <label>📅 Fecha Desde:</label>
                        <input 
                            className="filtro-control"
                            type="date" 
                            name="fecha_inicio" 
                            value={filtros.fecha_inicio} 
                            onChange={handleFilterChange} 
                        />
                    </div>
                    <div className="filtro-field">
                        <label>📅 Fecha Hasta:</label>
                        <input 
                            className="filtro-control"
                            type="date" 
                            name="fecha_fin" 
                            value={filtros.fecha_fin} 
                            onChange={handleFilterChange} 
                        />
                    </div>
                    <div className="filtro-field">
                        <label>💵 Monto Esperado por Afiliado:</label>
                        <input
                            className="filtro-control"
                            type="number"
                            name="monto_esperado"
                            min="0"
                            step="0.01"
                            placeholder="Ej: 50.00"
                            value={filtros.monto_esperado}
                            onChange={handleFilterChange}
                        />
                    </div>
                    <div className="filtro-field">
                        <button type="submit" className="btn-generar-reporte" disabled={loading}>
                            {loading ? (
                                <>⌛ Generando...</>
                            ) : (
                                <>🔍 Generar Reporte</>
                            )}
                        </button>
                    </div>
                </form>
                {error && <div className="error-message" style={{ marginTop: '1rem', padding: '0.75rem', background: '#fee2e2', color: '#b91c1c', borderRadius: '8px' }}>{error}</div>}
            </div>

            {reporte && (
                <>
                    {/* Barra de Exportación */}
                    <div className="export-toolbar">
                        <div className="export-toolbar-info">
                            <span>📄 Formatos de descarga oficial listos:</span>
                        </div>
                        <div className="export-toolbar-actions">
                            <button className="btn-export-pill pdf" onClick={handleDownloadPdf}>
                                📄 Exportar a PDF
                            </button>
                            <button className="btn-export-pill excel" onClick={handleDownloadExcel}>
                                📊 Exportar a Excel
                            </button>
                        </div>
                    </div>

                    {reporte.categorias ? (
                        <>
                            {/* KPIs Ejecutivos Globales */}
                            <div className="kpis-container-grid">
                                <div className="kpi-stat-card">
                                    <div className="kpi-stat-icon recaudado">💰</div>
                                    <div className="kpi-stat-info">
                                        <label>Total Recaudado</label>
                                        <div className="value">Bs. {Number(reporte.resumen.total_recaudado || 0).toFixed(2)}</div>
                                    </div>
                                </div>
                                {reporte.resumen.total_esperado !== null && reporte.resumen.total_esperado !== undefined && (
                                    <div className="kpi-stat-card">
                                        <div className="kpi-stat-icon esperado">📌</div>
                                        <div className="kpi-stat-info">
                                            <label>Total Esperado</label>
                                            <div className="value">Bs. {Number(reporte.resumen.total_esperado || 0).toFixed(2)}</div>
                                        </div>
                                    </div>
                                )}
                                {reporte.resumen.monto_faltante !== null && reporte.resumen.monto_faltante !== undefined && (
                                    <div className="kpi-stat-card">
                                        <div className="kpi-stat-icon faltante">⚠️</div>
                                        <div className="kpi-stat-info">
                                            <label>Monto Faltante</label>
                                            <div className="value" style={{ color: '#dc2626' }}>Bs. {Number(reporte.resumen.monto_faltante || 0).toFixed(2)}</div>
                                        </div>
                                    </div>
                                )}
                                <div className="kpi-stat-card">
                                    <div className="kpi-stat-icon categorias">🎯</div>
                                    <div className="kpi-stat-info">
                                        <label>Categorías</label>
                                        <div className="value">{reporte.resumen.total_categorias}</div>
                                    </div>
                                </div>
                                <div className="kpi-stat-card">
                                    <div className="kpi-stat-icon afiliados">👥</div>
                                    <div className="kpi-stat-info">
                                        <label>Afiliados Activos</label>
                                        <div className="value">{reporte.resumen.total_afiliados_activos}</div>
                                    </div>
                                </div>
                            </div>

                            {/* Tabla Resumen Clasificado */}
                            <div className="seccion-card">
                                <h3 className="seccion-card-title">📊 Resumen Clasificado por Categoría</h3>
                                <div className="tabla-wrapper">
                                    <table className="tabla-custom">
                                        <thead>
                                            <tr>
                                                <th>Categoría</th>
                                                <th>Ya Cancelaron</th>
                                                <th>Faltan Pagar</th>
                                                <th>Afiliados Activos</th>
                                                <th>% Cobertura</th>
                                                <th>Total Recaudado</th>
                                                <th>Total Esperado</th>
                                                <th>Monto Faltante</th>
                                                <th>Revisión</th>
                                                <th>Duplicados</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {reporte.categorias.map(item => (
                                                <tr key={item.categoria.id}>
                                                    <td style={{ fontWeight: '700', color: '#0f172a' }}>{item.categoria.nombre}</td>
                                                    <td>
                                                        <span className="badge-pill success">{item.count_pagaron}</span>
                                                    </td>
                                                    <td>
                                                        <span className="badge-pill danger">{item.count_pendientes}</span>
                                                    </td>
                                                    <td>{item.total_afiliados_activos}</td>
                                                    <td>
                                                        <span className={`badge-pill ${item.porcentaje_cobertura >= 70 ? 'success' : item.porcentaje_cobertura >= 40 ? 'warning' : 'danger'}`}>
                                                            {item.porcentaje_cobertura}%
                                                        </span>
                                                    </td>
                                                    <td style={{ fontWeight: '700', color: '#059669' }}>Bs. {Number(item.total_recaudado || 0).toFixed(2)}</td>
                                                    <td>{item.total_esperado !== null && item.total_esperado !== undefined ? `Bs. ${Number(item.total_esperado || 0).toFixed(2)}` : '-'}</td>
                                                    <td style={{ color: '#dc2626', fontWeight: '700' }}>{item.monto_faltante !== null && item.monto_faltante !== undefined ? `Bs. ${Number(item.monto_faltante || 0).toFixed(2)}` : '-'}</td>
                                                    <td>{(item.count_pagos_pendientes_revision || 0) + (item.count_pagos_anulados_cancelados || 0)}</td>
                                                    <td>{item.count_afiliados_con_pago_duplicado || 0}</td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </>
                    ) : (
                        <>
                            {/* KPIs Categoría Individual */}
                            <div className="kpis-container-grid">
                                <div className="kpi-stat-card">
                                    <div className="kpi-stat-icon recaudado">💰</div>
                                    <div className="kpi-stat-info">
                                        <label>Total Recaudado</label>
                                        <div className="value">Bs. {Number(reporte.resumen.total_recaudado || 0).toFixed(2)}</div>
                                    </div>
                                </div>
                                <div className="kpi-stat-card">
                                    <div className="kpi-stat-icon afiliados">✅</div>
                                    <div className="kpi-stat-info">
                                        <label>Afiliados que Pagaron</label>
                                        <div className="value">{reporte.resumen.count_pagaron} <span style={{ fontSize: '0.85rem', color: '#64748b', fontWeight: '500' }}>/ {reporte.resumen.total_afiliados_activos}</span></div>
                                    </div>
                                </div>
                                <div className="kpi-stat-card">
                                    <div className="kpi-stat-icon faltante">❌</div>
                                    <div className="kpi-stat-info">
                                        <label>Afiliados Pendientes</label>
                                        <div className="value" style={{ color: '#dc2626' }}>{reporte.resumen.count_pendientes}</div>
                                    </div>
                                </div>
                                {reporte.resumen.total_esperado !== null && reporte.resumen.total_esperado !== undefined && (
                                    <div className="kpi-stat-card">
                                        <div className="kpi-stat-icon esperado">📌</div>
                                        <div className="kpi-stat-info">
                                            <label>Total Esperado</label>
                                            <div className="value">Bs. {Number(reporte.resumen.total_esperado || 0).toFixed(2)}</div>
                                        </div>
                                    </div>
                                )}
                                {reporte.resumen.monto_faltante !== null && reporte.resumen.monto_faltante !== undefined && (
                                    <div className="kpi-stat-card">
                                        <div className="kpi-stat-icon faltante">⚠️</div>
                                        <div className="kpi-stat-info">
                                            <label>Monto Faltante</label>
                                            <div className="value" style={{ color: '#dc2626' }}>Bs. {Number(reporte.resumen.monto_faltante || 0).toFixed(2)}</div>
                                        </div>
                                    </div>
                                )}
                                <div className="kpi-stat-card">
                                    <div className="kpi-stat-icon categorias">📊</div>
                                    <div className="kpi-stat-info">
                                        <label>% Cobertura</label>
                                        <div className="value">{reporte.resumen.porcentaje_cobertura}%</div>
                                    </div>
                                </div>
                            </div>

                            {/* Alertas y Duplicados */}
                            <div className="seccion-card">
                                <h3 className="seccion-card-title">⚠️ Alertas de Revisión</h3>
                                <div className="tabla-wrapper">
                                    <table className="tabla-custom">
                                        <thead>
                                            <tr>
                                                <th>Indicador</th>
                                                <th>Cantidad</th>
                                                <th>Monto</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            <tr>
                                                <td>Pagos pendientes de revisión</td>
                                                <td><span className="badge-pill warning">{reporte.resumen.count_pagos_pendientes_revision || 0}</span></td>
                                                <td>Bs. {Number(reporte.resumen.total_pagos_pendientes_revision || 0).toFixed(2)}</td>
                                            </tr>
                                            <tr>
                                                <td>Pagos anulados/cancelados</td>
                                                <td><span className="badge-pill danger">{reporte.resumen.count_pagos_anulados_cancelados || 0}</span></td>
                                                <td>Bs. {Number(reporte.resumen.total_pagos_anulados_cancelados || 0).toFixed(2)}</td>
                                            </tr>
                                            <tr>
                                                <td>Afiliados con posible pago duplicado</td>
                                                <td><span className="badge-pill info">{reporte.resumen.count_afiliados_con_pago_duplicado || 0}</span></td>
                                                <td>-</td>
                                            </tr>
                                        </tbody>
                                    </table>
                                </div>
                            </div>

                            {reporte.duplicados?.length > 0 && (
                                <div className="seccion-card">
                                    <h3 className="seccion-card-title" style={{ color: '#ea580c' }}>⚠️ Posibles Pagos Duplicados</h3>
                                    <div className="tabla-wrapper">
                                        <table className="tabla-custom">
                                            <thead>
                                                <tr>
                                                    <th>Afiliado</th>
                                                    <th>C.I.</th>
                                                    <th>Cantidad Pagos</th>
                                                    <th>Total Pagado</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {reporte.duplicados.map(item => (
                                                    <tr key={item.afiliado_id}>
                                                        <td style={{ fontWeight: '600' }}>{item.nombre}</td>
                                                        <td>{item.ci}</td>
                                                        <td><span className="badge-pill warning">{item.cantidad_pagos}</span></td>
                                                        <td style={{ fontWeight: '700', color: '#059669' }}>Bs. {Number(item.total_pagado || 0).toFixed(2)}</td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            )}

                            {/* Tabla de Pendientes */}
                            <div className="seccion-card">
                                <h3 className="seccion-card-title" style={{ color: '#dc2626' }}>
                                    ❌ Afiliados que FALTAN Cancelar ({reporte.pendientes.length})
                                </h3>
                                {reporte.pendientes.length > 0 ? (
                                    <div className="tabla-wrapper">
                                        <table className="tabla-custom">
                                            <thead>
                                                <tr>
                                                    <th>#</th>
                                                    <th>Nombre Completo</th>
                                                    <th>C.I.</th>
                                                    <th>Teléfono</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {reporte.pendientes.map((af, idx) => (
                                                    <tr key={af.afiliado_id}>
                                                        <td style={{ color: '#94a3b8' }}>{idx + 1}</td>
                                                        <td style={{ fontWeight: '600', color: '#0f172a' }}>{af.nombre}</td>
                                                        <td>{af.ci}</td>
                                                        <td>{af.telefono || '-'}</td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                ) : (
                                    <p style={{ padding: '1.5rem', textAlign: 'center', color: '#059669', fontWeight: '700' }}>
                                        ✅ ¡Excelente! Todos los afiliados activos han cancelado esta categoría en el período seleccionado.
                                    </p>
                                )}
                            </div>

                            {/* Tabla de Pagos Realizados */}
                            <div className="seccion-card">
                                <h3 className="seccion-card-title" style={{ color: '#059669' }}>
                                    ✅ Afiliados que YA Cancelaron ({reporte.pagaron.length} pagos)
                                </h3>
                                {reporte.pagaron.length > 0 ? (
                                    <div className="tabla-wrapper">
                                        <table className="tabla-custom">
                                            <thead>
                                                <tr>
                                                    <th>#</th>
                                                    <th>Nombre Completo</th>
                                                    <th>C.I.</th>
                                                    <th>Fecha Pago</th>
                                                    <th>Monto</th>
                                                    <th>Estado</th>
                                                    <th>Nro. Recibo</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {reporte.pagaron.map((pago, idx) => (
                                                    <tr key={`${pago.afiliado_id}-${idx}`}>
                                                        <td style={{ color: '#94a3b8' }}>{idx + 1}</td>
                                                        <td style={{ fontWeight: '600', color: '#0f172a' }}>{pago.nombre}</td>
                                                        <td>{pago.ci}</td>
                                                        <td>{new Date(pago.fecha_pago).toLocaleDateString()}</td>
                                                        <td style={{ fontWeight: '700', color: '#059669' }}>Bs. {Number(pago.monto || 0).toFixed(2)}</td>
                                                        <td>
                                                            <span className="badge-pill success">{pago.estado}</span>
                                                        </td>
                                                        <td>{pago.nro_recibo || '-'}</td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                ) : (
                                    <p style={{ padding: '1.5rem', textAlign: 'center', color: '#64748b' }}>
                                        No hay registros de pagos para esta categoría en el período seleccionado.
                                    </p>
                                )}
                            </div>
                        </>
                    )}
                </>
            )}
        </div>
    );
}

export default ReportePorCategoria;
