import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import YapeQRModal from '../components/YapeQRModal';
import '../css/PizarraPublica.css';

function PizarraPublica() {
    const navigate = useNavigate();
    const [hojas, setHojas] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [destino, setDestino] = useState('La Paz');

    // Estados para Reserva
    const [hojaSeleccionada, setHojaSeleccionada] = useState(null);
    const [selectedSeats, setSelectedSeats] = useState([]);
    const [form, setForm] = useState({ cliente: '', telefono: '' });
    const [metodoPago, setMetodoPago] = useState('efectivo');
    const [qrData, setQrData] = useState(null);
    const [submitting, setSubmitting] = useState(false);

    useEffect(() => {
        loadHojas();
    }, [destino]);

    const loadHojas = async () => {
        try {
            setLoading(true);
            const res = await api.getHojasRutaDisponibles({ destino });
            setHojas(res.data || []);
        } catch (err) {
            setError('Error al cargar la pizarra de rutas.');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const handleReservaClick = (hoja) => {
        setHojaSeleccionada(hoja);
        setSelectedSeats([]);
        setQrData(null);
    };

    const toggleSeat = (num) => {
        if (hojaSeleccionada?.asientos_ocupados?.includes(num)) return;
        setSelectedSeats(prev =>
            prev.includes(num) ? prev.filter(s => s !== num) : [...prev, num].sort((a, b) => a - b)
        );
    };

    const renderSingleSeat = (num) => {
        const isOcc = hojaSeleccionada?.asientos_ocupados?.includes(num);
        const isSel = selectedSeats.includes(num);
        return (
            <div
                key={num}
                className={`public-seat ${isOcc ? 'occ' : isSel ? 'sel' : ''}`}
                onClick={() => toggleSeat(num)}
            >
                {num}
            </div>
        );
    };

    const confirmReserva = async () => {
        if (!form.cliente || !form.telefono || selectedSeats.length === 0) {
            alert('Por favor complete todos los campos y seleccione al menos un asiento.');
            return;
        }

        try {
            setSubmitting(true);
            const promises = selectedSeats.map(asiento => {
                return api.createReserva({
                    cliente: form.cliente,
                    telefono: form.telefono,
                    ruta: hojaSeleccionada.ruta.id,
                    afiliado: hojaSeleccionada.afiliado?.id,
                    fecha_viaje: hojaSeleccionada.fecha_salida,
                    cantidad: 1,
                    asiento: asiento,
                    estado: 'pendiente'
                });
            });

            const results = await Promise.all(promises);

            if (metodoPago === 'qr') {
                const qrRes = await api.generarPagoQrReserva(results[0].data.id);
                setQrData({ ...qrRes.data, reservaId: results[0].data.id });
            } else {
                alert('✅ Reserva realizada con éxito. Por favor pase por oficina para pagar.');
                cerrarReserva();
                loadHojas();
            }
        } catch (err) {
            alert(err.response?.data?.detail || 'Error al crear la reserva');
        } finally {
            setSubmitting(false);
        }
    };

    const cerrarReserva = () => {
        setHojaSeleccionada(null);
        setSelectedSeats([]);
        setQrData(null);
        setForm({ cliente: '', telefono: '' });
    };

    return (
        <div className="pizarra-publica">
            <header className="pizarra-header">
                <div className="logo-container">
                    <div className="pizarra-titles">
                        <h1>SINDICATO MIXTO "INTEGRACIÓN TAIPIPLAYA"</h1>
                        <h2>TABLERO DE SALIDAS Y RESERVAS ONLINE</h2>
                    </div>
                </div>
                <div className="header-actions">
                    <button className="btn-volver-public" onClick={() => navigate('/dashboard')}>
                        ⬅️ Volver al Sistema
                    </button>
                    <button className="btn-login-public" onClick={() => navigate('/login')}>
                        Acceso Personal
                    </button>
                </div>
            </header>

            <main className="pizarra-content">
                <div className="pizarra-controls">
                    <div className="destino-selector">
                        <span className="selector-label">VER DESTINO:</span>
                        <div className="tabs">
                            {['La Paz', 'Taipiplaya', 'Caranavi'].map(d => (
                                <button
                                    key={d}
                                    className={`tab-btn ${destino === d ? 'active' : ''}`}
                                    onClick={() => setDestino(d)}
                                >
                                    {d.toUpperCase()}
                                </button>
                            ))}
                        </div>
                    </div>
                    <div className="pizarra-clock">
                        <Clock />
                    </div>
                </div>

                {loading ? (
                    <div className="pizarra-status">Cargando salidas en tiempo real...</div>
                ) : hojas.length === 0 ? (
                    <div className="pizarra-no-data">
                        No hay salidas programadas para {destino} en este momento.
                    </div>
                ) : (
                    <div className="pizarra-grid">
                        {hojas.map(hoja => (
                            <div key={hoja.id} className="pizarra-card">
                                <div className="card-top">
                                    <div className="route-info">
                                        <span className="route-path">{hoja.ruta.origen} ➔ {hoja.ruta.destino}</span>
                                        <span className="route-time">Salida: {new Date(hoja.fecha_salida).toLocaleDateString()}</span>
                                    </div>
                                    <div className="price-tag">
                                        Bs. {parseFloat(hoja.precio).toFixed(0)}
                                    </div>
                                </div>
                                <div className="card-mid">
                                    <div className="driver-info">
                                        <span className="label">CONDUCTOR</span>
                                        <span className="value">{hoja.afiliado?.nombre_completo || 'POR ASIGNAR'}</span>
                                    </div>
                                    <div className="vehicle-info">
                                        <span className="label">VEHÍCULO</span>
                                        <span className="value">{hoja.vehiculo?.placa} ({hoja.vehiculo?.tipo?.toUpperCase()})</span>
                                    </div>
                                </div>
                                <div className="card-bottom">
                                    <div className="cupos-indicator">
                                        <div className="cupos-dots">
                                            {Array.from({ length: hoja.capacidad_total }).map((_, i) => (
                                                <div key={i} className={`dot ${hoja.asientos_ocupados.includes(i + 1) ? 'occupied' : 'free'}`}></div>
                                            ))}
                                        </div>
                                        <span className="cupos-text">{hoja.cupos_disponibles} Libres</span>
                                    </div>
                                    <button
                                        className="btn-reserva-public"
                                        disabled={hoja.cupos_disponibles === 0}
                                        onClick={() => handleReservaClick(hoja)}
                                    >
                                        {hoja.cupos_disponibles === 0 ? 'LLENO' : 'RESERVAR'}
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </main>

            {/* Modal de Reserva Simplificado para el Público */}
            {hojaSeleccionada && (
                <div className="public-modal-overlay">
                    <div className="public-modal">
                        <div className="modal-header">
                            <h3>Nueva Reserva: {hojaSeleccionada.ruta.nombre}</h3>
                            <button className="close-x" onClick={cerrarReserva}>&times;</button>
                        </div>

                        {!qrData ? (
                            <div className="modal-body-public">
                                <div className="seat-selection-zone">
                                    <p className="hint">Seleccione sus asientos (Haga clic en los números):</p>

                                    {hojaSeleccionada.vehiculo?.tipo?.toLowerCase() === 'ipsum' ? (
                                        <div className="ipsum-layout">
                                            {/* Fila 1: Chofer + 1 */}
                                            <div className="seat-row">
                                                <div className="seat-driver">D</div>
                                                <div className="seat-space"></div>
                                                {renderSingleSeat(1)}
                                            </div>
                                            {/* Fila 2: 3 Pasajeros */}
                                            <div className="seat-row">
                                                {renderSingleSeat(2)}
                                                {renderSingleSeat(3)}
                                                {renderSingleSeat(4)}
                                            </div>
                                            {/* Fila 3: 2 Pasajeros */}
                                            <div className="seat-row" style={{ justifyContent: 'center', gap: '20px' }}>
                                                {renderSingleSeat(5)}
                                                {renderSingleSeat(6)}
                                            </div>
                                        </div>
                                    ) : (
                                        <div className="minibus-layout">
                                            <div className="seat-row">
                                                <div className="seat-driver">D</div>
                                                {renderSingleSeat(1)}
                                                {renderSingleSeat(2)}
                                            </div>
                                            <div className="seat-row">
                                                {renderSingleSeat(3)}
                                                {renderSingleSeat(4)}
                                                {renderSingleSeat(5)}
                                            </div>
                                            <div className="seat-row">
                                                {renderSingleSeat(6)}
                                                {renderSingleSeat(7)}
                                                {renderSingleSeat(8)}
                                            </div>
                                            <div className="seat-row">
                                                {renderSingleSeat(9)}
                                                {renderSingleSeat(10)}
                                                {renderSingleSeat(11)}
                                            </div>
                                            <div className="seat-row">
                                                {renderSingleSeat(12)}
                                                {renderSingleSeat(13)}
                                                {renderSingleSeat(14)}
                                            </div>
                                        </div>
                                    )}

                                    <div className="seat-legend-public">
                                        <div className="leg-item"><span className="box free"></span> Libre</div>
                                        <div className="leg-item"><span className="box sel"></span> Seleccionado</div>
                                        <div className="leg-item"><span className="box occ"></span> Ocupado</div>
                                    </div>
                                </div>

                                <div className="form-zone-public">
                                    <div className="input-group">
                                        <label>Nombre del Pasajero:</label>
                                        <input
                                            type="text"
                                            value={form.cliente}
                                            onChange={e => setForm({ ...form, cliente: e.target.value })}
                                            placeholder="Nombre completo"
                                        />
                                    </div>
                                    <div className="input-group">
                                        <label>Celular (WhatsApp):</label>
                                        <input
                                            type="tel"
                                            value={form.telefono}
                                            onChange={e => setForm({ ...form, telefono: e.target.value })}
                                            placeholder="Nro de celular"
                                        />
                                    </div>
                                    <div className="payment-select">
                                        <label>Método de Pago:</label>
                                        <div className="pay-options">
                                            <button
                                                className={`pay-opt ${metodoPago === 'efectivo' ? 'active' : ''}`}
                                                onClick={() => setMetodoPago('efectivo')}
                                            >
                                                💵 Efectivo
                                            </button>
                                            <button
                                                className={`pay-opt ${metodoPago === 'qr' ? 'active' : ''}`}
                                                onClick={() => setMetodoPago('qr')}
                                            >
                                                📱 Yape (QR)
                                            </button>
                                        </div>
                                    </div>

                                    <div className="resumen-total">
                                        <span>Total ( {selectedSeats.length} Pasajes ):</span>
                                        <strong>Bs. {(selectedSeats.length * parseFloat(hojaSeleccionada.precio)).toFixed(2)}</strong>
                                    </div>

                                    <button
                                        className="btn-confirm-public"
                                        disabled={submitting}
                                        onClick={confirmReserva}
                                    >
                                        {submitting ? 'PROCESANDO...' : 'CONFIRMAR RESERVA'}
                                    </button>
                                </div>
                            </div>
                        ) : (
                            <div className="qr-zone-public">
                                <h4>Reserva Creada - Pago Pendiente</h4>
                                <p>Escanee con Yape para confirmar su reserva:</p>
                                <div className="qr-container-public">
                                    <img src={`data:image/png;base64,${qrData.imagen_base64}`} alt="QR Yape" />
                                </div>
                                <div className="qr-details">
                                    <p><strong>Monto:</strong> Bs. {qrData.monto}</p>
                                    <p><strong>Glosa:</strong> {qrData.glosa}</p>
                                </div>
                                <div className="voucher-link-zone" style={{ margin: '1rem 0', padding: '1rem', background: '#f0fdf4', borderRadius: '8px', border: '1px solid #bbf7d0' }}>
                                    <p style={{ margin: 0, fontSize: '0.85rem' }}>🎫 <strong>Boleto Digital generado:</strong></p>
                                    <button
                                        onClick={() => window.open(`/voucher/${qrData.reservaId}`, '_blank')}
                                        style={{ background: '#10b981', color: 'white', border: 'none', padding: '0.5rem 1rem', borderRadius: '6px', fontWeight: 'bold', marginTop: '0.5rem', cursor: 'pointer' }}
                                    >
                                        VER MI BOLETO
                                    </button>
                                </div>
                                <button className="btn-finish-public" onClick={() => { cerrarReserva(); loadHojas(); }}>
                                    Entendido, ya pagué
                                </button>
                            </div>
                        )}
                    </div>
                </div>
            )}

            <footer className="pizarra-footer">
                <p>&copy; 2024 Sindicato Integración Taipiplaya - Sistema de Gestión de Transportes</p>
            </footer>

            {/* Menú Volver Flotante */}
            <div className="floating-volver-menu">
                <button className="btn-floating-volver" onClick={() => navigate('/dashboard')}>
                    ⬅️ Volver al Sistema
                </button>
            </div>
        </div>
    );
}

function Clock() {
    const [time, setTime] = useState(new Date());
    useEffect(() => {
        const timer = setInterval(() => setTime(new Date()), 1000);
        return () => clearInterval(timer);
    }, []);
    return <div className="clock-display">{time.toLocaleTimeString()}</div>;
}

export default PizarraPublica;
