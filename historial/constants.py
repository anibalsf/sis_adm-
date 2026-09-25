"""Nombre legible de cada módulo, para el filtro de la pantalla de bitácora."""

MODULOS = {
    'afiliados': 'Afiliados',
    'asistencias': 'Asistencias',
    'auth': 'Usuarios',
    'comunicacion': 'Comunicación',
    'cuotas': 'Cuotas',
    'directorio': 'Directorio',
    'encomiendas': 'Encomiendas',
    'hojasruta': 'Hojas de Ruta',
    'mantenimiento': 'Mantenimiento',
    'pagos_qr': 'Pagos QR',
    'reservas': 'Reservas',
    'reuniones': 'Reuniones',
    'rutas': 'Rutas',
    'sanciones': 'Sanciones',
    'tesoreria': 'Tesorería',
    'usuarios': 'Usuarios',
    'vehiculos': 'Vehículos',
    'web_publica': 'Sitio público',
}


def nombre_modulo(app_label):
    return MODULOS.get(app_label, (app_label or '').title())
