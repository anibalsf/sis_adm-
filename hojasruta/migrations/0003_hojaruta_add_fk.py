from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hojasruta', '0002_hojaruta_timestamps'),
        ('vehiculos', '0002_vehiculo_timestamps'),
        ('rutas', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='hojaruta',
            name='vehiculo',
            field=models.ForeignKey(null=True, blank=True, on_delete=models.deletion.PROTECT, related_name='hojas_ruta', to='vehiculos.vehiculo'),
        ),
        migrations.AddField(
            model_name='hojaruta',
            name='ruta',
            field=models.ForeignKey(null=True, blank=True, on_delete=models.deletion.PROTECT, related_name='hojas_ruta', to='rutas.ruta'),
        ),
    ]