from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vehiculos', '0006_alter_vehiculo_estado'),
    ]

    operations = [
        migrations.AddField(
            model_name='vehiculo',
            name='color',
            field=models.CharField(blank=True, max_length=50, verbose_name='Color'),
        ),
    ]
