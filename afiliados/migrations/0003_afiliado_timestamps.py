from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('afiliados', '0002_afiliado_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='afiliado',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='afiliado',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, null=True, blank=True),
        ),
    ]