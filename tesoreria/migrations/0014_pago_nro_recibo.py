from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tesoreria', '0013_alter_pago_uuid'),
    ]

    operations = [
        migrations.AddField(
            model_name='pago',
            name='nro_recibo',
            field=models.PositiveIntegerField(blank=True, help_text='Número correlativo de recibo de ingreso (reinicia secuencia)', null=True),
        ),
    ]