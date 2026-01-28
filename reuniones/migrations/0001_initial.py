from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Reunion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha', models.DateField()),
                ('tema', models.CharField(max_length=200)),
                ('tipo', models.CharField(default='ordinaria', max_length=30)),
                ('quorum', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True, blank=True)),
                ('updated_at', models.DateTimeField(auto_now=True, null=True, blank=True)),
            ],
            options={
                'ordering': ['-fecha'],
            },
        ),
    ]