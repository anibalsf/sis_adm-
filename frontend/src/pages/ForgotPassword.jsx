import { useState } from 'react';
import { Link } from 'react-router-dom';
import AuthShell from '../components/AuthShell';
import { IconArrowLeft, IconCheckCircle, IconUser } from '../components/Icons';
import './Login.css';

const ForgotPassword = () => {
    const [identifier, setIdentifier] = useState('');
    const [submitted, setSubmitted] = useState(false);

    const handleSubmit = (e) => {
        e.preventDefault();
        setSubmitted(true);
    };

    return (
        <AuthShell>
            {!submitted ? (
                <>
                    <header className="auth-header">
                        <span className="auth-kicker">Soporte de acceso</span>
                        <h1>Recuperar contraseña</h1>
                        <p>
                            Ingresa tu usuario o C.I. para solicitar el restablecimiento
                            de tu acceso.
                        </p>
                    </header>

                    <form onSubmit={handleSubmit} className="auth-form">
                        <label className="auth-field" htmlFor="identifier">
                            <span className="auth-label">Usuario o C.I.</span>
                            <span className="auth-input-wrap">
                                <IconUser className="auth-input-icon" />
                                <input
                                    id="identifier"
                                    name="identifier"
                                    type="text"
                                    className="auth-input"
                                    value={identifier}
                                    onChange={(e) => setIdentifier(e.target.value)}
                                    placeholder="Ingresa tu usuario o C.I."
                                    autoComplete="username"
                                    required
                                    autoFocus
                                />
                            </span>
                        </label>

                        <button type="submit" className="auth-submit">
                            Enviar solicitud
                        </button>
                    </form>

                    <p className="auth-back-row">
                        <Link to="/login" className="auth-link auth-link--back">
                            <IconArrowLeft />
                            Volver a iniciar sesión
                        </Link>
                    </p>
                </>
            ) : (
                <div className="auth-success">
                    <span className="auth-success-icon">
                        <IconCheckCircle />
                    </span>
                    <h1>Solicitud recibida</h1>
                    <p>
                        Si tus datos coinciden con un usuario registrado, la
                        administración se pondrá en contacto contigo para restablecer
                        el acceso.
                    </p>
                    <Link to="/login" className="auth-secondary">
                        <IconArrowLeft />
                        Volver a iniciar sesión
                    </Link>
                </div>
            )}
        </AuthShell>
    );
};

export default ForgotPassword;
