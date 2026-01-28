import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Link, useNavigate } from 'react-router-dom';
import './Login.css';

const Login = () => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const [showPassword, setShowPassword] = useState(false);
    const [remember, setRemember] = useState(true);
    const { login } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        const result = await login(username, password, remember);

        if (result.success) {
            navigate('/');
        } else {
            setError(result.error);
        }

        setLoading(false);
    };

    return (
        <div className="login-page">
            <div className="login-container">
                <div className="login-card">
                    <div className="login-header">
                        <div className="user-icon-container">
                            👤
                        </div>
                        <h1>SINDICATO INTEGRACIÓN</h1>
                    </div>

                    <form onSubmit={handleSubmit} className="login-form">
                        {error && <div className="error-message">{error}</div>}

                        <div className="form-group">
                            <span className="input-icon">👤</span>
                            <input
                                id="username"
                                type="text"
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                                placeholder="Usuario"
                                required
                                autoFocus
                            />
                        </div>

                        <div className="form-group" style={{ display: 'flex', alignItems: 'center' }}>
                            <span className="input-icon">🔒</span>
                            <input
                                id="password"
                                type={showPassword ? 'text' : 'password'}
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                placeholder="Contraseña"
                                required
                            />
                            <button
                                type="button"
                                onClick={() => setShowPassword(v => !v)}
                                className="btn-toggle-password"
                                style={{ marginLeft: '8px' }}
                                aria-label="Mostrar/Ocultar contraseña"
                                title={showPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'}
                            >
                                {showPassword ? '🙈' : '👁️'}
                            </button>
                        </div>

                        <div className="form-options">
                            <label>
                                <input type="checkbox" checked={remember} onChange={(e) => setRemember(e.target.checked)} />
                                Recordarme
                            </label>
                            <a href="#" className="forgot-password" onClick={(e) => e.preventDefault()}>¿Olvidó su contraseña?</a>
                        </div>

                        <button type="submit" className="btn-login" disabled={loading}>
                            {loading ? 'Validando...' : 'INICIAR SESIÓN'}
                        </button>

                        <div className="create-account">
                            ¿No es miembro?
                            <a href="#" onClick={(e) => e.preventDefault()}>Crear cuenta</a>
                            <div style={{ marginTop: '10px', borderTop: '1px solid #eee', paddingTop: '10px' }}>
                                <Link to="/web" style={{ color: '#1a73e8', fontWeight: 'bold' }}>
                                    ← Volver al Sitio Web
                                </Link>
                            </div>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    );
};

export default Login;
