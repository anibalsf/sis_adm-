from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hojasruta', '0003_hojaruta_add_fk'),
    ]

    operations = [
        migrations.AlterField(
            model_name='hojaruta',
            name='nro',
            field=models.CharField(max_length=30),
        ),
    ]