import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import api, { API_URL } from '../services/api';
import './VoucherReserva.css';

const DOMAIN = 'https://administracion.sindicatointegracion.com';

function VoucherReserva() {
    const { id } = useParams();
    const [reserva, setReserva] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        const fetchReserva = async () => {
            try {
                const res = await api.getReservaPublica(id);
                setReserva(res.data);
            } catch (err) {
                setError('No se pudo encontrar la reserva o el enlace ha expirado.');
                console.error(err);
            } finally {
                setLoading(false);
            }
        };
        fetchReserva();
    }, [id]);

    if (loading) return <div className="voucher-loader">Generando Boleto Digital...</div>;
    if (error) return <div className="voucher-error">{error}</div>;

    const fechaFormateada = new Date(reserva.fecha_viaje).toLocaleDateString('es-ES', {
        weekday: 'long', year: 'numeric', month: 'long', day: 'numeric'
    });

    // URL del QR generado por el backend (incluye datos del afiliado)
    const qrUrl = `${API_URL}/reservas/${id}/generar_qr/`;

    return (
        <div className="voucher-page">
            <div className="voucher-container">

                {/* Header */}
                <header className="voucher-header">
                    <img src="/logo_smit.jpg" alt="Logo SMIT" className="voucher-logo" />
                    <div className="header-text">
                        <h2>SINDICATO INTEGRACIÓN TAIPIPLAYA</h2>
                        <p>Boleto Digital de Pasajero</p>
                    </div>
                </header>

                <div className="voucher-body">

                    {/* Estado */}
                    <div className="status-banner" data-status={reserva.estado}>
                        {reserva.estado === 'confirmada' ? '✅ CONFIRMADA' :
                         reserva.estado === 'pendiente' ? '⏳ PENDIENTE' :
                         reserva.estado.toUpperCase()}
                    </div>

                    {/* Número de reserva */}
                    <div className="voucher-ref-header">
                        <span className="voucher-ref-label">N° de Reserva</span>
                        <span className="voucher-ref-number">RES-{String(reserva.id).padStart(6, '0')}</span>
                    </div>

                    {/* Info del pasajero y viaje */}
                    <div className="ticket-info">
                        <div className="info-section-title">🧍 Datos del Pasajero</div>
                        <div className="info-group">
                            <label>Pasajero:</label>
                            <span className="value">{reserva.cliente}</span>
                        </div>
                        <div className="info-group">
                            <label>Destino:</label>
                            <span className="value">{reserva.ruta_nombre}</span>
                        </div>
                        <div className="info-grid">
                            <div className="info-group">
                                <label>Fecha Viaje:</label>
                                <span className="value date-value">{fechaFormateada}</span>
                            </div>
                            <div className="info-group">
                                <label>Hora Salida:</label>
                                <span className="value">{reserva.hora_salida || 'Por confirmar'}</span>
                            </div>
                            <div className="info-group">
                                <label>Asiento:</label>
                                <span className="value seat-num">{reserva.asiento || '–'}</span>
                            </div>
                        </div>
                        <div className="info-group">
                            <label>Cantidad de Pasajes:</label>
                            <span className="value">{reserva.cantidad}</span>
                        </div>
                    </div>

                    {/* Separador punteado */}
                    <div className="voucher-divider"></div>

                    {/* Info del conductor/afiliado */}
                    <div className="ticket-info conductor-info">
                        <div className="info-section-title">🚌 Datos del Conductor</div>
                        <div className="info-group">
                            <label>Conductor:</label>
                            <span className="value">{reserva.afiliado_nombre || '–'}</span>
                        </div>
                        <div className="info-grid">
                            <div className="info-group">
                                <label>Celular:</label>
                                <span className="value conductor-phone">
                                    {reserva.afiliado_telefono
                                        ? <a href={`tel:${reserva.afiliado_telefono}`}>{reserva.afiliado_telefono}</a>
                                        : '–'}
                                </span>
                            </div>
                            <div className="info-group">
                                <label>Placa:</label>
                                <span className="value placa-badge">
                                    {reserva.vehiculo_placa || '–'}
                                </span>
                            </div>
                        </div>
                        {reserva.vehiculo_tipo && (
                            <div className="info-group">
                                <label>Tipo Vehículo:</label>
                                <span className="value" style={{ textTransform: 'capitalize' }}>
                                    {reserva.vehiculo_tipo}
                                </span>
                            </div>
                        )}
                        {reserva.afiliado_direccion && (
                            <div className="info-group">
                                <label>Dirección:</label>
                                <span className="value">{reserva.afiliado_direccion}</span>
                            </div>
                        )}
                    </div>

                    {/* QR Section */}
                    <div className="voucher-divider"></div>
                    <div className="qr-section">
                        <p>Escanea para verificar esta reserva</p>
                        <div className="qr-box">
                            <img
                                src={qrUrl}
                                alt="QR de Verificación"
                                onError={(e) => {
                                    // Fallback a QR externo con URL del dominio
                                    e.target.src = `https://api.qrserver.com/v1/create-qr-code/?size=180x180&data=${encodeURIComponent(`${DOMAIN}/voucher/${reserva.id}`)}`;
                                }}
                            />
                        </div>
                        <span className="ref-code">Ref: RES-{String(reserva.id).padStart(6, '0')}</span>
                        <div className="qr-domain">{DOMAIN}</div>
                    </div>
                </div>

                {/* Footer */}
                <footer className="voucher-footer">
                    <p>⏰ Por favor llegue 15 minutos antes de la salida.</p>
                    <p className="legal">Documento generado por el Sistema de Administración del Sindicato Mixto Integración Taipiplaya.</p>
                </footer>
            </div>

            <button className="btn-save-image" onClick={() => window.print()}>
                📥 GUARDAR O IMPRIMIR
            </button>
        </div>
    );
}

export default VoucherReserva;
