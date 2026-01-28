import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import './Login.css'; // Reuse Login styles

const Register = () => {
    const [formData, setFormData] = useState({
        username: '',
        password: '',
        nombres: '',
        apellidos: '',
        ci: '',
        telefono: '',
        fecha_ingreso: new Date().toISOString().split('T')[0]
    });
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    const handleChange = (e) => {
        setFormData({ ...formData, [e.target.id]: e.target.value });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            await axios.post('/auth/register', formData);
            alert('Cuenta creada exitosamente. Por favor inicie sesión.');
            navigate('/login');
        } catch (err) {
            console.error(err);
            setError(err.response?.data?.detail || 'Error al crear cuenta. Verifique los datos.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="login-page">
            <div className="login-container" style={{ maxWidth: '500px' }}>
                <div className="login-card">
                    <div className="login-header">
                        <h1>Crear Cuenta</h1>
                        <p style={{ color: '#6b7280', marginTop: '5px' }}>Sindicato Taipiplaya</p>
                    </div>

                    <form onSubmit={handleSubmit} className="login-form">
                        {error && <div className="error-message">{error}</div>}

                        <div className="form-group">
                            <span className="input-icon">👤</span>
                            <input id="username" type="text" placeholder="Usuario" value={formData.username} onChange={handleChange} required />
                        </div>

                        <div className="form-group">
                            <span className="input-icon">🔒</span>
                            <input id="password" type="password" placeholder="Contraseña" value={formData.password} onChange={handleChange} required />
                        </div>

                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                            <div className="form-group">
                                <span className="input-icon">Aa</span>
                                <input id="nombres" type="text" placeholder="Nombres" value={formData.nombres} onChange={handleChange} required />
                            </div>
                            <div className="form-group">
                                <span className="input-icon">Aa</span>
                                <input id="apellidos" type="text" placeholder="Apellidos" value={formData.apellidos} onChange={handleChange} required />
                            </div>
                        </div>

                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                            <div className="form-group">
                                <span className="input-icon">🆔</span>
                                <input id="ci" type="text" placeholder="C.I." value={formData.ci} onChange={handleChange} required />
                            </div>
                            <div className="form-group">
                                <span className="input-icon">📞</span>
                                <input id="telefono" type="text" placeholder="Teléfono" value={formData.telefono} onChange={handleChange} />
                            </div>
                        </div>

                        <div className="form-group">
                            <span className="input-icon">📅</span>
                            <input id="fecha_ingreso" type="date" value={formData.fecha_ingreso} onChange={handleChange} required />
                        </div>

                        <button type="submit" className="btn-login" disabled={loading}>
                            {loading ? 'Creando...' : 'REGISTRARSE'}
                        </button>

                        <div className="create-account">
                            ¿Ya tiene cuenta?
                            <Link to="/login">Iniciar Sesión</Link>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    );
};

export default Register;
