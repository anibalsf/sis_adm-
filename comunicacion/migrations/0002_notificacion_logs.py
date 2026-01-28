from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('comunicacion', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='notificacion',
            name='webhook_url',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='notificacion',
            name='status_code',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='notificacion',
            name='response_body',
            field=models.TextField(blank=True),
        ),
    ]