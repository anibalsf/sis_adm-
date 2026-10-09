import { useEffect, useState } from 'react';
import { Html5QrcodeScanner } from 'html5-qrcode';
import { useNavigate } from 'react-router-dom';
import './QRScanner.css';

const RUTAS_QR = [
    { match: '/movilidades-lapaz', ruta: () => '/movilidades-lapaz' },
    { match: '/voucher/', ruta: (t) => extraerRuta(t, '/voucher/') },
    { match: '/pizarra', ruta: () => '/pizarra' },
    { match: '/verificar-hoja/', ruta: (t) => extraerRuta(t, '/verificar-hoja/') },
];

function extraerRuta(texto, marca) {
    const idx = texto.indexOf(marca);
    const resto = texto.slice(idx + 1);
    const limpio = resto.split(/[?\s#]/)[0];
    return `/${limpio.replace(/\/+$/, '')}`;
}

function resolverRuta(decodedText) {
    const texto = (decodedText || '').trim();

    // QR del PDF de confirmación: JSON {"tipo":"reserva","id":N}
    if (texto.startsWith('{') && texto.includes('"tipo"')) {
        try {
            const datos = JSON.parse(texto);
            if (datos.tipo === 'reserva' && datos.id) {
                return `/voucher/${datos.id}`;
            }
        } catch {
            // no es JSON válido, continuar con las demás reglas
        }
    }

    for (const regla of RUTAS_QR) {
        if (texto.includes(regla.match)) {
            return regla.ruta(texto);
        }
    }

    // QR del módulo de reservas: abre el módulo, que sin sesión muestra
    // la movilidad designada a La Paz (nombre, placa y color).
    if (/\/reservas(\/|[?\s#]|$)/.test(texto)) {
        return '/reservas';
    }

    // Es una URL externa del dominio del sistema: abrirla tal cual (ruta interna).
    if (/^https?:\/\//i.test(texto)) {
        try {
            const url = new URL(texto);
            if (url.pathname && url.pathname !== '/') {
                return `${url.pathname}${url.search}${url.hash}`;
            }
        } catch {
            // contenido no parseable, cae al comportamiento por defecto
        }
    }

    // Texto plano (ID de hoja de ruta impreso sin URL)
    return `/verificar-hoja/${texto}`;
}

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
        const loadTimer = setTimeout(() => setScannerLoaded(true), 0);

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

            navigate(resolverRuta(decodedText));
            if (onClose) onClose();
        }

        function onScanFailure() {
            // Silencio en fallos de escaneo continuo
        }

        return () => {
            clearTimeout(loadTimer);
            clearInterval(interval);
            scanner.clear().catch(err => console.warn("Scanner stop error", err));
        };
    }, [navigate, onClose]);

    return (
        <div className="qr-scanner-overlay">
            <div className="qr-scanner-modal">
                <div className="qr-scanner-header">
                    <h3>Escáner de QR</h3>
                    <button onClick={onClose} className="close-btn">✕</button>
                </div>
                <div id="reader" className="qr-reader"></div>
                {!scannerLoaded && <div className="scanner-loading">Iniciando cámara...</div>}
                <div className="qr-scanner-footer">
                    <p>Encuadre el QR de la reserva, la hoja de ruta o el voucher para abrirlo automáticamente.</p>
                </div>
            </div>
        </div>
    );
};

export default QRScanner;
