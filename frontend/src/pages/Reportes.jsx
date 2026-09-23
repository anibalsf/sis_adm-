import { useState } from 'react';
import ReportesFinancieros from './ReportesFinancieros';
import ReportesOperativos from './ReportesOperativos';
import ReporteDeudas from './ReporteDeudas';
import ReportesAvanzados from './ReportesAvanzados';
import ReportePorCategoria from './ReportePorCategoria';
import './ReportesFinancieros.css';

function Reportes() {
    const [tabActiva, setTabActiva] = useState('financieros');

    return (
        <div className="reportes-wrapper">
            <div className="tabs-container">
                <button
                    className={`tab-button ${tabActiva === 'financieros' ? 'active' : ''}`}
                    onClick={() => setTabActiva('financieros')}
                >
                    📊 Reportes Financieros
                </button>
                <button
                    className={`tab-button ${tabActiva === 'operativos' ? 'active' : ''}`}
                    onClick={() => setTabActiva('operativos')}
                >
                    📈 Reportes Operativos
                </button>
                <button
                    className={`tab-button ${tabActiva === 'deudas' ? 'active' : ''}`}
                    onClick={() => setTabActiva('deudas')}
                >
                    💰 Estado de Cuentas
                </button>
                <button
                    className={`tab-button ${tabActiva === 'avanzados' ? 'active' : ''}`}
                    onClick={() => setTabActiva('avanzados')}
                >
                    🚀 Reportes Avanzados
                </button>
                <button
                    className={`tab-button ${tabActiva === 'categoria' ? 'active' : ''}`}
                    onClick={() => setTabActiva('categoria')}
                >
                    🎯 Por Categoría
                </button>
            </div>

            <div className="tab-content">
                {tabActiva === 'financieros' && <ReportesFinancieros />}
                {tabActiva === 'operativos' && <ReportesOperativos />}
                {tabActiva === 'deudas' && <ReporteDeudas />}
                {tabActiva === 'avanzados' && <ReportesAvanzados />}
                {tabActiva === 'categoria' && <ReportePorCategoria />}
            </div>
        </div>
    );
}

export default Reportes;
