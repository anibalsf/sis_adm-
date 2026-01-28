import React from 'react';

class ErrorBoundary extends React.Component {
    constructor(props) {
        super(props);
        this.state = { hasError: false, error: null };
    }

    static getDerivedStateFromError(error) {
        return { hasError: true, error };
    }

    componentDidCatch(error, errorInfo) {
        console.error("Uncaught error:", error, errorInfo);
    }

    render() {
        if (this.state.hasError) {
            return (
                <div className="error-boundary-container" style={{
                    padding: '40px',
                    textAlign: 'center',
                    backgroundColor: '#fff1f2',
                    border: '1px solid #fda4af',
                    borderRadius: '12px',
                    margin: '20px'
                }}>
                    <h1 style={{ color: '#9f1239' }}>¡Ups! Algo salió mal.</h1>
                    <p style={{ color: '#be123c' }}>
                        El sistema ha detectado un error inesperado al renderizar esta sección.
                    </p>
                    <button
                        onClick={() => window.location.reload()}
                        style={{
                            padding: '10px 20px',
                            backgroundColor: '#e11d48',
                            color: 'white',
                            border: 'none',
                            borderRadius: '6px',
                            cursor: 'pointer',
                            fontWeight: 'bold',
                            marginTop: '15px'
                        }}
                    >
                        🔄 Recargar Aplicación
                    </button>
                    <div style={{ marginTop: '20px', textAlign: 'left', fontSize: '0.8rem', color: '#888' }}>
                        <details>
                            <summary>Ver detalles técnicos</summary>
                            <pre>{this.state.error?.toString()}</pre>
                        </details>
                    </div>
                </div>
            );
        }

        return this.props.children;
    }
}

export default ErrorBoundary;
