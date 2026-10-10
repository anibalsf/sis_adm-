import './SancionesAlert.css';

function SancionesAlert({
    afiliado,
    sanciones,
    totalAdeudado,
    onContinue,
    onCancel,
    onPay,
    onPayQR,
    onPayAll,
    processingId,
    payingAll,
}) {
    const busy = Boolean(processingId) || Boolean(payingAll);
    const total = Number(totalAdeudado || 0);

    return (
        <div className="sanciones-alert-overlay">
            <div className="sanciones-alert-modal">
                <div className="sanciones-alert-header">
                    <div className="warning-icon">⚠️</div>
                    <h2>Sanciones Pendientes</h2>
                </div>

                <div className="sanciones-alert-content">
                    {afiliado && (
                        <p className="afiliado-info">
                            <strong>Afiliado:</strong> {afiliado}
                        </p>
                    )}

                    <div className="sanciones-resumen">
                        <div className="resumen-item">
                            <span className="label">Total de sanciones:</span>
                            <span className="value">{sanciones.length}</span>
                        </div>
                        <div className="resumen-item total">
                            <span className="label">Monto total adeudado:</span>
                            <span className="value">Bs. {total.toFixed(2)}</span>
                        </div>
                    </div>

                    <div className="sanciones-lista">
                        <h3>Detalle de Sanciones:</h3>
                        <div className="sanciones-table">
                            {sanciones.map((sancion, index) => (
                                <div key={sancion.id || index} className="sancion-item">
                                    <div className="sancion-tipo">{sancion.tipo}</div>
                                    <div className="sancion-detalle">
                                        <span className="motivo">{sancion.motivo}</span>
                                        <span className="monto">Bs. {parseFloat(sancion.monto).toFixed(2)}</span>
                                    </div>
                                    <div className="sancion-estado">
                                        <span className={`badge ${sancion.estado}`}>
                                            {sancion.estado}
                                        </span>
                                    </div>
                                    {(onPay || onPayQR) && sancion.id && (
                                        <div className="sancion-acciones" style={{ display: 'flex', gap: '6px', marginLeft: 'auto' }}>
                                            {onPay && (
                                                <button
                                                    className="btn btn-sm btn-success"
                                                    disabled={busy}
                                                    onClick={() => onPay(sancion)}
                                                    title="Registrar pago en efectivo"
                                                >
                                                    💵 Efectivo
                                                </button>
                                            )}
                                            {onPayQR && (
                                                <button
                                                    className="btn btn-sm btn-primary"
                                                    disabled={busy}
                                                    onClick={() => onPayQR(sancion)}
                                                    title="Pagar con QR"
                                                >
                                                    📱 QR
                                                </button>
                                            )}
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    </div>

                    <div className="sanciones-warning">
                        <p>
                            ⚠️ <strong>Advertencia:</strong> Este afiliado tiene sanciones pendientes.
                            Puede cancelarlas ahora antes de continuar con su hoja de ruta.
                        </p>
                    </div>
                </div>

                <div className="sanciones-alert-actions">
                    <button className="btn btn-secondary" onClick={onCancel} disabled={busy}>
                        Cancelar
                    </button>
                    {onPayAll && (
                        <button className="btn btn-success" onClick={onPayAll} disabled={busy}>
                            {payingAll ? 'Procesando...' : `💵 Pagar todo (Bs. ${total.toFixed(2)})`}
                        </button>
                    )}
                    <button className="btn btn-primary" onClick={onContinue} disabled={busy}>
                        Continuar de todas formas
                    </button>
                </div>
            </div>
        </div>
    );
}

export default SancionesAlert;
