import { useState } from 'react';
import './SancionesAlert.css';

function SancionesAlert({ afiliado, sanciones, totalAdeudado, onContinue, onCancel }) {
    return (
        <div className="sanciones-alert-overlay">
            <div className="sanciones-alert-modal">
                <div className="sanciones-alert-header">
                    <div className="warning-icon">⚠️</div>
                    <h2>Sanciones Pendientes</h2>
                </div>

                <div className="sanciones-alert-content">
                    <p className="afiliado-info">
                        <strong>Afiliado:</strong> {afiliado}
                    </p>

                    <div className="sanciones-resumen">
                        <div className="resumen-item">
                            <span className="label">Total de sanciones:</span>
                            <span className="value">{sanciones.length}</span>
                        </div>
                        <div className="resumen-item total">
                            <span className="label">Monto total adeudado:</span>
                            <span className="value">Bs. {totalAdeudado.toFixed(2)}</span>
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
                                </div>
                            ))}
                        </div>
                    </div>

                    <div className="sanciones-warning">
                        <p>
                            ⚠️ <strong>Advertencia:</strong> Este afiliado tiene sanciones pendientes.
                            Por favor, regularice su situación lo antes posible.
                        </p>
                    </div>
                </div>

                <div className="sanciones-alert-actions">
                    <button className="btn btn-secondary" onClick={onCancel}>
                        Cancelar
                    </button>
                    <button className="btn btn-primary" onClick={onContinue}>
                        Continuar de todas formas
                    </button>
                </div>
            </div>
        </div>
    );
}

export default SancionesAlert;
