import { Link } from 'react-router-dom';
import { IconBus, IconCheckCircle, IconShield } from './Icons';
import './AuthShell.css';

const AuthShell = ({ children }) => {
    const year = new Date().getFullYear();

    return (
        <div className="auth-page">
            <div className="auth-shell">
                <aside className="auth-brand" aria-label="Información del sistema">
                    <div className="auth-brand-content">
                        <div className="auth-brand-top">
                            <span className="auth-logo-frame">
                                <img
                                    src="/logo_smmit.png"
                                    alt="Escudo del Sindicato Mixto de Transporte Integración Taipiplaya"
                                    className="auth-logo"
                                />
                            </span>
                            <div className="auth-brand-titles">
                                <span className="auth-eyebrow">Sistema de Administración</span>
                                <p className="auth-brand-title">Sindicato Mixto de Transporte</p>
                                <p className="auth-brand-subtitle">Integración Taipiplaya</p>
                            </div>
                        </div>

                        <div className="auth-brand-copy">
                            <h2>Gestión institucional, clara y segura.</h2>
                            <p>
                                Afiliados, hojas de ruta, reservas y tesorería en una sola
                                plataforma, con información disponible en todo momento.
                            </p>
                        </div>

                        <ul className="auth-features">
                            <li>
                                <IconCheckCircle />
                                <span>Control operativo y financiero</span>
                            </li>
                            <li>
                                <IconCheckCircle />
                                <span>Reservas y pizarra de salidas en línea</span>
                            </li>
                            <li>
                                <IconCheckCircle />
                                <span>Accesos diferenciados según el rol</span>
                            </li>
                        </ul>

                        <div className="auth-brand-footer">
                            <Link to="/pizarra" className="auth-brand-link">
                                <IconBus />
                                Ver pizarra pública de salidas
                            </Link>
                            <span className="auth-brand-security">
                                <IconShield />
                                Acceso exclusivo para personal autorizado
                            </span>
                        </div>
                    </div>
                </aside>

                <main className="auth-panel">
                    <div className="auth-panel-inner">
                        <div className="auth-mobile-brand">
                            <span className="auth-logo-frame auth-logo-frame--sm">
                                <img
                                    src="/logo_smmit.png"
                                    alt="Escudo del Sindicato Mixto de Transporte Integración Taipiplaya"
                                    className="auth-logo"
                                />
                            </span>
                            <div>
                                <span className="auth-eyebrow">Sistema de Administración</span>
                                <p className="auth-brand-title">Integración Taipiplaya</p>
                            </div>
                        </div>

                        {children}

                        <p className="auth-legal">
                            © {year} Sindicato Mixto de Transporte Integración Taipiplaya
                        </p>
                    </div>
                </main>
            </div>
        </div>
    );
};

export default AuthShell;
