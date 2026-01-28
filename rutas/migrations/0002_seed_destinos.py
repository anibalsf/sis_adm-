from django.db import migrations


def seed_destinos(apps, schema_editor):
    Ruta = apps.get_model('rutas', 'Ruta')
    seeds = [
        {
            'nombre': 'La Paz',
            'origen': 'Caranavi',
            'destino': 'La Paz',
            'tarifa_base': 120.00,
        },
        {
            'nombre': 'Convenio Integración Caranavi',
            'origen': 'Caranavi',
            'destino': 'Convenio Integración Caranavi',
            'tarifa_base': 80.00,
        },
        {
            'nombre': 'Caranavi',
            'origen': 'Caranavi',
            'destino': 'Caranavi',
            'tarifa_base': 50.00,
        },
    ]
    for s in seeds:
        obj = Ruta.objects.filter(nombre=s['nombre']).first()
        if obj:
            changed = False
            if not obj.tarifa_base or float(obj.tarifa_base) == 0.0:
                obj.tarifa_base = s['tarifa_base']
                changed = True
            if not obj.origen:
                obj.origen = s['origen']
                changed = True
            if not obj.destino:
                obj.destino = s['destino']
                changed = True
            if changed:
                obj.save(update_fields=['origen', 'destino', 'tarifa_base'])
        else:
            Ruta.objects.create(**s)


class Migration(migrations.Migration):

    dependencies = [
        ('rutas', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_destinos, migrations.RunPython.noop),
    ]