import React from 'react';

/**
 * Componente YapeQRModal
 * Muestra un modal estilizado al estilo Yape para pagos con QR.
 * 
 * @param {Object} qrData - Datos del QR (imagen_base64, monto, glosa, transaction_id)
 * @param {Function} onVerify - Función para verificar el pago
 * @param {Function} onClose - Función para cerrar el modal
 * @param {Boolean} verifying - Estado de carga de la verificación
 */
const YapeQRModal = ({ qrData, onVerify, onClose, verifying }) => {
    if (!qrData) return null;

    return (
        <div className="modal-overlay" style={{ zIndex: 2000 }}>
            <div className="modal-content" style={{ maxWidth: '400px', textAlign: 'center', padding: '0', overflow: 'hidden', borderRadius: '25px', border: 'none' }}>
                {/* Header Estilo Yape Púrpura */}
                <div style={{ background: '#7B1FA2', color: 'white', padding: '15px', position: 'relative', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <span style={{ position: 'absolute', left: '15px', fontSize: '1.2rem', cursor: 'pointer' }} onClick={onClose}>&larr;</span>
                    <h2 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 'normal' }}>Mi código QR</h2>
                </div>

                <div className="modal-body" style={{ padding: '30px 20px' }}>
                    {/* Logo Yape con burbuja Bs */}
                    <div style={{ marginBottom: '25px', position: 'relative', display: 'inline-block' }}>
                        <div style={{ background: '#00D1B2', color: 'white', fontSize: '0.6rem', padding: '2px 5px', borderRadius: '10px', position: 'absolute', top: '-10px', left: '50%', transform: 'translateX(-50%)', fontWeight: 'bold' }}>Bs</div>
                        <span style={{ color: '#7B1FA2', fontWeight: 'bold', fontSize: '2.2rem', fontStyle: 'italic', fontFamily: 'sans-serif' }}>yape</span>
                    </div>

                    <div style={{
                        background: 'white',
                        padding: '15px',
                        borderRadius: '20px',
                        boxShadow: '0 10px 30px rgba(0,0,0,0.08)',
                        display: 'inline-block',
                        marginBottom: '20px',
                        position: 'relative',
                        border: '1px solid #f0f0f0'
                    }}>
                        <img
                            src={`data:image/png;base64,${qrData.imagen_base64}`}
                            alt="QR de Pago"
                            style={{ width: '230px', height: '230px', display: 'block' }}
                        />
                        {/* Símbolo $ en el centro simulación */}
                        <div style={{
                            position: 'absolute',
                            top: '50%',
                            left: '50%',
                            transform: 'translate(-50%, -50%)',
                            background: 'white',
                            borderRadius: '50%',
                            width: '50px',
                            height: '50px',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            fontSize: '1.8rem',
                            fontWeight: 'bold',
                            color: '#333',
                            boxShadow: '0 0 15px rgba(0,0,0,0.1)'
                        }}>$</div>
                    </div>

                    <div style={{ color: '#666', fontSize: '0.95rem', marginBottom: '8px' }}>Escanea este QR para pagar a:</div>
                    <h3 style={{ margin: '0 0 15px 0', fontSize: '1.6rem', color: '#333', fontWeight: 'bold' }}>Anibal Choque Aguirre</h3>

                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', color: '#888', fontSize: '0.9rem' }}>
                        <span style={{ fontSize: '1.2rem' }}>🗓️</span>
                        <span>Vencimiento: {new Date().toLocaleDateString('es-BO', { day: 'numeric', month: 'long', year: 'numeric' })}</span>
                    </div>

                    <div style={{ marginTop: '25px', fontSize: '2.2rem', fontWeight: 'bold', color: '#333' }}>
                        <span style={{ fontSize: '1.2rem', marginRight: '5px' }}>Bs.</span>
                        {parseFloat(qrData.monto).toFixed(2)}
                    </div>
                </div>

                <div className="modal-footer" style={{ padding: '0 25px 30px 25px', display: 'flex', flexDirection: 'column', gap: '15px' }}>
                    <button
                        className="btn"
                        onClick={onVerify}
                        disabled={verifying}
                        style={{
                            width: '100%',
                            background: '#00D1B2',
                            color: 'white',
                            padding: '18px',
                            fontWeight: 'bold',
                            borderRadius: '12px',
                            border: 'none',
                            fontSize: '1.2rem',
                            cursor: 'pointer',
                            boxShadow: '0 5px 20px rgba(0,209,178,0.3)'
                        }}
                    >
                        {verifying ? '🕒 Verificando...' : 'Confirmar Pago'}
                    </button>
                    <button
                        className="btn"
                        onClick={onClose}
                        style={{ width: '100%', background: 'none', color: '#7B1FA2', fontWeight: 'bold', border: 'none', cursor: 'pointer', fontSize: '1.1rem' }}
                    >
                        Cancelar
                    </button>
                </div>
            </div>
        </div>
    );
};

export default YapeQRModal;
