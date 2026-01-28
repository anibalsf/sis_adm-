import { useEffect, useState } from 'react';
import { Html5QrcodeScanner } from 'html5-qrcode';
import { useNavigate } from 'react-router-dom';
import './QRScanner.css';

const QRScanner = ({ onClose }) => {
    const navigate = useNavigate();
    const [scannerLoaded, setScannerLoaded] = useState(false);

    useEffect(() => {
        const scanner = new Html5QrcodeScanner(
            "reader",
            {
                fps: 15,
                qrbox: { width: 250, height: 250 },
                aspectRatio: 1.0,
                showTorchButtonIfSupported: true,
            },
            /* verbose= */ false
        );

        scanner.render(onScanSuccess, onScanFailure);
        setScannerLoaded(true);

        // Traducir etiquetas de la librería (que vienen en inglés por defecto)
        const translateLabels = () => {
            const camBtn = document.getElementById('html5-qrcode-button-camera-permission');
            if (camBtn && camBtn.innerText.includes('Request')) {
                camBtn.innerText = "Solicitar Permiso de Cámara";
            }
            const fileAnchor = document.getElementById('html5-qrcode-anchor-scan-type-change');
            if (fileAnchor && fileAnchor.innerText.includes('Scan an Image')) {
                fileAnchor.innerText = "Escanear un archivo de imagen";
            } else if (fileAnchor && fileAnchor.innerText.includes('Scan using camera')) {
                fileAnchor.innerText = "Usar cámara directamente";
            }
        };

        const interval = setInterval(translateLabels, 200);

        function onScanSuccess(decodedText) {
            console.log(`Code matched = ${decodedText}`);
            scanner.clear();
            clearInterval(interval);

            // Si es una URL del sistema o solo el ID
            if (decodedText.includes('/verificar-hoja/')) {
                const parts = decodedText.split('/');
                const id = parts[parts.length - 1];
                navigate(`/verificar-hoja/${id}`);
            } else {
                navigate(`/verificar-hoja/${decodedText}`);
            }
            if (onClose) onClose();
        }

        function onScanFailure() {
            // Silencio en fallos de escaneo continuo
        }

        return () => {
            clearInterval(interval);
            scanner.clear().catch(err => console.warn("Scanner stop error", err));
        };
    }, [navigate, onClose]);

    return (
        <div className="qr-scanner-overlay">
            <div className="qr-scanner-modal">
                <div className="qr-scanner-header">
                    <h3>Escáner de Hoja de Ruta</h3>
                    <button onClick={onClose} className="close-btn">✕</button>
                </div>
                <div id="reader" className="qr-reader"></div>
                {!scannerLoaded && <div className="scanner-loading">Iniciando cámara...</div>}
                <div className="qr-scanner-footer">
                    <p>Encuadre el código QR de la hoja de ruta para verificarla automáticamente.</p>
                </div>
            </div>
        </div>
    );
};

export default QRScanner;
