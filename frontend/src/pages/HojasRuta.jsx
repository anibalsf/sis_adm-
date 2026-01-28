import { useEffect, useState, useCallback } from 'react'
import { api } from '../services/api'
import { useNavigate } from 'react-router-dom'
import SancionesAlert from '../components/SancionesAlert'
import '../css/Common.css'
import { IconPencil, IconFile, IconBus, IconPrinter, IconWhatsApp, IconTrash } from '../components/Icons'

function HojasRuta() {
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState('agentes') // 'agentes' | 'designaciones' | 'asignacion-la-paz'

  // Estados para Designaciones (Hojas de Ruta)
  const [items, setItems] = useState([])
  const [afiliados, setAfiliados] = useState([])
  const [vehiculos, setVehiculos] = useState([])
  const [rutas, setRutas] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [filtroRuta, setFiltroRuta] = useState('')
  const [desde, setDesde] = useState('')
  const [hasta, setHasta] = useState('')
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)
  const [totalCount, setTotalCount] = useState(0)
  const [showModal, setShowModal] = useState(false)
  const [modalMode, setModalMode] = useState('create')
  const [submitError, setSubmitError] = useState('')
  const [fieldErrors, setFieldErrors] = useState({})
  const [form, setForm] = useState({ nro: '', fecha_emision: '', fecha_salida: '', afiliado: '', vehiculo: '', ruta: '', agente_parada: '', precio: '' })
  const [editingId, setEditingId] = useState(null)

  // Estados para Listado de Agentes (Afiliados)
  const [listaAgentes, setListaAgentes] = useState([])
  const [loadingAgentes, setLoadingAgentes] = useState(false)
  const [searchAgentes, setSearchAgentes] = useState('')
  const [pageAgentes, setPageAgentes] = useState(1)
  const [totalAgentes, setTotalAgentes] = useState(0)

  // Sanciones Alert State
  const [showSancionesAlert, setShowSancionesAlert] = useState(false)
  const [sancionesData, setSancionesData] = useState(null)
  const [pendingFormData, setPendingFormData] = useState(null)

  useEffect(() => {
    if (activeTab === 'designaciones') {
      load()
    } else if (activeTab === 'asignacion-la-paz') {
      loadLaPaz()
    } else if (activeTab === 'asignacion-caranavi') {
      loadCaranavi()
    } else {
      loadAgentes()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab])

  const loadAgentes = useCallback(async () => {
    try {
      setLoadingAgentes(true)
      const params = { page: pageAgentes, page_size: pageSize }
      if (searchAgentes) params.search = searchAgentes
      const res = await api.getAfiliados(params)
      const list = res.data?.results || res.data || []
      setListaAgentes(list)
      setTotalAgentes(res.data?.count ?? (Array.isArray(list) ? list.length : 0))
    } catch (err) {
      console.error(err)
    } finally {
      setLoadingAgentes(false)
    }
  }, [pageAgentes, pageSize, searchAgentes])

  const load = useCallback(async () => {
    try {
      setLoading(true)
      const params = { page, page_size: pageSize }
      if (search) params.search = search
      if (filtroRuta) params.ruta_id = filtroRuta
      if (desde) params.desde = desde
      if (hasta) params.hasta = hasta
      const res = await api.getHojasRuta(params)
      const list = res.data?.results || res.data || []
      setItems(list)
      setTotalCount(res.data?.count ?? (Array.isArray(list) ? list.length : 0))
      if (afiliados.length === 0) {
        const [afRes, veRes, ruRes] = await Promise.all([
          api.getAfiliados({ page_size: 200, ordering: 'apellidos', estado: 'activo', is_active: 'true' }),
          api.getVehiculos({ page_size: 200, ordering: 'placa' }),
          api.getRutas({ page_size: 200, ordering: 'nombre' }),
        ])
        const afiliadosActivos = (afRes.data?.results || afRes.data || []).filter(
          a => a.is_active && a.estado === 'activo'
        )
        setAfiliados(afiliadosActivos)
        setVehiculos(veRes.data?.results || veRes.data || [])
        setRutas(ruRes.data?.results || ruRes.data || [])
      }
      setError('')
    } catch (err) { setError('Error al cargar hojas'); console.error(err) }
    finally { setLoading(false) }
  }, [page, pageSize, search, filtroRuta, desde, hasta, afiliados.length])

  const loadLaPaz = useCallback(async () => {
    try {
      setLoading(true)
      const params = { page, page_size: pageSize, destino: 'La Paz' }
      if (search) params.search = search
      if (desde) params.desde = desde
      if (hasta) params.hasta = hasta
      const res = await api.getHojasRuta(params)
      setItems(res.data?.results || res.data || [])
      setTotalCount(res.data?.count ?? 0)
      if (afiliados.length === 0) {
        const [afRes, veRes, ruRes] = await Promise.all([
          api.getAfiliados({ page_size: 200, estado: 'activo' }),
          api.getVehiculos({ page_size: 200 }),
          api.getRutas({ page_size: 200 }),
        ])
        setAfiliados(afRes.data?.results || afRes.data || [])
        const vehiculosDoc = (veRes.data?.results || veRes.data || []).filter(v => !v.indocumentado)
        setVehiculos(vehiculosDoc)
        setRutas(ruRes.data?.results || ruRes.data || [])
      }
      setError('')
    } catch (err) { setError('Error al cargar asignaciones La Paz'); console.error(err) }
    finally { setLoading(false) }
  }, [page, pageSize, search, desde, hasta, afiliados.length])

  const loadCaranavi = useCallback(async () => {
    try {
      setLoading(true)
      const params = { page, page_size: pageSize, destino: 'Caranavi' }
      if (search) params.search = search
      if (desde) params.desde = desde
      if (hasta) params.hasta = hasta
      const res = await api.getHojasRuta(params)
      setItems(res.data?.results || res.data || [])
      setTotalCount(res.data?.count ?? 0)
      if (afiliados.length === 0) {
        const [afRes, veRes, ruRes] = await Promise.all([
          api.getAfiliados({ page_size: 200, estado: 'activo' }),
          api.getVehiculos({ page_size: 200 }),
          api.getRutas({ page_size: 200 }),
        ])
        setAfiliados(afRes.data?.results || afRes.data || [])
        const vehiculosDoc = (veRes.data?.results || veRes.data || []).filter(v => !v.indocumentado)
        setVehiculos(vehiculosDoc)
        setRutas(ruRes.data?.results || ruRes.data || [])
      }
      setError('')
    } catch (err) { setError('Error al cargar asignaciones Caranavi'); console.error(err) }
    finally { setLoading(false) }
  }, [page, pageSize, search, desde, hasta, afiliados.length])

  const openCreate = () => {
    setModalMode('create')

    // Pre-seleccionar ruta según el tab activo
    let initialForm = { nro: '', fecha_emision: '', fecha_salida: '', afiliado: '', vehiculo: '', ruta: '', agente_parada: '', precio: '' }

    if (activeTab === 'asignacion-la-paz') {
      const rutaLaPaz = rutas.find(r => (r.nombre || '').toLowerCase().includes('la paz') || (r.destino || '').toLowerCase() === 'la paz')
      if (rutaLaPaz) {
        initialForm.ruta = rutaLaPaz.id
        initialForm.precio = String(rutaLaPaz.tarifa_base || '80')
      }
    } else if (activeTab === 'asignacion-caranavi') {
      const rutaCaranavi = rutas.find(r => (r.nombre || '').toLowerCase().includes('caranavi') || (r.destino || '').toLowerCase() === 'caranavi')
      if (rutaCaranavi) {
        initialForm.ruta = rutaCaranavi.id
        initialForm.precio = String(rutaCaranavi.tarifa_base || '80')
      }
    }

    setForm(initialForm)
    setSubmitError('')
    setFieldErrors({})
    setShowModal(true)
  }

  const openEdit = (it) => {
    setModalMode('edit')
    setForm({ nro: it.nro || '', fecha_emision: it.fecha_emision || '', fecha_salida: it.fecha_salida || '', afiliado: it.afiliado || '', vehiculo: it.vehiculo || '', ruta: it.ruta || '', agente_parada: it.agente_parada || '', precio: String(it.precio || '') })
    setSubmitError('')
    setFieldErrors({})
    setShowModal(true)
    setEditingId(it.id)
  }

  const onChange = (e) => {
    const { name, value } = e.target; setForm(prev => {
      const next = { ...prev, [name]: value }
      if (name === 'ruta') {
        const r = rutas.find(rr => String(rr.id) === String(value))
        if (r) { next.precio = String(r.tarifa_base || '') }
      }
      if (name === 'afiliado') {
        const a = afiliados.find(aa => String(aa.id) === String(value))
        if (a) {
          // Autofill agente_parada (telefono o CI)
          next.agente_parada = a.telefono || a.ci || ''

          // Autofill vehiculo
          // Para la ruta La Paz, buscamos específicamente minibus o ipsum
          const vehiculosAptos = vehiculos.filter(vv =>
            String(vv.afiliado) === String(value) &&
            ['minibus', 'ipsum'].includes((vv.tipo || '').toLowerCase())
          );

          if (vehiculosAptos.length > 0) {
            next.vehiculo = vehiculosAptos[0].id
          } else {
            next.vehiculo = ''
          }
        } else {
          next.agente_parada = ''
          next.vehiculo = ''
        }
      }
      return next
    })
  }

  const validateForm = () => {
    const errs = {}
    if (!form.fecha_emision) errs.fecha_emision = 'Requerido'
    if (activeTab !== 'designaciones' && !form.fecha_salida) errs.fecha_salida = 'Requerido'
    if (!form.afiliado) errs.afiliado = 'Requerido'
    if (!form.ruta) errs.ruta = 'Requerido'
    if (activeTab !== 'designaciones' && !form.vehiculo) errs.vehiculo = 'Requerido'
    const precioNum = parseFloat(String(form.precio || '0'))
    if (isNaN(precioNum) || precioNum <= 0) errs.precio = 'Monto inválido'
    if (form.fecha_emision && form.fecha_salida && form.fecha_salida < form.fecha_emision) errs.fecha_salida = 'Debe ser igual o posterior a emisión'
    const r = rutas.find(rr => String(rr.id) === String(form.ruta))
    const v = vehiculos.find(vv => String(vv.id) === String(form.vehiculo))
    if (r && (r.nombre || '').toLowerCase() === 'la paz') {
      const tipo = (v?.tipo || '').toLowerCase()
      if (tipo && !['minibus', 'ipsum'].includes(tipo)) errs.vehiculo = 'Solo Minibus/Ipsum para La Paz'
    }
    setFieldErrors(errs)
    setSubmitError(Object.values(errs)[0] || '')
    return Object.keys(errs).length === 0
  }

  const save = async (e, force = false) => {
    if (e) e.preventDefault()
    try {
      setSubmitError('')
      setFieldErrors({})
      if (!validateForm()) return
      const payload = {
        nro: form.nro,
        fecha_emision: form.fecha_emision,
        fecha_salida: form.fecha_salida || null,
        afiliado: form.afiliado || null,
        vehiculo: form.vehiculo || null,
        ruta: form.ruta || null,
        agente_parada: form.agente_parada || '',
        precio: form.precio || 0,
        estado: 'emitida',
        force: force
      }
      if (modalMode === 'create') {
        const res = await api.createHojaRuta(payload)
        const newId = res.data?.id
        if (newId) {
          // navigate(`/hojas-ruta/print?id=${newId}`)
          // No navegar a la impresion automáticamente, quedarse en la lista
        }
      } else {
        await api.updateHojaRuta(editingId, payload)
      }
      setShowModal(false)
      if (activeTab === 'asignacion-la-paz') {
        await loadLaPaz()
      } else if (activeTab === 'asignacion-caranavi') {
        await loadCaranavi()
      } else {
        await load()
      }
    } catch (err) {
      if (err.response?.status === 409 && err.response?.data?.requires_confirmation) {
        setSancionesData(err.response.data.sanciones)
        setPendingFormData({ ...form, total_adeudado: err.response.data.total_adeudado })
        setShowSancionesAlert(true)
        return
      }

      const data = err.response?.data
      if (data && typeof data === 'object') {
        setFieldErrors(data)
        setSubmitError(data.detail || data.non_field_errors?.[0] || '')
      } else setSubmitError('Error al guardar')
      console.error(err)
    }
  }

  const handleContinueWithSanciones = () => {
    setShowSancionesAlert(false)
    save(null, true)
  }

  const remove = async (id) => {
    if (!window.confirm('¿Eliminar registro?')) return;
    try {
      await api.deleteHojaRuta(id);
      if (activeTab === 'asignacion-la-paz') {
        await loadLaPaz()
      } else if (activeTab === 'asignacion-caranavi') {
        await loadCaranavi()
      } else {
        await load()
      }
    } catch (err) {
      alert('Error al eliminar');
      console.error(err)
    }
  }

  const enviarWhatsapp = (item) => {
    const afiliado = afiliados.find(a => a.id === item.afiliado);
    const ruta = rutas.find(r => r.id === item.ruta);
    const telefono = afiliado?.telefono || '';

    if (!telefono) {
      alert('El afiliado no tiene número de teléfono registrado');
      return;
    }

    // Formatear fecha a DD/MM/YYYY
    const fechaRaw = item.fecha_salida || item.fecha_emision;
    let fechaFmt = fechaRaw;
    if (fechaRaw) {
      const [year, month, day] = fechaRaw.split('-');
      fechaFmt = `${day}/${month}/${year}`;
    }

    const mensaje = `🚌 *Designación de Ruta*

Señor afiliado, usted fue designado a la ruta: ${ruta?.nombre || 'No especificada'}
Fecha: ${fechaFmt}
• Hoja Nº: ${item.nro}
• Multa por incumplimiento, de acuerdo a normativas internas

Por favor confirme su disponibilidad.

_Sindicato Mixto de Transporte Integración Taipiplaya_`;

    const url = `https://wa.me/591${telefono}?text=${encodeURIComponent(mensaje)}`;
    window.open(url, '_blank');
  }

  const generarPdf = async (id) => {
    try {
      await api.generarPdfHoja(id);
      await load();
      alert('PDF generado')
    } catch (err) {
      alert('Error al generar PDF');
      console.error(err)
    }
  }

  const generarPlanillaIpsum = async (id) => {
    try {
      const res = await api.generarPdfIpsum(id)
      if (res.data?.archivo_url) {
        let url = res.data.archivo_url;
        if (url.startsWith('/')) {
          const baseUrl = 'http://localhost:8000';
          url = `${baseUrl}${url}`;
        }
        window.open(url, '_blank')
      } else {
        alert('Planilla generada, pero no se recibió URL')
      }
    } catch (err) {
      alert('Error al generar Planilla Ipsum')
      console.error(err)
    }
  }

  const handleGenerarListaPunteros = async () => {
    try {
      const res = await api.generarListaPunteros()
      if (res.data) {
        // Si el backend devuelve un blob directamente
        const blob = new Blob([res.data], { type: 'application/pdf' })
        const url = window.URL.createObjectURL(blob)
        window.open(url, '_blank')
      } else {
        alert('Lista de punteros generada')
      }
    } catch (err) {
      alert('Error al generar lista de punteros')
      console.error(err)
    }
  }

  // Efecto para autocompletar agente según la fecha
  useEffect(() => {
    if (showModal && (modalMode === 'create' || modalMode === 'edit') && (form.fecha_salida || form.fecha_emision)) {
      const fecha = form.fecha_salida || form.fecha_emision;
      // Solo buscar si no hay afiliado seleccionado o si queremos sugerir (opcional)
      // Por ahora, solo si el usuario cambia la fecha, sugerimos.
      // Pero para evitar sobrescribir si ya eligió, podríamos poner una condición.
      // Vamos a hacer que siempre sugiera si el campo afiliado está vacío.
      if (!form.afiliado) {
        checkTurno(fecha);
      }
    }
  }, [form.fecha_salida, form.fecha_emision, showModal, modalMode]);

  const checkTurno = async (fecha) => {
    try {
      const res = await api.getTurnoDelDia(fecha);
      if (res.data?.found && res.data?.afiliado) {
        const af = res.data.afiliado;
        setForm(prev => ({
          ...prev,
          afiliado: af.id,
          agente_parada: af.telefono || af.ci || ''
          // Podríamos autocompletar vehículo también si lo tuviera asignado
        }));
        // Buscar vehículo del afiliado si es necesario
        const v = vehiculos.find(vv => String(vv.afiliado) === String(af.id) && !vv.indocumentado);
        if (v) {
          setForm(prev => ({ ...prev, vehiculo: v.id }));
        }
      }
    } catch (err) {
      console.log("No hay turno o error al buscar turno:", err);
    }
  }

  const handleGenerarNominaAgentes = async () => {
    try {
      // 1. Primero intentar generar turnos si no existen (o forzar regeneración/completar)
      // O simplemente llamar a generar, el backend decide si añade o no.
      await api.generarTurnos();

      // 2. Luego generar el PDF
      const res = await api.generarNominaAgentes()
      if (res.data) {
        const blob = new Blob([res.data], { type: 'application/pdf' })
        const url = window.URL.createObjectURL(blob)
        window.open(url, '_blank')
      } else {
        alert('Nómina de agentes generada')
      }
    } catch (err) {
      alert('Error al generar nómina de agentes')
      console.error(err)
    }
  }

  const handleExportExcel = async () => {
    const params = {}
    if (search) params.search = search
    if (filtroRuta) params.ruta_id = filtroRuta
    if (desde) params.desde = desde
    if (hasta) params.hasta = hasta
    if (activeTab === 'asignacion-la-paz') params.destino = 'La Paz'
    if (activeTab === 'asignacion-caranavi') params.destino = 'Caranavi'

    await api.downloadHojasRutaExcel(params)
  }


  return (
    <div className="afiliados-container">
      <div className="page-header">
        <h1>Módulo Agentes de Parada</h1>
      </div>

      <div className="tabs" style={{ marginBottom: '20px' }}>
        <button
          className={`tab-button tab-agentes ${activeTab === 'agentes' ? 'active' : ''}`}
          onClick={() => setActiveTab('agentes')}
        >
          👥 Listado de Agentes
        </button>
        <button
          className={`tab-button tab-designaciones ${activeTab === 'designaciones' ? 'active' : ''}`}
          onClick={() => setActiveTab('designaciones')}
        >
          📋 Designaciones (Hojas de Ruta)
        </button>
        <button
          className={`tab-button tab-la-paz ${activeTab === 'asignacion-la-paz' ? 'active' : ''}`}
          onClick={() => setActiveTab('asignacion-la-paz')}
        >
          🚌 Asignación Ruta La Paz
        </button>
        <button
          className={`tab-button tab-caranavi ${activeTab === 'asignacion-caranavi' ? 'active' : ''}`}
          onClick={() => setActiveTab('asignacion-caranavi')}
        >
          🚌 Asignación Ruta Caranavi
        </button>
      </div>

      {activeTab === 'agentes' && (
        // VISTA LISTADO DE AGENTES (Similar a Afiliados)
        <>
          <div className="filters-section">
            <div className="search-box">
              <input
                className="search-input"
                type="text"
                placeholder="Buscar por nombre, CI..."
                value={searchAgentes}
                onChange={e => { setSearchAgentes(e.target.value); setPageAgentes(1) }}
              />
            </div>
            <div className="filter-box">
              <input
                className="search-input"
                type="number"
                min="1"
                value={pageSize}
                onChange={e => { setPageSize(parseInt(e.target.value || '10', 10)); setPageAgentes(1) }}
              />
            </div>
            <button
              className="btn btn-primary"
              onClick={handleGenerarListaPunteros}
              style={{
                backgroundColor: '#2E7D32',
                color: 'white',
                padding: '8px 16px',
                fontSize: '0.9rem',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                fontWeight: '500'
              }}
            >
              <span style={{ fontSize: '1.1rem' }}>📋</span> Imprimir Lista de Punteros
            </button>
            <button
              className="btn btn-primary"
              onClick={handleGenerarNominaAgentes}
              style={{
                backgroundColor: '#1976D2',
                color: 'white',
                padding: '8px 16px',
                fontSize: '0.9rem',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                fontWeight: '500'
              }}
            >
              <span style={{ fontSize: '1.1rem' }}>📄</span> Nómina de Agentes
            </button>
          </div>

          {loadingAgentes ? (<div className="loading">Cargando agentes...</div>) : (
            <div className="table-container">
              <table className="afiliados-table">
                <thead>
                  <tr>
                    <th>Nombre Completo</th>
                    <th>CI</th>
                    <th>Teléfono</th>
                    <th>Dirección</th>
                    <th>Estado</th>
                    <th>Fecha Ingreso</th>
                  </tr>
                </thead>
                <tbody>
                  {listaAgentes.length === 0 ? (
                    <tr><td colSpan="6" className="no-data">No se encontraron agentes</td></tr>
                  ) : listaAgentes.map(agente => (
                    <tr key={agente.id}>
                      <td><span className="afiliado-name">{agente.apellidos} {agente.nombres}</span></td>
                      <td>{agente.ci}</td>
                      <td>{agente.telefono || '-'}</td>
                      <td>{agente.direccion || '-'}</td>
                      <td><span className={`badge badge-${agente.estado}`}>{agente.estado}</span></td>
                      <td>{agente.fecha_ingreso}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          <div style={{ display: 'flex', gap: '10px', alignItems: 'center', marginTop: '12px' }}>
            <button className="btn btn-secondary" disabled={pageAgentes <= 1} onClick={() => setPageAgentes(p => Math.max(1, p - 1))}>Anterior</button>
            <span>Página {pageAgentes}</span>
            <button className="btn btn-secondary" disabled={pageAgentes * pageSize >= totalAgentes} onClick={() => setPageAgentes(p => p + 1)}>Siguiente</button>
            <span>Total {totalAgentes}</span>
          </div>
        </>
      )}
      {activeTab === 'designaciones' && (
        // VISTA DESIGNACIONES (Hojas de Ruta)
        <>
          <div className="page-header">
            <h2>Gestión de Designaciones</h2>
            <button className="btn btn-primary" onClick={openCreate}><span className="icon">+</span> Designar Agente</button>
          </div>
          <p style={{ color: '#666', marginBottom: '20px', fontSize: '14px', lineHeight: '1.6' }}>
            Administra la designación de los agentes de parada de acuerdo con la lista de afiliados activos y la fecha correspondiente.
          </p>

          <div className="filters-section">
            <div className="search-box">
              <input className="search-input" type="text" placeholder="Buscar por nro, CI, ruta" value={search} onChange={e => setSearch(e.target.value)} />
            </div>
            <div className="filter-box">
              <select className="filter-select" value={filtroRuta} onChange={e => { setFiltroRuta(e.target.value); setPage(1) }}>
                <option value="">Todas las rutas</option>
                {rutas.map(r => <option key={r.id} value={r.id}>{r.nombre}</option>)}
              </select>
            </div>
            <div className="filter-box">
              <input type="date" value={desde} onChange={e => { setDesde(e.target.value); setPage(1) }} title="Desde" />
            </div>
            <div className="filter-box">
              <input type="date" value={hasta} onChange={e => { setHasta(e.target.value); setPage(1) }} title="Hasta" />
            </div>
            <div className="filter-box">
              <button className="btn btn-success" onClick={handleExportExcel}>
                📥 Descargar Excel
              </button>
            </div>

          </div>

          {loading ? (<div className="loading">Cargando...</div>) : error ? (<div className="error">{error}</div>) : (
            <div className="table-container">
              <table className="vehiculos-table">
                <thead>
                  <tr>
                    <th>Nº</th>
                    <th>FECHA</th>
                    <th>AFILIADO (CHOFER)</th>
                    <th>AGENTE DE PARADA</th>
                    <th>RUTA</th>
                    <th>VEHÍCULO</th>
                    <th>MONTO</th>
                    <th>ACCIONES</th>
                  </tr>
                </thead>
                <tbody>
                  {items.length === 0 ? (
                    <tr><td colSpan="8" className="no-data">Sin registros</td></tr>
                  ) : items.map((it, index) => {
                    const af = afiliados.find(a => a.id === it.afiliado);
                    const ve = vehiculos.find(v => v.id === it.vehiculo);
                    const ru = rutas.find(r => r.id === it.ruta);
                    return (
                      <tr key={it.id}>
                        <td>{(page - 1) * pageSize + index + 1}</td>
                        <td>{it.fecha_salida || it.fecha_emision}</td>
                        <td>{af?.apellidos} {af?.nombres}</td>
                        <td style={{ fontWeight: 'bold', color: '#2E7D32' }}>{it.agente_parada || '-'}</td>
                        <td>{ru?.nombre || '-'}</td>
                        <td>{ve ? `${ve.placa} (${ve.tipo})` : '-'}</td>
                        <td>{it.precio}</td>
                        <td className="actions">
                          <button className="btn-icon btn-edit" onClick={() => openEdit(it)} title="Editar"><IconPencil /></button>
                          <button className="btn-icon btn-view" onClick={() => enviarWhatsapp(it)} title="Notificar WhatsApp"><IconWhatsApp /></button>
                          <button className="btn-icon btn-delete" onClick={() => remove(it.id)} title="Eliminar"><IconTrash /></button>
                        </td>
                      </tr>
                    );
                  })}
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
        </>
      )}
      {activeTab === 'asignacion-la-paz' && (
        <>
          {/* VISTA ASIGNACIÓN RUTA LA PAZ */}
          <div className="page-header">
            <h2>🚌 Asignación Ruta La Paz</h2>
            <button className="btn btn-primary" onClick={openCreate}><span className="icon">+</span> Designación Ruta La Paz</button>
          </div>
          <p style={{ color: '#666', marginBottom: '20px', fontSize: '14px', lineHeight: '1.6' }}>
            Gestiona las asignaciones de vehículos <strong>documentados (con placa)</strong> para la ruta a La Paz. Solo se muestran vehículos Minibus/Ipsum aptos para esta ruta.
          </p>

          <div className="filters-section">
            <div className="search-box">
              <input className="search-input" type="text" placeholder="Buscar por nro, afiliado" value={search} onChange={e => setSearch(e.target.value)} />
            </div>
            <div className="filter-box">
              <input type="date" value={desde} onChange={e => { setDesde(e.target.value); setPage(1) }} title="Desde" />
            </div>
            <div className="filter-box">
              <input type="date" value={hasta} onChange={e => { setHasta(e.target.value); setPage(1) }} title="Hasta" />
            </div>
          </div>

          {loading ? (<div className="loading">Cargando...</div>) : error ? (<div className="error">{error}</div>) : (
            <div className="table-container">
              <table className="vehiculos-table">
                <thead>
                  <tr>
                    <th>NÚMERO</th>
                    <th>AFILIADO</th>
                    <th>VEHÍCULO</th>
                    <th>FECHA SALIDA</th>
                    <th>PLACA DE LA MOVILIDAD</th>
                    <th>PRECIO (BS.)</th>
                    <th>ESTADO</th>
                    <th>ACCIONES</th>
                  </tr>
                </thead>
                <tbody>
                  {items.length === 0 ? (
                    <tr><td colSpan="8" style={{ textAlign: 'center', color: '#999', padding: '20px' }}>No hay asignaciones para La Paz</td></tr>
                  ) : (
                    items.map(item => (
                      <tr key={item.id}>
                        <td>{item.nro}</td>
                        <td>{afiliados.find(a => a.id === item.afiliado)?.apellidos} {afiliados.find(a => a.id === item.afiliado)?.nombres}</td>
                        <td>{vehiculos.find(v => v.id === item.vehiculo)?.tipo || '-'}</td>
                        <td>{item.fecha_salida || item.fecha_emision}</td>
                        <td>{vehiculos.find(v => v.id === item.vehiculo)?.placa || '-'}</td>
                        <td>{item.precio}</td>
                        <td><span className={`badge badge-${item.estado}`}>{item.estado}</span></td>
                        <td className="actions">
                          <td className="actions">
                            <button className="btn-icon btn-edit" onClick={() => openEdit(item)} title="Editar"><IconPencil /></button>
                            <button className="btn-icon btn-edit" onClick={() => generarPlanillaIpsum(item.id)} title="Planilla Ipsum"><IconBus /></button>
                            <button className="btn-icon btn-view" onClick={() => enviarWhatsapp(item)} title="WhatsApp"><IconWhatsApp /></button>
                            <button className="btn-icon btn-delete" onClick={() => remove(item.id)} title="Eliminar"><IconTrash /></button>
                          </td>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          )}

          <div className="pagination">
            <button className="btn btn-secondary" disabled={page <= 1} onClick={() => setPage(p => p - 1)}>Anterior</button>
            <span>Página {page}</span>
            <button className="btn btn-secondary" disabled={page * pageSize >= totalCount} onClick={() => setPage(p => p + 1)}>Siguiente</button>
            <span>Total {totalCount}</span>
          </div>
        </>
      )}
      {activeTab === 'asignacion-caranavi' && (
        <>
          {/* VISTA ASIGNACIÓN RUTA CARANAVI */}
          <div className="page-header">
            <h2>🚌 Asignación Ruta Caranavi</h2>
            <button className="btn btn-primary" onClick={openCreate}><span className="icon">+</span> Designación Ruta Caranavi</button>
          </div>
          <p style={{ color: '#666', marginBottom: '20px', fontSize: '14px', lineHeight: '1.6' }}>
            Gestiona las asignaciones de vehículos <strong>documentados (con placa)</strong> para la ruta a Caranavi. Solo se muestran vehículos Minibus/Ipsum aptos para esta ruta.
          </p>

          <div className="filters-section">
            <div className="search-box">
              <input className="search-input" type="text" placeholder="Buscar por nro, afiliado" value={search} onChange={e => setSearch(e.target.value)} />
            </div>
            <div className="filter-box">
              <input type="date" value={desde} onChange={e => { setDesde(e.target.value); setPage(1) }} title="Desde" />
            </div>
            <div className="filter-box">
              <input type="date" value={hasta} onChange={e => { setHasta(e.target.value); setPage(1) }} title="Hasta" />
            </div>
          </div>

          {loading ? (<div className="loading">Cargando...</div>) : error ? (<div className="error">{error}</div>) : (
            <div className="table-container">
              <table className="vehiculos-table">
                <thead>
                  <tr>
                    <th>NÚMERO</th>
                    <th>AFILIADO</th>
                    <th>VEHÍCULO</th>
                    <th>FECHA SALIDA</th>
                    <th>PLACA DE LA MOVILIDAD</th>
                    <th>PRECIO (BS.)</th>
                    <th>ESTADO</th>
                    <th>ACCIONES</th>
                  </tr>
                </thead>
                <tbody>
                  {items.length === 0 ? (
                    <tr><td colSpan="8" style={{ textAlign: 'center', color: '#999', padding: '20px' }}>No hay asignaciones para Caranavi</td></tr>
                  ) : (
                    items.map(item => (
                      <tr key={item.id}>
                        <td>{item.nro}</td>
                        <td>{afiliados.find(a => a.id === item.afiliado)?.apellidos} {afiliados.find(a => a.id === item.afiliado)?.nombres}</td>
                        <td>{vehiculos.find(v => v.id === item.vehiculo)?.tipo || '-'}</td>
                        <td>{item.fecha_salida || item.fecha_emision}</td>
                        <td>{vehiculos.find(v => v.id === item.vehiculo)?.placa || '-'}</td>
                        <td>{item.precio}</td>
                        <td><span className={`badge badge-${item.estado}`}>{item.estado}</span></td>
                        <td className="actions">
                          <td className="actions">
                            <button className="btn-icon btn-edit" onClick={() => openEdit(item)} title="Editar"><IconPencil /></button>
                            <button className="btn-icon btn-edit" onClick={() => generarPlanillaIpsum(item.id)} title="Planilla Ipsum"><IconBus /></button>
                            <button className="btn-icon btn-view" onClick={() => enviarWhatsapp(item)} title="WhatsApp"><IconWhatsApp /></button>
                            <button className="btn-icon btn-delete" onClick={() => remove(item.id)} title="Eliminar"><IconTrash /></button>
                          </td>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          )}

          <div className="pagination">
            <button className="btn btn-secondary" disabled={page <= 1} onClick={() => setPage(p => p - 1)}>Anterior</button>
            <span>Página {page}</span>
            <button className="btn btn-secondary" disabled={page * pageSize >= totalCount} onClick={() => setPage(p => p + 1)}>Siguiente</button>
            <span>Total {totalCount}</span>
          </div>
        </>
      )}

      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>{modalMode === 'create' ? (activeTab === 'asignacion-la-paz' ? 'Designación Ruta La Paz' : activeTab === 'asignacion-caranavi' ? 'Designación Ruta Caranavi' : 'Designar Agente de Parada') : 'Modificar Designación'}</h2>
              <button className="modal-close" onClick={() => setShowModal(false)}>✕</button>
            </div>
            {submitError && <div className="error" style={{ marginBottom: '10px' }}>{submitError}</div>}
            <form onSubmit={save} className="afiliado-form">
              {(activeTab === 'asignacion-la-paz' || activeTab === 'asignacion-caranavi') ? (
                <>
                  <div className="form-row">
                    <div className="form-group">
                      <label htmlFor="nro">Número *</label>
                      <input
                        id="nro"
                        name="nro"
                        type="text"
                        value={form.nro}
                        onChange={onChange}
                        placeholder="Automático"
                        readOnly
                        style={{ backgroundColor: '#f5f5f5' }}
                      />
                      <small style={{ color: '#666', fontSize: '11px' }}>Se generará automáticamente</small>
                      {fieldErrors.nro && <div className="error">{Array.isArray(fieldErrors.nro) ? fieldErrors.nro[0] : String(fieldErrors.nro)}</div>}
                    </div>
                    <div className="form-group">
                      <label htmlFor="precio">Monto *</label>
                      <input id="precio" name="precio" type="number" step="0.01" value={form.precio} onChange={onChange} required />
                      {fieldErrors.precio && <div className="error">{Array.isArray(fieldErrors.precio) ? fieldErrors.precio[0] : String(fieldErrors.precio)}</div>}
                    </div>
                  </div>

                  <div className="form-row">
                    <div className="form-group">
                      <label htmlFor="fecha_emision">Fecha emisión *</label>
                      <input id="fecha_emision" name="fecha_emision" type="date" value={form.fecha_emision} onChange={onChange} required />
                      {fieldErrors.fecha_emision && <div className="error">{Array.isArray(fieldErrors.fecha_emision) ? fieldErrors.fecha_emision[0] : String(fieldErrors.fecha_emision)}</div>}
                    </div>
                    <div className="form-group">
                      <label htmlFor="fecha_salida">Fecha salida *</label>
                      <input id="fecha_salida" name="fecha_salida" type="date" value={form.fecha_salida} onChange={onChange} required />
                      {fieldErrors.fecha_salida && <div className="error">{Array.isArray(fieldErrors.fecha_salida) ? fieldErrors.fecha_salida[0] : String(fieldErrors.fecha_salida)}</div>}
                    </div>
                  </div>

                  <div className="form-row">
                    <div className="form-group">
                      <label htmlFor="afiliado">Afiliado *</label>
                      <select id="afiliado" name="afiliado" value={form.afiliado} onChange={onChange} required>
                        <option value="">Selecciona...</option>
                        {afiliados.map(a => (
                          <option key={a.id} value={a.id}>{a.apellidos} {a.nombres}</option>
                        ))}
                      </select>
                      {fieldErrors.afiliado && <div className="error">{Array.isArray(fieldErrors.afiliado) ? fieldErrors.afiliado[0] : String(fieldErrors.afiliado)}</div>}
                    </div>
                    <div className="form-group">
                      <label htmlFor="vehiculo">Vehículo *</label>
                      <select id="vehiculo" name="vehiculo" value={form.vehiculo} onChange={onChange} required>
                        <option value="">Selecciona...</option>
                        {vehiculos.map(v => (
                          <option key={v.id} value={v.id}>{v.placa} - {v.tipo}</option>
                        ))}
                      </select>
                      {fieldErrors.vehiculo && <div className="error">{Array.isArray(fieldErrors.vehiculo) ? fieldErrors.vehiculo[0] : String(fieldErrors.vehiculo)}</div>}
                    </div>
                  </div>

                  <div className="form-group">
                    <label htmlFor="ruta">Ruta / Destino</label>
                    <select id="ruta" name="ruta" value={form.ruta} onChange={onChange} disabled style={{ backgroundColor: '#f5f5f5' }}>
                      <option value="">Selecciona...</option>
                      {rutas.map(r => (
                        <option key={r.id} value={r.id}>{r.nombre}</option>
                      ))}
                    </select>
                    {fieldErrors.ruta && <div className="error">{Array.isArray(fieldErrors.ruta) ? fieldErrors.ruta[0] : String(fieldErrors.ruta)}</div>}
                  </div>
                </>
              ) : (
                <>
                  <div className="form-row">
                    <div className="form-group">
                      <label htmlFor="nro">Número *</label>
                      <input id="nro" name="nro" type="text" value={form.nro} onChange={onChange} />
                      {fieldErrors.nro && <div className="error">{Array.isArray(fieldErrors.nro) ? fieldErrors.nro[0] : String(fieldErrors.nro)}</div>}
                    </div>
                    <div className="form-group">
                      <label htmlFor="precio">Monto *</label>
                      <input id="precio" name="precio" type="number" step="0.01" value={form.precio} onChange={onChange} />
                      {fieldErrors.precio && <div className="error">{Array.isArray(fieldErrors.precio) ? fieldErrors.precio[0] : String(fieldErrors.precio)}</div>}
                    </div>
                  </div>
                  <div className="form-row">
                    <div className="form-group">
                      <label htmlFor="fecha_emision">Fecha emisión *</label>
                      <input id="fecha_emision" name="fecha_emision" type="date" value={form.fecha_emision} onChange={onChange} />
                      {fieldErrors.fecha_emision && <div className="error">{Array.isArray(fieldErrors.fecha_emision) ? fieldErrors.fecha_emision[0] : String(fieldErrors.fecha_emision)}</div>}
                    </div>
                    <div className="form-group">
                      <label htmlFor="fecha_salida">Fecha salida</label>
                      <input id="fecha_salida" name="fecha_salida" type="date" value={form.fecha_salida} onChange={onChange} />
                      {fieldErrors.fecha_salida && <div className="error">{Array.isArray(fieldErrors.fecha_salida) ? fieldErrors.fecha_salida[0] : String(fieldErrors.fecha_salida)}</div>}
                    </div>
                  </div>
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
                      <label htmlFor="vehiculo">Vehículo</label>
                      <select id="vehiculo" name="vehiculo" value={form.vehiculo} onChange={onChange}>
                        <option value="">Selecciona...</option>
                        {vehiculos.map(v => (
                          <option key={v.id} value={v.id}>{v.placa}</option>
                        ))}
                      </select>
                      {fieldErrors.vehiculo && <div className="error">{Array.isArray(fieldErrors.vehiculo) ? fieldErrors.vehiculo[0] : String(fieldErrors.vehiculo)}</div>}
                    </div>
                  </div>
                  <div className="form-row">
                    <div className="form-group">
                      <label htmlFor="ruta">Ruta / Destino</label>
                      <select id="ruta" name="ruta" value={form.ruta} onChange={onChange}>
                        <option value="">Selecciona...</option>
                        {rutas.map(r => (
                          <option key={r.id} value={r.id}>{r.nombre}</option>
                        ))}
                      </select>
                      {fieldErrors.ruta && <div className="error">{Array.isArray(fieldErrors.ruta) ? fieldErrors.ruta[0] : String(fieldErrors.ruta)}</div>}
                    </div>
                    <div className="form-group">
                      <label htmlFor="agente_parada">Agente de parada</label>
                      <input id="agente_parada" name="agente_parada" type="text" value={form.agente_parada} onChange={onChange} />
                      {fieldErrors.agente_parada && <div className="error">{Array.isArray(fieldErrors.agente_parada) ? fieldErrors.agente_parada[0] : String(fieldErrors.agente_parada)}</div>}
                    </div>
                  </div>
                </>
              )}
              <div className="form-actions">
                <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>Cancelar</button>
                <button type="submit" className="btn btn-primary">Guardar</button>
              </div>
            </form>
          </div>
        </div>
      )}
      {showSancionesAlert && sancionesData && (
        <SancionesAlert
          sanciones={sancionesData}
          totalAdeudado={pendingFormData?.total_adeudado || 0}
          onContinue={handleContinueWithSanciones}
          onCancel={() => setShowSancionesAlert(false)}
        />
      )}
    </div>
  )
}

export default HojasRuta
