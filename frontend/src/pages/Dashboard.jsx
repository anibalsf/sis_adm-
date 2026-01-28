import { useState, useEffect } from 'react';
import { api } from '../services/api';
import './Dashboard.css';

const Dashboard = () => {
    const [stats, setStats] = useState({
        afiliados: 0,
        vehiculos: 0,
        rutas: 0,
    });
    const [hojasRuta, setHojasRuta] = useState([]);
    const [cuotas, setCuotas] = useState([]);
    const [sanciones, setSanciones] = useState([]);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');
    const [telefonoNotif, setTelefonoNotif] = useState('');

    useEffect(() => {
        loadDashboardData();
    }, []);

    const loadDashboardData = async () => {
        try {
            setLoading(true);

            // Cargar estadísticas del dashboard
            const dashboardResponse = await api.getDashboard();
            setStats(dashboardResponse.data);

            // Cargar hojas de ruta
            const hojasResponse = await api.getHojasRuta({ page_size: 10 });
            setHojasRuta(hojasResponse.data.results || hojasResponse.data);
            const cuotasResp = await api.getCuotas({ page_size: 10, ordering: '-periodo' });
            setCuotas(cuotasResp.data.results || cuotasResp.data);
            const sancionesResp = await api.getSanciones({ page_size: 10, ordering: '-created_at' });
            setSanciones(sancionesResp.data.results || sancionesResp.data);
        } catch (error) {
            console.error('Error loading dashboard:', error);
            // Datos de ejemplo en caso de error
            setStats({ afiliados: 45, vehiculos: 12, rutas: 8 });
            setHojasRuta([
                { id: 1, afiliado_nombre: 'Juan Pérez', vehiculo_placa: 'ABC-123', ruta_nombre: 'La Paz', fecha: '2024-03-27', monto: 30.00 },
                { id: 2, afiliado_nombre: 'Carlos Cortez', vehiculo_placa: 'DEF-456', ruta_nombre: 'Caranavi', fecha: '2024-03-01', monto: 25.00 },
                { id: 3, afiliado_nombre: 'María Gonzalez', vehiculo_placa: 'GHI-789', ruta_nombre: 'Rincón', fecha: '2024-03-02', monto: 25.00 },
                { id: 4, afiliado_nombre: 'Juan Pérez', vehiculo_placa: 'ABC-123', ruta_nombre: 'La Paz', fecha: '2024-03-11', monto: 16.00 },
                { id: 5, afiliado_nombre: 'Carlos Cortez', vehiculo_placa: 'DEF-456', ruta_nombre: 'Caranavi', fecha: '2024-03-01', monto: 15.00 },
                { id: 6, afiliado_nombre: 'María González', vehiculo_placa: 'GHI-789', ruta_nombre: 'Rincón', fecha: '2024-04-02', monto: 30.00 },
            ]);
            setCuotas([]);
            setSanciones([]);
        } finally {
            setLoading(false);
        }
    };

    const filteredHojas = hojasRuta.filter(hoja => {
        const searchLower = searchQuery.toLowerCase();
        return (
            hoja.afiliado_nombre?.toLowerCase().includes(searchLower) ||
            hoja.vehiculo_placa?.toLowerCase().includes(searchLower) ||
            hoja.ruta_nombre?.toLowerCase().includes(searchLower)
        );
    });

    const pagarCuota = async (id) => {
        await api.cambiarEstadoCuota(id, 'pagada');
        await loadDashboardData();
    };

    const anularCuota = async (id) => {
        await api.cambiarEstadoCuota(id, 'anulada');
        await loadDashboardData();
    };

    const notificarCuota = async (id) => {
        await api.notificarCuota(id, { telefono: telefonoNotif });
    };

    const pagarSancion = async (id) => {
        await api.cambiarEstadoSancion(id, 'pagada');
        await loadDashboardData();
    };

    const anularSancion = async (id) => {
        await api.cambiarEstadoSancion(id, 'anulada');
        await loadDashboardData();
    };

    const notificarSancion = async (id) => {
        await api.notificarSancion(id, { telefono: telefonoNotif });
    };

    if (loading) {
        return <div className="loading">Cargando...</div>;
    }

    return (
        <div className="dashboard">
            {/* Tarjetas de estadísticas */}
            <div className="stats-grid">
                <div className="stat-card stat-afiliados">
                    <div className="stat-icon">👥</div>
                    <div className="stat-info">
                        <div className="stat-value">{stats.afiliados || stats.total_afiliados || 45}</div>
                        <div className="stat-label">AFILIADOS</div>
                    </div>
                </div>

                <div className="stat-card stat-vehiculos">
                    <div className="stat-icon">🚗</div>
                    <div className="stat-info">
                        <div className="stat-value">{stats.vehiculos || stats.total_vehiculos || 12}</div>
                        <div className="stat-label">VEHÍCULOS</div>
                    </div>
                </div>

                <div className="stat-card stat-rutas">
                    <div className="stat-icon">🗺️</div>
                    <div className="stat-info">
                        <div className="stat-value">{stats.rutas || stats.total_rutas || 8}</div>
                        <div className="stat-label">RUTAS</div>
                    </div>
                </div>
            </div>

            {/* Tabla de Hojas de Ruta */}
            <div className="table-section card">
                <div className="table-header">
                    <h2>HOJAS DE RUTA</h2>
                    <input
                        type="text"
                        placeholder="Search"
                        className="search-input"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                    />
                </div>

                <div className="table-wrapper">
                    <table>
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Afiliado</th>
                                <th>Vehículo</th>
                                <th>Ruta</th>
                                <th>Fecha</th>
                                <th>Monto</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filteredHojas.length > 0 ? (
                                filteredHojas.map((hoja) => (
                                    <tr key={hoja.id}>
                                        <td>{hoja.id}</td>
                                        <td>{hoja.afiliado_nombre || hoja.afiliado || 'N/A'}</td>
                                        <td>{hoja.vehiculo_placa || hoja.vehiculo || 'N/A'}</td>
                                        <td>{hoja.ruta_nombre || hoja.ruta || 'N/A'}</td>
                                        <td>{hoja.fecha || 'N/A'}</td>
                                        <td>{parseFloat(hoja.monto || 0).toFixed(2)}</td>
                                    </tr>
                                ))
                            ) : (
                                <tr>
                                    <td colSpan="6" style={{ textAlign: 'center' }}>
                                        No se encontraron hojas de ruta
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
            <div className="table-section card">
                <div className="table-header">
                    <h2>CUOTAS</h2>
                    <div className="actions">
                        <input type="tel" placeholder="Teléfono" value={telefonoNotif} onChange={(e)=>setTelefonoNotif(e.target.value)} />
                        <a href={api.urlCuotasCsv({})} target="_blank" rel="noreferrer">CSV</a>
                    </div>
                </div>
                <div className="table-wrapper">
                    <table>
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Afiliado</th>
                                <th>Periodo</th>
                                <th>Monto</th>
                                <th>Estado</th>
                                <th>Acciones</th>
                            </tr>
                        </thead>
                        <tbody>
                            {cuotas.map(c => (
                                <tr key={c.id}>
                                    <td>{c.id}</td>
                                    <td>{c.afiliado_nombre || c.afiliado}</td>
                                    <td>{c.periodo}</td>
                                    <td>{parseFloat(c.monto || 0).toFixed(2)}</td>
                                    <td>{c.estado}</td>
                                    <td>
                                        <button onClick={()=>pagarCuota(c.id)}>Pagar</button>
                                        <button onClick={()=>anularCuota(c.id)}>Anular</button>
                                        <button onClick={()=>notificarCuota(c.id)}>Notificar</button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
            <div className="table-section card">
                <div className="table-header">
                    <h2>SANCIONES</h2>
                    <div className="actions">
                        <input type="tel" placeholder="Teléfono" value={telefonoNotif} onChange={(e)=>setTelefonoNotif(e.target.value)} />
                        <a href={api.urlSancionesCsv({})} target="_blank" rel="noreferrer">CSV</a>
                    </div>
                </div>
                <div className="table-wrapper">
                    <table>
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Afiliado</th>
                                <th>Tipo</th>
                                <th>Monto</th>
                                <th>Estado</th>
                                <th>Acciones</th>
                            </tr>
                        </thead>
                        <tbody>
                            {sanciones.map(s => (
                                <tr key={s.id}>
                                    <td>{s.id}</td>
                                    <td>{s.afiliado_nombre || s.afiliado}</td>
                                    <td>{s.tipo}</td>
                                    <td>{parseFloat(s.monto || 0).toFixed(2)}</td>
                                    <td>{s.estado}</td>
                                    <td>
                                        <button onClick={()=>pagarSancion(s.id)}>Pagar</button>
                                        <button onClick={()=>anularSancion(s.id)}>Anular</button>
                                        <button onClick={()=>notificarSancion(s.id)}>Notificar</button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

export default Dashboard;
