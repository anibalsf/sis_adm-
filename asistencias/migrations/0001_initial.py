from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('afiliados', '0003_afiliado_timestamps'),
        ('reuniones', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='Asistencia',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('presente', models.BooleanField(default=True)),
                ('observaciones', models.CharField(blank=True, max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True, blank=True)),
                ('updated_at', models.DateTimeField(auto_now=True, null=True, blank=True)),
                ('afiliado', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='asistencias', to='afiliados.afiliado')),
                ('reunion', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='asistencias', to='reuniones.reunion')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AlterUniqueTogether(
            name='asistencia',
            unique_together={('reunion', 'afiliado')},
        ),
    ]