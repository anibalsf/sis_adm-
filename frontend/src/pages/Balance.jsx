import { useState, useEffect } from 'react';
import api from '../services/api';
import './Balance.css';

function Balance() {
    const [balance, setBalance] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [fechaInicio, setFechaInicio] = useState('');
    const [fechaFin, setFechaFin] = useState('');
    const [activeTab, setActiveTab] = useState('resumen'); // 'resumen' | 'ingresos' | 'egresos'
    const [searchIngreso, setSearchIngreso] = useState('');
    const [searchEgreso, setSearchEgreso] = useState('');
    const [filtroEstadoEgreso, setFiltroEstadoEgreso] = useState('todos');

    useEffect(() => {
        loadBalance();
    }, []);

    const loadBalance = async () => {
        try {
            setLoading(true);
            const params = {};
            if (fechaInicio) params.fecha_inicio = fechaInicio;
            if (fechaFin) params.fecha_fin = fechaFin;

            const response = await api.getBalance(params);
            setBalance(response.data);
            setError('');
        } catch (err) {
            setError('Error al cargar el balance');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const handleFiltrar = (e) => {
        e.preventDefault();
        loadBalance();
    };

    const limpiarFiltros = () => {
        setFechaInicio('');
        setFechaFin('');
        setSearchIngreso('');
        setSearchEgreso('');
        setTimeout(() => loadBalance(), 100);
    };

    const formatFecha = (fecha) => {
        if (!fecha) return '-';
        const [y, m, d] = fecha.split('-');
        return `${d}/${m}/${y}`;
    };

    const formatMonto = (monto) => {
        return parseFloat(monto || 0).toLocaleString('es-BO', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        });
    };

    // Filtrado de registros por búsqueda
    const ingresosFiltrados = (balance?.lista_ingresos || []).filter(item => {
        const q = searchIngreso.toLowerCase();
        return (
            item.afiliado?.toLowerCase().includes(q) ||
            item.concepto?.toLowerCase().includes(q) ||
            item.fecha?.includes(q) ||
            String(item.nro_recibo).includes(q)
        );
    });

    // Listado completo de egresos (incluye pendientes de aprobación y anulados)
    const egresosBase = balance?.lista_egresos_todos || balance?.lista_egresos || [];

    const egresosFiltrados = egresosBase.filter(item => {
        const q = searchEgreso.toLowerCase();
        const coincideTexto =
            item.concepto?.toLowerCase().includes(q) ||
            item.descripcion?.toLowerCase().includes(q) ||
            item.fecha?.includes(q);
        const coincideEstado =
            filtroEstadoEgreso === 'todos' ||
            (filtroEstadoEgreso === 'validos' && item.es_valido !== false) ||
            item.estado === filtroEstadoEgreso;
        return coincideTexto && coincideEstado;
    });

    return (
        <div className="balance-container">
            <h1>Balance Financiero</h1>
            <p>Estado financiero completo del sindicato</p>

            {/* Filtros de fecha */}
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
                        <button type="submit" className="btn btn-primary">🔍 Filtrar</button>
                        <button type="button" className="btn btn-secondary" onClick={limpiarFiltros}>✕ Limpiar</button>
                    </div>
                </form>
                {(balance?.fecha_inicio || balance?.fecha_fin) && (
                    <div className="periodo-badge">
                        📅 Periodo:{balance?.fecha_inicio && ` Desde ${formatFecha(balance.fecha_inicio)}`}
                        {balance?.fecha_fin && ` hasta ${formatFecha(balance.fecha_fin)}`}
                    </div>
                )}
            </div>

            {loading ? (
                <div className="loading-state">
                    <div className="spinner"></div>
                    <p>Cargando balance...</p>
                </div>
            ) : error ? (
                <div className="error-state">⚠️ {error}</div>
            ) : balance ? (
                <>
                    {/* Tarjetas de resumen */}
                    <div className="balance-cards">
                        <div className="balance-card ingresos" onClick={() => setActiveTab('ingresos')}>
                            <div className="card-icon">💰</div>
                            <div className="card-content">
                                <h3>Total Ingresos</h3>
                                <div className="amount">Bs. {formatMonto(balance.total_ingresos)}</div>
                                <div className="count">{balance.count_ingresos} registro(s)</div>
                            </div>
                            <div className="card-arrow">›</div>
                        </div>

                        <div className="balance-card egresos" onClick={() => setActiveTab('egresos')}>
                            <div className="card-icon">📤</div>
                            <div className="card-content">
                                <h3>Total Egresos</h3>
                                <div className="amount">Bs. {formatMonto(balance.total_egresos)}</div>
                                <div className="count">
                                    {balance.totales_egresos
                                        ? `${balance.totales_egresos.count_aprobado} aprobado(s) · ${balance.totales_egresos.count_pendiente_aprobacion} pendiente(s) · ${balance.totales_egresos.count_anulado} anulado(s)`
                                        : `${balance.count_egresos} registro(s)`}
                                </div>
                                {balance.totales_egresos && (
                                    <div className="count total-todos">
                                        Total todos: Bs. {formatMonto(balance.totales_egresos.total_monto)}
                                    </div>
                                )}
                            </div>
                            <div className="card-arrow">›</div>
                        </div>

                        <div className={`balance-card saldo ${balance.saldo >= 0 ? 'positivo' : 'negativo'}`}>
                            <div className="card-icon">{balance.saldo >= 0 ? '✅' : '⚠️'}</div>
                            <div className="card-content">
                                <h3>Saldo Actual</h3>
                                <div className="amount">Bs. {formatMonto(balance.saldo)}</div>
                                <div className="count">{balance.saldo >= 0 ? 'Positivo' : 'Negativo'}</div>
                            </div>
                        </div>
                    </div>

                    {/* Pestañas de navegación */}
                    <div className="tabs-container">
                        <button
                            className={`tab-btn ${activeTab === 'resumen' ? 'active' : ''}`}
                            onClick={() => setActiveTab('resumen')}
                        >
                            📊 Resumen por Categoría
                        </button>
                        <button
                            className={`tab-btn ingresos-tab ${activeTab === 'ingresos' ? 'active' : ''}`}
                            onClick={() => setActiveTab('ingresos')}
                        >
                            💰 Todos los Ingresos
                            <span className="tab-badge">{balance.count_ingresos}</span>
                        </button>
                        <button
                            className={`tab-btn egresos-tab ${activeTab === 'egresos' ? 'active' : ''}`}
                            onClick={() => setActiveTab('egresos')}
                        >
                            📤 Todos los Egresos
                            <span className="tab-badge">{balance.count_egresos}</span>
                        </button>
                    </div>

                    {/* ---- PESTAÑA RESUMEN ---- */}
                    {activeTab === 'resumen' && (
                        <div className="tab-content">
                            {/* Desglose Ingresos por Categoría */}
                            <div className="card categories-card">
                                <h2 className="section-title ingresos-title">
                                    💰 Desglose de Ingresos por Categoría / Tipo de Pago
                                </h2>
                                {balance.ingresos_por_tipo && balance.ingresos_por_tipo.length > 0 ? (
                                    <div className="table-container">
                                        <table className="data-table">
                                            <thead>
                                                <tr>
                                                    <th>Categoría / Tipo de Ingreso</th>
                                                    <th style={{ textAlign: 'center' }}>Cantidad Pagos</th>
                                                    <th style={{ textAlign: 'right' }}>Total (Bs.)</th>
                                                    <th style={{ textAlign: 'right' }}>% del Total</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {balance.ingresos_por_tipo.map((item, idx) => (
                                                    <tr key={idx}>
                                                        <td><strong>{item.tipo}</strong></td>
                                                        <td style={{ textAlign: 'center' }}>{item.count}</td>
                                                        <td style={{ textAlign: 'right', fontWeight: 'bold', color: '#2e7d32' }}>
                                                            {formatMonto(item.total)}
                                                        </td>
                                                        <td style={{ textAlign: 'right' }}>
                                                            {((item.total / (balance.total_ingresos || 1)) * 100).toFixed(1)}%
                                                        </td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                            <tfoot>
                                                <tr className="total-row ingresos-total">
                                                    <td>TOTAL INGRESOS</td>
                                                    <td style={{ textAlign: 'center' }}>{balance.count_ingresos}</td>
                                                    <td style={{ textAlign: 'right' }}>Bs. {formatMonto(balance.total_ingresos)}</td>
                                                    <td style={{ textAlign: 'right' }}>100%</td>
                                                </tr>
                                            </tfoot>
                                        </table>
                                    </div>
                                ) : (
                                    <div className="empty-state">No hay ingresos registrados en este período.</div>
                                )}
                            </div>

                            {/* Desglose Egresos por Categoría */}
                            <div className="card categories-card" style={{ marginTop: '1.5rem' }}>
                                <h2 className="section-title egresos-title">
                                    📤 Desglose de Gastos (Egresos) por Categoría
                                </h2>
                                {balance.egresos_por_tipo && balance.egresos_por_tipo.length > 0 ? (
                                    <div className="table-container">
                                        <table className="data-table">
                                            <thead>
                                                <tr>
                                                    <th>Categoría / Tipo de Egreso</th>
                                                    <th style={{ textAlign: 'center' }}>Cantidad Gastos</th>
                                                    <th style={{ textAlign: 'right' }}>Total (Bs.)</th>
                                                    <th style={{ textAlign: 'right' }}>% del Total</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {balance.egresos_por_tipo.map((item, idx) => (
                                                    <tr key={idx}>
                                                        <td><strong>{item.tipo}</strong></td>
                                                        <td style={{ textAlign: 'center' }}>{item.count}</td>
                                                        <td style={{ textAlign: 'right', fontWeight: 'bold', color: '#c62828' }}>
                                                            {formatMonto(item.total)}
                                                        </td>
                                                        <td style={{ textAlign: 'right' }}>
                                                            {((item.total / (balance.total_egresos || 1)) * 100).toFixed(1)}%
                                                        </td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                            <tfoot>
                                                <tr className="total-row egresos-total">
                                                    <td>TOTAL EGRESOS</td>
                                                    <td style={{ textAlign: 'center' }}>{balance.count_egresos}</td>
                                                    <td style={{ textAlign: 'right' }}>Bs. {formatMonto(balance.total_egresos)}</td>
                                                    <td style={{ textAlign: 'right' }}>100%</td>
                                                </tr>
                                            </tfoot>
                                        </table>
                                    </div>
                                ) : (
                                    <div className="empty-state">No hay egresos registrados en este período.</div>
                                )}
                            </div>

                            {/* Saldo Final */}
                            <div className={`saldo-final-card ${balance.saldo >= 0 ? 'positivo' : 'negativo'}`}>
                                <div className="saldo-row">
                                    <span>Total Ingresos</span>
                                    <span className="saldo-amount ingreso">+ Bs. {formatMonto(balance.total_ingresos)}</span>
                                </div>
                                <div className="saldo-row">
                                    <span>Total Egresos</span>
                                    <span className="saldo-amount egreso">- Bs. {formatMonto(balance.total_egresos)}</span>
                                </div>
                                <div className="saldo-divider"></div>
                                <div className="saldo-row saldo-final">
                                    <span>{balance.saldo >= 0 ? '✅' : '⚠️'} Saldo Actual en Bs.</span>
                                    <span className={`saldo-amount final ${balance.saldo >= 0 ? 'positivo' : 'negativo'}`}>
                                        Bs. {formatMonto(balance.saldo)}
                                    </span>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* ---- PESTAÑA TODOS LOS INGRESOS ---- */}
                    {activeTab === 'ingresos' && (
                        <div className="tab-content">
                            <div className="card categories-card">
                                <div className="table-header-row">
                                    <h2 className="section-title ingresos-title">
                                        💰 Todos los Ingresos
                                    </h2>
                                    <input
                                        type="text"
                                        className="search-input"
                                        placeholder="Buscar por afiliado, concepto, fecha..."
                                        value={searchIngreso}
                                        onChange={(e) => setSearchIngreso(e.target.value)}
                                    />
                                </div>
                                {ingresosFiltrados.length > 0 ? (
                                    <div className="table-container">
                                        <table className="data-table">
                                            <thead>
                                                <tr>
                                                    <th>Nº Recibo</th>
                                                    <th>Fecha</th>
                                                    <th>Afiliado</th>
                                                    <th>Concepto</th>
                                                    <th>Método de Pago</th>
                                                    <th style={{ textAlign: 'right' }}>Monto (Bs.)</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {ingresosFiltrados.map((item, idx) => (
                                                    <tr key={item.id || idx} className="ingreso-row">
                                                        <td>
                                                            <span className="recibo-badge">
                                                                #{String(item.nro_recibo).padStart(4, '0')}
                                                            </span>
                                                        </td>
                                                        <td>{formatFecha(item.fecha)}</td>
                                                        <td><strong>{item.afiliado}</strong></td>
                                                        <td>
                                                            <span className="concepto-tag ingreso-tag">{item.concepto}</span>
                                                        </td>
                                                        <td>{item.metodo_pago}</td>
                                                        <td style={{ textAlign: 'right', fontWeight: 'bold', color: '#2e7d32' }}>
                                                            {formatMonto(item.monto)}
                                                        </td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                            <tfoot>
                                                <tr className="total-row ingresos-total">
                                                    <td colSpan={5}>TOTAL INGRESOS ({ingresosFiltrados.length} registros)</td>
                                                    <td style={{ textAlign: 'right' }}>
                                                        Bs. {formatMonto(
                                                            ingresosFiltrados.reduce((acc, i) => acc + i.monto, 0)
                                                        )}
                                                    </td>
                                                </tr>
                                            </tfoot>
                                        </table>
                                    </div>
                                ) : (
                                    <div className="empty-state">
                                        {searchIngreso ? 'No se encontraron resultados para tu búsqueda.' : 'No hay ingresos registrados en este período.'}
                                    </div>
                                )}
                            </div>

                            {/* Saldo parcial */}
                            <div className="saldo-final-card positivo" style={{ marginTop: '1.5rem' }}>
                                <div className="saldo-row saldo-final">
                                    <span>💰 Total Ingresos mostrados</span>
                                    <span className="saldo-amount ingreso">
                                        Bs. {formatMonto(ingresosFiltrados.reduce((acc, i) => acc + i.monto, 0))}
                                    </span>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* ---- PESTAÑA TODOS LOS EGRESOS ---- */}
                    {activeTab === 'egresos' && (
                        <div className="tab-content">
                            <div className="card categories-card">
                                <div className="table-header-row">
                                    <h2 className="section-title egresos-title">
                                        📤 Todos los Egresos
                                    </h2>
                                    <div className="header-filters">
                                        <input
                                            type="text"
                                            className="search-input"
                                            placeholder="Buscar por concepto, descripción, fecha..."
                                            value={searchEgreso}
                                            onChange={(e) => setSearchEgreso(e.target.value)}
                                        />
                                        <select
                                            className="estado-filter"
                                            value={filtroEstadoEgreso}
                                            onChange={(e) => setFiltroEstadoEgreso(e.target.value)}
                                            aria-label="Filtrar egresos por estado"
                                        >
                                            <option value="todos">Todos los estados</option>
                                            <option value="validos">Solo válidos (balance)</option>
                                            <option value="aprobado">Aprobados</option>
                                            <option value="pendiente_aprobacion">Pendientes de aprobación</option>
                                            <option value="anulado">Anulados</option>
                                        </select>
                                    </div>
                                </div>

                                {balance.totales_egresos && (
                                    <div className="egresos-totales">
                                        <div className="egresos-total-card principal">
                                            <span className="label">Total de egresos (todos)</span>
                                            <span className="valor">
                                                Bs. {formatMonto(balance.totales_egresos.total_monto)}
                                            </span>
                                            <span className="detalle">
                                                {balance.totales_egresos.count_todos} registros
                                            </span>
                                        </div>
                                        <div className="egresos-total-card">
                                            <span className="label">Aprobados (cuentan en el balance)</span>
                                            <span className="valor verde">
                                                Bs. {formatMonto(balance.totales_egresos.total_aprobado)}
                                            </span>
                                            <span className="detalle">
                                                {balance.totales_egresos.count_aprobado} registros
                                            </span>
                                        </div>
                                        <div className="egresos-total-card">
                                            <span className="label">Pendientes de aprobación</span>
                                            <span className="valor ambar">
                                                Bs. {formatMonto(balance.totales_egresos.total_pendiente_aprobacion)}
                                            </span>
                                            <span className="detalle">
                                                {balance.totales_egresos.count_pendiente_aprobacion} registros
                                            </span>
                                        </div>
                                        <div className="egresos-total-card">
                                            <span className="label">Anulados</span>
                                            <span className="valor tachado">
                                                Bs. {formatMonto(balance.totales_egresos.total_anulado)}
                                            </span>
                                            <span className="detalle">
                                                {balance.totales_egresos.count_anulado} registros
                                            </span>
                                        </div>
                                    </div>
                                )}
                                {egresosFiltrados.length > 0 ? (
                                    <div className="table-container">
                                        <table className="data-table">
                                            <thead>
                                                <tr>
                                                    <th>#</th>
                                                    <th>Fecha</th>
                                                    <th>Concepto</th>
                                                    <th>Descripción</th>
                                                    <th>Método de Pago</th>
                                                    <th style={{ textAlign: 'center' }}>Estado</th>
                                                    <th style={{ textAlign: 'right' }}>Monto (Bs.)</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {egresosFiltrados.map((item, idx) => (
                                                    <tr
                                                        key={item.id || idx}
                                                        className="egreso-row"
                                                        style={{
                                                            opacity: item.estado === 'anulado' ? 0.6 : 1,
                                                            textDecoration: item.estado === 'anulado' ? 'line-through' : 'none'
                                                        }}
                                                    >
                                                        <td>
                                                            <span className="recibo-badge egreso-badge">
                                                                #{String(item.id).padStart(4, '0')}
                                                            </span>
                                                        </td>
                                                        <td>{formatFecha(item.fecha)}</td>
                                                        <td>
                                                            <span className="concepto-tag egreso-tag">{item.concepto}</span>
                                                        </td>
                                                        <td className="descripcion-cell">{item.descripcion || '-'}</td>
                                                        <td>{item.metodo_pago}</td>
                                                        <td style={{ textAlign: 'center' }}>
                                                            <span className={`estado-badge ${item.estado}`}>
                                                                {item.estado === 'pendiente_aprobacion'
                                                                    ? 'PENDIENTE'
                                                                    : (item.estado || 'aprobado').toUpperCase()}
                                                            </span>
                                                        </td>
                                                        <td style={{ textAlign: 'right', fontWeight: 'bold', color: '#c62828' }}>
                                                            {formatMonto(item.monto)}
                                                        </td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                            <tfoot>
                                                <tr className="total-row egresos-total">
                                                    <td colSpan={6}>
                                                        TOTAL EGRESOS MOSTRADOS ({egresosFiltrados.length} registros)
                                                    </td>
                                                    <td style={{ textAlign: 'right' }}>
                                                        Bs. {formatMonto(
                                                            egresosFiltrados.reduce((acc, e) => acc + e.monto, 0)
                                                        )}
                                                    </td>
                                                </tr>
                                            </tfoot>
                                        </table>
                                    </div>
                                ) : (
                                    <div className="empty-state">
                                        {searchEgreso ? 'No se encontraron resultados para tu búsqueda.' : 'No hay egresos registrados en este período.'}
                                    </div>
                                )}
                            </div>

                            {/* Saldo parcial */}
                            <div className="saldo-final-card negativo" style={{ marginTop: '1.5rem' }}>
                                <div className="saldo-row">
                                    <span>📤 Total de egresos (todos los estados)</span>
                                    <span className="saldo-amount egreso">
                                        Bs. {formatMonto(balance.totales_egresos?.total_monto ?? balance.total_egresos)}
                                    </span>
                                </div>
                                <div className="saldo-row">
                                    <span>✅ Egresos que afectan al balance (aprobados)</span>
                                    <span className="saldo-amount egreso">
                                        Bs. {formatMonto(balance.total_egresos)}
                                    </span>
                                </div>
                            </div>
                        </div>
                    )}
                </>
            ) : null}
        </div>
    );
}

export default Balance;
