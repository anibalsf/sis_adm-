import { useEffect, useState } from 'react'
import { api } from '../services/api'
import { SkeletonTable } from '../components/Skeleton/Skeleton'
import './Afiliados.css'
import { IconPencil, IconTrash } from '../components/Icons'
import { useToast } from '../context/ToastContext'

function Vehiculos() {
  const toast = useToast()
  const [vehiculos, setVehiculos] = useState([])
  const [afiliados, setAfiliados] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [filtroEstado, setFiltroEstado] = useState('')
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)
  const [totalCount, setTotalCount] = useState(0)
  const [showModal, setShowModal] = useState(false)
  const [modalMode, setModalMode] = useState('create')
  const [submitError, setSubmitError] = useState('')
  const [fieldErrors, setFieldErrors] = useState({})
  const [form, setForm] = useState({ placa: '', tipo: '', capacidad: '', estado: 'activo', afiliado: '' })
  const [editingId, setEditingId] = useState(null)

  useEffect(() => { load() }, [search, filtroEstado, page, pageSize])

  const load = async () => {
    try {
      setLoading(true)
      const params = { page, page_size: pageSize }
      if (search) params.search = search
      if (filtroEstado) params.estado = filtroEstado
      const res = await api.getVehiculos(params)
      const list = res.data?.results || res.data || []
      setVehiculos(list)
      setTotalCount(res.data?.count ?? (Array.isArray(list) ? list.length : 0))
      const afRes = await api.getAfiliados({ page_size: 100, ordering: 'apellidos' })
      setAfiliados(afRes.data?.results || afRes.data || [])
      setError('')
    } catch (err) {
      setError('Error al cargar vehículos')
      toast.error('Error al cargar la lista de vehículos')
      console.error(err)
    } finally { setLoading(false) }
  }

  const openCreate = () => {
    setModalMode('create')
    setForm({ placa: '', tipo: '', capacidad: '', estado: 'activo', afiliado: '' })
    setSubmitError('')
    setFieldErrors({})
    setShowModal(true)
  }

  const openEdit = (v) => {
    setModalMode('edit')
    setForm({ placa: v.placa || '', tipo: v.tipo || '', capacidad: String(v.capacidad || ''), estado: v.estado || 'activo', afiliado: v.afiliado || v.afiliado_id || '' })
    setSubmitError('')
    setFieldErrors({})
    setEditingId(v.id)
    setShowModal(true)
  }

  const onChange = (e) => {
    const { name, value } = e.target
    setForm(prev => ({ ...prev, [name]: value }))
  }

  const save = async (e) => {
    e.preventDefault()
    try {
      setSubmitError('')
      setFieldErrors({})
      const payload = { placa: form.placa, tipo: form.tipo, capacidad: parseInt(form.capacidad || '0', 10), estado: form.estado, afiliado: form.afiliado || null }
      if (modalMode === 'create') {
        await api.createVehiculo(payload)
        toast.success('Vehículo registrado correctamente')
      } else {
        await api.updateVehiculo(editingId, payload)
        toast.success('Vehículo actualizado correctamente')
      }
      setShowModal(false)
      await load()
    } catch (err) {
      const data = err.response?.data
      if (data && typeof data === 'object') {
        setFieldErrors(data)
        const msg = data.detail || data.non_field_errors?.[0] || 'Error al guardar vehículo'
        setSubmitError(String(msg))
        toast.error(String(msg))
      } else {
        setSubmitError('Error al guardar vehículo')
        toast.error('Error de conexión al guardar')
      }
      console.error(err)
    }
  }

  const remove = async (id) => {
    if (!window.confirm('¿Eliminar vehículo?')) return
    try {
      await api.deleteVehiculo(id)
      toast.success('Vehículo eliminado')
      await load()
    } catch (err) {
      toast.error('Error al intentar eliminar el vehículo')
      console.error(err)
    }
  }

  return (
    <div className="afiliados-container">
      <div className="page-header">
        <h1>Gestión de Vehículos</h1>
      </div>

      <div className="filters-section">
        <div className="search-box">
          <input className="search-input" type="text" placeholder="Buscar por placa, tipo, CI afiliado" value={search} onChange={e => setSearch(e.target.value)} />
        </div>
        <div className="filter-box">
          <button className="btn btn-primary" onClick={openCreate}>
            <span className="icon">+</span> Nuevo Registro
          </button>
        </div>
        <div className="filter-box">
          <button className="btn btn-success" onClick={() => api.downloadVehiculosExcel()}>
            📥 Descargar Excel
          </button>
        </div>
        <div className="filter-box">
          <button className="btn btn-secondary" onClick={async () => {

            const result = await api.downloadVehiculosReporte();
            if (!result.success) {
              setError(result.error);
            }
          }}>
            📄 Reporte
          </button>
        </div>
        <div className="filter-box">
          <select className="filter-select" value={filtroEstado} onChange={e => { setFiltroEstado(e.target.value); setPage(1) }}>
            <option value="">Todos</option>
            <option value="activo">Activo</option>
            <option value="inactivo">Inactivo</option>
          </select>
        </div>
        <div className="filter-box">
          <input className="search-input" type="number" min="1" value={pageSize} onChange={e => { setPageSize(parseInt(e.target.value || '10', 10)); setPage(1) }} />
        </div>
      </div>

      {loading ? (
        <SkeletonTable rows={pageSize} columns={6} />
      ) : error ? (
        <div className="error">{error}</div>
      ) : (
        <div className="table-container">
          <table className="vehiculos-table">
            <thead>
              <tr>
                <th>Placa</th>
                <th>Tipo</th>
                <th>Capacidad</th>
                <th>Afiliado</th>
                <th>Estado</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {vehiculos.length === 0 ? (
                <tr><td colSpan="6" className="no-data">Sin vehículos</td></tr>
              ) : vehiculos.map(v => (
                <tr key={v.id}>
                  <td>{v.placa}</td>
                  <td>{v.tipo}</td>
                  <td>{v.capacidad}</td>
                  <td>{v.afiliado_nombre || v.afiliado || '-'}</td>
                  <td><span className={`badge badge-${v.estado || 'activo'}`}>{v.estado || 'activo'}</span></td>
                  <td className="actions">
                    <button className="btn-icon btn-edit" onClick={() => openEdit(v)} title="Editar"><IconPencil /></button>
                    <button className="btn-icon btn-delete" onClick={() => remove(v.id)} title="Eliminar"><IconTrash /></button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div style={{ display: 'flex', gap: '10px', alignItems: 'center', marginTop: '12px' }}>
        <button className="btn btn-secondary" disabled={page <= 1} onClick={() => setPage(p => Math.max(1, p - 1))}>Anterior</button>
        <span>Página {page}</span>
        <button className="btn btn-secondary" disabled={page * pageSize >= totalCount} onClick={() => setPage(p => p + 1)}>Siguiente</button>
        <span>Total {totalCount}</span>
      </div>

      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>{modalMode === 'create' ? 'Nuevo Registro' : 'Editar Vehículo'}</h2>
              <button className="modal-close" onClick={() => setShowModal(false)}>✕</button>
            </div>
            {submitError && <div className="error" style={{ marginBottom: '10px' }}>{submitError}</div>}
            <form onSubmit={save} className="afiliado-form">
              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="placa">Placa *</label>
                  <input
                    id="placa"
                    name="placa"
                    type="text"
                    value={form.placa}
                    onChange={onChange}
                    className={fieldErrors.placa ? 'error' : ''}
                  />
                  {fieldErrors.placa && <div className="error-message">{Array.isArray(fieldErrors.placa) ? fieldErrors.placa[0] : String(fieldErrors.placa)}</div>}
                </div>
                <div className="form-group">
                  <label htmlFor="tipo">Tipo *</label>
                  <select
                    id="tipo"
                    name="tipo"
                    value={form.tipo}
                    onChange={onChange}
                    className={fieldErrors.tipo ? 'error' : ''}
                  >

                    <option value="">Selecciona...</option>
                    <option value="minibus">Minibus</option>
                    <option value="ipsum">Ipsum</option>
                    <option value="micro">Micro</option>
                    <option value="bus">Bus</option>
                    <option value="taxi">Taxi</option>
                    <option value="camioneta">Camioneta</option>
                    <option value="camion">Camión</option>
                    <option value="trufi">Trufi</option>
                    <option value="coaster">Coaster</option>
                    <option value="vagoneta">Vagoneta</option>
                    <option value="otros">Otros</option>
                  </select>
                  {fieldErrors.tipo && <div className="error">{Array.isArray(fieldErrors.tipo) ? fieldErrors.tipo[0] : String(fieldErrors.tipo)}</div>}
                </div>
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="capacidad">Capacidad *</label>
                  <input
                    id="capacidad"
                    name="capacidad"
                    type="number"
                    value={form.capacidad}
                    onChange={onChange}
                    className={fieldErrors.capacidad ? 'error' : ''}
                  />
                  {fieldErrors.capacidad && <div className="error-message">{Array.isArray(fieldErrors.capacidad) ? fieldErrors.capacidad[0] : String(fieldErrors.capacidad)}</div>}
                </div>

                <div className="form-group">
                  <label htmlFor="afiliado">Afiliado</label>
                  <select id="afiliado" name="afiliado" value={form.afiliado} onChange={onChange}>
                    <option value="">Sin afiliado</option>
                    {afiliados.map(a => (
                      <option key={a.id} value={a.id}>{a.apellidos} {a.nombres}</option>
                    ))}
                  </select>
                  {fieldErrors.afiliado && <div className="error">{Array.isArray(fieldErrors.afiliado) ? fieldErrors.afiliado[0] : String(fieldErrors.afiliado)}</div>}
                </div>
              </div>
              <div className="form-group">
                <label htmlFor="estado">Estado</label>
                <select id="estado" name="estado" value={form.estado} onChange={onChange}>
                  <option value="activo">Activo</option>
                  <option value="inactivo">Inactivo</option>
                </select>
                {fieldErrors.estado && <div className="error">{Array.isArray(fieldErrors.estado) ? fieldErrors.estado[0] : String(fieldErrors.estado)}</div>}
              </div>
              <div className="form-actions">
                <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>Cancelar</button>
                <button type="submit" className="btn btn-primary">{modalMode === 'create' ? 'Crear' : 'Guardar'}</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default Vehiculos