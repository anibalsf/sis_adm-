from django.db import migrations

# app_label -> modelos ya auditados antes de que existiera el campo app_label
MODELOS = {
    'afiliados': ['afiliado'],
    'asistencias': ['asistencia'],
    'cuotas': ['cuota'],
    'directorio': ['miembrodirectorio'],
    'hojasruta': ['hojaruta', 'turnosalida'],
    'reservas': ['reserva'],
    'reuniones': ['reunion'],
    'rutas': ['ruta'],
    'sanciones': ['sancion'],
    'tesoreria': ['pago', 'egreso', 'tipopago', 'arqueocaja'],
    'usuarios': ['user'],
    'vehiculos': ['vehiculo'],
    'encomiendas': ['encomienda'],
    'mantenimiento': ['mantenimientovehiculo'],
}


def rellenar_app_label(apps, schema_editor):
    LogAuditoria = apps.get_model('historial', 'LogAuditoria')
    for app_label, modelos in MODELOS.items():
        for modelo in modelos:
            LogAuditoria.objects.filter(app_label='', tabla=modelo).update(app_label=app_label)


def quitar_app_label(apps, schema_editor):
    LogAuditoria = apps.get_model('historial', 'LogAuditoria')
    LogAuditoria.objects.update(app_label='')


class Migration(migrations.Migration):

    dependencies = [
        ('historial', '0003_logauditoria_app_label_logauditoria_cambios_labels'),
    ]

    operations = [
        migrations.RunPython(rellenar_app_label, quitar_app_label),
    ]
