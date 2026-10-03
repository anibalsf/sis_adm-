import { useState, useEffect, useMemo } from 'react';
import api from '../services/api';
import './ReportesFinancieros.css';
import './ReportePorCategoria.css';

const FILTROS_INICIO = {
    tipo_pago_id: 'todos',
    fecha_inicio: '',
    fecha_fin: '',
    monto_esperado: ''
};

const FILAS_POR_PAGINA = 25;

const bs = (valor) => `Bs. ${Number(valor || 0).toFixed(2)}`;

const badgeEstado = (estado) => {
    if (estado === 'aprobado') return 'badge-pill success';
    if (estado === 'anulado') return 'badge-pill danger';
    if (estado === 'pendiente_aprobacion') return 'badge-pill warning';
    return 'badge-pill info';
};

const fechaLegible = (iso) => (iso ? new Date(`${iso}T00:00:00`).toLocaleDateString() : '-');

const normalizar = (texto) =>
    String(texto || '').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');

function KpiEgresos({ icono, clase, label, valor, color }) {
    return (
        <div className="kpi-stat-card">
            <div className={`kpi-stat-icon ${clase}`}>{icono}</div>
            <div className="kpi-stat-info">
                <label>{label}</label>
                <div className="value" style={color ? { color } : undefined}>{valor}</div>
            </div>
        </div>
    );
}

function BarraParticipacion({ porcentaje }) {
    return (
        <div className="barra-participacion">
            <div className="barra-participacion-track">
                <div className="barra-participacion-fill" style={{ width: `${Math.min(porcentaje, 100)}%` }} />
            </div>
            <span>{porcentaje}%</span>
        </div>
    );
}

function Paginacion({ pagina, totalPaginas, onCambiar }) {
    if (totalPaginas <= 1) return null;
    return (
        <div className="tabla-paginacion">
            <button type="button" className="btn-pagina" onClick={() => onCambiar(pagina - 1)} disabled={pagina <= 1}>
                ‹ Anterior
            </button>
            <span>Página {pagina} de {totalPaginas}</span>
            <button type="button" className="btn-pagina" onClick={() => onCambiar(pagina + 1)} disabled={pagina >= totalPaginas}>
                Siguiente ›
            </button>
        </div>
    );
}

function BuscadorTabla({ valor, onChange, placeholder }) {
    return (
        <input
            type="search"
            className="tabla-buscador"
            value={valor}
            placeholder={placeholder}
            onChange={(e) => onChange(e.target.value)}
            aria-label={placeholder}
        />
    );
}

/**
 * Tabla reutilizada por la vista de categoría única y la de "todas las
 * categorías": muestra la deuda de cada afiliado activo, con búsqueda,
 * orden por monto y paginación para que siga siendo legible con muchos socios.
 */
function TablaDuplicados({ duplicados = [], conCategoria = false, montoTotal }) {
    const total = duplicados.reduce((acc, d) => acc + Number(d.total_pagado || 0), 0);

    return (
        <div className="seccion-card">
            <h3 className="seccion-card-title" style={{ color: '#ea580c' }}>
                ⚠️ Posibles Pagos Duplicados ({duplicados.length})
            </h3>
            {duplicados.length === 0 ? (
                <p className="estado-vacio" style={{ color: '#059669' }}>
                    ✅ No se detectaron posibles pagos duplicados en el período seleccionado.
                </p>
            ) : (
                <>
                    <p className="seccion-subtitulo">
                        Afiliados con más de un pago completado en la misma categoría. Revisá los
                        recibos antes de anular: {bs(total)}
                        {montoTotal != null && montoTotal !== total && ` · ${duplicados.length} caso(s)`}
                    </p>
                    <div className="tabla-wrapper">
                        <table className="tabla-custom">
                            <thead>
                                <tr>
                                    {conCategoria && <th>Categoría</th>}
                                    <th>Afiliado</th>
                                    <th>C.I.</th>
                                    <th style={{ textAlign: 'center' }}>Pagos</th>
                                    <th style={{ textAlign: 'right' }}>Total Pagado</th>
                                    <th>Detalle de pagos</th>
                                </tr>
                            </thead>
                            <tbody>
                                {duplicados.map(item => (
                                    <tr key={`${item.categoria?.id ?? ''}_${item.afiliado_id}`}>
                                        {conCategoria && (
                                            <td>
                                                <span className="badge-pill info">
                                                    {item.categoria?.nombre || '-'}
                                                </span>
                                            </td>
                                        )}
                                        <td style={{ fontWeight: '600' }}>{item.nombre}</td>
                                        <td>{item.ci || '-'}</td>
                                        <td style={{ textAlign: 'center' }}>
                                            <span className="badge-pill warning">{item.cantidad_pagos}</span>
                                        </td>
                                        <td style={{ fontWeight: '700', color: '#059669', textAlign: 'right' }}>
                                            {bs(item.total_pagado)}
                                        </td>
                                        <td className="duplicados-detalle">
                                            {(item.pagos || []).map(p => (
                                                <div key={p.id}>
                                                    {p.fecha_pago} · {bs(p.monto)}
                                                    {p.nro_recibo ? ` · Nro ${p.nro_recibo}` : ''}
                                                </div>
                                            ))}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                            <tfoot>
                                <tr className="tabla-custom-total">
                                    <td colSpan={conCategoria ? 4 : 3} style={{ textAlign: 'right' }}>
                                        TOTAL EN PAGOS DUPLICADOS
                                    </td>
                                    <td style={{ fontWeight: 800, color: '#ea580c', textAlign: 'right' }}>
                                        {bs(total)}
                                    </td>
                                    <td></td>
                                </tr>
                            </tfoot>
                        </table>
                    </div>
                </>
            )}
        </div>
    );
}

function TablaPendientes({
    pendientes = [],
    totalPendientes,
    montoTotalPendiente,
    montoEsperado,
    truncados = false,
    titulo,
    subtitulo,
    mensajeVacio
}) {
    const [busqueda, setBusqueda] = useState('');
    const [orden, setOrden] = useState('nombre');
    const [pagina, setPagina] = useState(1);

    const conDeuda = montoEsperado != null;

    const filtrados = useMemo(() => {
        const termino = normalizar(busqueda);
        const base = termino
            ? pendientes.filter(p =>
                [p.nombre, p.ci, p.telefono].some(campo => normalizar(campo).includes(termino))
            )
            : pendientes;
        return [...base].sort((a, b) => {
            if (orden === 'deuda') return (b.deuda ?? 0) - (a.deuda ?? 0);
            if (orden === 'pagado') return (b.pagado ?? 0) - (a.pagado ?? 0);
            return String(a.nombre).localeCompare(String(b.nombre), 'es');
        });
    }, [pendientes, busqueda, orden]);

    const totalPaginas = Math.max(1, Math.ceil(filtrados.length / FILAS_POR_PAGINA));
    const paginaActual = Math.min(pagina, totalPaginas);
    const visibles = filtrados.slice((paginaActual - 1) * FILAS_POR_PAGINA, paginaActual * FILAS_POR_PAGINA);
    const encabezado = totalPendientes ?? pendientes.length;

    if (pendientes.length === 0) {
        return (
            <div className="seccion-card">
                <h3 className="seccion-card-title" style={{ color: '#dc2626' }}>{titulo} (0)</h3>
                <p className="estado-vacio" style={{ color: '#059669' }}>{mensajeVacio}</p>
            </div>
        );
    }

    return (
        <div className="seccion-card">
            <h3 className="seccion-card-title" style={{ color: '#dc2626' }}>
                ❌ {titulo} ({encabezado})
            </h3>
            {subtitulo && <p className="seccion-subtitulo">{subtitulo}</p>}
            {montoTotalPendiente != null && (
                <p className="deuda-total">💸 Monto total pendiente: {bs(montoTotalPendiente)}</p>
            )}
            {!conDeuda && (
                <p className="aviso-truncado">
                    ℹ️ Indicá el <strong>monto esperado</strong> en los filtros para ver cuánto debe
                    pagar cada afiliado. Acá se listan los que no registraron ningún pago.
                </p>
            )}

            <div className="tabla-herramientas">
                <BuscadorTabla
                    valor={busqueda}
                    onChange={valor => { setBusqueda(valor); setPagina(1); }}
                    placeholder="Buscar por nombre, C.I. o teléfono"
                />
                <select
                    className="filtro-control tabla-orden"
                    value={orden}
                    onChange={(e) => { setOrden(e.target.value); setPagina(1); }}
                    aria-label="Ordenar pendientes"
                >
                    <option value="nombre">Ordenar por nombre</option>
                    {conDeuda && <option value="deuda">Mayor deuda primero</option>}
                    <option value="pagado">Mayor monto pagado primero</option>
                </select>
            </div>

            {truncados && (
                <p className="aviso-truncado">
                    ⚠️ Mostrando {pendientes.length} de {encabezado} afiliados. Exportá a Excel para el detalle completo.
                </p>
            )}

            {filtrados.length === 0 ? (
                <p className="estado-vacio">Sin resultados para «{busqueda}».</p>
            ) : (
                <>
                    <div className="tabla-wrapper">
                    <table className="tabla-custom">
                        <thead>
                            <tr>
                                <th>#</th>
                                <th>Nombre Completo</th>
                                <th>C.I.</th>
                                <th>Teléfono</th>
                                <th style={{ textAlign: 'right' }}>Monto a Pagar</th>
                                <th style={{ textAlign: 'right' }}>Pagó</th>
                            </tr>
                        </thead>
                        <tbody>
                            {visibles.map((af, idx) => (
                                <tr key={af.afiliado_id}>
                                    <td style={{ color: '#94a3b8' }}>
                                        {(paginaActual - 1) * FILAS_POR_PAGINA + idx + 1}
                                    </td>
                                    <td style={{ fontWeight: '600', color: '#0f172a' }}>{af.nombre}</td>
                                    <td>{af.ci}</td>
                                    <td>{af.telefono || '-'}</td>
                                    <td style={{ textAlign: 'right', fontWeight: '700', color: '#dc2626' }}>
                                        {af.deuda != null ? bs(af.deuda) : <span style={{ color: '#94a3b8' }}>—</span>}
                                    </td>
                                    <td style={{ textAlign: 'right', color: af.pagado > 0 ? '#b45309' : '#94a3b8' }}>
                                        {af.pagado > 0 ? bs(af.pagado) : '-'}
                                        {conDeuda && af.pagado > 0 && af.pagado < montoEsperado && (
                                            <div style={{ fontSize: '0.72rem', fontWeight: '600' }}>pago parcial</div>
                                        )}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                        <tfoot>
                            <tr className="tabla-custom-total">
                                <td colSpan={4} style={{ textAlign: 'right' }}>
                                    TOTAL {conDeuda ? 'FALTANTE' : 'A COBRAR (sin monto esperado)'}
                                </td>
                                <td style={{ fontWeight: 800, color: '#dc2626', textAlign: 'right' }}>
                                    {montoTotalPendiente != null ? bs(montoTotalPendiente) : '—'}
                                </td>
                                <td style={{ fontWeight: 700, color: '#b45309', textAlign: 'right' }}>
                                    {bs(filtrados.reduce((acc, p) => acc + Number(p.pagado || 0), 0))}
                                </td>
                            </tr>
                        </tfoot>
                    </table>
                </div>
                </>
            )}

            <Paginacion pagina={paginaActual} totalPaginas={totalPaginas} onCambiar={setPagina} />
        </div>
    );
}

function TablaDetalleEgresos({ egresos, titulo, colorTitulo, mensajeVacio }) {
    const [busqueda, setBusqueda] = useState('');
    const [pagina, setPagina] = useState(1);

    const filas = useMemo(() => {
        const termino = normalizar(busqueda);
        return termino
            ? egresos.filter(e =>
                [e.categoria, e.descripcion, e.banco, e.nro_operacion, e.estado_label]
                    .some(campo => normalizar(campo).includes(termino))
            )
            : egresos;
    }, [egresos, busqueda]);

    const total = filas.reduce((acc, e) => acc + Number(e.monto || 0), 0);
    const totalPaginas = Math.max(1, Math.ceil(filas.length / FILAS_POR_PAGINA));
    const paginaActual = Math.min(pagina, totalPaginas);
    const visibles = filas.slice((paginaActual - 1) * FILAS_POR_PAGINA, paginaActual * FILAS_POR_PAGINA);

    return (
        <div className="seccion-card">
            <h3 className="seccion-card-title" style={colorTitulo ? { color: colorTitulo } : undefined}>
                {titulo} ({egresos.length})
            </h3>
            {egresos.length > 0 ? (
                <>
                    {egresos.length > FILAS_POR_PAGINA && (
                        <div className="tabla-herramientas">
                            <BuscadorTabla
                                valor={busqueda}
                                onChange={valor => { setBusqueda(valor); setPagina(1); }}
                                placeholder="Buscar por categoría, descripción o estado"
                            />
                        </div>
                    )}
                    {filas.length === 0 ? (
                        <p className="estado-vacio">Sin resultados para «{busqueda}».</p>
                    ) : (
                        <>
                            <div className="tabla-wrapper">
                                <table className="tabla-custom">
                                    <thead>
                                        <tr>
                                            <th>#</th>
                                            <th>Fecha</th>
                                            <th>Categoría</th>
                                            <th>Descripción</th>
                                            <th>Método</th>
                                            <th>Banco / Nro. Op.</th>
                                            <th>Monto</th>
                                            <th>Estado</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {visibles.map((egreso, idx) => (
                                            <tr key={egreso.id}>
                                                <td style={{ color: '#94a3b8' }}>
                                                    {(paginaActual - 1) * FILAS_POR_PAGINA + idx + 1}
                                                </td>
                                                <td>{fechaLegible(egreso.fecha)}</td>
                                                <td style={{ fontWeight: '600', color: '#0f172a' }}>{egreso.categoria}</td>
                                                <td>{egreso.descripcion || '-'}</td>
                                                <td>{egreso.metodo_pago_label}</td>
                                                <td>
                                                    {egreso.banco || egreso.nro_operacion
                                                        ? [egreso.banco, egreso.nro_operacion].filter(Boolean).join(' / ')
                                                        : '-'}
                                                </td>
                                                <td style={{ fontWeight: '700', color: '#dc2626' }}>{bs(egreso.monto)}</td>
                                                <td>
                                                    <span className={badgeEstado(egreso.estado)}>{egreso.estado_label}</span>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                    <tfoot>
                                        <tr className="tabla-custom-total">
                                            <td colSpan={6} style={{ textAlign: 'right' }}>
                                                TOTAL ({filas.length} de {egresos.length})
                                            </td>
                                            <td style={{ fontWeight: 800, color: '#dc2626' }}>{bs(total)}</td>
                                            <td />
                                        </tr>
                                    </tfoot>
                                </table>
                            </div>
                            <Paginacion pagina={paginaActual} totalPaginas={totalPaginas} onCambiar={setPagina} />
                        </>
                    )}
                </>
            ) : (
                <p className="estado-vacio">{mensajeVacio}</p>
            )}
        </div>
    );
}

function TablaResumenCategoriasEgreso({ categorias, resumen }) {
    return (
        <div className="seccion-card">
            <h3 className="seccion-card-title">📊 Egresos por Categoría</h3>
            <div className="tabla-wrapper">
                <table className="tabla-custom">
                    <thead>
                        <tr>
                            <th>Categoría</th>
                            <th>N° Egresos</th>
                            <th>Total</th>
                            <th>% del Total</th>
                            <th>Promedio</th>
                            <th>Mayor Egreso</th>
                            <th>Pendientes</th>
                            <th>Anulados</th>
                        </tr>
                    </thead>
                    <tbody>
                        {categorias.map(item => (
                            <tr key={item.categoria.id}>
                                <td style={{ fontWeight: '700', color: '#0f172a' }}>{item.categoria.nombre}</td>
                                <td><span className="badge-pill info">{item.count_egresos}</span></td>
                                <td style={{ fontWeight: '700', color: '#dc2626' }}>{bs(item.total_egresos)}</td>
                                <td><BarraParticipacion porcentaje={item.porcentaje_participacion} /></td>
                                <td>{bs(item.promedio_egreso)}</td>
                                <td>{bs(item.egreso_maximo)}</td>
                                <td>
                                    <span className={`badge-pill ${item.count_pendientes_aprobacion > 0 ? 'warning' : 'success'}`}>
                                        {item.count_pendientes_aprobacion}
                                    </span>
                                </td>
                                <td>
                                    <span className={`badge-pill ${item.count_anulados > 0 ? 'danger' : 'success'}`}>
                                        {item.count_anulados}
                                    </span>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                    <tfoot>
                        <tr className="tabla-custom-total">
                            <td>TOTAL GENERAL</td>
                            <td>{resumen.count_egresos}</td>
                            <td style={{ fontWeight: 800, color: '#dc2626' }}>{bs(resumen.total_egresos)}</td>
                            <td>100%</td>
                            <td>{bs(resumen.promedio_egreso)}</td>
                            <td>{bs(resumen.egreso_maximo)}</td>
                            <td>{resumen.count_pendientes_aprobacion}</td>
                            <td>{resumen.count_anulados}</td>
                        </tr>
                    </tfoot>
                </table>
            </div>
        </div>
    );
}

function TablaMetodosPago({ metodos, totalGeneral }) {
    if (!metodos?.length) return null;
    return (
        <div className="seccion-card">
            <h3 className="seccion-card-title">💳 Desglose por Método de Pago</h3>
            <div className="tabla-wrapper">
                <table className="tabla-custom">
                    <thead>
                        <tr>
                            <th>Método de Pago</th>
                            <th>N° Egresos</th>
                            <th>Total</th>
                            <th>% del Total</th>
                        </tr>
                    </thead>
                    <tbody>
                        {metodos.map(m => {
                            const pct = totalGeneral > 0
                                ? Math.round((m.total / totalGeneral) * 1000) / 10
                                : 0;
                            return (
                                <tr key={m.metodo_pago}>
                                    <td style={{ fontWeight: '600', color: '#0f172a' }}>{m.metodo_pago_label}</td>
                                    <td><span className="badge-pill info">{m.count}</span></td>
                                    <td style={{ fontWeight: '700', color: '#dc2626' }}>{bs(m.total)}</td>
                                    <td><BarraParticipacion porcentaje={pct} /></td>
                                </tr>
                            );
                        })}
                    </tbody>
                </table>
            </div>
        </div>
    );
}

function IndicadoresCategoriaEgreso({ reporte }) {
    const cat = reporte.resumen;
    const global = reporte.resumen_global;
    const filas = [
        ['Total de la categoría', bs(cat.total_egresos)],
        ['Número de egresos', <span className="badge-pill info" key="n">{cat.count_egresos}</span>],
        ['Promedio por egreso', bs(cat.promedio_egreso)],
        ['Egreso más alto', bs(cat.egreso_maximo)],
        ['Egreso más bajo', bs(cat.egreso_minimo)],
        ['Participación en el total general', `${cat.porcentaje_participacion}%`],
        ['Primer egreso', cat.fecha_primer_egreso || '-'],
        ['Último egreso', cat.fecha_ultimo_egreso || '-'],
        ['Total general de egresos del período', `${bs(global.total_egresos)} (${global.count_egresos} egresos)`],
        ['Pendientes de aprobación', (
            <span key="p">
                <span className="badge-pill warning">{cat.count_pendientes_aprobacion}</span>{' '}
                {bs(cat.total_pendientes_aprobacion)}
            </span>
        )],
        ['Egresos anulados', (
            <span key="a">
                <span className="badge-pill danger">{cat.count_anulados}</span>{' '}
                {bs(cat.total_anulados)}
            </span>
        )],
    ];

    return (
        <div className="seccion-card">
            <h3 className="seccion-card-title">📈 Indicadores de la Categoría</h3>
            <div className="tabla-wrapper">
                <table className="tabla-custom">
                    <thead>
                        <tr><th>Indicador</th><th>Valor</th></tr>
                    </thead>
                    <tbody>
                        {filas.map(([label, valor]) => (
                            <tr key={label}>
                                <td style={{ fontWeight: '600', color: '#0f172a' }}>{label}</td>
                                <td>{valor}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}

function VistaEgresos({ reporte }) {
    if (reporte.categorias) {
        const r = reporte.resumen;
        return (
            <>
                <div className="kpis-container-grid">
                    <KpiEgresos icono="💸" clase="recaudado" label="Total Egresos"
                        valor={bs(r.total_egresos)} color="#dc2626" />
                    <KpiEgresos icono="🧾" clase="categorias" label="N° de Egresos" valor={r.count_egresos} />
                    <KpiEgresos icono="📊" clase="esperado" label="Promedio por Egreso" valor={bs(r.promedio_egreso)} />
                    <KpiEgresos icono="⚠️" clase="faltante" label="Pendientes Aprobación"
                        valor={`${r.count_pendientes_aprobacion} · ${bs(r.total_pendientes_aprobacion)}`}
                        color="#b45309" />
                    <KpiEgresos icono="🚫" clase="anulado" label="Anulados"
                        valor={`${r.count_anulados} · ${bs(r.total_anulados)}`} color="#94a3b8" />
                    <KpiEgresos icono="🏷️" clase="afiliados" label="Categorías"
                        valor={`${r.total_categorias} / ${r.total_categorias_registradas}`} />
                </div>

                <TablaResumenCategoriasEgreso categorias={reporte.categorias} resumen={r} />
                <TablaMetodosPago metodos={r.por_metodo_pago} totalGeneral={r.total_egresos} />
                <TablaDetalleEgresos egresos={reporte.egresos} titulo="🧾 Detalle de Egresos Aprobados"
                    colorTitulo="#059669" mensajeVacio="No hay egresos aprobados en el período seleccionado." />
                <TablaDetalleEgresos egresos={reporte.egresos_revision}
                    titulo="⚠️ Pendientes de Aprobación / Anulados" colorTitulo="#b45309"
                    mensajeVacio="No hay egresos pendientes de aprobación ni anulados en esta categoría." />
            </>
        );
    }

    const cat = reporte.resumen;
    return (
        <>
            <div className="kpis-container-grid">
                <KpiEgresos icono="💸" clase="recaudado" label={`Total — ${cat.categoria.nombre}`}
                    valor={bs(cat.total_egresos)} color="#dc2626" />
                <KpiEgresos icono="🧾" clase="categorias" label="N° de Egresos" valor={cat.count_egresos} />
                <KpiEgresos icono="📊" clase="esperado" label="Promedio" valor={bs(cat.promedio_egreso)} />
                <KpiEgresos icono="🔝" clase="faltante" label="Mayor Egreso" valor={bs(cat.egreso_maximo)} />
                <KpiEgresos icono="📉" clase="esperado" label="Menor Egreso" valor={bs(cat.egreso_minimo)} />
                <KpiEgresos icono="🥧" clase="afiliados" label="% del Total General"
                    valor={`${cat.porcentaje_participacion}%`} />
            </div>

            <IndicadoresCategoriaEgreso reporte={reporte} />
            <TablaDetalleEgresos egresos={reporte.egresos} titulo="🧾 Detalle de Egresos Aprobados"
                colorTitulo="#059669" mensajeVacio="No hay egresos aprobados en el período seleccionado." />
            <TablaDetalleEgresos egresos={reporte.egresos_revision}
                titulo="⚠️ Pendientes de Aprobación / Anulados" colorTitulo="#b45309"
                mensajeVacio="No hay egresos pendientes de aprobación ni anulados en esta categoría." />
        </>
    );
}

function VistaIngresos({ reporte }) {
    const [busquedaCategorias, setBusquedaCategorias] = useState('');

    const categoriasVisibles = useMemo(() => {
        const termino = normalizar(busquedaCategorias);
        if (!termino) return reporte.categorias;
        return reporte.categorias.filter(item =>
            normalizar(item.categoria.nombre).includes(termino)
        );
    }, [reporte.categorias, busquedaCategorias]);

    if (reporte.categorias) {
        return (
            <>
                <div className="kpis-container-grid">
                    <div className="kpi-stat-card">
                        <div className="kpi-stat-icon recaudado">💰</div>
                        <div className="kpi-stat-info">
                            <label>Total Recaudado</label>
                            <div className="value">{bs(reporte.resumen.total_recaudado)}</div>
                        </div>
                    </div>
                    {reporte.resumen.total_esperado !== null && reporte.resumen.total_esperado !== undefined && (
                        <div className="kpi-stat-card">
                            <div className="kpi-stat-icon esperado">📌</div>
                            <div className="kpi-stat-info">
                                <label>Total Esperado</label>
                                <div className="value">{bs(reporte.resumen.total_esperado)}</div>
                            </div>
                        </div>
                    )}
                    {reporte.resumen.monto_faltante !== null && reporte.resumen.monto_faltante !== undefined && (
                        <div className="kpi-stat-card">
                            <div className="kpi-stat-icon faltante">⚠️</div>
                            <div className="kpi-stat-info">
                                <label>Monto Faltante</label>
                                <div className="value" style={{ color: '#dc2626' }}>{bs(reporte.resumen.monto_faltante)}</div>
                            </div>
                        </div>
                    )}
                    <div className="kpi-stat-card">
                        <div className="kpi-stat-icon categorias">🎯</div>
                        <div className="kpi-stat-info">
                            <label>Categorías</label>
                            <div className="value">{reporte.resumen.total_categorias}</div>
                        </div>
                    </div>
                    <div className="kpi-stat-card">
                        <div className="kpi-stat-icon afiliados">👥</div>
                        <div className="kpi-stat-info">
                            <label>Afiliados Activos</label>
                            <div className="value">{reporte.resumen.total_afiliados_activos}</div>
                        </div>
                    </div>
                    <div className="kpi-stat-card">
                        <div className="kpi-stat-icon faltante">❌</div>
                        <div className="kpi-stat-info">
                            <label>Deudas Registradas</label>
                            <div className="value" style={{ color: '#dc2626' }}>
                                {reporte.resumen.total_pendientes}
                            </div>
                            <small className="kpi-nota">
                                {reporte.categorias.reduce((acc, c) => acc + (c.count_parciales || 0), 0)} pagos parciales
                            </small>
                        </div>
                    </div>
                </div>

                <div className="seccion-card">
                    <h3 className="seccion-card-title">📊 Resumen Clasificado por Categoría</h3>
                    <div className="tabla-herramientas">
                        <BuscadorTabla
                            valor={busquedaCategorias}
                            onChange={setBusquedaCategorias}
                            placeholder="Buscar categoría"
                        />
                    </div>
                    <div className="tabla-wrapper">
                        <table className="tabla-custom">
                            <thead>
                                <tr>
                                    <th>Categoría</th>
                                    <th>Ya Cancelaron</th>
                                    <th>Faltan Pagar</th>
                                    <th>Afiliados Activos</th>
                                    <th>% Cobertura</th>
                                    <th>Total Recaudado</th>
                                    <th>Total Esperado</th>
                                    <th>Monto Faltante</th>
                                    <th>Revisión</th>
                                    <th>Duplicados</th>
                                </tr>
                            </thead>
                            <tbody>
                                {categoriasVisibles.map(item => (
                                    <tr key={item.categoria.id}>
                                        <td style={{ fontWeight: '700', color: '#0f172a' }}>{item.categoria.nombre}</td>
                                        <td><span className="badge-pill success">{item.count_pagaron}</span></td>
                                        <td><span className="badge-pill danger">{item.count_pendientes}</span></td>
                                        <td>{item.total_afiliados_activos}</td>
                                        <td>
                                            <span className={`badge-pill ${item.porcentaje_cobertura >= 70 ? 'success' : item.porcentaje_cobertura >= 40 ? 'warning' : 'danger'}`}>
                                                {item.porcentaje_cobertura}%
                                            </span>
                                        </td>
                                        <td style={{ fontWeight: '700', color: '#059669' }}>{bs(item.total_recaudado)}</td>
                                        <td>{item.total_esperado != null ? bs(item.total_esperado) : '-'}</td>
                                        <td style={{ color: '#dc2626', fontWeight: '700' }}>{item.monto_faltante != null ? bs(item.monto_faltante) : '-'}</td>
                                        <td>{(item.count_pagos_pendientes_revision || 0) + (item.count_pagos_anulados_cancelados || 0)}</td>
                                        <td>{item.count_afiliados_con_pago_duplicado || 0}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                    {categoriasVisibles.length === 0 && (
                        <p className="estado-vacio">Sin categorías para «{busquedaCategorias}».</p>
                    )}
                </div>

                <TablaDuplicados
                    duplicados={reporte.duplicados || []}
                    conCategoria
                    montoTotal={reporte.resumen.total_afiliados_con_pago_duplicado}
                />

                {reporte.categorias
                    .filter(item => (item.pendientes?.length || 0) > 0)
                    .map(item => (
                        <TablaPendientes
                            key={`pend_${item.categoria.id}`}
                            titulo={`Faltan Cancelar: ${item.categoria.nombre}`}
                            subtitulo={`${item.count_sin_pago} sin ningún pago · ${item.count_parciales} con pago parcial`}
                            pendientes={item.pendientes}
                            totalPendientes={item.count_pendientes}
                            montoTotalPendiente={item.monto_total_pendiente}
                            montoEsperado={item.monto_esperado_por_afiliado}
                            truncados={item.pendientes_truncados}
                            mensajeVacio="Todos los afiliados activos cancelaron esta categoría."
                        />
                    ))}
            </>
        );
    }

    return (
        <>
            <div className="kpis-container-grid">
                <div className="kpi-stat-card">
                    <div className="kpi-stat-icon recaudado">💰</div>
                    <div className="kpi-stat-info">
                        <label>Total Recaudado</label>
                        <div className="value">{bs(reporte.resumen.total_recaudado)}</div>
                    </div>
                </div>
                <div className="kpi-stat-card">
                    <div className="kpi-stat-icon afiliados">✅</div>
                    <div className="kpi-stat-info">
                        <label>Afiliados que Pagaron</label>
                        <div className="value">
                            {reporte.resumen.count_pagaron}{' '}
                            <span style={{ fontSize: '0.85rem', color: '#64748b', fontWeight: '500' }}>
                                / {reporte.resumen.total_afiliados_activos}
                            </span>
                        </div>
                    </div>
                </div>
                <div className="kpi-stat-card">
                    <div className="kpi-stat-icon faltante">❌</div>
                    <div className="kpi-stat-info">
                        <label>Afiliados Pendientes</label>
                        <div className="value" style={{ color: '#dc2626' }}>{reporte.resumen.count_pendientes}</div>
                        <small className="kpi-nota">
                            {reporte.resumen.count_sin_pago} sin pago · {reporte.resumen.count_parciales} parcial
                        </small>
                    </div>
                </div>
                {reporte.resumen.total_esperado !== null && reporte.resumen.total_esperado !== undefined && (
                    <div className="kpi-stat-card">
                        <div className="kpi-stat-icon esperado">📌</div>
                        <div className="kpi-stat-info">
                            <label>Total Esperado</label>
                            <div className="value">{bs(reporte.resumen.total_esperado)}</div>
                        </div>
                    </div>
                )}
                {reporte.resumen.monto_faltante !== null && reporte.resumen.monto_faltante !== undefined && (
                    <div className="kpi-stat-card">
                        <div className="kpi-stat-icon faltante">⚠️</div>
                        <div className="kpi-stat-info">
                            <label>Monto Faltante</label>
                            <div className="value" style={{ color: '#dc2626' }}>{bs(reporte.resumen.monto_faltante)}</div>
                        </div>
                    </div>
                )}
                <div className="kpi-stat-card">
                    <div className="kpi-stat-icon categorias">📊</div>
                    <div className="kpi-stat-info">
                        <label>% Cobertura</label>
                        <div className="value">{reporte.resumen.porcentaje_cobertura}%</div>
                    </div>
                </div>
            </div>

            <div className="seccion-card">
                <h3 className="seccion-card-title">⚠️ Alertas de Revisión</h3>
                <div className="tabla-wrapper">
                    <table className="tabla-custom">
                        <thead>
                            <tr><th>Indicador</th><th>Cantidad</th><th>Monto</th></tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>Pagos pendientes de revisión</td>
                                <td><span className="badge-pill warning">{reporte.resumen.count_pagos_pendientes_revision || 0}</span></td>
                                <td>{bs(reporte.resumen.total_pagos_pendientes_revision)}</td>
                            </tr>
                            <tr>
                                <td>Pagos anulados/cancelados</td>
                                <td><span className="badge-pill danger">{reporte.resumen.count_pagos_anulados_cancelados || 0}</span></td>
                                <td>{bs(reporte.resumen.total_pagos_anulados_cancelados)}</td>
                            </tr>
                            <tr>
                                <td>Afiliados con posible pago duplicado</td>
                                <td><span className="badge-pill info">{reporte.resumen.count_afiliados_con_pago_duplicado || 0}</span></td>
                                <td>-</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <TablaDuplicados
                duplicados={reporte.duplicados || []}
                montoTotal={reporte.resumen.count_afiliados_con_pago_duplicado}
            />

            <TablaPendientes
                titulo={`Afiliados que FALTAN Cancelar — ${reporte.categoria.nombre}`}
                subtitulo={`${reporte.resumen.count_sin_pago} sin ningún pago · ${reporte.resumen.count_parciales} con pago parcial`}
                pendientes={reporte.pendientes}
                totalPendientes={reporte.resumen.count_pendientes}
                montoTotalPendiente={reporte.resumen.monto_total_pendiente}
                montoEsperado={reporte.resumen.monto_esperado_por_afiliado}
                truncados={reporte.resumen.pendientes_truncados}
                mensajeVacio="¡Excelente! Todos los afiliados activos han cancelado esta categoría en el período seleccionado."
            />

            <div className="seccion-card">
                <h3 className="seccion-card-title" style={{ color: '#059669' }}>
                    ✅ Afiliados que YA Cancelaron ({reporte.pagaron.length} pagos)
                </h3>
                {reporte.pagaron.length > 0 ? (
                    <div className="tabla-wrapper">
                        <table className="tabla-custom">
                            <thead>
                                <tr>
                                    <th>#</th><th>Nombre Completo</th><th>C.I.</th><th>Fecha Pago</th>
                                    <th>Monto</th><th>Estado</th><th>Nro. Recibo</th>
                                </tr>
                            </thead>
                            <tbody>
                                {reporte.pagaron.map((pago, idx) => (
                                    <tr key={`${pago.afiliado_id}-${idx}`}>
                                        <td style={{ color: '#94a3b8' }}>{idx + 1}</td>
                                        <td style={{ fontWeight: '600', color: '#0f172a' }}>{pago.nombre}</td>
                                        <td>{pago.ci}</td>
                                        <td>{new Date(pago.fecha_pago).toLocaleDateString()}</td>
                                        <td style={{ fontWeight: '700', color: '#059669' }}>{bs(pago.monto)}</td>
                                        <td><span className="badge-pill success">{pago.estado}</span></td>
                                        <td>{pago.nro_recibo || '-'}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                ) : (
                    <p style={{ padding: '1.5rem', textAlign: 'center', color: '#64748b' }}>
                        No hay registros de pagos para esta categoría en el período seleccionado.
                    </p>
                )}
            </div>
        </>
    );
}

function ReportePorCategoria() {
    const [tipoReporte, setTipoReporte] = useState('ingreso');
    const esEgreso = tipoReporte === 'egreso';

    const [tiposPago, setTiposPago] = useState([]);
    const [filtros, setFiltros] = useState(FILTROS_INICIO);
    const [reporte, setReporte] = useState(null);
    const [loading, setLoading] = useState(false);
    const [descargando, setDescargando] = useState(null);
    const [error, setError] = useState('');

    useEffect(() => {
        let cancelado = false;
        const cargarTiposPago = async () => {
            try {
                const res = await api.getReporteCategoria({ tipo: tipoReporte });
                if (!cancelado && res.data?.tipos_pago) {
                    setTiposPago(res.data.tipos_pago);
                }
            } catch (err) {
                console.error(`Error al cargar categorías de ${tipoReporte}:`, err);
                if (!cancelado) setError(`Error al cargar categorías de ${tipoReporte === 'egreso' ? 'egreso' : 'ingreso'}`);
            }
        };
        cargarTiposPago();
        return () => { cancelado = true; };
    }, [tipoReporte]);

    const handleTipoChange = (nuevoTipo) => {
        setTipoReporte(nuevoTipo);
        setFiltros(FILTROS_INICIO);
        setTiposPago([]);
        setReporte(null);
        setError('');
    };

    const handleFilterChange = (e) => {
        const { name, value } = e.target;
        setFiltros(prev => ({ ...prev, [name]: value }));
    };

    const aplicarPeriodo = (meses) => {
        const hoy = new Date();
        const inicio = new Date(hoy.getFullYear(), hoy.getMonth() - (meses - 1), 1);
        setFiltros(prev => ({
            ...prev,
            fecha_inicio: inicio.toISOString().slice(0, 10),
            fecha_fin: hoy.toISOString().slice(0, 10)
        }));
    };

    const aplicarTodo = () => {
        setFiltros(prev => ({ ...prev, fecha_inicio: '', fecha_fin: '' }));
    };

    const buildParams = (conNombreCategoria = false) => {
        const params = filtros.tipo_pago_id === 'todos'
            ? { todas: '1' }
            : { tipo_pago_id: filtros.tipo_pago_id };
        params.tipo = tipoReporte;
        if (filtros.fecha_inicio) params.fecha_inicio = filtros.fecha_inicio;
        if (filtros.fecha_fin) params.fecha_fin = filtros.fecha_fin;
        if (!esEgreso && filtros.monto_esperado) params.monto_esperado = filtros.monto_esperado;
        if (conNombreCategoria) {
            if (filtros.tipo_pago_id === 'todos') {
                params.nombre_categoria = 'todas_las_categorias';
            } else {
                const seleccionada = tiposPago.find(t => t.id.toString() === filtros.tipo_pago_id.toString());
                params.nombre_categoria = seleccionada ? seleccionada.nombre : '';
            }
        }
        return params;
    };

    const cargarReporte = async () => {
        if (!filtros.tipo_pago_id) {
            setError('Debe seleccionar una categoría');
            return;
        }
        if (filtros.fecha_inicio && filtros.fecha_fin && filtros.fecha_inicio > filtros.fecha_fin) {
            setError('La fecha "Desde" no puede ser posterior a la fecha "Hasta"');
            return;
        }
        try {
            setLoading(true);
            setError('');
            const res = await api.getReporteCategoria(buildParams());
            if (res.data && (res.data.resumen || res.data.categorias)) {
                setReporte(res.data);
            } else {
                setError(res.data?.error || 'Error al generar reporte');
            }
        } catch (err) {
            console.error('Error al cargar el reporte:', err);
            setError(err.response?.data?.error || 'Error al cargar el reporte');
            setReporte(null);
        } finally {
            setLoading(false);
        }
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        cargarReporte();
    };

    const descargar = async (formato) => {
        if (!filtros.tipo_pago_id || descargando) return;
        try {
            setDescargando(formato);
            setError('');
            const params = buildParams(true);
            const res = formato === 'pdf'
                ? await api.downloadReporteCategoriaPdf(params)
                : await api.downloadReporteCategoriaExcel(params);
            if (!res.success) {
                setError(`Error al descargar ${formato.toUpperCase()}: ${res.error}`);
            }
        } catch (err) {
            console.error(`Error al descargar ${formato.toUpperCase()}:`, err);
            setError(`Error al descargar ${formato.toUpperCase()}`);
        } finally {
            setDescargando(null);
        }
    };

    return (
        <div className="reporte-categoria-wrapper">
            <div className="categoria-hero">
                <div className="hero-title-group">
                    <span className="hero-icon">🎯</span>
                    <div>
                        <h1>Reporte por Categoría</h1>
                        <p>
                            {esEgreso
                                ? 'Analiza todos los egresos registrados y genera el reporte por categoría de gasto'
                                : 'Analiza el estado de cumplimiento y pagos de afiliados por concepto de ingreso'}
                        </p>
                    </div>
                </div>
            </div>

            <div className="tipo-reporte-switch">
                <button
                    type="button"
                    className={`tipo-reporte-btn ${!esEgreso ? 'active' : ''}`}
                    onClick={() => handleTipoChange('ingreso')}
                    disabled={loading}
                >
                    💰 Ingresos
                </button>
                <button
                    type="button"
                    className={`tipo-reporte-btn egreso ${esEgreso ? 'active' : ''}`}
                    onClick={() => handleTipoChange('egreso')}
                    disabled={loading}
                >
                    💸 Egresos
                </button>
            </div>

            <div className="filtros-card">
                <div className="filtros-card-header">
                    <span>⚡ Parámetros del Reporte</span>
                    <div className="atajos-periodo">
                        {[1, 3, 6, 12].map(meses => (
                            <button
                                key={meses}
                                type="button"
                                className="chip-periodo"
                                onClick={() => aplicarPeriodo(meses)}
                                disabled={loading}
                            >
                                {meses}m
                            </button>
                        ))}
                        <button type="button" className="chip-periodo" onClick={() => aplicarTodo()} disabled={loading}>
                            Todo
                        </button>
                    </div>
                </div>
                <form className="filtros-grid" onSubmit={handleSubmit}>
                    <div className="filtro-field">
                        <label>🏷️ Categoría de {esEgreso ? 'Egreso' : 'Ingreso'}:</label>
                        <select
                            className="filtro-control"
                            name="tipo_pago_id"
                            value={filtros.tipo_pago_id}
                            onChange={handleFilterChange}
                            required
                        >
                            <option value="todos">Todas las categorías</option>
                            {tiposPago.map(tipo => (
                                <option key={tipo.id} value={tipo.id}>{tipo.nombre}</option>
                            ))}
                        </select>
                    </div>
                    <div className="filtro-field">
                        <label>📅 Fecha Desde:</label>
                        <input className="filtro-control" type="date" name="fecha_inicio"
                            value={filtros.fecha_inicio} onChange={handleFilterChange} />
                    </div>
                    <div className="filtro-field">
                        <label>📅 Fecha Hasta:</label>
                        <input className="filtro-control" type="date" name="fecha_fin"
                            value={filtros.fecha_fin} onChange={handleFilterChange} />
                    </div>
                    {!esEgreso && (
                        <div className="filtro-field">
                            <label>💵 Monto Esperado por Afiliado:</label>
                            <input className="filtro-control" type="number" name="monto_esperado" min="0"
                                step="0.01" placeholder="Ej: 50.00" value={filtros.monto_esperado}
                                onChange={handleFilterChange} />
                        </div>
                    )}
                    <div className="filtro-field">
                        <button type="submit" className="btn-generar-reporte" disabled={loading}>
                            {loading ? <>⌛ Generando...</> : <>🔍 Generar Reporte</>}
                        </button>
                    </div>
                </form>
                {error && (
                    <div className="alerta-error" role="alert">⚠️ {error}</div>
                )}
            </div>

            {loading && (
                <div className="cargando-panel">
                    <div className="spinner" />
                    <p>Generando reporte…</p>
                </div>
            )}

            {reporte && (
                <>
                    <div className="export-toolbar">
                        <div className="export-toolbar-info">
                            <span>📄 Formatos de descarga oficial listos:</span>
                            <span className="export-toolbar-periodo">
                                {reporte.filtros?.fecha_inicio || 'inicio'} → {reporte.filtros?.fecha_fin || 'hoy'}
                            </span>
                        </div>
                        <div className="export-toolbar-actions">
                            <button className="btn-export-pill print" onClick={() => window.print()}>
                                🖨️ Imprimir
                            </button>
                            <button
                                className="btn-export-pill pdf"
                                onClick={() => descargar('pdf')}
                                disabled={!!descargando}
                            >
                                {descargando === 'pdf' ? '⏳ Generando PDF…' : '📄 Exportar a PDF'}
                            </button>
                            <button
                                className="btn-export-pill excel"
                                onClick={() => descargar('excel')}
                                disabled={!!descargando}
                            >
                                {descargando === 'excel' ? '⏳ Generando Excel…' : '📊 Exportar a Excel'}
                            </button>
                        </div>
                    </div>

                    {esEgreso ? <VistaEgresos reporte={reporte} /> : <VistaIngresos reporte={reporte} />}
                </>
            )}
        </div>
    );
}

export default ReportePorCategoria;
