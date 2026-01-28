import { useState, useEffect } from 'react';
import api from '../services/api';
import '../css/Common.css';
import { SkeletonTable } from '../components/Skeleton/Skeleton';
import { IconPencil, IconTrash } from '../components/Icons';

function Rutas() {
    const [rutas, setRutas] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [showModal, setShowModal] = useState(false);
    const [modalMode, setModalMode] = useState('create');
    const [editingId, setEditingId] = useState(null);
    const [form, setForm] = useState({
        nombre: '',
        origen: '',
        destino: '',
        tarifa_base: '',
        prefijo: ''
    });

    useEffect(() => {
        loadRutas();
    }, []);

    const loadRutas = async () => {
        setLoading(true);
        try {
            const res = await api.getRutas();
            setRutas(res.data.results || res.data);
        } catch (err) {
            setError('Error al cargar rutas');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const openCreate = () => {
        setModalMode('create');
        setForm({ nombre: '', origen: '', destino: '', tarifa_base: '', prefijo: '' });
        setShowModal(true);
    };

    const openEdit = (ruta) => {
        setModalMode('edit');
        setEditingId(ruta.id);
        setForm({
            nombre: ruta.nombre,
            origen: ruta.origen,
            destino: ruta.destino,
            tarifa_base: String(ruta.tarifa_base),
            prefijo: ruta.prefijo || ''
        });
        setShowModal(true);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            const payload = {
                ...form,
                tarifa_base: parseFloat(form.tarifa_base)
            };

            if (modalMode === 'create') {
                await api.createRuta(payload);
            } else {
                await api.updateRuta(editingId, payload);
            }

            setShowModal(false);
            loadRutas();
        } catch (err) {
            const errorMsg = err.response?.data?.detail ||
                (err.response?.data && typeof err.response.data === 'object'
                    ? Object.values(err.response.data).flat().join(', ')
                    : 'Error al guardar ruta');
            alert(errorMsg);
            console.error(err);
        }
    };

    const handleDelete = async (id) => {
        if (!window.confirm('¿Eliminar esta ruta?')) return;
        try {
            await api.deleteRuta(id);
            loadRutas();
        } catch (err) {
            alert('Error al eliminar ruta');
            console.error(err);
        }
    };

    return (
        <div className="page-container">
            <div className="page-header">
                <h1>Gestión de Rutas</h1>
                <p>Administra las rutas de transporte del sindicato</p>
            </div>

            <div className="card">
                <div className="table-header">
                    <button className="btn btn-primary" onClick={openCreate}>
                        + Nueva Ruta
                    </button>
                </div>

                {loading ? (
                    <div className="loading">Cargando...</div>
                ) : error ? (
                    <div className="error">{error}</div>
                ) : (
                    <div className="table-wrapper">
                        <table className="data-table">
                            <thead>
                                <tr>
                                    <th>Nombre</th>
                                    <th>Origen</th>
                                    <th>Destino</th>
                                    <th>Tarifa Base (Bs.)</th>
                                    <th>Prefijo</th>
                                    <th>Acciones</th>
                                </tr>
                            </thead>
                            <tbody>
                                {rutas.map(ruta => (
                                    <tr key={ruta.id}>
                                        <td><strong>{ruta.nombre}</strong></td>
                                        <td>{ruta.origen}</td>
                                        <td>{ruta.destino}</td>
                                        <td>{parseFloat(ruta.tarifa_base).toFixed(2)}</td>
                                        <td>{ruta.prefijo || '-'}</td>
                                        <td className="actions">
                                            <button className="btn-icon btn-edit" onClick={() => openEdit(ruta)} title="Editar"><IconPencil /></button>
                                            <button className="btn-icon btn-delete" onClick={() => handleDelete(ruta.id)} title="Eliminar"><IconTrash /></button>
                                        </td>
                                    </tr>
                                ))}
                                {rutas.length === 0 && (
                                    <tr>
                                        <td colSpan="6" style={{ textAlign: 'center' }}>
                                            No hay rutas registradas
                                        </td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>

            {/* MODAL */}
            {showModal && (
                <div className="modal-overlay" onClick={() => setShowModal(false)}>
                    <div className="modal-content" onClick={e => e.stopPropagation()}>
                        <div className="modal-header">
                            <h2>{modalMode === 'create' ? 'Nueva Ruta' : 'Editar Ruta'}</h2>
                            <button className="modal-close" onClick={() => setShowModal(false)}>✕</button>
                        </div>
                        <form onSubmit={handleSubmit} className="modal-form">
                            <div className="form-group">
                                <label>Nombre</label>
                                <input
                                    type="text"
                                    required
                                    value={form.nombre}
                                    onChange={e => setForm({ ...form, nombre: e.target.value })}
                                    placeholder="Ej: La Paz, Caranavi"
                                />
                            </div>
                            <div className="form-group">
                                <label>Origen</label>
                                <input
                                    type="text"
                                    required
                                    value={form.origen}
                                    onChange={e => setForm({ ...form, origen: e.target.value })}
                                    placeholder="Ej: Taipiplaya"
                                />
                            </div>
                            <div className="form-group">
                                <label>Destino</label>
                                <input
                                    type="text"
                                    required
                                    value={form.destino}
                                    onChange={e => setForm({ ...form, destino: e.target.value })}
                                    placeholder="Ej: La Paz"
                                />
                            </div>
                            <div className="form-group">
                                <label>Tarifa Base (Bs.)</label>
                                <input
                                    type="number"
                                    step="0.01"
                                    min="0"
                                    required
                                    value={form.tarifa_base}
                                    onChange={e => setForm({ ...form, tarifa_base: e.target.value })}
                                />
                            </div>
                            <div className="form-group">
                                <label>Prefijo (Opcional)</label>
                                <input
                                    type="text"
                                    maxLength="10"
                                    value={form.prefijo}
                                    onChange={e => setForm({ ...form, prefijo: e.target.value })}
                                    placeholder="Ej: LP, CAR"
                                />
                            </div>
                            <div className="form-actions">
                                <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>
                                    Cancelar
                                </button>
                                <button type="submit" className="btn btn-primary">
                                    Guardar
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}

export default Rutas;
