import { useEffect, useState } from 'react'
import { api } from '../services/api'
import './Afiliados.css'
import { IconPencil, IconTrash } from '../components/Icons'

function Directorio() {
  const [items, setItems] = useState([])
  const [afiliados, setAfiliados] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [filtroCargo, setFiltroCargo] = useState('')
  const [soloActivos, setSoloActivos] = useState(true)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)
  const [totalCount, setTotalCount] = useState(0)
  const [showModal, setShowModal] = useState(false)
  const [modalMode, setModalMode] = useState('create')
  const [submitError, setSubmitError] = useState('')
  const [fieldErrors, setFieldErrors] = useState({})
  const [form, setForm] = useState({ afiliado: '', cargo: '', fecha_inicio: '', fecha_fin: '', estado: 'activo' })
  const [editingId, setEditingId] = useState(null)

  useEffect(() => { load() }, [search, filtroCargo, soloActivos, page, pageSize])

  const load = async () => {
    try {
      setLoading(true)
      const params = { page, page_size: pageSize }
      if (search) params.search = search
      if (filtroCargo) params.cargo = filtroCargo
      if (soloActivos) params.activo = 'true'
      const res = await api.getDirectorio(params)
      const list = res.data?.results || res.data || []
      setItems(list)
      setTotalCount(res.data?.count ?? (Array.isArray(list) ? list.length : 0))
      const afRes = await api.getAfiliados({ page_size: 200, ordering: 'apellidos' })
      setAfiliados(afRes.data?.results || afRes.data || [])
      setError('')
    } catch (err) { setError('Error al cargar directorio'); console.error(err) }
    finally { setLoading(false) }
  }

  const openCreate = () => {
    setModalMode('create')
    setForm({ afiliado: '', cargo: '', fecha_inicio: '', fecha_fin: '', estado: 'activo' })
    setSubmitError('')
    setFieldErrors({})
    setShowModal(true)
  }

  const openEdit = (it) => {
    setModalMode('edit')
    setForm({ afiliado: it.afiliado || it.afiliado_id || '', cargo: it.cargo || '', fecha_inicio: it.fecha_inicio || '', fecha_fin: it.fecha_fin || '', estado: it.estado || 'activo' })
    setSubmitError('')
    setFieldErrors({})
    setShowModal(true)
    setEditingId(it.id)
  }

  const onChange = (e) => { const { name, value } = e.target; setForm(prev => ({ ...prev, [name]: value })) }

  const save = async (e) => {
    e.preventDefault()
    try {
      setSubmitError('')
      setFieldErrors({})
      const payload = { afiliado: form.afiliado || null, cargo: form.cargo, fecha_inicio: form.fecha_inicio, fecha_fin: form.fecha_fin || null, estado: form.estado }
      if (modalMode === 'create') await api.createMiembroDirectorio(payload)
      else await api.updateMiembroDirectorio(editingId, payload)
      setShowModal(false)
      await load()
    } catch (err) {
      const data = err.response?.data
      if (data && typeof data === 'object') {
        setFieldErrors(data)
        setSubmitError(data.detail || data.non_field_errors?.[0] || '')
      } else setSubmitError('Error al guardar')
      console.error(err)
    }
  }

  const remove = async (id) => { if (!window.confirm('¿Eliminar registro?')) return; try { await api.deleteMiembroDirectorio(id); await load() } catch (err) { alert('Error al eliminar'); console.error(err) } }

  return (
    <div className="afiliados-container">
      <div className="page-header">
        <h1>Gestión de Directorio</h1>
      </div>

      <div className="filters-section">
        <div className="search-box">
          <input className="search-input" type="text" placeholder="Buscar por CI o nombre" value={search} onChange={e => setSearch(e.target.value)} />
        </div>
        <div className="filter-box">
          <button className="btn btn-primary" onClick={openCreate}>
            <span className="icon">+</span> Nuevo Registro
          </button>
        </div>
        <div className="filter-box">
          <button className="btn btn-secondary" onClick={async () => {
            const result = await api.downloadDirectorioReporte();
            if (!result.success) {
              setError(result.error);
            }
          }}>
            📄 Reporte
          </button>
        </div>
        <div className="filter-box">
          <select className="filter-select" value={filtroCargo} onChange={e => { setFiltroCargo(e.target.value); setPage(1) }}>
            <option value="">Todos los cargos</option>
            <option value="secretario_general">Secretario General</option>
            <option value="secretario_relaciones">Secretario de Relaciones</option>
            <option value="secretario_hacienda">Secretario de Hacienda</option>
            <option value="secretario_actas">Secretario de Actas</option>
            <option value="secretario_conflictos">Secretario de Conflictos</option>
            <option value="secretario_deportes">Secretario de Deportes</option>
            <option value="vocal">Vocal</option>
          </select>
        </div>
        <div className="filter-box">
          <label style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <input type="checkbox" checked={soloActivos} onChange={e => { setSoloActivos(e.target.checked); setPage(1) }} /> Solo activos
          </label>
        </div>
        <div className="filter-box">
          <input className="search-input" type="number" min="1" value={pageSize} onChange={e => { setPageSize(parseInt(e.target.value || '10', 10)); setPage(1) }} />
        </div>
      </div>

      {loading ? (<div className="loading">Cargando...</div>) : error ? (<div className="error">{error}</div>) : (
        <div className="table-container">
          <table className="vehiculos-table">
            <thead>
              <tr>
                <th>Afiliado</th>
                <th>Cargo</th>
                <th>Inicio</th>
                <th>Fin</th>
                <th>Estado</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {items.length === 0 ? (
                <tr><td colSpan="6" className="no-data">Sin registros</td></tr>
              ) : items.map(it => (
                <tr key={it.id}>
                  <td>{it.afiliado_nombre || it.afiliado || '-'}</td>
                  <td>{it.cargo_label || it.cargo}</td>
                  <td>{it.fecha_inicio}</td>
                  <td>{it.fecha_fin || '-'}</td>
                  <td><span className={`badge badge-${it.estado || 'activo'}`}>{it.estado_label || it.estado || 'activo'}</span></td>
                  <td className="actions">
                    <td className="actions">
                      <button className="btn-icon btn-edit" onClick={() => openEdit(it)} title="Editar"><IconPencil /></button>
                      <button className="btn-icon btn-delete" onClick={() => remove(it.id)} title="Eliminar"><IconTrash /></button>
                    </td>
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
              <h2>{modalMode === 'create' ? 'Nuevo Registro' : 'Editar Miembro'}</h2>
              <button className="modal-close" onClick={() => setShowModal(false)}>✕</button>
            </div>
            {submitError && <div className="error" style={{ marginBottom: '10px' }}>{submitError}</div>}
            <form onSubmit={save} className="afiliado-form">
              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="afiliado">Afiliado *</label>
                  <select id="afiliado" name="afiliado" value={form.afiliado} onChange={onChange}>
                    <option value="">Selecciona...</option>
                    {afiliados.map(a => (
                      <option key={a.id} value={a.id}>{a.apellidos} {a.nombres}</option>
                    ))}
                  </select>
                  {fieldErrors.afiliado && <div className="error">{Array.isArray(fieldErrors.afiliado) ? fieldErrors.afiliado[0] : String(fieldErrors.afiliado)}</div>}
                </div>
                <div className="form-group">
                  <label htmlFor="cargo">Cargo *</label>
                  <select id="cargo" name="cargo" value={form.cargo} onChange={onChange}>
                    <option value="">Selecciona...</option>
                    <option value="secretario_general">Secretario General</option>
                    <option value="secretario_relaciones">Secretario de Relaciones</option>
                    <option value="secretario_hacienda">Secretario de Hacienda</option>
                    <option value="secretario_actas">Secretario de Actas</option>
                    <option value="secretario_conflictos">Secretario de Conflictos</option>
                    <option value="secretario_deportes">Secretario de Deportes</option>
                    <option value="vocal">Vocal</option>
                  </select>
                  {fieldErrors.cargo && <div className="error">{Array.isArray(fieldErrors.cargo) ? fieldErrors.cargo[0] : String(fieldErrors.cargo)}</div>}
                </div>
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="fecha_inicio">Inicio *</label>
                  <input id="fecha_inicio" name="fecha_inicio" type="date" value={form.fecha_inicio} onChange={onChange} />
                  {fieldErrors.fecha_inicio && <div className="error">{Array.isArray(fieldErrors.fecha_inicio) ? fieldErrors.fecha_inicio[0] : String(fieldErrors.fecha_inicio)}</div>}
                </div>
                <div className="form-group">
                  <label htmlFor="fecha_fin">Fin</label>
                  <input id="fecha_fin" name="fecha_fin" type="date" value={form.fecha_fin} onChange={onChange} />
                  {fieldErrors.fecha_fin && <div className="error">{Array.isArray(fieldErrors.fecha_fin) ? fieldErrors.fecha_fin[0] : String(fieldErrors.fecha_fin)}</div>}
                </div>
              </div>
              <div className="form-group">
                <label htmlFor="estado">Estado</label>
                <select id="estado" name="estado" value={form.estado} onChange={onChange}>
                  <option value="activo">Activo</option>
                  <option value="concluido">Concluido</option>
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

export default Directorio