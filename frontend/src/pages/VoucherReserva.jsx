import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import api from '../services/api';
import './VoucherReserva.css';

function VoucherReserva() {
    const { id } = useParams();
    const [reserva, setReserva] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        const fetchReserva = async () => {
            try {
                // Usamos un endpoint público para ver el voucher
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

    return (
        <div className="voucher-page">
            <div className="voucher-container">
                <header className="voucher-header">
                    <img src="/logo_smit.jpg" alt="Logo SMIT" className="voucher-logo" />
                    <div className="header-text">
                        <h2>SINDICATO INTEGRACIÓN TAIPIPLAYA</h2>
                        <p>Boleto Digital de Pasajero</p>
                    </div>
                </header>

                <div className="voucher-body">
                    <div className="status-banner" data-status={reserva.estado}>
                        {reserva.estado.toUpperCase()}
                    </div>

                    <div className="ticket-info">
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
                                <label>Vehículo:</label>
                                <span className="value" style={{ textTransform: 'capitalize' }}>
                                    {reserva.vehiculo_tipo} {reserva.vehiculo_placa && `(${reserva.vehiculo_placa})`}
                                </span>
                            </div>
                            <div className="info-group">
                                <label>Asiento:</label>
                                <span className="value seat-num">{reserva.asiento}</span>
                            </div>
                        </div>
                        <div className="info-group">
                            <label>Fecha Viaje:</label>
                            <span className="value">{new Date(reserva.fecha_viaje).toLocaleDateString('es-ES', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}</span>
                        </div>
                    </div>

                    <div className="qr-section">
                        <p>Presente este código al abordar:</p>
                        <div className="qr-box">
                            {/* Aquí iría un código QR generado que contiene el ID de la reserva */}
                            <img
                                src={`https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=RESERVA-${reserva.id}`}
                                alt="QR de Validación"
                            />
                        </div>
                        <span className="ref-code">Ref: #{reserva.id}</span>
                    </div>
                </div>

                <footer className="voucher-footer">
                    <p>Por favor llegue 15 minutos antes de la salida.</p>
                    <p className="legal">Este documento es un comprobante de reserva digital.</p>
                </footer>
            </div>

            <button className="btn-save-image" onClick={() => window.print()}>
                📥 GUARDAR O IMPRIMIR
            </button>
        </div>
    );
}

export default VoucherReserva;
