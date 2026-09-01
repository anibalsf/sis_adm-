import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';
import YapeQRModal from '../components/YapeQRModal';
import '../css/Reservas.css';

function Reservas() {
    const [hojasDisponibles, setHojasDisponibles] = useState([]);
    const [hojaSeleccionada, setHojaSeleccionada] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [submitError, setSubmitError] = useState('');
    const [showForm, setShowForm] = useState(false);
    const [selectedSeats, setSelectedSeats] = useState([]);
    const [form, setForm] = useState({
        cliente: '',
        telefono: '',
        fecha_viaje: '',
        cantidad: 1
    });
    const [phoneError, setPhoneError] = useState('');
    const [showConfirmation, setShowConfirmation] = useState(false);
    const [reservationData, setReservationData] = useState(null);
    const [metodoPago, setMetodoPago] = useState('efectivo');
    const [qrData, setQrData] = useState(null);
    const [verificandoPago, setVerificandoPago] = useState(false);

    // Estados para Ver Pasajeros (Nombres únicos para evitar colisiones)
    const [verPasajerosModulo, setVerPasajerosModulo] = useState(false);
    const [datosPasajeros, setDatosPasajeros] = useState([]);
    const [cargandoPasajerosModulo, setCargandoPasajerosModulo] = useState(false);

    // Estado para el Afiliado de Turno
    const [afiliadoTurno, setAfiliadoTurno] = useState(null);
    const [cargandoTurno, setCargandoTurno] = useState(true);

    const isSeatOccupied = (seatNum) => {
        return hojaSeleccionada?.asientos_ocupados?.includes(seatNum);
    };

    const toggleSeat = (seatNum) => {
        if (isSeatOccupied(seatNum)) return;
        setSelectedSeats(prev => {
            if (prev.includes(seatNum)) {
                return prev.filter(s => s !== seatNum);
            } else {
                return [...prev, seatNum].sort((a, b) => a - b);
            }
        });
    };

    const renderSeatButton = (num) => {
        const occupied = isSeatOccupied(num);
        const selected = selectedSeats.includes(num);
        return (
            <div
                key={num}
                className={`seat-box seat-regular ${occupied ? 'occupied' : selected ? 'selected' : ''}`}
                onClick={() => toggleSeat(num)}
            >
                <span className="seat-number">{num}</span>
                <input
                    type="checkbox"
                    className="seat-checkbox"
                    checked={selected || occupied}
                    disabled={occupied}
                    readOnly
                />
            </div>
        );
    };

    const verificarPago = async () => {
        if (!qrData) return;
        try {
            setVerificandoPago(true);
            const res = await api.getReserva(qrData.id); // Consultamos la reserva para ver si cambió de estado
            if (res.data.estado === 'confirmada' || res.data.estado === 'pagada') {
                alert('✅ ¡Pago confirmado exitosamente!');
                setQrData(null);
                setHojaSeleccionada(null);
                setSelectedSeats([]);
                setShowForm(false);
                loadHojasDisponibles();
            } else {
                alert('El pago aún figura como pendiente. Por favor escanee el QR con Yape.');
            }
        } catch (err) {
            console.error(err);
            alert('Error al verificar el estado del pago.');
        } finally {
            setVerificandoPago(false);
        }
    };


    useEffect(() => {
        loadHojasDisponibles();
        loadAfiliadoTurno();
    }, []);

    const loadAfiliadoTurno = async () => {
        try {
            setCargandoTurno(true);
            const res = await api.getTurnoLaPazHoy();
            if (res.data?.found && res.data?.afiliado) {
                setAfiliadoTurno(res.data.afiliado);
            } else {
                setAfiliadoTurno(null);
            }
        } catch (err) {
            console.error('Error al obtener afiliado de turno La Paz:', err);
            setAfiliadoTurno(null);
        } finally {
            setCargandoTurno(false);
        }
    };

    const loadHojasDisponibles = async () => {
        try {
            setLoading(true);
            const response = await api.getHojasRutaDisponibles();
            setHojasDisponibles(response.data || []);
            setError('');
        } catch (err) {
            setError('Error al cargar rutas disponibles');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const seleccionarRuta = (hoja) => {
        setHojaSeleccionada(hoja);
        setShowForm(true);
        // Pre-llenar la fecha de viaje con la fecha de salida de la hoja
        setForm(prev => ({
            ...prev,
            fecha_viaje: hoja.fecha_salida || ''
        }));
    };

    const onChange = (e) => {
        const { name, value } = e.target;
        setForm(prev => ({ ...prev, [name]: value }));

        // Validar teléfono en tiempo real
        if (name === 'telefono') {
            validatePhone(value);
        }
    };

    const validatePhone = (phone) => {
        // Teléfono boliviano: 8 dígitos
        const phoneRegex = /^[67]\d{7}$/;

        if (!phone) {
            setPhoneError('');
            return true;
        }

        if (!phoneRegex.test(phone)) {
            setPhoneError('Teléfono inválido. Debe tener 8 dígitos y comenzar con 6 o 7');
            return false;
        }

        setPhoneError('');
        return true;
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        if (!hojaSeleccionada) {
            setSubmitError('Debe seleccionar una ruta');
            return;
        }

        if (selectedSeats.length === 0) {
            setSubmitError('Debe seleccionar al menos un asiento');
            return;
        }

        // Validar teléfono antes de continuar
        if (!validatePhone(form.telefono)) {
            setSubmitError('Por favor corrija el número de teléfono');
            return;
        }

        // Calcular total
        const precioUnitario = parseFloat(hojaSeleccionada.ruta?.tarifa_base || hojaSeleccionada.precio);
        const total = precioUnitario * selectedSeats.length;

        // Mostrar modal de confirmación
        setReservationData({
            cliente: form.cliente,
            telefono: form.telefono,
            fecha_viaje: form.fecha_viaje,
            asientos: selectedSeats.join(', '),
            cantidad: selectedSeats.length,
            precioUnitario: precioUnitario,
            total: total,
            ruta: hojaSeleccionada.ruta?.nombre,
            conductor: hojaSeleccionada.afiliado?.nombre_completo
        });
        setShowConfirmation(true);
    };

    const confirmReservation = async () => {
        try {
            setSubmitError('');

            // Crear una reserva por cada asiento seleccionado
            const promises = selectedSeats.map(asiento => {
                const payload = {
                    cliente: form.cliente,
                    telefono: form.telefono,
                    ruta: hojaSeleccionada.ruta.id,
                    afiliado: hojaSeleccionada.afiliado?.id,
                    fecha_viaje: form.fecha_viaje,
                    cantidad: 1, // Siempre 1 por asiento
                    asiento: asiento,
                    estado: 'pendiente'
                };
                return api.createReserva(payload);
            });

            const results = await Promise.all(promises);

            // Si es pago QR, generar el QR para la primera reserva del grupo
            if (metodoPago === 'qr') {
                try {
                    const firstReservaId = results[0].data.id;
                    const qrResponse = await api.generarPagoQrReserva(firstReservaId);
                    setQrData(qrResponse.data);
                } catch (qrErr) {
                    console.error('Error al generar QR:', qrErr);
                    alert('La reserva se creó pero hubo un error al generar el código QR.');
                }
            } else {
                alert('✅ Reserva(s) creada(s) exitosamente');
                setHojaSeleccionada(null);
                setSelectedSeats([]);
                setShowForm(false);
                loadHojasDisponibles();
            }

            setShowConfirmation(false);
            setForm({
                cliente: '',
                telefono: '',
                fecha_viaje: '',
                cantidad: 1
            });
            setPhoneError('');

        } catch (err) {
            console.error(err);
            setSubmitError(err.response?.data?.detail || 'Error al crear la reserva');
            setShowConfirmation(false);
        }
    };

    const cancelar = () => {
        setShowForm(false);
        setHojaSeleccionada(null);
        setMetodoPago('efectivo');
        setQrData(null);
        setForm({
            cliente: '',
            telefono: '',
            fecha_viaje: '',
            cantidad: 1
        });
        setSelectedSeats([]);
        setSubmitError('');
    };

    const handleImprimirPlanilla = async (hojaId) => {
        if (!hojaId) return;
        try {
            const res = await api.generarPlanillaLaPaz(hojaId);
            const blob = new Blob([res.data], { type: 'application/pdf' });
            const url = window.URL.createObjectURL(blob);
            window.open(url, '_blank');
        } catch (err) {
            console.error(err);
            alert('Error al generar la planilla');
        }
    };

    // MARKER_VITE_DEBUG
    const abrirModalPasajeros = async (e, hoja) => {
        e.stopPropagation();
        setHojaSeleccionada(hoja);
        setVerPasajerosModulo(true);
        setCargandoPasajerosModulo(true);
        try {
            const res = await api.getPasajeros(hoja.id);
            setDatosPasajeros(res.data || []);
        } catch (err) {
            console.error(err);
            alert('Error al cargar pasajeros');
        } finally {
            setCargandoPasajerosModulo(false);
        }
    };

    const cerrarModalPasajeros = () => {
        setVerPasajerosModulo(false);
        setDatosPasajeros([]);
        setHojaSeleccionada(null);
    };

    if (loading) return <div className="loading">Cargando rutas disponibles...</div>;
    if (error) return <div className="error">{error}</div>;

    return (
        <div className="reservas-container">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <div>
                    <h1>Módulo de Reservas</h1>
                    <p>Selecciona una ruta para realizar tu reserva</p>
                </div>
                <Link to="/pizarra" style={{
                    background: '#10b981',
                    color: 'white',
                    padding: '0.8rem 1.5rem',
                    borderRadius: '12px',
                    textDecoration: 'none',
                    fontWeight: 'bold',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                    boxShadow: '0 4px 10px rgba(16, 185, 129, 0.2)'
                }}>
                    🚌 IR A PIZARRA PÚBLICA
                </Link>
            </div>

                {/* Banner: Afiliado de Turno La Paz del Día */}
            <div style={{
                background: 'linear-gradient(135deg, #1a3a2a 0%, #2d6a4f 50%, #1a3a2a 100%)',
                border: '2px solid #40916c',
                borderRadius: '16px',
                padding: '1.2rem 1.5rem',
                marginBottom: '1.5rem',
                display: 'flex',
                alignItems: 'center',
                gap: '1rem',
                boxShadow: '0 4px 20px rgba(0,0,0,0.25)',
                position: 'relative',
                overflow: 'hidden'
            }}>
                {/* Decoración de fondo */}
                <div style={{
                    position: 'absolute', top: 0, right: 0, width: '120px', height: '120px',
                    background: 'rgba(64,145,108,0.15)', borderRadius: '50%',
                    transform: 'translate(30px, -30px)'
                }} />
                <div style={{
                    position: 'absolute', bottom: 0, left: '200px', width: '80px', height: '80px',
                    background: 'rgba(64,145,108,0.1)', borderRadius: '50%',
                    transform: 'translate(0, 30px)'
                }} />

                {/* Ícono bus */}
                <div style={{
                    fontSize: '2.5rem',
                    background: 'rgba(64,145,108,0.3)',
                    borderRadius: '12px',
                    padding: '0.5rem 0.8rem',
                    flexShrink: 0
                }}>🚌</div>

                {/* Contenido */}
                <div style={{ flex: 1, zIndex: 1 }}>
                    <div style={{
                        color: '#74c69d',
                        fontSize: '0.78rem',
                        fontWeight: '700',
                        textTransform: 'uppercase',
                        letterSpacing: '0.1em',
                        marginBottom: '0.3rem'
                    }}>
                        📍 SOCIO DE TURNO — La Paz — Hoy | Para reservar su pasaje contacte a:
                    </div>

                    {cargandoTurno ? (
                        <div style={{ color: '#b7e4c7', fontSize: '1rem' }}>Buscando socio de turno...</div>
                    ) : afiliadoTurno ? (
                        <div style={{ display: 'flex', alignItems: 'center', gap: '1.2rem', flexWrap: 'wrap' }}>
                            {/* Nombre */}
                            <span style={{
                                color: '#ffffff',
                                fontSize: '1.3rem',
                                fontWeight: '800',
                                textShadow: '0 1px 4px rgba(0,0,0,0.4)'
                            }}>
                                👤 {afiliadoTurno.nombre_completo}
                            </span>

                            {/* Placa */}
                            {afiliadoTurno.vehiculo_placa && (
                                <span style={{
                                    background: 'rgba(255,255,255,0.15)',
                                    color: '#d8f3dc',
                                    padding: '0.3rem 0.9rem',
                                    borderRadius: '8px',
                                    fontWeight: '700',
                                    fontSize: '1rem',
                                    letterSpacing: '0.08em',
                                    border: '1px solid rgba(255,255,255,0.2)'
                                }}>
                                    🚗 {afiliadoTurno.vehiculo_placa}
                                    {afiliadoTurno.vehiculo_tipo && (
                                        <span style={{ fontWeight: '400', marginLeft: '6px', fontSize: '0.85rem', opacity: 0.8 }}>
                                            ({afiliadoTurno.vehiculo_tipo})
                                        </span>
                                    )}
                                </span>
                            )}

                            {/* Botones de contacto */}
                            {afiliadoTurno.telefono && (
                                <a
                                    href={`tel:${afiliadoTurno.telefono}`}
                                    style={{
                                        display: 'flex', alignItems: 'center', gap: '0.5rem',
                                        background: '#40916c', color: 'white',
                                        padding: '0.5rem 1.1rem', borderRadius: '50px',
                                        textDecoration: 'none', fontWeight: '700', fontSize: '1.05rem',
                                        boxShadow: '0 2px 10px rgba(0,0,0,0.3)'
                                    }}
                                >
                                    📱 {afiliadoTurno.telefono}
                                </a>
                            )}
                            {afiliadoTurno.telefono && (
                                <a
                                    href={`https://wa.me/591${afiliadoTurno.telefono}?text=Hola%2C%20quiero%20reservar%20un%20pasaje%20a%20La%20Paz.`}
                                    target="_blank" rel="noopener noreferrer"
                                    style={{
                                        display: 'flex', alignItems: 'center', gap: '0.4rem',
                                        background: '#25D366', color: 'white',
                                        padding: '0.5rem 1rem', borderRadius: '50px',
                                        textDecoration: 'none', fontWeight: '700', fontSize: '0.95rem',
                                        boxShadow: '0 2px 10px rgba(0,0,0,0.3)'
                                    }}
                                >
                                    💬 WhatsApp
                                </a>
                            )}
                        </div>
                    ) : (
                        <div style={{ color: '#b7e4c7', fontSize: '1rem', fontStyle: 'italic' }}>
                            No hay socio de turno programado para hoy a La Paz. Comuníquese con la oficina.
                        </div>
                    )}
                </div>
            </div>

            {verPasajerosModulo && (
                <div className="modal-overlay">
                    <div className="modal-content" style={{ maxWidth: '600px' }}>
                        <div className="modal-header">
                            <h2>Lista de Pasajeros</h2>
                            <button className="close-button" onClick={cerrarModalPasajeros}>&times;</button>
                        </div>
                        <div className="modal-body">
                            {hojaSeleccionada && (
                                <div style={{ marginBottom: '15px', padding: '10px', background: '#f5f5f5', borderRadius: '4px' }}>
                                    <strong>Ruta:</strong> {hojaSeleccionada.ruta?.nombre} <br />
                                    <strong>Fecha:</strong> {hojaSeleccionada.fecha_salida} <br />
                                    <strong>Vehículo:</strong> {hojaSeleccionada.vehiculo?.placa}
                                </div>
                            )}

                            {cargandoPasajerosModulo ? (
                                <p>Cargando...</p>
                            ) : datosPasajeros.length === 0 ? (
                                <p>No hay pasajeros registrados.</p>
                            ) : (
                                <table className="table">
                                    <thead>
                                        <tr>
                                            <th>Asiento</th>
                                            <th>Pasajero</th>
                                            <th>Teléfono</th>
                                            <th>Estado</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {datosPasajeros.map(p => (
                                            <tr key={p.id}>
                                                <td>{p.asiento || '-'}</td>
                                                <td>{p.cliente}</td>
                                                <td>{p.telefono || 'Sin teléfono'}</td>
                                                <td>
                                                    <span className={`status-badge ${p.estado}`}>
                                                        {p.estado}
                                                    </span>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            )}
                        </div>
                        <div className="modal-footer">
                            <button
                                className="btn btn-primary"
                                onClick={() => handleImprimirPlanilla(hojaSeleccionada?.id)}
                                disabled={!hojaSeleccionada}
                                style={{ marginRight: 'auto' }}
                            >
                                🖨️ Imprimir Planilla
                            </button>
                            <button className="btn btn-secondary" onClick={cerrarModalPasajeros}>Cerrar</button>
                        </div>
                    </div>
                </div>
            )}

            {!showForm ? (
                <div className="rutas-disponibles">
                    <h2>Rutas Disponibles</h2>
                    {hojasDisponibles.length === 0 ? (
                        <div className="no-rutas">No hay rutas disponibles en este momento</div>
                    ) : (
                        <div className="rutas-grid">
                            {hojasDisponibles.map((hoja) => {
                                const estaLleno = hoja.cupos_disponibles < 1;
                                const porcentajeOcupacion = hoja.capacidad_total > 0
                                    ? (hoja.cupos_reservados / hoja.capacidad_total) * 100
                                    : 0;

                                return (
                                    <div
                                        key={hoja.id}
                                        className={`ruta-card ${estaLleno ? 'disabled' : ''}`}
                                        onClick={() => !estaLleno && seleccionarRuta(hoja)}
                                        style={{ position: 'relative' }}
                                    >
                                        <div className="ruta-header">
                                            <h3 className="ruta-nombre">{hoja.ruta?.nombre || 'Sin nombre'}</h3>
                                            <span className="ruta-tarifa">Bs. {hoja.ruta?.tarifa_base || hoja.precio}</span>
                                        </div>

                                        <div className="ruta-destino">
                                            {hoja.ruta?.origen || 'Origen'} → {hoja.ruta?.destino || 'Destino'}
                                        </div>

                                        <div className="info-row">
                                            <span className="info-label">Fecha salida:</span>
                                            <span className="fecha-salida">{hoja.fecha_salida}</span>
                                        </div>

                                        <div className="info-row">
                                            <span className="info-label">Hora salida:</span>
                                            <span className="info-value">{hoja.hora_salida || 'Por confirmar'}</span>
                                        </div>

                                        {/* Indicador de cupos */}
                                        <div className="cupos-info">
                                            <div className="cupos-text">
                                                <span className={`cupos-badge ${estaLleno ? 'lleno' : porcentajeOcupacion > 70 ? 'casi-lleno' : 'disponible'}`}>
                                                    {estaLleno ? '🚫 LLENO' : `✓ ${hoja.cupos_disponibles} de ${hoja.capacidad_total} cupos`}
                                                </span>
                                            </div>
                                            <div className="cupos-barra">
                                                <div
                                                    className="cupos-progreso"
                                                    style={{ width: `${porcentajeOcupacion}%` }}
                                                ></div>
                                            </div>
                                        </div>

                                        <div className="ruta-info">
                                            {hoja.afiliado && (
                                                <>
                                                    <div className="info-row">
                                                        <span className="info-label">Conductor:</span>
                                                        <span className="info-value">{hoja.afiliado.nombre_completo}</span>
                                                    </div>
                                                    {hoja.afiliado.telefono && (
                                                        <div className="info-row">
                                                            <span className="info-label">Teléfono:</span>
                                                            <span className="info-value">{hoja.afiliado.telefono}</span>
                                                        </div>
                                                    )}
                                                </>
                                            )}

                                            {hoja.vehiculo && (
                                                <div className="info-row">
                                                    <span className="info-label">Vehículo:</span>
                                                    <span className="info-value">
                                                        {hoja.vehiculo.placa} {hoja.vehiculo.tipo ? `- ${hoja.vehiculo.tipo}` : ''}
                                                    </span>
                                                </div>
                                            )}
                                        </div>

                                        <div style={{ marginTop: '10px', textAlign: 'center' }}>
                                            <button
                                                className="btn-small"
                                                onClick={(e) => abrirModalPasajeros(e, hoja)}
                                                style={{
                                                    background: '#1976D2',
                                                    color: 'white',
                                                    border: 'none',
                                                    padding: '5px 10px',
                                                    borderRadius: '4px',
                                                    cursor: 'pointer',
                                                    fontSize: '0.85rem'
                                                }}
                                            >
                                                👥 Ver Pasajeros
                                            </button>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    )}
                </div>
            ) : (
                <div className="formulario-reserva">
                    <p style={{ fontSize: '1.2rem', marginBottom: '20px', color: '#333' }}>Selecciona una ruta para tu reserva real</p>
                    <h2 style={{ display: 'none' }}>Realizar Reserva</h2>

                    {submitError && <div className="error">{submitError}</div>}

                    <div className="reserva-layout">
                        {/* Columna Izquierda: Info Ruta */}
                        <div className="reserva-info-col">
                            <div style={{ height: '100%', padding: '0px' }}>
                                <div style={{ marginBottom: '15px' }}>
                                    <h3 style={{ margin: 0, fontSize: '1.5rem', color: '#000', textTransform: 'uppercase', fontWeight: 'bold' }}>{hojaSeleccionada.ruta?.nombre}</h3>
                                    <div style={{ fontSize: '1rem', color: '#333', marginTop: '5px' }}>Ruta Seleccionada: {hojaSeleccionada.ruta?.nombre}</div>
                                </div>

                                {(() => {
                                    const isIpsum = String(hojaSeleccionada.vehiculo?.tipo || '').toLowerCase() === 'ipsum';
                                    const totalPasajeros = isIpsum ? 6 : (hojaSeleccionada.capacidad_total > 7 ? 14 : 7);
                                    return (
                                        <div style={{ color: '#000', fontSize: '1.05rem', lineHeight: '1.8' }}>
                                            <p style={{ margin: '15px 0' }}><strong>Origen:</strong> {hojaSeleccionada.ruta?.origen} → <strong>Destino:</strong> {hojaSeleccionada.ruta?.destino}</p>
                                            <p style={{ margin: '10px 0' }}><strong>Conductor:</strong> {hojaSeleccionada.afiliado?.nombre_completo || 'Sin asignar'}</p>
                                            <p style={{ margin: '10px 0' }}><strong>Fecha: salida</strong> {hojaSeleccionada.fecha_salida}</p>
                                            <p style={{ margin: '10px 0' }}><strong>Hora de salida:</strong> {hojaSeleccionada.hora_salida || 'Por confirmar'}</p>
                                            <p style={{ margin: '10px 0' }}><strong>Tarifa:</strong> Bs. {parseFloat(hojaSeleccionada.ruta?.tarifa_base || hojaSeleccionada.precio).toFixed(2)}</p>
                                            <p style={{ margin: '10px 0' }}><strong>Vehículo:</strong> {hojaSeleccionada.vehiculo?.tipo || 'Minibús'}</p>
                                            <p style={{ margin: '10px 0' }}><strong>Capacidad:</strong> {totalPasajeros} Pasajeros</p>

                                            <div style={{ marginTop: '20px' }}>
                                                <button
                                                    className="btn btn-secondary"
                                                    onClick={(e) => { e.preventDefault(); handleImprimirPlanilla(hojaSeleccionada?.id); }}
                                                    style={{ width: '100%', border: '2px solid #333' }}
                                                >
                                                    🖨️ Imprimir Planilla de Ruta
                                                </button>
                                            </div>

                                            {/* Socio de Turno La Paz en formulario */}
                                            {afiliadoTurno && (
                                                <div style={{
                                                    marginTop: '18px',
                                                    background: 'linear-gradient(135deg, #1a3a2a, #2d6a4f)',
                                                    border: '2px solid #40916c',
                                                    borderRadius: '12px',
                                                    padding: '14px',
                                                    color: 'white'
                                                }}>
                                                    <div style={{
                                                        fontSize: '0.72rem',
                                                        color: '#74c69d',
                                                        fontWeight: '700',
                                                        textTransform: 'uppercase',
                                                        letterSpacing: '0.08em',
                                                        marginBottom: '8px'
                                                    }}>
                                                        🚌 Socio de turno La Paz — Contacto
                                                    </div>
                                                    <div style={{ fontWeight: '800', fontSize: '1rem', marginBottom: '4px' }}>
                                                        {afiliadoTurno.nombre_completo}
                                                    </div>
                                                    {afiliadoTurno.vehiculo_placa && (
                                                        <div style={{
                                                            fontSize: '0.88rem', color: '#b7e4c7',
                                                            marginBottom: '8px', fontWeight: '600'
                                                        }}>
                                                            🚗 Placa: <strong style={{ color: '#d8f3dc' }}>{afiliadoTurno.vehiculo_placa}</strong>
                                                            {afiliadoTurno.vehiculo_tipo && (
                                                                <span style={{ opacity: 0.8, marginLeft: '6px' }}>({afiliadoTurno.vehiculo_tipo})</span>
                                                            )}
                                                        </div>
                                                    )}
                                                    {afiliadoTurno.telefono && (
                                                        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                                                            <a href={`tel:${afiliadoTurno.telefono}`}
                                                                style={{
                                                                    background: '#40916c', color: 'white',
                                                                    padding: '5px 12px', borderRadius: '20px',
                                                                    textDecoration: 'none', fontWeight: '700',
                                                                    fontSize: '0.9rem'
                                                                }}>
                                                                📱 {afiliadoTurno.telefono}
                                                            </a>
                                                            <a href={`https://wa.me/591${afiliadoTurno.telefono}?text=Hola%2C%20quiero%20reservar%20un%20pasaje%20a%20La%20Paz.`}
                                                                target="_blank" rel="noopener noreferrer"
                                                                style={{
                                                                    background: '#25D366', color: 'white',
                                                                    padding: '5px 12px', borderRadius: '20px',
                                                                    textDecoration: 'none', fontWeight: '700',
                                                                    fontSize: '0.9rem'
                                                                }}>
                                                                💬 WhatsApp
                                                            </a>
                                                        </div>
                                                    )}
                                                </div>
                                            )}
                                        </div>
                                    );
                                })()}
                            </div>
                        </div>

                        {/* Columna Derecha: Grilla Asientos */}
                        <div className="reserva-seats-col">
                            {(() => {
                                const isIpsum = String(hojaSeleccionada.vehiculo?.tipo || '').toLowerCase() === 'ipsum';

                                if (isIpsum) {
                                    return (
                                        <div className="seat-grid-ipsum-enhanced">
                                            {/* Fila 1: Chofer + 1 */}
                                            <div className="seat-row-ipsum">
                                                <div className="seat-box seat-conductor">CHOFER</div>
                                                <div className="seat-spacer"></div>
                                                {renderSeatButton(1)}
                                            </div>
                                            {/* Fila 2: 3 Pasajeros */}
                                            <div className="seat-row-ipsum">
                                                {renderSeatButton(2)}
                                                {renderSeatButton(3)}
                                                {renderSeatButton(4)}
                                            </div>
                                            {/* Fila 3: 2 Pasajeros */}
                                            <div className="seat-row-ipsum" style={{ justifyContent: 'center', gap: '15px' }}>
                                                {renderSeatButton(5)}
                                                {renderSeatButton(6)}
                                            </div>
                                        </div>
                                    );
                                } else if (hojaSeleccionada.capacidad_total > 8) {
                                    return (
                                        <div className="seat-grid-minibus-enhanced">
                                            <div className="seat-row-minibus">
                                                <div className="seat-box seat-conductor">CHOFER</div>
                                                {renderSeatButton(1)}
                                                {renderSeatButton(2)}
                                            </div>
                                            {[3, 6, 9, 12].map(base => (
                                                <div key={base} className="seat-row-minibus">
                                                    {renderSeatButton(base)}
                                                    {renderSeatButton(base + 1)}
                                                    {renderSeatButton(base + 2)}
                                                </div>
                                            ))}
                                        </div>
                                    );
                                } else {
                                    // Layout genérico para otros casos o vehículos pequeños
                                    return (
                                        <div className="seat-grid-generic">
                                            {Array.from({ length: hojaSeleccionada.capacidad_total }).map((_, i) => renderSeatButton(i + 1))}
                                        </div>
                                    );
                                }
                            })()}
                        </div>
                    </div>

                    {submitError && <div className="error">{submitError}</div>}

                    <form onSubmit={handleSubmit}>
                        <div className="form-reserva-bottom">
                            <div className="form-group">
                                <label htmlFor="cliente">*Nombre completo</label>
                                <input
                                    id="cliente"
                                    name="cliente"
                                    type="text"
                                    value={form.cliente}
                                    onChange={onChange}
                                    required
                                    placeholder="Ej: Anibal Choque Aguirre"
                                    style={{ border: '2px solid #333' }}
                                />
                            </div>

                            <div className="form-group">
                                <label htmlFor="telefono">*Teléfono</label>
                                <input
                                    id="telefono"
                                    name="telefono"
                                    type="tel"
                                    value={form.telefono}
                                    onChange={onChange}
                                    placeholder="Ej: 71275002"
                                    className={phoneError ? 'input-error' : form.telefono && !phoneError ? 'input-success' : ''}
                                    style={{ border: '2px solid #333' }}
                                    required
                                />
                                {phoneError && <div className="error-message">{phoneError}</div>}
                                {form.telefono && !phoneError && (
                                    <div style={{ color: '#4CAF50', fontSize: '0.85rem', marginTop: '0.25rem' }}>
                                        ✓ Teléfono válido
                                    </div>
                                )}
                            </div>

                            <div className="form-group">
                                <label htmlFor="fecha_viaje">*Fecha de Viaje</label>
                                <input
                                    id="fecha_viaje"
                                    name="fecha_viaje"
                                    type="date"
                                    value={form.fecha_viaje}
                                    onChange={onChange}
                                    required
                                    style={{ border: '2px solid #333' }}
                                />
                            </div>

                            <div className="form-group">
                                <label htmlFor="cantidad">*Cantidad de Pasajeros</label>
                                <input
                                    id="cantidad"
                                    name="cantidad"
                                    type="number"
                                    value={selectedSeats.length}
                                    readOnly
                                    style={{ border: '2px solid #333', background: '#f9f9f9' }}
                                />
                            </div>
                        </div>

                        {/* Resumen de reserva */}
                        {selectedSeats.length > 0 && (
                            <div style={{
                                background: '#E8F5E9',
                                border: '2px solid #4CAF50',
                                padding: '1rem',
                                borderRadius: '8px',
                                marginBottom: '1.5rem'
                            }}>
                                <h4 style={{ margin: '0 0 0.75rem 0', color: '#2E7D32' }}>📋 Resumen de Reserva</h4>
                                <div style={{ display: 'grid', gap: '0.5rem' }}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                        <span><strong>Asientos seleccionados:</strong></span>
                                        <span>{selectedSeats.join(', ')}</span>
                                    </div>
                                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                        <span><strong>Cantidad:</strong></span>
                                        <span>{selectedSeats.length} pasajero(s)</span>
                                    </div>
                                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                        <span><strong>Precio unitario:</strong></span>
                                        <span>Bs. {parseFloat(hojaSeleccionada.ruta?.tarifa_base || hojaSeleccionada.precio).toFixed(2)}</span>
                                    </div>
                                    <div style={{
                                        display: 'flex',
                                        justifyContent: 'space-between',
                                        paddingTop: '0.5rem',
                                        borderTop: '2px solid #4CAF50',
                                        marginTop: '0.5rem'
                                    }}>
                                        <span style={{ fontSize: '1.2rem' }}><strong>TOTAL:</strong></span>
                                        <span style={{ fontSize: '1.2rem', fontWeight: 'bold', color: '#2E7D32' }}>
                                            Bs. {(parseFloat(hojaSeleccionada.ruta?.tarifa_base || hojaSeleccionada.precio) * selectedSeats.length).toFixed(2)}
                                        </span>
                                    </div>
                                </div>
                            </div>
                        )}

                        <div className="form-actions">
                            <button type="button" className="btn" onClick={cancelar} style={{ border: '2px solid #333', background: '#f44336', color: 'white', fontWeight: 'bold' }}>
                                Cancelar
                            </button>
                            <button type="submit" className="btn" style={{ border: '2px solid #333', background: '#4CAF50', color: 'white', fontWeight: 'bold' }}>
                                Confirmar Reserva
                            </button>
                        </div>
                    </form>
                </div>
            )}

            {/* Modal de Confirmación */}
            {showConfirmation && reservationData && (
                <div className="confirmation-modal" onClick={() => setShowConfirmation(false)}>
                    <div className="confirmation-content" onClick={(e) => e.stopPropagation()}>
                        <div className="confirmation-header">
                            <div className="confirmation-icon">✅</div>
                            <h2 className="confirmation-title">Confirmar Reserva</h2>
                        </div>

                        <div className="confirmation-body">
                            <p style={{ marginBottom: '1rem', color: '#666' }}>
                                Por favor revise los detalles de su reserva antes de confirmar:
                            </p>

                            <div className="confirmation-detail">
                                <span className="confirmation-label">Ruta:</span>
                                <span className="confirmation-value">{reservationData.ruta}</span>
                            </div>

                            <div className="confirmation-detail">
                                <span className="confirmation-label">Conductor:</span>
                                <span className="confirmation-value">{reservationData.conductor}</span>
                            </div>

                            <div className="confirmation-detail">
                                <span className="confirmation-label">Pasajero:</span>
                                <span className="confirmation-value">{reservationData.cliente}</span>
                            </div>

                            <div className="confirmation-detail">
                                <span className="confirmation-label">Teléfono:</span>
                                <span className="confirmation-value">{reservationData.telefono}</span>
                            </div>

                            <div className="confirmation-detail">
                                <span className="confirmation-label">Fecha de viaje:</span>
                                <span className="confirmation-value">{reservationData.fecha_viaje}</span>
                            </div>

                            <div className="confirmation-detail">
                                <span className="confirmation-label">Asientos:</span>
                                <span className="confirmation-value">{reservationData.asientos}</span>
                            </div>

                            <div className="confirmation-detail">
                                <span className="confirmation-label">Cantidad:</span>
                                <span className="confirmation-value">{reservationData.cantidad} pasajero(s)</span>
                            </div>

                            <div className="confirmation-detail" style={{ borderTop: '1px solid #eee', paddingTop: '10px', marginTop: '10px' }}>
                                <span className="confirmation-label" style={{ fontWeight: 'bold' }}>Modo de Pago:</span>
                                <div style={{ display: 'flex', gap: '15px', marginTop: '5px' }}>
                                    <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer', gap: '5px' }}>
                                        <input
                                            type="radio"
                                            name="metodoPago"
                                            value="efectivo"
                                            checked={metodoPago === 'efectivo'}
                                            onChange={() => setMetodoPago('efectivo')}
                                        />
                                        Efectivo
                                    </label>
                                    <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer', gap: '5px' }}>
                                        <input
                                            type="radio"
                                            name="metodoPago"
                                            value="qr"
                                            checked={metodoPago === 'qr'}
                                            onChange={() => setMetodoPago('qr')}
                                        />
                                        Yape (QR)
                                    </label>
                                </div>
                            </div>

                            <div className="confirmation-total">
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                    <span className="confirmation-total-label">TOTAL A PAGAR:</span>
                                    <span className="confirmation-total-value">Bs. {reservationData.total.toFixed(2)}</span>
                                </div>
                                <div style={{ fontSize: '0.85rem', color: '#666', marginTop: '0.5rem' }}>
                                    ({reservationData.cantidad} × Bs. {reservationData.precioUnitario.toFixed(2)})
                                </div>
                            </div>
                        </div>

                        <div className="confirmation-actions">
                            <button
                                type="button"
                                className="btn"
                                onClick={() => setShowConfirmation(false)}
                                style={{
                                    border: '2px solid #333',
                                    background: 'white',
                                    color: '#333',
                                    fontWeight: 'bold',
                                    padding: '0.75rem 1.5rem'
                                }}
                            >
                                Cancelar
                            </button>
                            <button
                                type="button"
                                className="btn"
                                onClick={confirmReservation}
                                style={{
                                    border: '2px solid #4CAF50',
                                    background: '#4CAF50',
                                    color: 'white',
                                    fontWeight: 'bold',
                                    padding: '0.75rem 1.5rem'
                                }}
                            >
                                ✓ Confirmar Reserva
                            </button>
                        </div>
                    </div>
                </div>
            )}
            {/* Modal de Pago QR (Yape) Reutilizable */}
            <YapeQRModal
                qrData={qrData}
                onVerify={verificarPago}
                onClose={() => setQrData(null)}
                verifying={verificandoPago}
            />
        </div>
    );
}


export default Reservas;
