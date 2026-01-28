import { useState } from 'react';
import api from '../services/api';
import './Usuarios.css'; // Reusable styles

function ChangePassword() {
    const [formData, setFormData] = useState({
        old_password: '',
        new_password: '',
        confirm_password: ''
    });
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState({ text: '', type: '' });

    const handleSubmit = async (e) => {
        e.preventDefault();
        setMessage({ text: '', type: '' });

        if (formData.new_password !== formData.confirm_password) {
            setMessage({ text: 'Las nuevas contraseñas no coinciden', type: 'error' });
            return;
        }

        if (formData.new_password.length < 6) {
            setMessage({ text: 'La nueva contraseña debe tener al menos 6 caracteres', type: 'error' });
            return;
        }

        setLoading(true);
        try {
            await api.changePassword({
                old_password: formData.old_password,
                new_password: formData.new_password
            });
            setMessage({ text: 'Contraseña actualizada correctamente', type: 'success' });
            setFormData({ old_password: '', new_password: '', confirm_password: '' });
        } catch (err) {
            const errorMsg = err.response?.data?.old_password?.[0] ||
                err.response?.data?.detail ||
                'Error al actualizar la contraseña';
            setMessage({ text: errorMsg, type: 'error' });
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="usuarios-container">
            <div className="page-header">
                <h1>Seguridad de la Cuenta</h1>
            </div>

            <div className="card" style={{ maxWidth: '400px', margin: '20px auto' }}>
                <h3 style={{ marginBottom: '20px' }}>Cambiar Contraseña</h3>

                {message.text && (
                    <div className={`alert alert-${message.type}`} style={{
                        padding: '10px',
                        borderRadius: '5px',
                        marginBottom: '15px',
                        backgroundColor: message.type === 'success' ? '#d1e7dd' : '#f8d7da',
                        color: message.type === 'success' ? '#0f5132' : '#842029',
                        border: `1px solid ${message.type === 'success' ? '#badbcc' : '#f5c2c7'}`
                    }}>
                        {message.text}
                    </div>
                )}

                <form onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label>Contraseña Actual</label>
                        <input
                            type="password"
                            required
                            value={formData.old_password}
                            onChange={e => setFormData({ ...formData, old_password: e.target.value })}
                            disabled={loading}
                        />
                    </div>

                    <div className="form-group">
                        <label>Nueva Contraseña</label>
                        <input
                            type="password"
                            required
                            value={formData.new_password}
                            onChange={e => setFormData({ ...formData, new_password: e.target.value })}
                            disabled={loading}
                        />
                    </div>

                    <div className="form-group">
                        <label>Confirmar Nueva Contraseña</label>
                        <input
                            type="password"
                            required
                            value={formData.confirm_password}
                            onChange={e => setFormData({ ...formData, confirm_password: e.target.value })}
                            disabled={loading}
                        />
                    </div>

                    <button
                        type="submit"
                        className="btn btn-primary"
                        style={{ width: '100%', marginTop: '10px' }}
                        disabled={loading}
                    >
                        {loading ? 'Procesando...' : 'Actualizar Contraseña'}
                    </button>
                </form>
            </div>

            <div style={{ textAlign: 'center', marginTop: '20px', color: '#666', fontSize: '0.9em' }}>
                <p>⚠️ Se recomienda usar una combinación de letras, números y símbolos.</p>
            </div>
        </div>
    );
}

export default ChangePassword;
