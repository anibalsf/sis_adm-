import { useState, useEffect, useCallback } from 'react';
import api from '../services/api';
import './Bitacora.css';

function Bitacora() {
    const [events, setEvents] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [page, setPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const [pageCount, setPageCount] = useState(0);

    // Filters
    const [filters, setFilters] = useState({
        desde: '',
        hasta: '',
        tabla: '',
        accion: '',
        usuario_id: ''
    });

    const [users, setUsers] = useState([]);

    const loadData = useCallback(async () => {
        setLoading(true);
        try {
            const res = await api.getBitacora({ ...filters, page });
            setEvents(res.data.results);
            setPageCount(res.data.count);
            setTotalPages(Math.ceil(res.data.count / 50));
        } catch (err) {
            console.error(err);
            setError('Error al cargar la bitácora');
        } finally {
            setLoading(false);
        }
    }, [page, filters]);

    const loadUsers = async () => {
        try {
            const res = await api.getUsers({ page_size: 100 });
            setUsers(res.data.results || res.data);
        } catch (err) {
            console.error(err);
        }
    };

    useEffect(() => {
        loadUsers();
    }, []);

    useEffect(() => {
        loadData();
    }, [loadData]);

    const handleFilterChange = (e) => {
        const { name, value } = e.target;
        setFilters(prev => ({ ...prev, [name]: value }));
        setPage(1); // Reset page on filter change
    };

    const formatDate = (dateString) => {
        if (!dateString) return '';
        const date = new Date(dateString);
        return date.toLocaleString('es-BO', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    return (
        <div className="bitacora-container">
            <div className="page-header">
                <h1>Bitácora de Auditoría</h1>
                <p>Seguimiento de cambios y estados en el sistema</p>
            </div>

            <div className="filters-section">
                <div className="filter-group">
                    <label>Desde</label>
                    <input type="date" name="desde" value={filters.desde} onChange={handleFilterChange} />
                </div>
                <div className="filter-group">
                    <label>Hasta</label>
                    <input type="date" name="hasta" value={filters.hasta} onChange={handleFilterChange} />
                </div>
                <div className="filter-group">
                    <label>Módulo</label>
                    <select name="tabla" value={filters.tabla} onChange={handleFilterChange}>
                        <option value="">Todos</option>
                        <option value="afiliado">Afiliado</option>
                        <option value="vehiculo">Vehículo</option>
                        <option value="hojaruta">Hoja de Ruta</option>
                        <option value="pago">Pago</option>
                        <option value="cuota">Cuota</option>
                        <option value="sancion">Sanción</option>
                    </select>
                </div>
                <div className="filter-group">
                    <label>Acción</label>
                    <select name="accion" value={filters.accion} onChange={handleFilterChange}>
                        <option value="">Todas</option>
                        <option value="crear">Creación</option>
                        <option value="editar">Edición</option>
                        <option value="eliminar">Eliminación</option>
                        <option value="login">Login</option>
                    </select>
                </div>
                <div className="filter-group">
                    <label>Usuario</label>
                    <select name="usuario_id" value={filters.usuario_id} onChange={handleFilterChange}>
                        <option value="">Todos</option>
                        {users.map(u => (
                            <option key={u.id} value={u.id}>{u.username}</option>
                        ))}
                    </select>
                </div>
            </div>

            {error && <div className="error-message" style={{ color: 'red', marginBottom: '10px' }}>{error}</div>}

            {loading ? <div className="loading">Procesando bitácora...</div> : (
                <div className="table-container">
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>Fecha y Hora</th>
                                <th>Usuario</th>
                                <th>Acción</th>
                                <th>Descripción</th>
                                <th>Cambios Registrados</th>
                            </tr>
                        </thead>
                        <tbody>
                            {events.map(event => (
                                <tr key={event.id}>
                                    <td style={{ whiteSpace: 'nowrap' }}>{formatDate(event.fecha_hora)}</td>
                                    <td>
                                        <div style={{ fontWeight: 'bold' }}>{event.full_name || 'Sistema'}</div>
                                        <div style={{ fontSize: '0.75rem', color: '#888' }}>@{event.username}</div>
                                    </td>
                                    <td>
                                        <span className={`badge-accion ${event.accion}`}>
                                            {event.accion_display}
                                        </span>
                                    </td>
                                    <td>
                                        <div className="bitacora-tabla">{event.tabla.toUpperCase()}</div>
                                        <div className="bitacora-desc">{event.descripcion}</div>
                                    </td>
                                    <td>
                                        {event.cambios ? (
                                            <details className="cambios-details">
                                                <summary>Ver detalle ({Object.keys(event.cambios).length})</summary>
                                                <div className="cambios-grid">
                                                    {Object.entries(event.cambios).map(([campo, valores]) => (
                                                        <div key={campo} className="cambio-item">
                                                            <strong>{campo}:</strong>
                                                            <div className="cambio-valores">
                                                                <span className="val-antes">{valores.antes || 'vacio'}</span>
                                                                <span className="val-arrow">→</span>
                                                                <span className="val-despues">{valores.despues || 'vacio'}</span>
                                                            </div>
                                                        </div>
                                                    ))}
                                                </div>
                                            </details>
                                        ) : (
                                            <span style={{ color: '#aaa', fontSize: '0.8rem' }}>Sin cambios detallados</span>
                                        )}
                                    </td>
                                </tr>
                            ))}
                            {events.length === 0 && (
                                <tr>
                                    <td colSpan="4" style={{ textAlign: 'center', padding: '40px' }}>
                                        No se encontraron registros de auditoría.
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            )}

            <div className="pagination">
                <button
                    className="btn btn-secondary"
                    onClick={() => setPage(p => Math.max(1, p - 1))}
                    disabled={page === 1}
                >
                    Anterior
                </button>
                <span>Página {page} de {totalPages} ({pageCount} registros)</span>
                <button
                    className="btn btn-secondary"
                    onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                    disabled={page === totalPages}
                >
                    Siguiente
                </button>
            </div>
        </div>
    );
}

export default Bitacora;
