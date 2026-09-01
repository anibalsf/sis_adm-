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
    const [layout, setLayout] = useState('thermal'); // 'thermal' o 'standard'

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
    const numero = String(data.nro_recibo ?? data.id).padStart(6, '0');
    const esHojaRuta = isIngreso && /hoja/i.test(data.tipo_pago_nombre || '') && /ruta/i.test(data.tipo_pago_nombre || '');
    const total = parseFloat(data.monto || 0);

    const renderTicket = (copiaLabel) => {
        const horaImpresion = new Date().toLocaleString('es-BO', { 
            day: 'numeric', month: 'long', year: 'numeric', 
            hour: '2-digit', minute: '2-digit' 
        });
        
        return (
        <div className="ticket-thermal" key={copiaLabel}>
            {/* Etiqueta de Copia */}
            <div className="ticket-copy-label">*** {copiaLabel} ***</div>

            {/* Header */}
            {/* Header sin logo */}
            <div className="ticket-header">
                <div className="ticket-title">SINDICATO MIXTO</div>
                <div className="ticket-title">INTEGRACIÓN TAIPIPLAYA</div>
                <div className="ticket-separator"></div>
                <div className="ticket-doc-type">{titulo}</div>
                <div className="ticket-doc-number">Nº {numero}</div>
                <div className="ticket-separator"></div>
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

            <div className="ticket-separator-dots"></div>

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
                                <div className="ticket-separator-dots"></div>
                                <div className="ticket-detalle-title">DETALLE:</div>
                                <div className="ticket-row">
                                    <span>Hoja de Ruta</span>
                                    <span>{total.toFixed(2)} Bs</span>
                                </div>
                                <div className="ticket-separator-dots"></div>
                            </div>
                        )}

                        {data.observaciones && (
                            <div className="ticket-item">
                                <div className="ticket-label">OBSERVACIONES:</div>
                                <div className="ticket-value">{data.observaciones}</div>
                            </div>
                        )}
                        {data.metodo_pago === 'transferencia' && (
                            <>
                                <div className="ticket-item">
                                    <div className="ticket-label">BANCO:</div>
                                    <div className="ticket-value">{data.banco || '-'}</div>
                                </div>
                                <div className="ticket-item">
                                    <div className="ticket-label">NRO OPERACIÓN:</div>
                                    <div className="ticket-value">{data.nro_operacion || '-'}</div>
                                </div>
                            </>
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
                        
                        {data.metodo_pago === 'transferencia' && (
                            <>
                                <div className="ticket-item">
                                    <div className="ticket-label">BANCO:</div>
                                    <div className="ticket-value">{data.banco || '-'}</div>
                                </div>
                                <div className="ticket-item">
                                    <div className="ticket-label">NRO OPERACIÓN:</div>
                                    <div className="ticket-value">{data.nro_operacion || '-'}</div>
                                </div>
                            </>
                        )}
                    </>
                )}
            </div>

            {/* Total */}
            <div className="ticket-total-section">
                <div className="ticket-separator"></div>
                <div className="ticket-total">
                    <span>TOTAL:</span>
                    <span>Bs. {parseFloat(data.monto).toFixed(2)}</span>
                </div>
                <div className="ticket-separator"></div>
            </div>

            {/* QR Code */}
            <div className="ticket-qr">
                <QRCodeSVG
                    value={`${isIngreso ? 'INGRESO' : 'EGRESO'}:${id}|FECHA:${data.fecha_pago || data.fecha}|MONTO:${data.monto}|TIPO:${data.tipo_pago_nombre || ''}`}
                    size={100}
                    level="M"
                />
            </div>

            {/* Footer */}
            <div className="ticket-footer">
                <div className="ticket-separator-dots"></div>
                <div className="ticket-firma">
                    <div className="firma-line"></div>
                    <div className="firma-text">Firma Autorizada</div>
                </div>
                <div className="ticket-separator-dots"></div>
                <div className="ticket-thanks">{isIngreso ? '¡Gracias por su pago!' : 'Comprobante emitido correctamente'}</div>
                <div className="ticket-info">Impreso el {horaImpresion}</div>
                <div className="ticket-info">Documento generado por el Sistema de Administración</div>
            </div>
        </div>
        );
    };

    const renderStandardReceipt = (copiaLabel) => {
        const horaImpresion = new Date().toLocaleString('es-BO', { 
            day: 'numeric', month: 'long', year: 'numeric', 
            hour: '2-digit', minute: '2-digit' 
        });

        return (
        <div className="receipt-standard" key={copiaLabel}>
            <div className="standard-header">
                <div className="standard-logo-section">
                    <div className="standard-header-text">
                        <h3>S.M.I.T. "INTEGRACIÓN TAIPIPLAYA"</h3>
                        <p>FUNDADO EL 22 DE SEPTIEMBRE DEL 2011 CON PERSONERÍA JURÍDICA R.S. NRO. 20095</p>
                        <p>TAIPIPLAYA – CARANAVI LA PAZ BOLIVIA</p>
                    </div>
                </div>
                <div className="standard-number-section">
                    <div className="doc-number-box">
                        <small>{titulo}</small>
                        <h2>Nº {numero}</h2>
                    </div>
                    <div className="doc-date-box">
                        <p><strong>FECHA:</strong> {data.fecha_pago || data.fecha}</p>
                        <p><strong>MONTO:</strong> Bs. {total.toFixed(2)}</p>
                    </div>
                </div>
            </div>

            <div className="standard-copy-tag">{copiaLabel}</div>

            <div className="standard-body">
                <div className="standard-row">
                    <span className="label">RECIBÍ DE:</span>
                    <span className="value">{data.afiliado_nombre || 'Afiliado ID: ' + data.afiliado}</span>
                </div>

                <div className="standard-row">
                    <span className="label">LA SUMA DE:</span>
                    <span className="value text-capitalize">{total.toFixed(2)} BOLIVIANOS</span>
                </div>

                <div className="standard-row">
                    <span className="label">POR CONCEPTO DE:</span>
                    <span className="value">{data.tipo_pago_nombre || 'Tipo ID: ' + data.tipo_pago}</span>
                </div>

                {esHojaRuta && (
                    <div className="standard-details">
                        <table className="details-table">
                            <thead>
                                <tr>
                                    <th>Descripción</th>
                                    <th>Monto</th>
                                    <th>Multas/Recargos</th>
                                    <th>Total</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td>Hoja de Ruta</td>
                                    <td>{total.toFixed(2)} Bs.</td>
                                    <td>0.00 Bs.</td>
                                    <td>{total.toFixed(2)} Bs.</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                )}

                <div className="standard-row">
                    <span className="label">OBSERVACIONES:</span>
                    <span className="value">{data.observaciones || 'Sin observaciones adicionales.'}</span>
                </div>

                {data.metodo_pago === 'transferencia' && (
                    <div className="standard-row">
                        <span className="label">DATOS TRANSFERENCIA:</span>
                        <span className="value">Banco: {data.banco || '-'} | Operación: {data.nro_operacion || '-'}</span>
                    </div>
                )}
            </div>

            <div className="standard-footer">
                <div className="standard-qr-section">
                    <QRCodeSVG
                        value={`${isIngreso ? 'INGRESO' : 'EGRESO'}:${id}|FECHA:${data.fecha_pago || data.fecha}|MONTO:${data.monto}`}
                        size={80}
                    />
                </div>
                <div className="standard-signatures">
                    <div className="signature-box">
                        <div className="line"></div>
                        <span>ENTREGUE CONFORME</span>
                    </div>
                    <div className="signature-box">
                        <div className="line"></div>
                        <span>TESORERÍA / RECAUDACIONES</span>
                    </div>
                </div>
            </div>
            
            <div className="standard-print-info" style={{ textAlign: 'center', marginTop: '1rem', fontSize: '0.8rem', color: '#666' }}>
                <strong>Impreso el:</strong> {horaImpresion} <br/>
                <span style={{ fontSize: '0.7rem' }}>Documento generado por el Sistema de Administración</span>
            </div>
        </div>
        );
    };

    return (
        <div className="recibo-container">
            <div className="recibo-actions no-print">
                <button className="btn btn-secondary" onClick={handleBack}>Volver</button>

                <div className="layout-selector">
                    <button
                        className={`btn-layout ${layout === 'thermal' ? 'active' : ''}`}
                        onClick={() => setLayout('thermal')}
                    >
                        📟 Ticket Térmico
                    </button>
                    <button
                        className={`btn-layout ${layout === 'standard' ? 'active' : ''}`}
                        onClick={() => setLayout('standard')}
                    >
                        📄 Formato Carta/A4
                    </button>
                </div>

                <button className="btn btn-primary" onClick={handlePrint}>🖨️ Imprimir Formato {layout === 'thermal' ? 'Ticket' : 'Carta'}</button>
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

            {/* LISTA DE TICKETS (ORIGINAL Y COPIA) */}
            <div className={`tickets-wrapper ${layout}`}>
                {layout === 'thermal' ? (
                    <>
                        {renderTicket("ORIGINAL - CLIENTE")}
                        <div className="ticket-cut-line no-print">- - - - - - - - - - - - - - - - - - - - - - - -</div>
                        {renderTicket("COPIA - CONTABILIDAD")}
                    </>
                ) : (
                    <>
                        {renderStandardReceipt("ORIGINAL - CLIENTE")}
                        <div className="standard-separator"></div>
                        {renderStandardReceipt("COPIA - ARCHIVO SINDICATO")}
                    </>
                )}
            </div>
        </div>
    );
}


export default ReciboPago;
