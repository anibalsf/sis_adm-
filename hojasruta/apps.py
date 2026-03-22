# Configuración de Signals - hojasruta/apps.py

from django.apps import AppConfig


class HojasrutaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'hojasruta'
    path = r'c:\Users\Once\Documents\trae_projects\sistema_administracion\hojasruta'

    def ready(self):
        import hojasruta.signals  # Importar signals al iniciar la app
