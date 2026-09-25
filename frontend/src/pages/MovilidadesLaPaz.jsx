import { useState, useEffect } from 'react';
import api from '../services/api';
import './MovilidadesLaPaz.css';

// Reloj en tiempo real
function Reloj() {
    const [hora, setHora] = useState(new Date());
    useEffect(() => {
        const t = setInterval(() => setHora(new Date()), 1000);
        return () => clearInterval(t);
    }, []);
    return (
        <div className="mlp-clock">
            <span className="mlp-clock-time">
                {hora.toLocaleTimeString('es-BO', { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
            </span>
            <span className="mlp-clock-date">
                {hora.toLocaleDateString('es-BO', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
            </span>
        </div>
    );
}

const TIPO_LABELS = {
    ipsum: { label: 'IPSUM', emoji: '🚐', color: '#6366f1', bg: 'rgba(99,102,241,0.15)', border: '#6366f1' },
    minibus: { label: 'MINIBÚS', emoji: '🚌', color: '#f59e0b', bg: 'rgba(245,158,11,0.15)', border: '#f59e0b' },
};

const COLOR_MOVILIDAD = {
    blanco: '#f1f5f9',
    negro: '#0b0f19',
    gris: '#9ca3af',
    plata: '#cbd5e1',
    rojo: '#ef4444',
    azul: '#3b82f6',
    verde: '#22c55e',
    amarillo: '#facc15',
    dorado: '#f59e0b',
    naranja: '#fb923c',
    anaranjado: '#fb923c',
    cafe: '#92400e',
    marron: '#78350f',
    celeste: '#38bdf8',
    turquesa: '#2dd4bf',
    morado: '#a855f7',
    lila: '#c4b5fd',
    vino: '#7f1d1d',
    rosa: '#f472b6',
    beige: '#e7d8c9',
    crema: '#f5f5dc',
};

const colorHex = (color) => COLOR_MOVILIDAD[(color || '').trim().toLowerCase()] || '#94a3b8';

export default function MovilidadesLaPaz() {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    const cargar = async () => {
        try {
            setLoading(true);
            setError('');
            const res = await api.getMovilidadesLaPazHoy();
            setData(res.data);
        } catch (err) {
            setError('No se pudo conectar al servidor. Intente de nuevo.');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        cargar();
        // Refrescar cada 5 minutos automáticamente
        const interval = setInterval(cargar, 5 * 60 * 1000);
        return () => clearInterval(interval);
    }, []);

    const telefonoHref = (tel) => {
        const num = (tel || '').replace(/\D/g, '');
        return num ? `tel:${num}` : '#';
    };
    const whatsappHref = (tel) => {
        const num = (tel || '').replace(/\D/g, '');
        return num ? `https://wa.me/591${num}?text=Hola%2C%20quiero%20reservar%20un%20pasaje%20a%20La%20Paz.` : '#';
    };

    return (
        <div className="mlp-root">
            {/* Header */}
            <header className="mlp-header">
                <div className="mlp-header-inner">
                    <div className="mlp-logo">
                        <span className="mlp-logo-icon">🚍</span>
                        <div>
                            <h1 className="mlp-title">Sindicato Mixto "Integración Taipiplaya"</h1>
                            <p className="mlp-subtitle">Movilidades de Turno — La Paz</p>
                        </div>
                    </div>
                    <Reloj />
                </div>
            </header>

            {/* Hero Banner */}
            <div className="mlp-hero">
                <div className="mlp-hero-icon">🏙️</div>
                <div className="mlp-hero-text">
                    <h2>Reserva tu pasaje a <span className="mlp-hero-highlight">La Paz</span></h2>
                    <p>Contáctate directamente con el conductor de turno</p>
                </div>
                <a href="/pizarra" className="mlp-btn-reservar">🎫 Reservar mi pasaje</a>
            </div>

            {/* Contenido */}
            <main className="mlp-main">
                {loading && (
                    <div className="mlp-loading">
                        <div className="mlp-spinner"></div>
                        <p>Cargando movilidades de turno…</p>
                    </div>
                )}

                {error && !loading && (
                    <div className="mlp-error">
                        <span>⚠️</span>
                        <p>{error}</p>
                        <button className="mlp-btn-retry" onClick={cargar}>🔄 Reintentar</button>
                    </div>
                )}

                {!loading && !error && data && !data.found && (
                    <div className="mlp-no-turno">
                        <div className="mlp-no-turno-icon">😔</div>
                        <h3>No hay turno programado para hoy</h3>
                        <p>Comuníquese con la oficina del sindicato para más información.</p>
                        <a
                            href="https://wa.me/59178000000"
                            className="mlp-btn-oficina"
                            target="_blank"
                            rel="noopener noreferrer"
                        >
                            💬 Contactar Oficina
                        </a>
                    </div>
                )}

                {!loading && !error && data && data.found && (
                    <>
                        <div className="mlp-fecha-badge">
                            📅 Turnos del día:{' '}
                            {new Date(data.fecha + 'T12:00:00').toLocaleDateString('es-BO', {
                                weekday: 'long', day: 'numeric', month: 'long', year: 'numeric'
                            })}
                        </div>

                        {data.movilidades && data.movilidades.filter(m => m.habilitada).length === 0 && (
                            <div className="mlp-no-turno">
                                <div className="mlp-no-turno-icon">😔</div>
                                <h3>Todas las movilidades de hoy están llenas</h3>
                                <p>Las movilidades asignadas para hoy ya completaron sus asientos. Comuníquese con la oficina del sindicato para más información.</p>
                                <a
                                    href="https://wa.me/59178000000"
                                    className="mlp-btn-oficina"
                                    target="_blank"
                                    rel="noopener noreferrer"
                                >
                                    💬 Contactar Oficina
                                </a>
                            </div>
                        )}

                        <div className="mlp-cards-grid">
                            {data.movilidades.map((mov, i) => {
                                const info = TIPO_LABELS[mov.tipo] || {
                                    label: (mov.tipo || 'MOVILIDAD').toUpperCase(),
                                    emoji: '🚗',
                                    color: '#10b981',
                                    bg: 'rgba(16,185,129,0.15)',
                                    border: '#10b981',
                                };
                                return (
                                    <div
                                        key={`${mov.afiliado_id}-${mov.placa}-${i}`}
                                        className={mov.habilitada ? 'mlp-card' : 'mlp-card mlp-card-next'}
                                        style={{
                                            '--card-color': info.color,
                                            '--card-bg': info.bg,
                                            '--card-border': info.border,
                                        }}
                                    >
                                        {/* Estado: en turno o próxima */}
                                        <div className={mov.habilitada ? 'mlp-card-turno' : 'mlp-card-turno next'}>
                                            {mov.habilitada ? (
                                                <>
                                                    <span className="mlp-card-turno-dot"></span>
                                                    EN TURNO — MOVILIDAD EN PARADA
                                                </>
                                            ) : (
                                                <>
                                                    <span className="mlp-card-turno-dot next"></span>
                                                    PRÓXIMA MOVILIDAD
                                                </>
                                            )}
                                        </div>

                                        {/* Tipo badge */}
                                        <div className="mlp-card-type">
                                            <span className="mlp-card-type-emoji">{info.emoji}</span>
                                            <span className="mlp-card-type-label">{info.label}</span>
                                            {mov.capacidad && (
                                                <span className="mlp-card-cap">{mov.capacidad} pax</span>
                                            )}
                                        </div>

                                        {/* Disponibilidad */}
                                        {typeof mov.cupos_disponibles === 'number' && (
                                            <div
                                                className="mlp-card-asientos"
                                                style={mov.llena ? {
                                                    color: '#f87171',
                                                    borderColor: 'rgba(248,113,113,0.4)',
                                                    background: 'rgba(248,113,113,0.08)',
                                                } : undefined}
                                            >
                                                {mov.llena
                                                    ? '🚫 Movilidad llena — sin asientos'
                                                    : `🎫 ${mov.cupos_disponibles} asientos disponibles`}
                                            </div>
                                        )}

                                        {/* Nombre conductor */}
                                        <div className="mlp-card-nombre">
                                            <span className="mlp-card-icon-label">👤 Conductor</span>
                                            <h3>{mov.nombre_completo}</h3>
                                        </div>

                                        {/* Placa */}
                                        {mov.placa && (
                                            <div className="mlp-card-placa">
                                                <span className="mlp-placa-label">PLACA</span>
                                                <span className="mlp-placa-value">{mov.placa}</span>
                                            </div>
                                        )}

                                        {/* Color de la movilidad */}
                                        <div className="mlp-card-color">
                                            <span className="mlp-color-label">COLOR</span>
                                            <span className="mlp-color-value">
                                                <span
                                                    className="mlp-color-swatch"
                                                    style={{ background: colorHex(mov.color) }}
                                                ></span>
                                                {mov.color || 'Sin color registrado'}
                                            </span>
                                        </div>

                                        {/* Hora de salida registrada en la asignación */}
                                        <div className="mlp-card-hora">
                                            <span className="mlp-hora-label">HORA DE SALIDA A LA PAZ</span>
                                            <strong>{mov.hora_salida || 'Por confirmar'}</strong>
                                        </div>

                                        {/* Teléfono + acciones */}
                                        {mov.telefono ? (
                                            <div className="mlp-card-actions">
                                                <a
                                                    href={telefonoHref(mov.telefono)}
                                                    className="mlp-btn-call"
                                                >
                                                    📱 {mov.telefono}
                                                </a>
                                                <a
                                                    href={whatsappHref(mov.telefono)}
                                                    className="mlp-btn-whatsapp"
                                                    target="_blank"
                                                    rel="noopener noreferrer"
                                                >
                                                    💬 WhatsApp
                                                </a>
                                            </div>
                                        ) : (
                                            <div className="mlp-no-phone">Sin teléfono registrado</div>
                                        )}
                                    </div>
                                );
                            })}
                        </div>

                        {/* Nota informativa */}
                        <div className="mlp-nota">
                            <span>ℹ️</span>
                            <p>
                                Se muestran todas las movilidades asignadas de turno (ipsum y minibus).
                                La movilidad <strong>EN TURNO</strong> es la primera disponible; cuando
                                se llena de pasajeros, se habilita automáticamente la siguiente en orden.
                                Llama o escribe por WhatsApp al conductor para reservar tu pasaje.
                            </p>
                        </div>
                    </>
                )}
            </main>

            {/* Footer */}
            <footer className="mlp-footer">
                <p>© {new Date().getFullYear()} Sindicato Mixto "Integración Taipiplaya" · Todos los derechos reservados</p>
                <button className="mlp-btn-refresh" onClick={cargar} title="Actualizar">🔄 Actualizar</button>
            </footer>
        </div>
    );
}
