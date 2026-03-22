import React, { useState, useEffect, useCallback } from 'react';
import api from '../services/api';
import './LibroActas.css';
import { IconSearch, IconCalendar, IconEye, IconEdit, IconBook, IconFileText, IconCheckCircle } from '../components/Icons';

function LibroActas() {
    const [reuniones, setReuniones] = useState([]);
    const [loading, setLoading] = useState(false);
    const [page, setPage] = useState(1);
    const [searchTerm, setSearchTerm] = useState('');
    const [dateFrom, setDateFrom] = useState('');
    const [dateTo, setDateTo] = useState('');

    const [selectedActa, setSelectedActa] = useState(null);
    const [isEditMode, setIsEditMode] = useState(false);
    const [showModal, setShowModal] = useState(false);
    const [formData, setFormData] = useState({
        acta_texto: '',
        acuerdos: '',
        documento_adjunto: ''
    });

    const loadActas = useCallback(async () => {
        setLoading(true);
        try {
            const params = {
                page,
                search: searchTerm,
                ordering: '-fecha',
                // El backend de Django permite filtrar por fecha si el viewset está configurado,
                // si no lo está, lo filtraremos en el frontend o lo dejaremos como search básico.
            };
            const res = await api.getReuniones(params);
            setReuniones(res.data.results || res.data);
        } catch (error) {
            console.error('Error al cargar actas:', error);
        } finally {
            setLoading(false);
        }
    }, [page, searchTerm]);

    useEffect(() => {
        loadActas();
    }, [loadActas]);

    const openActaModal = (acta, edit = false) => {
        setSelectedActa(acta);
        setIsEditMode(edit);
        setFormData({
            acta_texto: acta.acta_texto || '',
            acuerdos: acta.acuerdos || '',
            documento_adjunto: acta.documento_adjunto || ''
        });
        setShowModal(true);
    };

    const handleSaveActa = async () => {
        if (!selectedActa) return;

        setLoading(true);
        try {
            await api.updateReunion(selectedActa.id, {
                ...selectedActa,
                ...formData
            });
            setShowModal(false);
            loadActas();
            alert('Acta actualizada correctamente');
        } catch (error) {
            console.error('Error al guardar acta:', error);
            alert('Error al guardar los cambios');
        } finally {
            setLoading(false);
        }
    };

    const filteredReuniones = reuniones.filter(r => {
        if (!dateFrom && !dateTo) return true;
        const rDate = new Date(r.fecha);
        const from = dateFrom ? new Date(dateFrom) : null;
        const to = dateTo ? new Date(dateTo) : null;

        if (from && rDate < from) return false;
        if (to && rDate > to) return false;
        return true;
    });

    return (
        <div className="libro-actas-container">
            <div className="page-header">
                <h1>Libro de Actas Digital</h1>
                <p>Gestiona y busca los acuerdos oficiales del sindicato</p>
            </div>

            <div className="search-filters">
                <div className="search-group">
                    <div style={{ position: 'relative' }}>
                        <div style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', opacity: 0.5 }}>
                            <IconSearch />
                        </div>
                        <input
                            type="text"
                            placeholder="Buscar en temas o acuerdos..."
                            className="filter-input"
                            style={{ paddingLeft: '40px' }}
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                        />
                    </div>
                </div>

                <div className="date-group">
                    <div className="filter-item">
                        <label style={{ display: 'block', fontSize: '0.8rem', marginBottom: '4px', fontWeight: 600 }}>Desde:</label>
                        <input
                            type="date"
                            className="filter-input"
                            value={dateFrom}
                            onChange={(e) => setDateFrom(e.target.value)}
                        />
                    </div>
                    <div className="filter-item">
                        <label style={{ display: 'block', fontSize: '0.8rem', marginBottom: '4px', fontWeight: 600 }}>Hasta:</label>
                        <input
                            type="date"
                            className="filter-input"
                            value={dateTo}
                            onChange={(e) => setDateTo(e.target.value)}
                        />
                    </div>
                </div>

                <button className="btn-detail" style={{ height: '45px', alignSelf: 'flex-end' }} onClick={loadActas}>
                    Actualizar
                </button>
            </div>

            {loading && !showModal ? (
                <div style={{ textAlign: 'center', padding: '3rem' }}>Cargando actas...</div>
            ) : (
                <div className="actas-grid">
                    {filteredReuniones.map(r => (
                        <div key={r.id} className="acta-card">
                            <div className="acta-header">
                                <div>
                                    <span className="acta-fecha">{new Date(r.fecha).toLocaleDateString('es-ES', { day: 'numeric', month: 'long', year: 'numeric' })}</span>
                                    <h2 className="acta-tema">{r.tema}</h2>
                                </div>
                                <span className="acta-tipo">{r.tipo}</span>
                            </div>

                            <div className="acta-acuerdos-preview">
                                <strong>Acuerdos:</strong><br />
                                {r.acuerdos || 'No se han registrado acuerdos específicos aún.'}
                            </div>

                            <div className="acta-footer">
                                <div style={{ display: 'flex', gap: '8px', alignItems: 'center', color: '#64748b', fontSize: '0.85rem' }}>
                                    <IconFileText />
                                    <span>{r.acta_texto ? 'Acta redactada' : 'Pendiente de redactar'}</span>
                                </div>
                                <div style={{ display: 'flex', gap: '10px' }}>
                                    <button className="btn-detail" style={{ background: 'transparent', color: '#6366f1', border: '1px solid #6366f1' }} onClick={() => openActaModal(r, true)}>
                                        <IconEdit />
                                    </button>
                                    <button className="btn-detail" onClick={() => openActaModal(r, false)}>
                                        <IconEye /> Ver Detalle
                                    </button>
                                </div>
                            </div>
                        </div>
                    ))}

                    {filteredReuniones.length === 0 && (
                        <div style={{ gridColumn: '1 / -1', textAlign: 'center', padding: '4rem', background: 'rgba(255,255,255,0.1)', borderRadius: '20px' }}>
                            <IconBook style={{ fontSize: '3rem', opacity: 0.2, marginBottom: '1rem' }} />
                            <h3>No se encontraron actas con los filtros actuales</h3>
                            <p>Prueba buscando en otro rango de fechas o con otros términos.</p>
                        </div>
                    )}
                </div>
            )}

            {/* Modal de Detalle/Edición */}
            {showModal && (
                <div className="modal-overlay" onClick={() => setShowModal(false)}>
                    <div className="modal-content modal-acta-full" onClick={e => e.stopPropagation()}>
                        <div className="modal-header">
                            <div>
                                <h2 style={{ margin: 0 }}>{isEditMode ? 'Editar Acta de Reunión' : 'Detalle de Acta'}</h2>
                                <p style={{ color: '#64748b', margin: '4px 0 0 0' }}>{selectedActa?.tema} - {selectedActa?.fecha}</p>
                            </div>
                            <button className="modal-close" onClick={() => setShowModal(false)}>✕</button>
                        </div>

                        <div className="acta-editor-grid" style={{ padding: '1.5rem', maxHeight: '70vh', overflowY: 'auto' }}>
                            <div className="acta-section">
                                <label><IconCheckCircle style={{ color: '#10b981' }} /> Acuerdos y Decisiones Finales</label>
                                {isEditMode ? (
                                    <textarea
                                        className="acta-textarea acuerdos-textarea"
                                        placeholder="Escribe aquí los puntos que se decidieron..."
                                        value={formData.acuerdos}
                                        onChange={(e) => setFormData({ ...formData, acuerdos: e.target.value })}
                                    />
                                ) : (
                                    <div className="acta-textarea acuerdos-textarea" style={{ minHeight: 'auto', background: 'rgba(16, 185, 129, 0.05)' }}>
                                        {formData.acuerdos || 'Sin acuerdos registrados.'}
                                    </div>
                                )}
                            </div>

                            <div className="acta-section" style={{ marginTop: '1rem' }}>
                                <label><IconFileText /> Contenido Detallado del Acta</label>
                                {isEditMode ? (
                                    <textarea
                                        className="acta-textarea"
                                        placeholder="Describe el desarrollo de la reunión, intervenciones, debates, etc..."
                                        value={formData.acta_texto}
                                        onChange={(e) => setFormData({ ...formData, acta_texto: e.target.value })}
                                    />
                                ) : (
                                    <div className="acta-textarea">
                                        {formData.acta_texto || 'No se ha redactado el contenido del acta aún.'}
                                    </div>
                                )}
                            </div>

                            {isEditMode && (
                                <div className="acta-section">
                                    <label>Link a Documento Escaneado (Opcional)</label>
                                    <input
                                        type="text"
                                        className="filter-input"
                                        placeholder="URL del documento en la nube..."
                                        value={formData.documento_adjunto}
                                        onChange={(e) => setFormData({ ...formData, documento_adjunto: e.target.value })}
                                    />
                                </div>
                            )}
                        </div>

                        <div className="modal-footer" style={{ padding: '1.5rem', borderTop: '1px solid #e2e8f0', display: 'flex', justifyContent: 'flex-end', gap: '1rem' }}>
                            <button className="btn-detail" style={{ background: 'transparent', color: '#64748b', border: '1px solid #e2e8f0' }} onClick={() => setShowModal(false)}>
                                Cerrar
                            </button>
                            {isEditMode && (
                                <button className="btn-detail" onClick={handleSaveActa} disabled={loading}>
                                    {loading ? 'Guardando...' : 'Guardar Acta'}
                                </button>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

export default LibroActas;
