import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../services/api';
import { QRCodeSVG } from 'qrcode.react';
import '../css/ReciboPago.css';

function ReciboPago() {
    const { type, id } = useParams();
    const navigate = useNavigate();
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        const fetchData = async () => {
            try {
                setLoading(true);
                let response;
                if (type === 'ingreso') {
                    response = await api.getPago(id);
                } else if (type === 'egreso') {
                    response = await api.getEgreso(id);
                } else {
                    throw new Error('Tipo de recibo no válido');
                }
                setData(response.data);
            } catch (err) {
                console.error(err);
                setError('Error al cargar los datos del recibo');
            } finally {
                setLoading(false);
            }
        };

        if (id && type) {
            fetchData();
        }
    }, [id, type]);

    const handlePrint = () => {
        window.print();
    };

    const handleBack = () => {
        navigate('/pagos-y-egresos');
    };

    if (loading) return <div className="loading">Cargando recibo...</div>;
    if (error) return <div className="error">{error}</div>;
    if (!data) return <div className="error">No se encontró el recibo</div>;

    const isIngreso = type === 'ingreso';
    const titulo = isIngreso ? 'RECIBO DE INGRESO' : 'COMPROBANTE DE EGRESO';
    const numero = String(data.id).padStart(6, '0');
    const esHojaRuta = isIngreso && /hoja/i.test(data.tipo_pago_nombre || '') && /ruta/i.test(data.tipo_pago_nombre || '');
    const total = parseFloat(data.monto || 0);
    const baseHoja = 20;
    const multaHoja = 50;

    return (
        <div className="recibo-container">
            <div className="recibo-actions no-print">
                <button className="btn btn-secondary" onClick={handleBack}>Volver</button>
                <button className="btn btn-primary" onClick={handlePrint}>🖨️ Imprimir</button>
                {isIngreso && (
                    <button
                        className="btn btn-primary"
                        onClick={async () => {
                            try {
                                const res = await api.generarQrPago(id);
                                const url = window.URL.createObjectURL(new Blob([res.data], { type: 'image/png' }));
                                const w = window.open();
                                const img = new Image();
                                img.src = url;
                                w.document.body.appendChild(img);
                            } catch (err) { console.error(err) }
                        }}
                    >
                        📱 Pagar con QR
                    </button>
                )}
            </div>

            {/* FORMATO TICKET TÉRMICO */}
            <div className="ticket-thermal">
                {/* Header */}
                <div className="ticket-header">
                    <div className="ticket-logo">
                        <img src="/logo-taipiplaya.png" alt="Logo Taipiplaya" className="logo-img" />
                    </div>
                    <div className="ticket-title">SINDICATO MIXTO</div>
                    <div className="ticket-title">INTEGRACIÓN TAIPIPLAYA</div>
                    <div className="ticket-separator">================================</div>
                    <div className="ticket-doc-type">{titulo}</div>
                    <div className="ticket-doc-number">Nº {numero}</div>
                    <div className="ticket-separator">================================</div>
                </div>

                {/* Meta Info */}
                <div className="ticket-meta">
                    <div className="ticket-row">
                        <span>Fecha:</span>
                        <span>{data.fecha_pago || data.fecha}</span>
                    </div>
                    <div className="ticket-row">
                        <span>Lugar:</span>
                        <span>Taipiplaya</span>
                    </div>
                </div>

                <div className="ticket-separator-dots">- - - - - - - - - - - - - - - -</div>

                {/* Body */}
                <div className="ticket-body">
                    {isIngreso ? (
                        <>
                            <div className="ticket-item">
                                <div className="ticket-label">RECIBÍ DE:</div>
                                <div className="ticket-value">{data.afiliado_nombre || 'Afiliado ID: ' + data.afiliado}</div>
                            </div>

                            <div className="ticket-item">
                                <div className="ticket-label">CONCEPTO:</div>
                                <div className="ticket-value">{data.tipo_pago_nombre || 'Tipo ID: ' + data.tipo_pago}</div>
                            </div>

                            {esHojaRuta && (
                                <div className="ticket-detalle">
                                    <div className="ticket-separator-dots">- - - - - - - - - - - - - - - -</div>
                                    <div className="ticket-detalle-title">DETALLE:</div>
                                    <div className="ticket-row">
                                        <span>Hoja de Ruta</span>
                                        <span>{baseHoja.toFixed(2)} Bs</span>
                                    </div>
                                    {total > baseHoja && (
                                        <div className="ticket-row">
                                            <span>Multa</span>
                                            <span>{multaHoja.toFixed(2)} Bs</span>
                                        </div>
                                    )}
                                    <div className="ticket-separator-dots">- - - - - - - - - - - - - - - -</div>
                                </div>
                            )}

                            {data.observaciones && (
                                <div className="ticket-item">
                                    <div className="ticket-label">OBSERVACIONES:</div>
                                    <div className="ticket-value">{data.observaciones}</div>
                                </div>
                            )}
                        </>
                    ) : (
                        <>
                            <div className="ticket-item">
                                <div className="ticket-label">PAGADO A:</div>
                                <div className="ticket-value">{data.descripcion}</div>
                            </div>

                            <div className="ticket-item">
                                <div className="ticket-label">CONCEPTO:</div>
                                <div className="ticket-value">{data.tipo_pago_nombre || 'Tipo ID: ' + data.tipo_pago}</div>
                            </div>
                        </>
                    )}
                </div>

                {/* Total */}
                <div className="ticket-total-section">
                    <div className="ticket-separator">================================</div>
                    <div className="ticket-total">
                        <span>TOTAL:</span>
                        <span>Bs. {parseFloat(data.monto).toFixed(2)}</span>
                    </div>
                    <div className="ticket-separator">================================</div>
                </div>

                {/* QR Code */}
                <div className="ticket-qr">
                    <QRCodeSVG
                        value={`${isIngreso ? 'INGRESO' : 'EGRESO'}:${id}|FECHA:${data.fecha_pago || data.fecha}|MONTO:${data.monto}|TIPO:${data.tipo_pago_nombre || ''}`}
                        size={120}
                        level="M"
                    />
                </div>

                {/* Footer */}
                <div className="ticket-footer">
                    <div className="ticket-separator-dots">- - - - - - - - - - - - - - - -</div>
                    <div className="ticket-firma">
                        <div className="firma-line">_____________________</div>
                        <div className="firma-text">Firma Autorizada</div>
                    </div>
                    <div className="ticket-separator-dots">- - - - - - - - - - - - - - - -</div>
                    <div className="ticket-thanks">¡Gracias por su pago!</div>
                    <div className="ticket-info">Sistema de Gestión v1.0</div>
                </div>
            </div>
        </div>
    );
}

export default ReciboPago;
