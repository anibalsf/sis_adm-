from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hojasruta', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='hojaruta',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='hojaruta',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, null=True, blank=True),
        ),
    ]