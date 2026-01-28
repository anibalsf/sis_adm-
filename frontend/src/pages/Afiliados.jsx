import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import api from '../services/api';
import SkeletonLoader from '../components/SkeletonLoader';
import './Afiliados.css';
import '../styles/action-buttons.css';
import { IconEye, IconPencil, IconTrash } from '../components/Icons';
import { useToast } from '../context/ToastContext';

function Afiliados() {
  const toast = useToast();
  const [afiliados, setAfiliados] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filtroEstado, setFiltroEstado] = useState('');
  const [ciTerm, setCiTerm] = useState('');
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [totalCount, setTotalCount] = useState(0);
  const [showModal, setShowModal] = useState(false);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [modalMode, setModalMode] = useState('create');
  const [selectedAfiliado, setSelectedAfiliado] = useState(null);
  const [vehiculosAfiliado, setVehiculosAfiliado] = useState([]);
  const [formData, setFormData] = useState({
    nombres: '',
    apellidos: '',
    ci: '',
    telefono: '',
    direccion: '',
    estado: 'activo',
    fecha_ingreso: '',
  });
  const [formErrors, setFormErrors] = useState({});
  const [submitError, setSubmitError] = useState('');
  const [searchParams] = useSearchParams();

  useEffect(() => {
    fetchAfiliados();
  }, [searchTerm, filtroEstado, ciTerm, page, pageSize]);

  const fetchAfiliados = async () => {
    try {
      setLoading(true);
      const params = { page, page_size: pageSize };
      if (searchTerm) params.search = searchTerm;
      if (filtroEstado) params.estado = filtroEstado;
      if (ciTerm) params.ci = ciTerm;

      const response = await api.getAfiliados(params);
      const list = response.data?.results || response.data || [];
      setAfiliados(list);
      setTotalCount(response.data?.count ?? (Array.isArray(list) ? list.length : 0));
      setError(null);
    } catch (err) {
      setError('Error al cargar afiliados');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setModalMode('create');
    setFormData({
      nombres: '',
      apellidos: '',
      ci: '',
      telefono: '',
      direccion: '',
      estado: 'activo',
      fecha_ingreso: new Date().toISOString().split('T')[0],
    });
    setFormErrors({});
    setShowModal(true);
  };

  const handleEdit = (afiliado) => {
    setModalMode('edit');
    setSelectedAfiliado(afiliado);
    setFormData({
      nombres: afiliado.nombres || '',
      apellidos: afiliado.apellidos || '',
      ci: afiliado.ci || '',
      telefono: afiliado.telefono || '',
      direccion: afiliado.direccion || '',
      estado: afiliado.estado || 'activo',
      fecha_ingreso: afiliado.fecha_ingreso || '',
    });
    setFormErrors({});
    setShowModal(true);
  };

  const handleViewDetails = async (afiliado) => {
    setSelectedAfiliado(afiliado);
    setShowDetailModal(true);
    try {
      const response = await api.getVehiculos({ afiliado: afiliado.id });
      setVehiculosAfiliado(response.data?.results || response.data || []);
    } catch (err) {
      console.error('Error al cargar vehículos:', err);
      setVehiculosAfiliado([]);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      setSubmitError('');
      if (modalMode === 'create') {
        await api.createAfiliado(formData);
        toast.success('Afiliado creado exitosamente');
      } else {
        await api.updateAfiliado(selectedAfiliado.id, formData);
        toast.success('Afiliado actualizado correctamente');
      }
      setShowModal(false);
      fetchAfiliados();
    } catch (err) {
      console.error('Error in handleSubmit:', err);
      const errorMsg = err.response?.data?.detail ||
        Object.values(err.response?.data || {}).flat()[0] ||
        'Error al guardar afiliado';
      setSubmitError(String(errorMsg));
      toast.error(String(errorMsg));
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('¿Está seguro de eliminar este afiliado?')) return;
    try {
      await api.deleteAfiliado(id);
      toast.success('Afiliado eliminado correctamente');
      fetchAfiliados();
    } catch (err) {
      toast.error('Error al intentar eliminar el afiliado');
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    if (formErrors[name]) setFormErrors(prev => ({ ...prev, [name]: '' }));
  };

  return (
    <div className="afiliados-container">
      <div className="page-header">
        <h1>Gestión de Afiliados</h1>
        <div className="header-buttons">
          <button className="btn btn-success" onClick={() => api.downloadAfiliadosExcel()}>
            📥 Descargar Excel
          </button>
          <button className="btn btn-primary" onClick={handleCreate}>
            + Nuevo Afiliado
          </button>
        </div>

      </div>

      <div className="filters-section">
        <div className="filter-group">
          <input
            type="text"
            placeholder="Buscar nombre..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="search-input"
          />
        </div>
        <div className="filter-group">
          <input
            type="text"
            placeholder="Filtrar por CI..."
            value={ciTerm}
            onChange={(e) => setCiTerm(e.target.value)}
            className="search-input"
          />
        </div>
        <div className="filter-group">
          <select value={filtroEstado} onChange={(e) => setFiltroEstado(e.target.value)}>
            <option value="">Todos los estados</option>
            <option value="activo">Activo</option>
            <option value="pasivo">Pasivo</option>
            <option value="sancionado">Sancionado</option>
          </select>
        </div>
      </div>

      <div className="table-container">
        <table className="afiliados-table">
          <thead>
            <tr>
              <th>Nombre Completo</th>
              <th>CI</th>
              <th>Teléfono</th>
              <th>Estado</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              Array.from({ length: pageSize }).map((_, i) => (
                <tr key={`skeleton-${i}`}>
                  <td colSpan="5"><SkeletonLoader type="table-row" /></td>
                </tr>
              ))
            ) : (
              afiliados.map((afiliado) => (
                <tr key={afiliado.id}>
                  <td>{afiliado.apellidos} {afiliado.nombres}</td>
                  <td>{afiliado.ci}</td>
                  <td>{afiliado.telefono || '-'}</td>
                  <td>
                    <span className={`badge badge-${afiliado.estado}`}>
                      {afiliado.estado}
                    </span>
                  </td>
                  <td className="actions">
                    <button
                      className="btn-icon btn-view"
                      onClick={() => handleViewDetails(afiliado)}
                      data-tooltip="Ver detalles"
                      title="Ver detalles"
                    >
                      <IconEye />
                    </button>
                    <button
                      className="btn-icon btn-edit"
                      onClick={() => handleEdit(afiliado)}
                      data-tooltip="Editar"
                      title="Editar"
                    >
                      <IconPencil />
                    </button>
                    <button
                      className="btn-icon btn-delete"
                      onClick={() => handleDelete(afiliado.id)}
                      data-tooltip="Eliminar"
                      title="Eliminar"
                    >
                      <IconTrash />
                    </button>
                  </td>
                </tr>
              ))
            )}
            {!loading && afiliados.length === 0 && (
              <tr>
                <td colSpan="5" className="no-data">No se encontraron afiliados</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="pagination">
        <button disabled={page <= 1} onClick={() => setPage(p => p - 1)}>Anterior</button>
        <span>Página {page} de {Math.ceil(totalCount / pageSize)}</span>
        <button disabled={page * pageSize >= totalCount} onClick={() => setPage(p => p + 1)}>Siguiente</button>
      </div>

      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <h2>{modalMode === 'create' ? 'Nuevo Registro' : 'Editar Afiliado'}</h2>
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label>Nombres</label>
                <input
                  name="nombres"
                  value={formData.nombres}
                  onChange={handleInputChange}
                  className={formErrors.nombres ? 'error' : ''}
                  required
                />
              </div>
              <div className="form-group">
                <label>Apellidos</label>
                <input
                  name="apellidos"
                  value={formData.apellidos}
                  onChange={handleInputChange}
                  className={formErrors.apellidos ? 'error' : ''}
                  required
                />
              </div>
              <div className="form-group">
                <label>CI</label>
                <input
                  name="ci"
                  value={formData.ci}
                  onChange={handleInputChange}
                  className={formErrors.ci ? 'error' : ''}
                  required
                />
              </div>

              <div className="form-group">
                <label>Teléfono</label>
                <input name="telefono" value={formData.telefono} onChange={handleInputChange} />
              </div>
              <div className="form-group">
                <label>Fecha de Ingreso</label>
                <input type="date" name="fecha_ingreso" value={formData.fecha_ingreso} onChange={handleInputChange} />
              </div>
              <div className="form-group">
                <label>Estado</label>
                <select name="estado" value={formData.estado} onChange={handleInputChange}>
                  <option value="activo">Activo</option>
                  <option value="pasivo">Pasivo</option>
                  <option value="sancionado">Sancionado</option>
                </select>
              </div>

              {submitError && (
                <div className="error-message" style={{ color: 'red', marginTop: '10px', textAlign: 'center' }}>
                  {submitError}
                </div>
              )}

              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>Cancelar</button>
                <button type="submit" className="btn btn-primary">Guardar</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {showDetailModal && selectedAfiliado && (
        <div className="modal-overlay" onClick={() => setShowDetailModal(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <h2>Detalles del Afiliado</h2>
            <div className="details-grid">
              <p><strong>Nombres:</strong> {selectedAfiliado.nombres}</p>
              <p><strong>Apellidos:</strong> {selectedAfiliado.apellidos}</p>
              <p><strong>CI:</strong> {selectedAfiliado.ci}</p>
              <p><strong>Estado:</strong> {selectedAfiliado.estado}</p>
            </div>
            <h3>Vehículos</h3>
            <ul>
              {vehiculosAfiliado.map(v => <li key={v.id}>{v.placa} - {v.tipo}</li>)}
              {vehiculosAfiliado.length === 0 && <li>Sin vehículos asociados</li>}
            </ul>
            <button onClick={() => setShowDetailModal(false)}>Cerrar</button>
          </div>
        </div>
      )}
    </div>
  );
}

export default Afiliados;
