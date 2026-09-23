import { useState, useEffect } from 'react';
import api from '../services/api';
import './Balance.css';

function Balance() {
    const [balance, setBalance] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [fechaInicio, setFechaInicio] = useState('');
    const [fechaFin, setFechaFin] = useState('');

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
        setTimeout(() => loadBalance(), 100);
    };

    return (
        <div className="balance-container">
            <h1>Módulo de Balance Financiero</h1>
            <p>Resumen del estado financiero del sindicato</p>

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
                        <button type="submit" className="btn btn-primary">Filtrar</button>
                        <button type="button" className="btn btn-secondary" onClick={limpiarFiltros}>Limpiar</button>
                    </div>
                </form>
            </div>

            {/* Tarjetas de balance */}
            {loading ? (
                <div className="loading">Cargando...</div>
            ) : error ? (
                <div className="error">{error}</div>
            ) : balance ? (
                <>
                    <div className="balance-cards">
                        <div className="balance-card ingresos">
                            <div className="card-icon">💰</div>
                            <div className="card-content">
                                <h3>Total Ingresos</h3>
                                <div className="amount">Bs. {balance.total_ingresos.toFixed(2)}</div>
                                <div className="count">{balance.count_ingresos} registro(s)</div>
                            </div>
                        </div>

                        <div className="balance-card egresos">
                            <div className="card-icon">📤</div>
                            <div className="card-content">
                                <h3>Total Egresos</h3>
                                <div className="amount">Bs. {balance.total_egresos.toFixed(2)}</div>
                                <div className="count">{balance.count_egresos} registro(s)</div>
                            </div>
                        </div>

                        <div className={`balance-card saldo ${balance.saldo >= 0 ? 'positivo' : 'negativo'}`}>
                            <div className="card-icon">{balance.saldo >= 0 ? '✅' : '⚠️'}</div>
                            <div className="card-content">
                                <h3>Saldo Actual</h3>
                                <div className="amount">Bs. {balance.saldo.toFixed(2)}</div>
                                <div className="count">{balance.saldo >= 0 ? 'Positivo' : 'Negativo'}</div>
                            </div>
                        </div>
                    </div>

                    {/* Desglose de Ingresos por Categoría */}
                    {balance.ingresos_por_tipo && balance.ingresos_por_tipo.length > 0 && (
                        <div className="card categories-card" style={{ marginTop: '2rem' }}>
                            <h2 style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '10px', color: '#2e7d32' }}>
                                💰 Desglose de Ingresos por Categoría / Tipo de Pago
                            </h2>
                            <div className="table-container">
                                <table className="data-table">
                                    <thead>
                                        <tr>
                                            <th>Categoría / Tipo de Ingreso</th>
                                            <th>Cantidad Pagos</th>
                                            <th style={{ textAlign: 'right' }}>Total (Bs.)</th>
                                            <th style={{ textAlign: 'right' }}>% del Total</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {balance.ingresos_por_tipo.map((item, idx) => (
                                            <tr key={idx}>
                                                <td><strong>{item.tipo}</strong></td>
                                                <td>{item.count}</td>
                                                <td style={{ textAlign: 'right', fontWeight: 'bold', color: '#2e7d32' }}>
                                                    {item.total.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                                                </td>
                                                <td style={{ textAlign: 'right' }}>
                                                    {((item.total / (balance.total_ingresos || 1)) * 100).toFixed(1)}%
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                    <tfoot>
                                        <tr style={{ background: 'rgba(46, 125, 50, 0.08)', fontWeight: 'bold' }}>
                                            <td>TOTAL INGRESOS</td>
                                            <td>{balance.count_ingresos}</td>
                                            <td style={{ textAlign: 'right', color: '#2e7d32' }}>Bs. {balance.total_ingresos.toFixed(2)}</td>
                                            <td style={{ textAlign: 'right' }}>100%</td>
                                        </tr>
                                    </tfoot>
                                </table>
                            </div>
                        </div>
                    )}

                    {/* Desglose de Egresos por Categoría */}
                    {balance.egresos_por_tipo && balance.egresos_por_tipo.length > 0 && (
                        <div className="card categories-card" style={{ marginTop: '2rem' }}>
                            <h2 style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '10px', color: '#c62828' }}>
                                📤 Desglose de Gastos (Egresos) por Categoría
                            </h2>
                            <div className="table-container">
                                <table className="data-table">
                                    <thead>
                                        <tr>
                                            <th>Categoría / Tipo de Egreso</th>
                                            <th>Cantidad Gastos</th>
                                            <th style={{ textAlign: 'right' }}>Total (Bs.)</th>
                                            <th style={{ textAlign: 'right' }}>% del Total</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {balance.egresos_por_tipo.map((item, idx) => (
                                            <tr key={idx}>
                                                <td><strong>{item.tipo}</strong></td>
                                                <td>{item.count}</td>
                                                <td style={{ textAlign: 'right', fontWeight: 'bold', color: '#c62828' }}>
                                                    {item.total.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                                                </td>
                                                <td style={{ textAlign: 'right' }}>
                                                    {((item.total / (balance.total_egresos || 1)) * 100).toFixed(1)}%
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                    <tfoot>
                                        <tr style={{ background: 'rgba(198, 40, 40, 0.08)', fontWeight: 'bold' }}>
                                            <td>TOTAL EGRESOS</td>
                                            <td>{balance.count_egresos}</td>
                                            <td style={{ textAlign: 'right', color: '#c62828' }}>Bs. {balance.total_egresos.toFixed(2)}</td>
                                            <td style={{ textAlign: 'right' }}>100%</td>
                                        </tr>
                                    </tfoot>
                                </table>
                            </div>
                        </div>
                    )}

                    {/* Información del periodo */}
                    {(balance.fecha_inicio || balance.fecha_fin) && (
                        <div className="periodo-info">
                            <strong>Periodo filtrado:</strong>
                            {balance.fecha_inicio && ` Desde ${balance.fecha_inicio}`}
                            {balance.fecha_fin && ` Hasta ${balance.fecha_fin}`}
                        </div>
                    )}
                </>
            ) : null}
        </div>
    );
}

export default Balance;
