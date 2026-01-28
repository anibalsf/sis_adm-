from django.db import migrations


def set_prefijos(apps, schema_editor):
    Ruta = apps.get_model('rutas', 'Ruta')
    mapping = {
        'La Paz': 'LP',
        'Convenio Integración Caranavi': 'CI',
        'Caranavi': 'CV',
    }
    for nombre, prefijo in mapping.items():
        Ruta.objects.filter(nombre=nombre).update(prefijo=prefijo)


class Migration(migrations.Migration):

    dependencies = [
        ('rutas', '0003_ruta_prefijo'),
    ]

    operations = [
        migrations.RunPython(set_prefijos, migrations.RunPython.noop),
    ]