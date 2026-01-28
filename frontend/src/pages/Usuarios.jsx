import { useState, useEffect, useCallback } from 'react';
import api from '../services/api';
import './Usuarios.css';
import '../styles/action-buttons.css';
import { IconKey, IconLock, IconCheck, IconBan } from '../components/Icons';

function Usuarios() {
    const [users, setUsers] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [search, setSearch] = useState('');
    const [page, setPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);

    // Modal State
    const [showRoleModal, setShowRoleModal] = useState(false);
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [showResetModal, setShowResetModal] = useState(false);
    const [selectedUser, setSelectedUser] = useState(null);
    const [selectedRole, setSelectedRole] = useState('');

    // Form States
    const [newUserForm, setNewUserForm] = useState({
        username: '',
        password: '',
        first_name: '',
        last_name: '',
        email: '',
        role: 'Afiliado'
    });
    const [resetPassForm, setResetPassForm] = useState({
        new_password: '',
        confirm_password: ''
    });

    const loadUsers = useCallback(async () => {
        setLoading(true);
        try {
            const res = await api.getUsers({ page, search, ordering: 'username' });
            const data = res.data.results || res.data;
            setUsers(Array.isArray(data) ? data : []);
            setTotalPages(Math.ceil((res.data.count || data.length || 1) / 10));
        } catch (err) {
            console.error(err);
            setError('Error al cargar usuarios');
        } finally {
            setLoading(false);
        }
    }, [page, search]);

    useEffect(() => {
        loadUsers();
    }, [loadUsers]);

    const handleToggleActive = async (user) => {
        if (!window.confirm(`¿${user.is_active ? 'Desactivar' : 'Activar'} al usuario ${user.username}?`)) return;
        try {
            await api.toggleUserActive(user.id);
            loadUsers();
        } catch (err) {
            alert(err.response?.data?.detail || 'Error al cambiar estado');
        }
    };

    const openRoleModal = (user) => {
        setSelectedUser(user);
        setSelectedRole(user.role || '');
        setShowRoleModal(true);
    };

    const handleAssignRole = async (e) => {
        e.preventDefault();
        try {
            await api.assignUserRole(selectedUser.id, selectedRole);
            alert(`Rol ${selectedRole} asignado correctamente`);
            setShowRoleModal(false);
            loadUsers();
        } catch (err) {
            alert(err.response?.data?.detail || 'Error al asignar rol');
        }
    };

    const handleCreateUser = async (e) => {
        e.preventDefault();
        try {
            await api.createUser(newUserForm);
            alert('Usuario creado exitosamente');
            setShowCreateModal(false);
            setNewUserForm({ username: '', password: '', first_name: '', last_name: '', email: '', role: 'Afiliado' });
            loadUsers();
        } catch (err) {
            const msg = err.response?.data ? Object.values(err.response.data).flat().join(', ') : 'Error al crear usuario';
            alert(msg);
        }
    };

    const handleResetPassword = async (e) => {
        e.preventDefault();
        if (resetPassForm.new_password !== resetPassForm.confirm_password) {
            alert('Las contraseñas no coinciden');
            return;
        }
        try {
            await api.resetUserPassword(selectedUser.id, resetPassForm.new_password);
            alert('Contraseña restablecida correctamente');
            setShowResetModal(false);
            setResetPassForm({ new_password: '', confirm_password: '' });
        } catch (err) {
            alert(err.response?.data?.detail || 'Error al restablecer contraseña');
        }
    };

    return (
        <div className="usuarios-container">
            <div className="page-header">
                <h1>Gestión de Usuarios</h1>
                <button className="btn btn-primary" onClick={() => setShowCreateModal(true)}>
                    + Nuevo Usuario
                </button>
            </div>

            <div className="filters-section">
                <div className="search-box">
                    <input
                        className="search-input"
                        type="text"
                        placeholder="Buscar por usuario, nombre o email..."
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                    />
                </div>
            </div>
            {error && <div className="error">{error}</div>}

            {loading ? <div className="loading">Cargando...</div> : (
                <div className="table-container">
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>Usuario</th>
                                <th>Nombre Completo</th>
                                <th>Email</th>
                                <th>Rol Actual</th>
                                <th>Estado</th>
                                <th>Acciones</th>
                            </tr>
                        </thead>
                        <tbody>
                            {users.map(user => (
                                <tr key={user.id}>
                                    <td><strong>@{user.username}</strong></td>
                                    <td>{user.first_name} {user.last_name}</td>
                                    <td>{user.email || '-'}</td>
                                    <td>
                                        <span className={`badge-role role-${user.role?.toLowerCase()}`}>
                                            {user.role}
                                        </span>
                                    </td>
                                    <td>
                                        <span className={`badge-status ${user.is_active ? 'active' : 'inactive'}`}>
                                            {user.is_active ? 'Activo' : 'Inactivo'}
                                        </span>
                                    </td>
                                    <td className="actions">
                                        <button
                                            className={`btn-icon ${user.is_active ? 'btn-delete' : 'btn-edit'}`}
                                            onClick={() => handleToggleActive(user)}
                                            title={user.is_active ? 'Desactivar' : 'Activar'}
                                        >
                                            {user.is_active ? <IconBan /> : <IconCheck />}
                                        </button>
                                        <button className="btn-icon btn-view" onClick={() => openRoleModal(user)} title="Asignar Rol">
                                            <IconKey />
                                        </button>
                                        <button className="btn-icon btn-edit" onClick={() => { setSelectedUser(user); setShowResetModal(true); }} title="Restablecer Contraseña">
                                            <IconLock />
                                        </button>
                                    </td>
                                </tr>
                            ))}
                            {users.length === 0 && <tr><td colSpan="6" style={{ textAlign: 'center' }}>No se encontraron usuarios</td></tr>}
                        </tbody>
                    </table>
                </div>
            )}

            <div className="pagination">
                <button disabled={page <= 1} onClick={() => setPage(p => p - 1)}>Anterior</button>
                <span>Página {page} de {totalPages}</span>
                <button disabled={page >= totalPages} onClick={() => setPage(p => p + 1)}>Siguiente</button>
            </div>

            {/* MODAL CREAR USUARIO */}
            {showCreateModal && (
                <div className="modal-overlay" onClick={() => setShowCreateModal(false)}>
                    <div className="modal-content" onClick={e => e.stopPropagation()}>
                        <h2>Crear Nuevo Usuario</h2>
                        <form onSubmit={handleCreateUser}>
                            <div className="form-group">
                                <label>Usuario (Username)</label>
                                <input required value={newUserForm.username} onChange={e => setNewUserForm({ ...newUserForm, username: e.target.value })} />
                            </div>
                            <div className="form-group">
                                <label>Contraseña Inicial</label>
                                <input type="password" required value={newUserForm.password} onChange={e => setNewUserForm({ ...newUserForm, password: e.target.value })} />
                            </div>
                            <div className="form-row">
                                <div className="form-group">
                                    <label>Nombres</label>
                                    <input value={newUserForm.first_name} onChange={e => setNewUserForm({ ...newUserForm, first_name: e.target.value })} />
                                </div>
                                <div className="form-group">
                                    <label>Apellidos</label>
                                    <input value={newUserForm.last_name} onChange={e => setNewUserForm({ ...newUserForm, last_name: e.target.value })} />
                                </div>
                            </div>
                            <div className="form-group">
                                <label>Email</label>
                                <input type="email" value={newUserForm.email} onChange={e => setNewUserForm({ ...newUserForm, email: e.target.value })} />
                            </div>
                            <div className="form-group">
                                <label>Rol de Sistema</label>
                                <select value={newUserForm.role} onChange={e => setNewUserForm({ ...newUserForm, role: e.target.value })}>
                                    <option value="Directiva">Directiva (Administrador)</option>
                                    <option value="Secretaria">Secretaria</option>
                                    <option value="Sistemas">Sistemas</option>
                                    <option value="Afiliado">Afiliado</option>
                                </select>
                            </div>
                            <div className="modal-actions">
                                <button type="button" onClick={() => setShowCreateModal(false)}>Cancelar</button>
                                <button type="submit" className="btn-primary">Crear Usuario</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* MODAL ASIGNAR ROL */}
            {showRoleModal && (
                <div className="modal-overlay" onClick={() => setShowRoleModal(false)}>
                    <div className="modal-content" onClick={e => e.stopPropagation()}>
                        <h2>Asignar Rol a @{selectedUser?.username}</h2>
                        <form onSubmit={handleAssignRole}>
                            <div className="form-group">
                                <label>Rol</label>
                                <select required value={selectedRole} onChange={e => setSelectedRole(e.target.value)}>
                                    <option value="Directiva">Directiva</option>
                                    <option value="Secretaria">Secretaria</option>
                                    <option value="Sistemas">Sistemas</option>
                                    <option value="Afiliado">Afiliado</option>
                                </select>
                            </div>
                            <div className="modal-actions">
                                <button type="button" onClick={() => setShowRoleModal(false)}>Cancelar</button>
                                <button type="submit" className="btn-primary">Guardar</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* MODAL RESET PASS */}
            {showResetModal && (
                <div className="modal-overlay" onClick={() => setShowResetModal(false)}>
                    <div className="modal-content" onClick={e => e.stopPropagation()}>
                        <h2>Restablecer Contraseña: @{selectedUser?.username}</h2>
                        <form onSubmit={handleResetPassword}>
                            <div className="form-group">
                                <label>Nueva Contraseña</label>
                                <input type="password" required value={resetPassForm.new_password} onChange={e => setResetPassForm({ ...resetPassForm, new_password: e.target.value })} />
                            </div>
                            <div className="form-group">
                                <label>Confirmar Contraseña</label>
                                <input type="password" required value={resetPassForm.confirm_password} onChange={e => setResetPassForm({ ...resetPassForm, confirm_password: e.target.value })} />
                            </div>
                            <div className="modal-actions">
                                <button type="button" onClick={() => setShowResetModal(false)}>Cancelar</button>
                                <button type="submit" className="btn-primary">Restablecer</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}

export default Usuarios;
