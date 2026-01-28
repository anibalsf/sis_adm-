import { useState } from 'react';
import { Link } from 'react-router-dom';
import './Login.css';

const ForgotPassword = () => {
    const [identifier, setIdentifier] = useState('');
    const [submitted, setSubmitted] = useState(false);

    const handleSubmit = (e) => {
        e.preventDefault();
        // Here we would call the backend password reset endpoint (e.g. /auth/reset-password)
        // Since it's not implemented yet, we show a message.
        setSubmitted(true);
    };

    return (
        <div className="login-page">
            <div className="login-container">
                <div className="login-card">
                    <div className="login-header">
                        <h1>Recuperar Contraseña</h1>
                    </div>

                    {!submitted ? (
                        <form onSubmit={handleSubmit} className="login-form">
                            <p style={{ textAlign: 'center', color: '#6b7280', marginBottom: '10px' }}>
                                Ingrese su usuario o C.I. para restablecer su contraseña.
                            </p>

                            <div className="form-group">
                                <span className="input-icon">👤</span>
                                <input
                                    id="identifier"
                                    type="text"
                                    value={identifier}
                                    onChange={(e) => setIdentifier(e.target.value)}
                                    placeholder="Usuario o C.I."
                                    required
                                    autoFocus
                                />
                            </div>

                            <button type="submit" className="btn-login">
                                ENVIAR SOLICITUD
                            </button>

                            <div className="create-account">
                                <Link to="/login">Volver al inicio</Link>
                            </div>
                        </form>
                    ) : (
                        <div className="login-form" style={{ textAlign: 'center' }}>
                            <div style={{ fontSize: '3rem', margin: '20px 0' }}>✅</div>
                            <h3 style={{ color: '#374151' }}>Solicitud Recibida</h3>
                            <p style={{ color: '#6b7280' }}>
                                Si sus datos coinciden, contacte con la administración o espere instrucciones vía WhatsApp.
                            </p>
                            <div className="create-account">
                                <Link to="/login">Volver al inicio</Link>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default ForgotPassword;
