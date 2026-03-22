import axios from 'axios';

export const API_URL = import.meta.env.VITE_API_URL || '/api';

// Configurar base URL
axios.defaults.baseURL = API_URL;
axios.defaults.withCredentials = false;

// Función auxiliar para descargar archivos con autenticación
const downloadFile = async (url, filename) => {
    try {
        const accessToken = localStorage.getItem('accessToken');
        const response = await axios.get(url, {
            responseType: 'blob',
            headers: {
                'Authorization': accessToken ? `Bearer ${accessToken}` : ''
            }
        });

        // Crear un enlace temporal para descargar el archivo
        const blob = new Blob([response.data]);
        const link = document.createElement('a');
        link.href = window.URL.createObjectURL(blob);
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(link.href);

        return { success: true };
    } catch (error) {
        console.error('Error downloading file:', error);
        return {
            success: false,
            error: error.response?.data?.detail || 'Error al descargar el archivo'
        };
    }
};

export const axiosInstance = axios;

export const api = {
    // Dashboard
    getDashboard: () => axios.get('/dashboard'),

    // Encomiendas
    getEncomiendas: (params) => axios.get('/encomiendas/', { params }),
    getEncomienda: (id) => axios.get(`/encomiendas/${id}/`),
    createEncomienda: (data) => axios.post('/encomiendas/', data),
    updateEncomienda: (id, data) => axios.put(`/encomiendas/${id}/`, data),
    deleteEncomienda: (id) => axios.delete(`/encomiendas/${id}/`),
    cambiarEstadoEncomienda: (id, estado) => axios.post(`/encomiendas/${id}/cambiar_estado/`, { estado }),
    asignarHojaEncomienda: (id, hojaId) => axios.post(`/encomiendas/${id}/asignar_hoja/`, { hoja_ruta_id: hojaId }),
    generarQrEncomienda: (id) => axios.get(`/encomiendas/${id}/generar_qr/`),
    notificarWhatsappEncomienda: (id, tipo) => axios.post(`/encomiendas/${id}/notificar_whatsapp/`, { tipo }),


    // Afiliados
    getAfiliados: (params) => axios.get('/afiliados/', { params }),
    getAfiliado: (id) => axios.get(`/afiliados/${id}/`),
    getListaTurnoLaPaz: () => axios.get('/afiliados/lista_turno_la_paz/'),
    createAfiliado: (data) => axios.post('/afiliados/', data),
    updateAfiliado: (id, data) => axios.put(`/afiliados/${id}/`, data),
    deleteAfiliado: (id) => axios.delete(`/afiliados/${id}/`),
    generarListaPunteros: () => axios.get('/afiliados/generar_lista_punteros/'),
    generarNominaAgentes: () => axios.get('/afiliados/generar_nomina_agentes/'),
    generarTurnos: () => axios.post('/afiliados/generar_turnos/'),
    getTurnoDelDia: (fecha) => axios.get(`/afiliados/turno_del_dia/?fecha=${fecha}`),
    generarPagoQrTotalAfiliado: (id) => axios.post(`/afiliados/${id}/generar_pago_qr_total/`),
    getMiPerfil: () => axios.get('/afiliados/mi_perfil/'),
    getKioscoConsulta: (ci, ci_exp) => axios.get(`/afiliados/kiosco_consulta/?ci=${ci}&ci_exp=${ci_exp}`),

    // Nuevas funciones - Fase 3: Reservas con QR
    generarQrReserva: (id) => axios.get(`/reservas/${id}/generar_qr/`, { responseType: 'blob' }),
    generarConfirmacionPdf: (id) => axios.get(`/reservas/${id}/generar_confirmacion_pdf/`, { responseType: 'blob' }),
    enviarConfirmacionWhatsapp: (id, data) => axios.post(`/reservas/${id}/enviar_confirmacion_whatsapp/`, data),

    // Nuevas funciones - Fase 4: Recibos Automáticos
    generarReciboPago: (id) => axios.get(`/pagos/${id}/generar_recibo/`, { responseType: 'blob' }),

    // Nuevas funciones - Fase 5: Asistencia Mejorada
    getInasistenciasFrecuentes: (params) => axios.get('/asistencias/inasistencias_frecuentes/', { params }),
    getEstadisticasAsistencia: () => axios.get('/asistencias/estadisticas_generales/'),

    // Nuevas funciones - Fase 7: Reportes Adicionales
    getAfiliadosMorosos: (params) => axios.get('/reportes/afiliados-morosos/', { params }),
    getRutasRentables: (params) => axios.get('/reportes/rutas-rentables/', { params }),
    getOcupacionHistorica: (params) => axios.get('/reportes/ocupacion-historica/', { params }),



    // Vehículos
    getVehiculos: (params) => axios.get('/vehiculos/', { params }),
    getVehiculo: (id) => axios.get(`/vehiculos/${id}/`),
    createVehiculo: (data) => axios.post('/vehiculos/', data),
    updateVehiculo: (id, data) => axios.put(`/vehiculos/${id}/`, data),
    deleteVehiculo: (id) => axios.delete(`/vehiculos/${id}/`),

    // Directorio
    getDirectorio: (params) => axios.get('/directorio/', { params }),
    getMiembroDirectorio: (id) => axios.get(`/directorio/${id}/`),
    createMiembroDirectorio: (data) => axios.post('/directorio/', data),
    updateMiembroDirectorio: (id, data) => axios.put(`/directorio/${id}/`, data),
    deleteMiembroDirectorio: (id) => axios.delete(`/directorio/${id}/`),

    // Rutas
    getRutas: (params) => axios.get('/rutas/', { params }),
    getRuta: (id) => axios.get(`/rutas/${id}/`),
    createRuta: (data) => axios.post('/rutas/', data),
    updateRuta: (id, data) => axios.put(`/rutas/${id}/`, data),
    deleteRuta: (id) => axios.delete(`/rutas/${id}/`),

    // Hojas de Ruta
    getHojasRuta: (params) => axios.get('/hojas-ruta/', { params }),
    getHojaRuta: (id) => axios.get(`/hojas-ruta/${id}/`),
    createHojaRuta: (data) => axios.post('/hojas-ruta/', data),
    updateHojaRuta: (id, data) => axios.put(`/hojas-ruta/${id}/`, data),
    deleteHojaRuta: (id) => axios.delete(`/hojas-ruta/${id}/`),
    generarPdfHoja: (id) => axios.post(`/hojas-ruta/${id}/generar_pdf/`),
    generarPlanillaLaPaz: (id) => axios.get(`/hojas-ruta/${id}/generar_planilla_la_paz/`, { responseType: 'blob' }),
    enviarHojaWhatsapp: (id, data) => axios.post(`/hojas-ruta/${id}/notificar/`, data),
    validarQr: (id) => axios.get(`/hojas-ruta/${id}/validar_qr/`),
    getPunteroHoy: () => axios.get('/hojas-ruta/puntero_hoy/'),

    // Rutas

    // Cuotas
    getCuotas: (params) => axios.get('/cuotas/', { params }),
    getCuota: (id) => axios.get(`/cuotas/${id}/`),
    createCuota: (data) => axios.post('/cuotas/', data),
    updateCuota: (id, data) => axios.put(`/cuotas/${id}/`, data),
    deleteCuota: (id) => axios.delete(`/cuotas/${id}/`),
    cambiarEstadoCuota: (id, estado) => axios.post(`/cuotas/${id}/cambiar_estado/`, { estado }),
    notificarCuota: (id, data) => axios.post(`/cuotas/${id}/notificar/`, data),
    generarPagoQrCuota: (id) => axios.post(`/cuotas/${id}/generar_pago_qr/`),

    // Reuniones
    getReuniones: (params) => axios.get('/reuniones/', { params }),
    getReunion: (id) => axios.get(`/reuniones/${id}/`),
    createReunion: (data) => axios.post('/reuniones/', data),
    updateReunion: (id, data) => axios.put(`/reuniones/${id}/`, data),
    deleteReunion: (id) => axios.delete(`/reuniones/${id}/`),
    cerrarReunion: (id) => axios.post(`/reuniones/${id}/cerrar_reunion/`),
    
    // Turnos Salida (Puntero La Paz)
    getTurnosSalida: (params) => axios.get('/turnos-salida/', { params }),
    generarProgramacionSalida: () => axios.post('/turnos-salida/generar_programacion/'),
    deleteTurnoSalida: (id) => axios.delete(`/turnos-salida/${id}/`),


    // Asistencias
    createAsistencia: (data) => axios.post('/asistencias/', data),
    updateAsistencia: (id, data) => axios.put(`/asistencias/${id}/`, data),

    // Sanciones
    getSanciones: (params) => axios.get('/sanciones/', { params }),
    createSancion: (data) => axios.post('/sanciones/', data),
    updateSancion: (id, data) => axios.put(`/sanciones/${id}/`, data),
    deleteSancion: (id) => axios.delete(`/sanciones/${id}/`),
    cambiarEstadoSancion: (id, estado) => axios.post(`/sanciones/${id}/cambiar_estado/`, { estado }),
    notificarSancion: (id, data) => axios.post(`/sanciones/${id}/notificar/`, data),
    getSancionesPendientes: (afiliadoId) => axios.get(`/sanciones/pendientes_afiliado/?afiliado=${afiliadoId}`),
    generarPagoQrSancion: (id) => axios.post(`/sanciones/${id}/generar_pago_qr/`),

    // Asistencias
    getAsistencias: (params) => axios.get('/asistencias/', { params }),
    exportarAsistenciasExcel: (params) => axios.get('/asistencias/exportar_excel/', { params, responseType: 'blob' }),
    inasistenciasFrecuentes: (params) => axios.get('/asistencias/inasistencias_frecuentes/', { params }),
    estadisticasAsistencia: (params) => axios.get('/asistencias/estadisticas/', { params }),


    // Reservas
    getReservas: (params) => axios.get('/reservas/', { params }),
    getReserva: (id) => axios.get(`/reservas/${id}/`),
    createReserva: (data) => axios.post('/reservas/', data),
    updateReserva: (id, data) => axios.put(`/reservas/${id}/`, data),
    deleteReserva: (id) => axios.delete(`/reservas/${id}/`),
    getHojasRutaDisponibles: (params) => axios.get('/hojas-ruta/disponibles_hoy/', { params }),
    getPasajeros: (id) => axios.get(`/hojas-ruta/${id}/pasajeros/`),
    generarPagoQrReserva: (id) => axios.post(`/reservas/${id}/generar_pago_qr/`),
    getReservaPublica: (id) => axios.get(`/reservas/${id}/public-retrieve/`),

    // Reportes
    getReporteFinanzas: (params) => axios.get('/reportes/finanzas', { params }),
    getBalance: (params) => axios.get('/reportes/balance', { params }),
    getReportesGraficos: (params) => axios.get('/reportes/graficos', { params }),
    getReportesOperativos: (params) => axios.get('/reportes/operativos', { params }),
    urlCuotasCsv: (params) => {
        const q = new URLSearchParams(params).toString()
        return `${API_URL}/reportes/cuotas.csv?${q}`
    },
    urlHojasRutaCsv: (params) => {
        const q = new URLSearchParams(params).toString()
        return `${API_URL}/reportes/hojas-ruta.csv?${q}`
    },
    urlHojasRutaPdf: (params) => {
        const q = new URLSearchParams(params).toString()
        return `${API_URL}/reportes/hojas-ruta.pdf?${q}`
    },
    urlSancionesCsv: (params) => {
        const q = new URLSearchParams(params).toString()
        return `${API_URL}/reportes/sanciones.csv?${q}`
    },
    urlOperativosPdf: (params) => {
        const q = new URLSearchParams(params).toString()
        return `${API_URL}/reportes/operativos/pdf?${q}`
    },
    urlOperativosCsv: (params) => {
        const q = new URLSearchParams(params).toString()
        return `${API_URL}/reportes/operativos/csv?${q}`
    },
    getTransacciones: (params) => axios.get('/reportes/transacciones/', { params }),
    urlTransaccionesPdf: (params) => {
        const q = new URLSearchParams(params).toString()
        return `${API_URL}/reportes/transacciones/pdf?${q}`
    },
    urlTransaccionesCsv: (params) => {
        const q = new URLSearchParams(params).toString()
        return `${API_URL}/reportes/transacciones/csv?${q}`
    },

    // Tipos de Pago
    getTiposPago: (params) => axios.get('/tipos-pago/', { params }),
    getTipoPago: (id) => axios.get(`/tipos-pago/${id}/`),
    createTipoPago: (data) => axios.post('/tipos-pago/', data),
    updateTipoPago: (id, data) => axios.put(`/tipos-pago/${id}/`, data),
    deleteTipoPago: (id) => axios.delete(`/tipos-pago/${id}/`),
    calcularMontoConMulta: (id, montoBase, aplicarMulta = true) => axios.post(`/tipos-pago/${id}/calcular_monto/`, { monto_base: montoBase, aplicar_multa: aplicarMulta }),

    // Pagos (Ingresos)
    getPagos: (params) => axios.get('/pagos/', { params }),
    getPago: (id) => axios.get(`/pagos/${id}/`),
    createPago: (data) => axios.post('/pagos/', data),
    updatePago: (id, data) => axios.put(`/pagos/${id}/`, data),
    deletePago: (id) => axios.delete(`/pagos/${id}/`),
    downloadRecibo: (id) => axios.get(`/pagos/${id}/recibo/`, { responseType: 'blob' }),
    generarPagoQrIngreso: (id) => axios.post(`/pagos/${id}/generar_pago_qr/`),

    // Egresos
    getEgresos: (params) => axios.get('/egresos/', { params }),
    getEgreso: (id) => axios.get(`/egresos/${id}/`),
    createEgreso: (data) => axios.post('/egresos/', data),
    updateEgreso: (id, data) => axios.put(`/egresos/${id}/`, data),
    deleteEgreso: (id) => axios.delete(`/egresos/${id}/`),
    // Usuarios
    getUsers: (params) => axios.get('/users/', { params }),
    createUser: (data) => axios.post('/users/', data),
    updateUser: (id, data) => axios.put(`/users/${id}/`, data),
    toggleUserActive: (id) => axios.post(`/users/${id}/toggle_active/`),
    assignUserRole: (id, role) => axios.post(`/users/${id}/assign_role/`, { role }),
    resetUserPassword: (id, new_password) => axios.post(`/users/${id}/reset_password/`, { new_password }),

    // Perfil y Seguridad
    changePassword: (data) => axios.post('/auth/change-password', data),

    // Bitácora / Logs de Auditoría
    getBitacora: (params) => axios.get('/bitacora/', { params }),

    // Métodos de descarga con autenticación
    downloadTransaccionesPdf: async (params) => {
        const q = new URLSearchParams(params).toString();
        const url = `/reportes/transacciones/pdf?${q}`;
        const fecha = params.fecha_inicio && params.fecha_fin
            ? `_${params.fecha_inicio}_a_${params.fecha_fin}`
            : '';
        return await downloadFile(url, `transacciones${fecha}.pdf`);
    },
    downloadTransaccionesCsv: async (params) => {
        const q = new URLSearchParams(params).toString();
        const url = `/reportes/transacciones/csv?${q}`;
        const fecha = params.fecha_inicio && params.fecha_fin
            ? `_${params.fecha_inicio}_a_${params.fecha_fin}`
            : '';
        return await downloadFile(url, `transacciones${fecha}.csv`);
    },
    downloadOperativosPdf: async (params = {}) => {
        const q = new URLSearchParams(params).toString();
        const url = `/reportes/operativos/pdf?${q}`;
        return await downloadFile(url, 'reportes_operativos.pdf');
    },
    downloadOperativosCsv: async (params = {}) => {
        const q = new URLSearchParams(params).toString();
        const url = `/reportes/operativos/csv?${q}`;
        return await downloadFile(url, 'reportes_operativos.csv');
    },
    downloadAfiliadosReporte: async () => {
        return await downloadFile('/afiliados/reporte/', 'afiliados.pdf');
    },
    downloadVehiculosReporte: async () => {
        return await downloadFile('/vehiculos/reporte/', 'vehiculos.pdf');
    },
    downloadDirectorioReporte: async () => {
        return await downloadFile('/directorio/reporte/', 'directorio.pdf');
    },
    downloadAfiliadosMorososPdf: async () => {
        return await downloadFile('/reportes/afiliados-morosos/pdf/', 'estado_cuentas.pdf');
    },
    // Excel Exports
    downloadAfiliadosExcel: async (params = {}) => {
        const q = new URLSearchParams(params).toString();
        return await downloadFile(`/afiliados/export_excel/?${q}`, 'afiliados.xlsx');
    },
    downloadVehiculosExcel: async (params = {}) => {
        const q = new URLSearchParams(params).toString();
        return await downloadFile(`/vehiculos/export_excel/?${q}`, 'vehiculos.xlsx');
    },
    downloadHojasRutaExcel: async (params = {}) => {
        const q = new URLSearchParams(params).toString();
        return await downloadFile(`/hojas-ruta/export_excel/?${q}`, 'hojas_ruta.xlsx');
    },
    downloadPagosExcel: async (params = {}) => {
        const q = new URLSearchParams(params).toString();
        return await downloadFile(`/pagos/export_excel/?${q}`, 'ingresos.xlsx');
    },
    downloadEgresosExcel: async (params = {}) => {
        const q = new URLSearchParams(params).toString();
        return await downloadFile(`/egresos/export_excel/?${q}`, 'egresos.xlsx');
    },

    // Nuevos Reportes Avanzados
    getRentabilidadRutas: (params) => axios.get('/reportes/rentabilidad-rutas/', { params }),
    getKPIsEjecutivos: () => axios.get('/reportes/kpis-ejecutivos/'),
    getTendenciasMensuales: (params) => axios.get('/reportes/tendencias-mensuales/', { params }),

    // Alertas de Sistema
    getAlertasNoLeidas: () => axios.get('/alertas/no_leidas/'),
    marcarAlertaLeida: (id) => axios.post(`/alertas/${id}/marcar_leida/`),
    marcarTodasAlertasLeidas: () => axios.post('/alertas/marcar_todas_leidas/'),
};



export default api;
