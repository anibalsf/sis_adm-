import { useState, useEffect, useCallback } from 'react';
import api from '../services/api';
import './Bitacora.css';

const PAGE_SIZE = 25;

const ACCIONES = [
    { value: 'crear', label: 'Creación' },
    { value: 'editar', label: 'Edición' },
    { value: 'eliminar', label: 'Eliminación' },
    { value: 'login', label: 'Inicio de sesión' },
    { value: 'otro', label: 'Otro' },
];

const FILTROS_INICIALES = {
    desde: '',
    hasta: '',
    modulo: '',
    accion: '',
    usuario_id: '',
    q: '',
};

function Bitacora() {
    const [events, setEvents] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [page, setPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const [pageCount, setPageCount] = useState(0);
    const [modulos, setModulos] = useState([]);
    const [resumen, setResumen] = useState(null);

    const [filters, setFilters] = useState(FILTROS_INICIALES);
    const [busqueda, setBusqueda] = useState('');
    const [users, setUsers] = useState([]);

    const loadData = useCallback(async () => {
        setLoading(true);
        setError('');
        const params = Object.fromEntries(
            Object.entries({ ...filters, page, page_size: PAGE_SIZE }).filter(([, v]) => v !== '' && v != null)
        );
        try {
            const res = await api.getBitacora(params);
            setEvents(res.data?.results || (Array.isArray(res.data) ? res.data : []));
            setPageCount(res.data?.count || 0);
            setModulos(res.data?.modulos || []);
            setResumen(res.data?.resumen || null);
            const size = res.data?.page_size || PAGE_SIZE;
            setTotalPages(Math.max(Math.ceil((res.data?.count || 0) / size), 1));
        } catch (err) {
            console.error(err);
            setError('Error al cargar la bitácora');
        } finally {
            setLoading(false);
        }
    }, [page, filters]);

    useEffect(() => {
        api.getUsers({ page_size: 100 })
            .then((res) => setUsers(res.data.results || res.data || []))
            .catch((err) => console.error(err));
    }, []);

    useEffect(() => {
        loadData();
    }, [loadData]);

    // Búsqueda con retardo para no pedir en cada tecla
    useEffect(() => {
        const t = setTimeout(() => {
            setFilters((prev) => (prev.q === busqueda ? prev : { ...prev, q: busqueda }));
            setPage(1);
        }, 400);
        return () => clearTimeout(t);
    }, [busqueda]);

    const handleFilterChange = (e) => {
        const { name, value } = e.target;
        setFilters((prev) => ({ ...prev, [name]: value }));
        setPage(1);
    };

    const limpiarFiltros = () => {
        setFilters(FILTROS_INICIALES);
        setBusqueda('');
        setPage(1);
    };

    const formatDate = (dateString) => {
        if (!dateString) return '';
        return new Date(dateString).toLocaleString('es-BO', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
        });
    };

    const accionesResumen = ACCIONES
        .map((a) => ({ ...a, total: resumen?.por_accion?.[a.value] || 0 }))
        .filter((a) => a.total > 0);

    return (
        <div className="bitacora-container">
            <div className="page-header">
                <h1>Bitácora de Auditoría</h1>
                <p>Todos los cambios registrados en cada módulo del sistema</p>
            </div>

            {resumen && (
                <div className="bitacora-resumen">
                    <div className="resumen-card">
                        <span className="resumen-valor">{resumen.total}</span>
                        <span className="resumen-label">Movimientos</span>
                    </div>
                    {accionesResumen.map((a) => (
                        <div key={a.value} className="resumen-card">
                            <span className="resumen-valor">{a.total}</span>
                            <span className="resumen-label">{a.label}</span>
                        </div>
                    ))}
                    <div className="resumen-card">
                        <span className="resumen-valor">{modulos.length}</span>
                        <span className="resumen-label">Módulos</span>
                    </div>
                    {resumen.sin_usuario > 0 && (
                        <div className="resumen-card resumen-card-warn">
                            <span className="resumen-valor">{resumen.sin_usuario}</span>
                            <span className="resumen-label">Sin usuario</span>
                        </div>
                    )}
                </div>
            )}

            <div className="filters-section">
                <div className="filter-group filter-group-search">
                    <label>Buscar</label>
                    <input
                        type="search"
                        placeholder="Descripción, modelo, ID o usuario..."
                        value={busqueda}
                        onChange={(e) => setBusqueda(e.target.value)}
                    />
                </div>
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
                    <select name="modulo" value={filters.modulo} onChange={handleFilterChange}>
                        <option value="">Todos los módulos</option>
                        {modulos.map((m) => (
                            <option key={m.app_label} value={m.app_label}>
                                {m.nombre} ({m.total})
                            </option>
                        ))}
                    </select>
                </div>
                <div className="filter-group">
                    <label>Acción</label>
                    <select name="accion" value={filters.accion} onChange={handleFilterChange}>
                        <option value="">Todas</option>
                        {ACCIONES.map((a) => (
                            <option key={a.value} value={a.value}>{a.label}</option>
                        ))}
                    </select>
                </div>
                <div className="filter-group">
                    <label>Usuario</label>
                    <select name="usuario_id" value={filters.usuario_id} onChange={handleFilterChange}>
                        <option value="">Todos</option>
                        {users.map((u) => (
                            <option key={u.id} value={u.id}>{u.username}</option>
                        ))}
                    </select>
                </div>
                <button className="btn btn-secondary btn-limpiar" onClick={limpiarFiltros}>
                    Limpiar filtros
                </button>
            </div>

            {error && <div className="error-message">{error}</div>}

            {loading ? (
                <div className="loading">Procesando bitácora...</div>
            ) : (
                <div className="table-container">
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>Fecha y Hora</th>
                                <th>Usuario</th>
                                <th>Acción</th>
                                <th>Módulo</th>
                                <th>Descripción</th>
                                <th>Cambios Registrados</th>
                            </tr>
                        </thead>
                        <tbody>
                            {events.map((event, index) => (
                                <tr key={event.id || index}>
                                    <td style={{ whiteSpace: 'nowrap' }}>{formatDate(event.fecha_hora)}</td>
                                    <td>
                                        <div style={{ fontWeight: 'bold' }}>{event.full_name || 'Sistema'}</div>
                                        <div style={{ fontSize: '0.75rem', color: '#888' }}>
                                            {event.username ? `@${event.username}` : 'sin usuario'}
                                        </div>
                                        {event.ip_address && (
                                            <div className="bitacora-ip">IP {event.ip_address}</div>
                                        )}
                                    </td>
                                    <td>
                                        <span className={`badge-accion ${event.accion || ''}`}>
                                            {event.accion_display || event.accion || '-'}
                                        </span>
                                    </td>
                                    <td>
                                        <div className="bitacora-modulo">{event.modulo_display || '-'}</div>
                                        <div className="bitacora-tabla">
                                            {event.tabla} #{event.objeto_id}
                                        </div>
                                    </td>
                                    <td>
                                        <div className="bitacora-desc">{String(event.descripcion || '')}</div>
                                    </td>
                                    <td>
                                        {event.cambios ? (
                                            <details className="cambios-details">
                                                <summary>
                                                    Ver detalle ({Object.keys(event.cambios).length})
                                                </summary>
                                                <div className="cambios-grid">
                                                    {Object.entries(event.cambios).map(([campo, valores]) => (
                                                        <div key={campo} className="cambio-item">
                                                            <strong>
                                                                {event.cambios_labels?.[campo] || campo}:
                                                            </strong>
                                                            <div className="cambio-valores">
                                                                <span className="val-antes">
                                                                    {String(valores.antes ?? '') || 'vacío'}
                                                                </span>
                                                                <span className="val-arrow">→</span>
                                                                <span className="val-despues">
                                                                    {String(valores.despues ?? '') || 'vacío'}
                                                                </span>
                                                            </div>
                                                        </div>
                                                    ))}
                                                </div>
                                            </details>
                                        ) : (
                                            <span className="sin-cambios">Sin cambios detallados</span>
                                        )}
                                    </td>
                                </tr>
                            ))}
                            {events.length === 0 && (
                                <tr>
                                    <td colSpan="6" style={{ textAlign: 'center', padding: '40px' }}>
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
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page === 1 || loading}
                >
                    Anterior
                </button>
                <span>Página {page} de {totalPages} ({pageCount} registros)</span>
                <button
                    className="btn btn-secondary"
                    onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                    disabled={page === totalPages || loading}
                >
                    Siguiente
                </button>
            </div>
        </div>
    );
}

export default Bitacora;
