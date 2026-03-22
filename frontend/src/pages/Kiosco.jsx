import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import './Kiosco.css';

const Kiosco = () => {
    const navigate = useNavigate();
    const [ci, setCi] = useState('');
    const [ciExp, setCiExp] = useState('LP');
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);
    const [error, setError] = useState(null);

    const handleKeyPress = (num) => {
        if (ci.length < 10) {
            setCi(prev => prev + num);
        }
    };

    const handleDelete = () => {
        setCi(prev => prev.slice(0, -1));
    };

    const handleClear = () => {
        setCi('');
        setResult(null);
        setError(null);
    };

    const handleConsultar = async () => {
        if (!ci || ci.length < 6) {
            setError('Por favor ingrese un CI válido (mínimo 6 dígitos).');
            return;
        }

        setLoading(true);
        setError(null);
        try {
            const res = await api.getKioscoConsulta(ci, ciExp);
            setResult(res.data);
        } catch (err) {
            console.error("Kiosko error:", err);
            setError(err.response?.data?.detail || 'No se encontró el afiliado.');
        } finally {
            setLoading(false);
        }
    };

    const reset = () => {
        setCi('');
        setResult(null);
        setError(null);
    };

    if (result) {
        const hasDebt = result.finanzas.total_deuda > 0;
        const isSancionado = result.estado === 'sancionado';

        return (
            <div className="kiosco-landing">
                <div className="kiosco-result">
                    <header className="result-header">
                        <button className="btn-back" onClick={reset}>
                            ← Nueva Consulta
                        </button>
                    </header>

                    <div className="profile-summary glass">
                        <div className="afiliado-main-info">
                            <span className="status-indicator">{result.ci_completo}</span>
                            <h2>{result.nombre_completo}</h2>
                            <span className={`status-pill ${result.estado} large`}>
                                {result.estado.toUpperCase()}
                            </span>

                            <div className="status-card" style={{ marginTop: '2rem' }}>
                                <div className={`status-icon-box ${isSancionado ? 'alert' : 'success'}`}>
                                    {isSancionado ? '⚠️' : '✅'}
                                </div>
                                <h3>{isSancionado ? 'BLOQUEADO' : 'HABILITADO PARA VIAJAR'}</h3>
                                <p>{isSancionado ? 'Comuníquese con la secretaría para regularizar su estado.' : 'Sus documentos están al día.'}</p>
                            </div>
                        </div>

                        <div className={`debt-card ${hasDebt ? 'has-debt' : 'clean'}`}>
                            <h3>Resumen Financiero</h3>
                            <span className="debt-amount">
                                Bs. {result.finanzas.total_deuda.toFixed(2)}
                            </span>
                            <p>{hasDebt ? 'Monto total pendiente de pago.' : '¡Usted no tiene deudas pendientes!'}</p>

                            {hasDebt && (
                                <div className="debt-breakdown" style={{ marginTop: '1.5rem', textAlign: 'left', background: 'rgba(0,0,0,0.2)', padding: '1rem', borderRadius: '1rem' }}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                                        <span>Mensualidades:</span>
                                        <strong>Bs. {result.finanzas.deuda_cuotas.toFixed(2)}</strong>
                                    </div>
                                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                        <span>Sanciones/Multas:</span>
                                        <strong>Bs. {result.finanzas.deuda_sanciones.toFixed(2)}</strong>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>

                    <div className="turns-list glass">
                        <h3 style={{ borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '1rem', marginBottom: '1rem' }}>
                            📅 Próximos Turnos (Agente de Parada)
                        </h3>
                        {result.turnos && result.turnos.length > 0 ? (
                            result.turnos.map((t, idx) => (
                                <div className="turn-item" key={idx}>
                                    <span className="turn-date">
                                        {new Date(t.fecha).toLocaleDateString('es-ES', { weekday: 'long', day: 'numeric', month: 'long' })}
                                    </span>
                                    <span>{t.observacion || 'Sin observación'}</span>
                                </div>
                            ))
                        ) : (
                            <p style={{ opacity: 0.6, textAlign: 'center', padding: '1rem' }}>No tiene turnos programados próximamente.</p>
                        )}
                        <p style={{ marginTop: '1.5rem', fontSize: '0.8rem', opacity: 0.5, textAlign: 'center' }}>
                            * El turno de PUNTERO empieza a las 04:00 AM en el punto de parada asignado.
                        </p>
                    </div>

                    <div style={{ textAlign: 'center', marginTop: '3rem' }}>
                        <button className="btn-large-primary" onClick={reset}>
                            Cerrar Sesión / Finalizar
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="kiosco-landing">
            <header className="kiosco-header">
                <h1>PIZARRA DIGITAL</h1>
                <p>Consulte su estado, deudas y próximos turnos con su CI</p>
            </header>

            <div className="kiosco-form-card">
                <div className="kiosco-input-group">
                    <div className="kiosco-input-wrapper">
                        <input
                            type="text"
                            className="kiosco-main-input"
                            value={ci}
                            placeholder="Ingrese su CI"
                            readOnly
                        />
                        <select
                            className="kiosco-select-exp"
                            value={ciExp}
                            onChange={(e) => setCiExp(e.target.value)}
                        >
                            {['LP', 'CB', 'SC', 'OR', 'PT', 'TJ', 'CH', 'BN', 'PA'].map(exp => (
                                <option key={exp} value={exp}>{exp}</option>
                            ))}
                        </select>
                    </div>

                    {error && (
                        <div className="kiosco-error-msg" style={{ background: 'rgba(239, 68, 68, 0.1)', color: '#ef4444', padding: '1rem', borderRadius: '1rem', textAlign: 'center' }}>
                            {error}
                        </div>
                    )}

                    <div className="kiosco-keypad">
                        {[1, 2, 3, 4, 5, 6, 7, 8, 9].map(num => (
                            <button key={num} className="keypad-btn" onClick={() => handleKeyPress(num)}>
                                {num}
                            </button>
                        ))}
                        <button className="keypad-btn danger" onClick={handleClear}>C</button>
                        <button className="keypad-btn" onClick={() => handleKeyPress(0)}>0</button>
                        <button className="keypad-btn danger" onClick={handleDelete}>←</button>
                    </div>

                    <button
                        className={`keypad-btn action ${loading ? 'loading' : ''}`}
                        style={{ marginTop: '1.5rem', width: '100%', fontSize: '1.5rem', padding: '1.5rem' }}
                        onClick={handleConsultar}
                        disabled={loading || ci.length < 6}
                    >
                        {loading ? 'CONSULTANDO...' : 'CONSULTAR AHORA'}
                    </button>
                </div>
            </div>

            <footer style={{ marginTop: '4rem', opacity: 0.3, textAlign: 'center' }}>
                <p>SINDICATO MIXTO INTEGRACIÓN TAIPIPLAYA - 2026</p>
                <p style={{ fontSize: '0.8rem' }}>Sistema Versión 2.1 (Pizarra v1.0)</p>
            </footer>

            {/* Menú Volver Flotante */}
            <div className="floating-volver-menu">
                <button className="btn-floating-volver" onClick={() => navigate('/dashboard')}>
                    ⬅️ Volver al Sistema
                </button>
            </div>
        </div>
    );
};

export default Kiosco;
