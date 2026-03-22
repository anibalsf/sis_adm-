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
            // Redirección inteligente según el rol
            const role = result.user?.role;
            if (role === 'Afiliado') {
                navigate('/mi-perfil');
            } else {
                navigate('/dashboard');
            }
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
                        <div className="logo-login-container">
                            <img src="/login_avatar.svg" alt="Login Avatar" className="login-logo" />
                        </div>
                        <h1>SINDICATO MIXTO</h1>
                        <h2 className="subtitle">"INTEGRACIÓN TAIPIPLAYA"</h2>
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
                                placeholder="Email ID / Usuario / CI"
                                required
                                autoFocus
                            />
                        </div>
                        <div className="login-hint">
                            💡 Afiliado: Su Usuario y Contraseña es su CI (sin extensión).
                        </div>

                        <div className="form-group">
                            <span className="input-icon">🔒</span>
                            <input
                                id="password"
                                type={showPassword ? 'text' : 'password'}
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                placeholder="Password"
                                required
                            />
                            <button
                                type="button"
                                onClick={() => setShowPassword(v => !v)}
                                className="btn-toggle-password"
                                aria-label="Mostrar/Ocultar contraseña"
                            >
                                {showPassword ? '🙈' : '👁️'}
                            </button>
                        </div>

                        <div className="form-options">
                            <label>
                                <input type="checkbox" checked={remember} onChange={(e) => setRemember(e.target.checked)} />
                                Remember me
                            </label>
                            <a href="#" className="forgot-password" onClick={(e) => e.preventDefault()}>Forgot Password?</a>
                        </div>

                        <button type="submit" className="btn-login" disabled={loading}>
                            {loading ? 'Validating...' : 'LOGIN'}
                        </button>
                    </form>

                    <div className="passenger-footer">
                        <Link to="/pizarra" className="link-pizarra">
                            🚌 VER SALIDAS Y RESERVAR
                        </Link>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Login;
