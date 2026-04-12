import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import '../css/PagosYEgresos.css';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';
import { Pie } from 'react-chartjs-2';

ChartJS.register(ArcElement, Tooltip, Legend);

function ArqueoCaja() {
    const [arqueos, setArqueos] = useState([]);
    const [loading, setLoading] = useState(false);
    const [showModal, setShowModal] = useState(false);
    const [error, setError] = useState('');
    
    // Formularios
    const [form, setForm] = useState({
        fecha_inicio: '',
        fecha_fin: '',
        saldo_real: '',
        observaciones: ''
    });
    const [calculo, setCalculo] = useState(null);
    const [calculando, setCalculando] = useState(false);

    // Desglose de efectivo
    const [desglose, setDesglose] = useState({
        b200: 0, b100: 0, b50: 0, b20: 0, b10: 0,
        m5: 0, m2: 0, m1: 0, m050: 0, m020: 0, m010: 0
    });

    const totalDesglose = (
        desglose.b200 * 200 +
        desglose.b100 * 100 +
        desglose.b50 * 50 +
        desglose.b20 * 20 +
        desglose.b10 * 10 +
        desglose.m5 * 5 +
        desglose.m2 * 2 +
        desglose.m1 * 1 +
        desglose.m050 * 0.5 +
        desglose.m020 * 0.2 +
        desglose.m010 * 0.1
    );

    // Actualizar el saldo real automáticamente cuando el desglose cambia
    useEffect(() => {
        if (calculo) { // Solo si ya hemos calculado la teoría, permitimos editar el real o se refleja
            setForm(prev => ({...prev, saldo_real: totalDesglose.toFixed(2)}));
        }
    }, [desglose]);


    useEffect(() => {
        loadArqueos();
    }, []);

    const loadArqueos = async () => {
        try {
            setLoading(true);
            const res = await api.getArqueos();
            setArqueos(res.data?.results || res.data || []);
        } catch (err) {
            console.error('Error cargando arqueos:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleCalcular = async () => {
        if (!form.fecha_inicio || !form.fecha_fin) {
            setError('Debe seleccionar fecha de inicio y fin para calcular.');
            return;
        }
        try {
            setCalculando(true);
            setError('');
            const res = await api.calcularArqueo({
                fecha_inicio: form.fecha_inicio,
                fecha_fin: form.fecha_fin
            });
            setCalculo(res.data);
            // Autofill saldo_real directly to match perfectly as requested
            setForm(prev => ({...prev, saldo_real: res.data.saldo_teorico}));
        } catch (err) {
            console.error('Error al calcular:', err);
            setError('Error al calcular los montos.');
        } finally {
            setCalculando(false);
        }
    };

    const handleGuardar = async () => {
        if (!calculo) {
            setError('Primero debe calcular los montos.');
            return;
        }
        if (form.saldo_real === '') {
            setError('Debe ingresar el saldo real(físico) de la caja.');
            return;
        }
        if (parseFloat(form.saldo_real) !== calculo.saldo_teorico) {
            setError('El Saldo Real debe coincidir exactamente con el Saldo Teórico total de las transacciones.');
            return;
        }
        
        try {
            setLoading(true);
            const payload = {
                fecha_inicio: form.fecha_inicio,
                fecha_fin: form.fecha_fin,
                total_ingresos: calculo.total_ingresos,
                total_egresos: calculo.total_egresos,
                saldo_teorico: calculo.saldo_teorico,
                saldo_real: parseFloat(form.saldo_real),
                diferencia: parseFloat(form.saldo_real) - calculo.saldo_teorico,
                observaciones: form.observaciones,
                detalle_efectivo: desglose,
                estado: 'cerrado'
            };
            await api.createArqueo(payload);
            setShowModal(false);
            setCalculo(null);
            setDesglose({
                b200: 0, b100: 0, b50: 0, b20: 0, b10: 0,
                m5: 0, m2: 0, m1: 0, m050: 0, m020: 0, m010: 0
            });
            setForm({ fecha_inicio: '', fecha_fin: '', saldo_real: '', observaciones: '' });
            await loadArqueos();
        } catch (err) {
            console.error('Error guardando arqueo:', err);
            setError('Error al guardar el arqueo.');
        } finally {
            setLoading(false);
        }
    };

    const handleExportarExcel = async () => {
        try {
            setLoading(true);
            await api.downloadArqueosExcel();
        } catch (err) {
            console.error('Error al exportar:', err);
            alert('Error al descargar el archivo Excel.');
        } finally {
            setLoading(false);
        }
    };

    const handleExportarIndividual = async (id) => {
        try {
            alert('Generando plantilla de Arqueo Físico...');
            await api.downloadArqueoIndividualExcel(id);
        } catch (err) {
            console.error('Error al exportar arqueo individual:', err);
            alert('Error al descargar el arqueo.');
        }
    };

    const formatCurrency = (val) => parseFloat(val || 0).toFixed(2) + ' Bs.';

    return (
        <div className="pagos-y-egresos-container">
            <h1>Arqueo de Caja (Cierres Mensuales)</h1>
            <p>Historial de arqueos de caja y control de cierre contable.</p>

            <div className="card">
                <div className="table-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <button className="btn btn-primary" onClick={() => setShowModal(true)}>
                        <span>➕ Nuevo Arqueo</span>
                    </button>
                    <button className="btn btn-secondary" onClick={handleExportarExcel} disabled={loading} style={{ background: '#217346', color: 'white', borderColor: '#217346' }}>
                        <span>📊 Exportar Informe a Excel</span>
                    </button>
                </div>

                {loading && !showModal ? (
                    <div className="loading">Cargando...</div>
                ) : (
                    <div className="table-wrapper">
                        <table>
                            <thead>
                                <tr>
                                    <th>Mes / Año</th>
                                    <th>Periodo</th>
                                    <th>Ingresos</th>
                                    <th>Egresos</th>
                                    <th>Saldo Teórico</th>
                                    <th>Saldo Real</th>
                                    <th>Diferencia</th>
                                    <th>Estado</th>
                                </tr>
                            </thead>
                            <tbody>
                                {arqueos.length > 0 ? (
                                    arqueos.map((arq) => (
                                        <tr key={arq.id}>
                                            <td><strong>{arq.mes} {arq.anho}</strong></td>
                                            <td>{arq.fecha_inicio} a {arq.fecha_fin}</td>
                                            <td style={{color: 'green'}}>{formatCurrency(arq.total_ingresos)}</td>
                                            <td style={{color: 'red'}}>{formatCurrency(arq.total_egresos)}</td>
                                            <td><strong>{formatCurrency(arq.saldo_teorico)}</strong></td>
                                            <td><strong>{formatCurrency(arq.saldo_real)}</strong></td>
                                            <td style={{ color: arq.diferencia < 0 ? 'red' : 'green', fontWeight: 'bold' }}>
                                                {formatCurrency(arq.diferencia)}
                                            </td>
                                            <td>
                                                <span className="badge badge-success" style={{background: '#2ecc71', color: 'white', padding: '4px 8px', borderRadius: '12px'}}>
                                                    {arq.estado.toUpperCase()}
                                                </span>
                                                <button 
                                                    className="btn btn-sm" 
                                                    style={{ background: '#217346', color: 'white', marginLeft: '10px', fontSize: '0.8em', padding: '2px 6px' }}
                                                    onClick={() => handleExportarIndividual(arq.id)}
                                                    title="Descargar Arqueo Físico y Detallado (Excel)"
                                                >
                                                    🖨️ Físico
                                                </button>
                                            </td>
                                        </tr>
                                    ))
                                ) : (
                                    <tr>
                                        <td colSpan="8" style={{ textAlign: 'center' }}>No existen arqueos registrados</td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>

            {showModal && (
                <div className="modal-overlay" onClick={() => setShowModal(false)}>
                    <div className="modal-content md:max-w-2xl" onClick={(e) => e.stopPropagation()}>
                        <div className="modal-header">
                            <h2>Nuevo Arqueo de Caja</h2>
                            <button className="modal-close" onClick={() => setShowModal(false)}>✕</button>
                        </div>
                        {error && <div className="alert-multa warning">{error}</div>}
                        <div className="modal-form">
                            <div style={{ display: 'flex', gap: '15px' }}>
                                <div className="form-group" style={{ flex: 1 }}>
                                    <label>Fecha Inicio *</label>
                                    <input 
                                        type="date" 
                                        value={form.fecha_inicio}
                                        onChange={(e) => setForm({...form, fecha_inicio: e.target.value})}
                                    />
                                </div>
                                <div className="form-group" style={{ flex: 1 }}>
                                    <label>Fecha Fin *</label>
                                    <input 
                                        type="date" 
                                        value={form.fecha_fin}
                                        onChange={(e) => setForm({...form, fecha_fin: e.target.value})}
                                    />
                                </div>
                            </div>

                            <button 
                                type="button"
                                className="btn btn-secondary" 
                                onClick={handleCalcular}
                                disabled={calculando}
                                style={{marginTop: '10px', marginBottom: '20px', width: '100%', display: 'flex', justifyContent: 'center'}}
                            >
                                {calculando ? 'Calculando...' : '🧮 Calcular Ingresos y Egresos del Periodo'}
                            </button>

                            {calculo && (
                                <div style={{ background: '#f8fafc', padding: '15px', borderRadius: '12px', marginBottom: '20px', border: '1px solid #e2e8f0' }}>
                                    <h3 style={{marginTop: 0, marginBottom: '15px'}}>Resultados del Cálculo (Acumulado Total)</h3>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
                                        <span>Total Ingresos (Histórico):</span>
                                        <strong style={{color: 'green'}}>{formatCurrency(calculo.total_ingresos)}</strong>
                                    </div>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
                                        <span>Total Egresos (Histórico):</span>
                                        <strong style={{color: 'red'}}>{formatCurrency(calculo.total_egresos)}</strong>
                                    </div>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px', fontSize: '0.9em', color: 'gray' }}>
                                        <span>Ingresos del periodo ({form.fecha_inicio} al {form.fecha_fin}):</span>
                                        <span>{formatCurrency(calculo.ingresos_periodo)}</span>
                                    </div>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px', fontSize: '0.9em', color: 'gray' }}>
                                        <span>Egresos del periodo ({form.fecha_inicio} al {form.fecha_fin}):</span>
                                        <span>{formatCurrency(calculo.egresos_periodo)}</span>
                                    </div>
                                    <hr style={{margin: '10px 0'}}/>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '1.2em' }}>
                                        <span>Saldo Teórico (Caja Ideal Acumulada):</span>
                                        <strong>{formatCurrency(calculo.saldo_teorico)}</strong>
                                    </div>
                                    
                                    {(calculo.ingresos_breakdown?.length > 0 || calculo.egresos_breakdown?.length > 0) && (
                                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '20px', marginTop: '20px', justifyContent: 'center', borderTop: '1px dashed #ccc', paddingTop: '15px' }}>
                                            <div style={{ width: '220px' }}>
                                                <h4 style={{ textAlign: 'center', margin: '5px 0', color: '#2ecc71' }}>Ingresos del Periodo</h4>
                                                {calculo.ingresos_breakdown.length > 0 ? (
                                                    <Pie 
                                                        data={{
                                                            labels: calculo.ingresos_breakdown.map(i => i.tipo_pago__nombre || 'Otros'),
                                                            datasets: [{
                                                                data: calculo.ingresos_breakdown.map(i => parseFloat(i.total)),
                                                                backgroundColor: ['#2ecc71', '#27ae60', '#1abc9c', '#16a085', '#a2d9ce', '#58d68d']
                                                            }]
                                                        }}
                                                        options={{ plugins: { legend: { position: 'bottom', labels: { boxWidth: 10, font: { size: 10 } } } } }}
                                                    />
                                                ) : <p style={{textAlign: 'center', fontSize: '0.8em', color: 'gray'}}>Sin ingresos</p>}
                                            </div>
                                            <div style={{ width: '220px' }}>
                                                <h4 style={{ textAlign: 'center', margin: '5px 0', color: '#e74c3c' }}>Egresos del Periodo</h4>
                                                {calculo.egresos_breakdown.length > 0 ? (
                                                    <Pie 
                                                        data={{
                                                            labels: calculo.egresos_breakdown.map(e => e.tipo_pago__nombre || 'Otros'),
                                                            datasets: [{
                                                                data: calculo.egresos_breakdown.map(e => parseFloat(e.total)),
                                                                backgroundColor: ['#e74c3c', '#c0392b', '#e67e22', '#d35400', '#f5b041', '#f1948a']
                                                            }]
                                                        }}
                                                        options={{ plugins: { legend: { position: 'bottom', labels: { boxWidth: 10, font: { size: 10 } } } } }}
                                                    />
                                                ) : <p style={{textAlign: 'center', fontSize: '0.8em', color: 'gray'}}>Sin egresos</p>}
                                            </div>
                                        </div>
                                    )}
                                </div>
                            )}

                            {calculo && (
                                <>
                                    <div className="form-group" style={{ background: '#fcfcfc', border: '1px solid #ddd', padding: '15px', borderRadius: '8px', marginTop: '20px' }}>
                                        <h3 style={{marginTop: '0', marginBottom: '15px'}}>Desglose de Efectivo en Caja</h3>
                                        <div style={{ display: 'flex', gap: '20px' }}>
                                            {/* Billetes */}
                                            <div style={{ flex: 1 }}>
                                                <h4 style={{marginTop: 0, paddingBottom: '5px', borderBottom: '1px solid #eee'}}>💵 Billetes</h4>
                                                {[200, 100, 50, 20, 10].map(den => (
                                                    <div key={`b${den}`} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                                                        <span>{den} Bs:</span>
                                                        <input 
                                                            type="number" min="0" 
                                                            value={desglose[`b${den}`] || ''} 
                                                            onChange={e => setDesglose({...desglose, [`b${den}`]: parseInt(e.target.value) || 0})}
                                                            style={{ width: '80px', padding: '4px 8px' }}
                                                        />
                                                    </div>
                                                ))}
                                            </div>
                                            {/* Monedas */}
                                            <div style={{ flex: 1 }}>
                                                <h4 style={{marginTop: 0, paddingBottom: '5px', borderBottom: '1px solid #eee'}}>🪙 Monedas</h4>
                                                {[{val: 5, lbl: '5 Bs'}, {val: 2, lbl: '2 Bs'}, {val: 1, lbl: '1 Bs'}, {val: '050', lbl: '0.50 Bs', exact: 0.5}, {val: '020', lbl: '0.20 Bs', exact: 0.2}, {val: '010', lbl: '0.10 Bs', exact: 0.1}].map(coin => (
                                                    <div key={`m${coin.val}`} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                                                        <span>{coin.lbl}:</span>
                                                        <input 
                                                            type="number" min="0" 
                                                            value={desglose[`m${coin.val}`] || ''} 
                                                            onChange={e => setDesglose({...desglose, [`m${coin.val}`]: parseInt(e.target.value) || 0})}
                                                            style={{ width: '80px', padding: '4px 8px' }}
                                                        />
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                        <div style={{ marginTop: '15px', paddingTop: '15px', borderTop: '2px solid #ddd', display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '1.2em' }}>
                                            <strong>Total Desglose:</strong>
                                            <strong style={{ color: totalDesglose === calculo.saldo_teorico ? 'green' : 'red' }}>
                                                {formatCurrency(totalDesglose)}
                                            </strong>
                                        </div>
                                    </div>

                                    <div className="form-group" style={{ display: 'none' }}>
                                        <label>Saldo Real en Caja Física (Bs.) *</label>
                                        <input 
                                            type="number" 
                                            placeholder="Ingresa el monto de billetes/monedas/etc." 
                                            value={form.saldo_real}
                                            onChange={(e) => setForm({...form, saldo_real: e.target.value})}
                                            style={{fontSize: '1.2em', padding: '10px'}}
                                            disabled // Se deshabilita para priorizar la tabla de desglose
                                        />
                                    </div>
                                    
                                    {(parseFloat(form.saldo_real) !== calculo.saldo_teorico) && (
                                        <div className="alert-multa warning" style={{marginTop: '10px', background: '#ffebee', color: '#c62828'}}>
                                            <strong>Diferencia detectada:</strong> El monto en billetes y monedas ({formatCurrency(form.saldo_real)}) no coincide con el sistema ({formatCurrency(calculo.saldo_teorico)}). Debe cuadrar exactamente o revisar las transacciones.
                                        </div>
                                    )}

                                    <div className="form-group" style={{marginTop: '15px'}}>
                                        <label>Observaciones</label>
                                        <textarea 
                                            rows={2}
                                            value={form.observaciones}
                                            onChange={(e) => setForm({...form, observaciones: e.target.value})}
                                            placeholder="Explicación si hay alguna diferencia..."
                                        />
                                    </div>

                                    <div style={{display: 'flex', justifyContent: 'flex-end', marginTop: '20px'}}>
                                        <button className="btn btn-primary" onClick={handleGuardar}>
                                            💾 Guardar Cierre de Caja
                                        </button>
                                    </div>
                                </>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

export default ArqueoCaja;
