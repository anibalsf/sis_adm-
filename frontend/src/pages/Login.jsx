import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Link, useNavigate } from 'react-router-dom';
import AuthShell from '../components/AuthShell';
import { IconAlertTriangle, IconBus, IconEye, IconLock, IconUser } from '../components/Icons';
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

        const result = await login(username.trim(), password, remember);

        if (result.success) {
            const role = result.user?.role;
            if (role === 'Afiliado') {
                navigate('/mi-perfil');
            } else {
                navigate('/dashboard');
            }
        } else {
            setError(result.error || 'No se pudo iniciar sesión. Intenta nuevamente.');
        }

        setLoading(false);
    };

    return (
        <AuthShell>
            <header className="auth-header">
                <span className="auth-kicker">Bienvenido</span>
                <h1>Iniciar sesión</h1>
                <p>Ingresa tus credenciales para acceder al sistema.</p>
            </header>

            <form onSubmit={handleSubmit} className="auth-form">
                {error && (
                    <div className="auth-error" role="alert">
                        <IconAlertTriangle />
                        <span>{error}</span>
                    </div>
                )}

                <label className="auth-field" htmlFor="username">
                    <span className="auth-label">Usuario</span>
                    <span className="auth-input-wrap">
                        <IconUser className="auth-input-icon" />
                        <input
                            id="username"
                            name="username"
                            type="text"
                            className="auth-input"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            placeholder="Usuario o C.I."
                            autoComplete="username"
                            required
                            autoFocus
                        />
                    </span>
                </label>

                <p className="auth-hint">
                    Afiliados: su usuario y contraseña son su C.I. sin extensión.
                </p>

                <label className="auth-field" htmlFor="password">
                    <span className="auth-label">Contraseña</span>
                    <span className="auth-input-wrap">
                        <IconLock className="auth-input-icon" />
                        <input
                            id="password"
                            name="password"
                            type={showPassword ? 'text' : 'password'}
                            className="auth-input auth-input--password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            placeholder="Ingresa tu contraseña"
                            autoComplete="current-password"
                            required
                        />
                        <button
                            type="button"
                            onClick={() => setShowPassword((value) => !value)}
                            className="auth-password-toggle"
                            aria-label={showPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'}
                            aria-pressed={showPassword}
                        >
                            <IconEye />
                            <span>{showPassword ? 'Ocultar' : 'Mostrar'}</span>
                        </button>
                    </span>
                </label>

                <div className="auth-options">
                    <label className="auth-checkbox">
                        <input
                            type="checkbox"
                            checked={remember}
                            onChange={(e) => setRemember(e.target.checked)}
                        />
                        <span>Mantener sesión iniciada</span>
                    </label>
                    <Link to="/forgot-password" className="auth-link">
                        ¿Olvidaste tu contraseña?
                    </Link>
                </div>

                <button type="submit" className="auth-submit" disabled={loading}>
                    {loading ? (
                        <>
                            <span className="auth-spinner" aria-hidden="true" />
                            Verificando...
                        </>
                    ) : (
                        'Ingresar al sistema'
                    )}
                </button>
            </form>

            <div className="auth-divider">
                <span>o</span>
            </div>

            <Link to="/pizarra" className="auth-secondary">
                <IconBus />
                Consultar salidas y reservar
            </Link>
        </AuthShell>
    );
};

export default Login;
