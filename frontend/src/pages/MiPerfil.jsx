import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import {
    IconUser, IconMail, IconPhone, IconMapPin, IconCalendar,
    IconCash, IconAlertTriangle, IconBus, IconClock, IconFingerprint, IconQrCode
} from '../components/Icons';
import { QRCodeCanvas } from 'qrcode.react';
import './MiPerfil.css';

const MiPerfil = () => {
    const [perfil, setPerfil] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [qrData, setQrData] = useState(null);
    const [showQrModal, setShowQrModal] = useState(false);
    const [loadingQR, setLoadingQR] = useState(false);
    const [downloadingID, setDownloadingID] = useState(null);
    const [activeTab, setActiveTab] = useState('resumen'); // 'resumen' o 'puntero'
    const [puntero, setPuntero] = useState([]);
    const [loadingPuntero, setLoadingPuntero] = useState(false);

    const fetchPuntero = async () => {
        setLoadingPuntero(true);
        try {
            const res = await api.getPunteroHoy();
            setPuntero(res.data);
        } catch (err) {
            console.error("Error fetching puntero:", err);
        } finally {
            setLoadingPuntero(false);
        }
    };

    useEffect(() => {
        if (activeTab === 'puntero') {
            fetchPuntero();
        }
    }, [activeTab]);

    useEffect(() => {
        const fetchPerfil = async () => {
            try {
                const res = await api.getMiPerfil();
                setPerfil(res.data);
            } catch (err) {
                console.error("Error fetching profile:", err);
                setError(err.response?.data?.detail || "No se pudo cargar el perfil.");
            } finally {
                setLoading(false);
            }
        };
        fetchPerfil();
    }, []);

    const handleGenerarQR = async () => {
        if (!perfil || perfil.total_deuda <= 0) return;
        setLoadingQR(true);
        try {
            const res = await api.generarPagoQrTotalAfiliado(perfil.id);
            setQrData(res.data);
            setShowQrModal(true);
        } catch (err) {
            console.error("Error al generar QR:", err);
            alert("No se pudo generar el código QR. Intente más tarde.");
        } finally {
            setLoadingQR(false);
        }
    };

    const handleDescargarPDF = async (id) => {
        setDownloadingID(id);
        try {
            const res = await api.generarPdfHoja(id);
            if (res.data?.archivo_url) {
                window.open(res.data.archivo_url, '_blank');
            }
        } catch (err) {
            console.error("Error download PDF:", err);
            alert("No se pudo descargar el PDF.");
        } finally {
            setDownloadingID(null);
        }
    };

    if (loading) return (
        <div className="perfil-loading">
            <div className="spinner"></div>
            <p>Cargando información personal...</p>
        </div>
    );

    if (error) return (
        <div className="perfil-error">
            <IconAlertTriangle />
            <p>{error}</p>
        </div>
    );

    if (perfil?.is_admin) return (
        <div className="perfil-admin-info fade-in">
            <div className="admin-message-card glass">
                <IconUser className="admin-icon" />
                <h2>Panel de Administrador</h2>
                <p>{perfil.detail}</p>
                <div className="admin-actions">
                    <p>Para ver este módulo como un afiliado real, puedes:</p>
                    <ul>
                        <li>Vincular tu cuenta de admin a un Afiliado en el módulo "Usuarios".</li>
                        <li>Crear una cuenta nueva desde el formulario de Registro.</li>
                    </ul>
                </div>
            </div>
        </div>
    );

    if (!perfil) return null;

    return (
        <div className="mi-perfil-container fade-in">
            <header className="perfil-header">
                <div className="perfil-info-main">
                    <div className="avatar-placeholder">
                        <IconUser className="w-16 h-16" />
                    </div>
                    <div>
                        <h1>{perfil.nombres} {perfil.apellidos}</h1>
                        <span className={`badge-perfil ${perfil.estado}`}>
                            {perfil.estado.toUpperCase()}
                        </span>
                        <p className="perfil-sub">Afiliado desde: {perfil.fecha_ingreso ? new Date(perfil.fecha_ingreso).toLocaleDateString() : 'N/A'}</p>
                    </div>
                </div>
            </header>

            <div className="perfil-tabs">
                <button
                    className={`tab-btn ${activeTab === 'resumen' ? 'active' : ''}`}
                    onClick={() => setActiveTab('resumen')}
                >
                    <IconUser /> Mi Resumen
                </button>
                <button
                    className={`tab-btn ${activeTab === 'puntero' ? 'active' : ''}`}
                    onClick={() => setActiveTab('puntero')}
                >
                    <IconBus /> Salidas del Día
                </button>
            </div>

            {activeTab === 'resumen' ? (
                <div className="perfil-grid">
                    {/* DASHBOARD DEL CHOFER (HOJA DEL DIA) */}
                    {perfil.hoja_hoy ? (
                        <div className="perfil-card glass hoja-hoy-card full-width">
                            <div className="card-header highlight">
                                <IconBus />
                                <h2>MI SALIDA DE HOY</h2>
                                <span className="hoja-nro">Nº {perfil.hoja_hoy.nro}</span>
                            </div>
                            <div className="hoja-hoy-body">
                                <div className="hoja-details">
                                    <div className="h-route">{perfil.hoja_hoy.ruta}</div>
                                    <div className="h-meta">
                                        <span><IconClock /> {new Date().toLocaleDateString()}</span>
                                        <span className={`status-pill ${perfil.hoja_hoy.estado}`}>{perfil.hoja_hoy.estado}</span>
                                    </div>
                                    <div className="verification-label">QR DE VERIFICACIÓN:</div>
                                    <p className="verification-text">Presente este código al pasajero o agente de parada para verificar su salida legal.</p>
                                </div>
                                <div className="hoja-qr">
                                    <div className="qr-wrapper-main">
                                        <QRCodeCanvas 
                                            value={`${window.location.origin}${perfil.hoja_hoy.qr_url}`} 
                                            size={160}
                                            level="M"
                                            includeMargin={true}
                                        />
                                        <div className="qr-scan-line"></div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    ) : (
                        <div className="perfil-card glass info-card full-width">
                            <p className="no-hoja-msg">
                                <IconBus style={{ opacity: 0.5, fontSize: '2rem' }} />
                                No tienes una Hoja de Ruta emitida para hoy todavía. 
                                <span>Pasa por la secretaría para tu despacho.</span>
                            </p>
                        </div>
                    )}

                    {/* Panel de Datos Personales */}
                    <section className="perfil-card glass">
                        <div className="card-header">
                            <IconFingerprint />
                            <h2>Datos Personales</h2>
                        </div>
                        <div className="card-body">
                            <div className="info-item">
                                <label><IconUser /> CI</label>
                                <span>{perfil.ci}</span>
                            </div>
                            <div className="info-item">
                                <label><IconMail /> Email</label>
                                <span>{perfil.email || 'No registrado'}</span>
                            </div>
                            <div className="info-item">
                                <label><IconPhone /> Teléfono</label>
                                <span>{perfil.telefono || 'No registrado'}</span>
                            </div>
                            <div className="info-item">
                                <label><IconMapPin /> Dirección</label>
                                <span>{perfil.direccion || 'No registrada'}</span>
                            </div>
                        </div>
                    </section>

                    {/* Panel de Resumen de Deuda */}
                    <section className="perfil-card glass highlight-card">
                        <div className="card-header">
                            <IconCash />
                            <h2>Estado de Cuentas</h2>
                        </div>
                        <div className="card-body">
                            <div className="stats-row">
                                <div className="stat-box">
                                    <span className="stat-label">Total Deuda</span>
                                    <span className="stat-value text-red">Bs. {perfil.total_deuda}</span>
                                </div>
                                <div className="stat-box">
                                    <span className="stat-label">Faltas/Multas</span>
                                    <span className="stat-value">{perfil.total_faltas}</span>
                                </div>
                            </div>

                            <div className="deuda-breakdown-compact">
                                <div className="b-item"><span>Mensualidad:</span> <span>Bs. {perfil.total_deuda_cuotas}</span></div>
                                <div className="b-item"><span>Sanciones:</span> <span>Bs. {perfil.total_deuda_sanciones}</span></div>
                            </div>

                            {perfil.total_deuda > 0 ? (
                                <div className="qr-pay-action">
                                    <button
                                        className="btn-qr-pay"
                                        onClick={handleGenerarQR}
                                        disabled={loadingQR}
                                    >
                                        {loadingQR ? (
                                            <div className="spinner-mini"></div>
                                        ) : (
                                            <IconQrCode />
                                        )}
                                        {loadingQR ? 'Generando...' : 'Pagar Total con QR'}
                                    </button>
                                </div>
                            ) : (
                                <div className="clean-status">
                                    <div className="success-circle">✓</div>
                                    <p>¡Tu cuenta está al día!</p>
                                </div>
                            )}
                        </div>
                    </section>

                    {/* Hojas de Ruta y Faltas (Tabs) */}
                    <section className="perfil-card glass full-width">
                        <div className="tabs-header-perfil">
                            <button className="tab-btn active">Actividad Reciente</button>
                        </div>

                        <div className="detalles-extended-grid">
                            <div className="detalle-seccion-new">
                                <div className="section-title">
                                    <IconBus />
                                    <h4>Hojas de Ruta</h4>
                                </div>
                                <div className="table-mini-wrapper">
                                    <table>
                                        <thead>
                                            <tr>
                                                <th>Nro</th>
                                                <th>Fecha</th>
                                                <th>Ruta</th>
                                                <th>Monto</th>
                                                <th>Estado</th>
                                                <th>PDF</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {perfil.hojas_recientes.map(h => (
                                                <tr key={h.id}>
                                                    <td data-label="Nro">{h.nro}</td>
                                                    <td data-label="Fecha">{h.fecha_salida ? new Date(h.fecha_salida).toLocaleDateString() : 'N/A'}</td>
                                                    <td data-label="Ruta">{h.ruta}</td>
                                                    <td data-label="Monto">Bs. {h.precio}</td>
                                                    <td data-label="Estado">
                                                        <span className={`status-pill ${h.estado}`}>
                                                            {h.estado === 'pagada' ? '✓ Pagado' : h.estado}
                                                        </span>
                                                    </td>
                                                    <td data-label="PDF">
                                                        <button
                                                            className="btn-icon-profile"
                                                            onClick={() => handleDescargarPDF(h.id)}
                                                            disabled={downloadingID === h.id}
                                                        >
                                                            {downloadingID === h.id ? '...' : <IconFingerprint style={{ width: '20px' }} />}
                                                        </button>
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </div>

                            <div className="detalle-seccion-new">
                                <div className="section-title">
                                    <IconAlertTriangle />
                                    <h4>Faltas y Sanciones</h4>
                                </div>
                                <ul className="lista-status">
                                    {perfil.sanciones_pendientes.map(s => (
                                        <li key={s.id} className="status-item">
                                            <div className="status-info">
                                                <span className="status-name">{s.tipo}</span>
                                                <span className="status-date">{s.fecha ? new Date(s.fecha).toLocaleDateString() : 'N/A'}</span>
                                            </div>
                                            <div className="status-amount-box pending">
                                                Bs. {s.monto}
                                            </div>
                                        </li>
                                    ))}
                                    {perfil.sanciones_pendientes.length === 0 && <p className="empty-msg">No tienes sanciones pendientes.</p>}
                                </ul>
                            </div>
                        </div>
                    </section>

                    {/* Historial de Pagos Realizados */}
                    <section className="perfil-card glass full-width">
                        <div className="card-header">
                            <IconCash />
                            <h2>Historial de Mis Pagos</h2>
                        </div>
                        <div className="table-wrapper">
                            {perfil.pagos_recientes && perfil.pagos_recientes.length > 0 ? (
                                <table>
                                    <thead>
                                        <tr>
                                            <th>Fecha</th>
                                            <th>Tipo de Pago</th>
                                            <th>Monto</th>
                                            <th>Observación</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {perfil.pagos_recientes.map(p => (
                                            <tr key={p.id}>
                                                <td>{p.fecha ? new Date(p.fecha).toLocaleDateString() : 'N/A'}</td>
                                                <td><strong>{p.tipo}</strong></td>
                                                <td className="text-green-bold">Bs. {p.monto}</td>
                                                <td className="text-muted">{p.observaciones || '-'}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            ) : (
                                <p className="no-data-perfil">No se encontraron pagos realizados recientemente.</p>
                            )}
                        </div>
                    </section>
                </div>
            ) : (
                <div className="puntero-section fade-in">
                    <div className="perfil-card glass full-width">
                        <div className="card-header">
                            <IconClock />
                            <h2>Puntero del Día - Lista de Salidas</h2>
                            <button className="btn-refresh" onClick={fetchPuntero} disabled={loadingPuntero}>
                                {loadingPuntero ? '...' : 'Actualizar'}
                            </button>
                        </div>
                        <div className="table-mini-wrapper">
                            <table>
                                <thead>
                                    <tr>
                                        <th>Nro</th>
                                        <th>Afiliado</th>
                                        <th>Ruta</th>
                                        <th>Placa</th>
                                        <th>Hora Compra</th>
                                        <th>Estado</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {puntero.length > 0 ? puntero.map((p, idx) => (
                                        <tr key={idx}>
                                            <td data-label="Nro">{p.nro}</td>
                                            <td data-label="Afiliado">{p.afiliado}</td>
                                            <td data-label="Ruta">{p.ruta}</td>
                                            <td data-label="Placa">{p.vehiculo}</td>
                                            <td data-label="Hora">{p.hora}</td>
                                            <td data-label="Estado">
                                                <span className={`status-pill ${p.estado}`}>
                                                    {p.estado}
                                                </span>
                                            </td>
                                        </tr>
                                    )) : (
                                        <tr>
                                            <td colSpan="6" style={{ textAlign: 'center', padding: '2rem' }}>
                                                No hay hojas de ruta emitidas hoy todavía.
                                            </td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            )}

            {/* Modal de QR */}
            {showQrModal && qrData && (
                <div className="modal-overlay" onClick={() => setShowQrModal(false)}>
                    <div className="modal-content qr-modal glass" onClick={e => e.stopPropagation()}>
                        <button className="modal-close" onClick={() => setShowQrModal(false)}>&times;</button>
                        <div className="qr-modal-header">
                            <IconQrCode />
                            <h3>Pago de Deuda Total</h3>
                        </div>
                        <div className="qr-container-view">
                            <img src={`data:image/png;base64,${qrData.imagen_base64}`} alt="QR de Pago" />
                            <div className="qr-details">
                                <p className="qr-amount">Bs. {qrData.monto}</p>
                                <p className="qr-glosa">{qrData.glosa}</p>
                            </div>
                        </div>
                        <div className="qr-instructions">
                            <p>1. Escanea el código con tu app bancaria.</p>
                            <p>2. Confirma el pago por el monto indicado.</p>
                            <p>3. El sistema procesará tu pago automáticamente al confirmarse.</p>
                        </div>
                        <button className="btn-close-modal" onClick={() => setShowQrModal(false)}>Cerrar</button>
                    </div>
                </div>
            )}
        </div>
    );
};

export default MiPerfil;
