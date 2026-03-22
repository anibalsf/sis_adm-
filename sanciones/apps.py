# Configuración de Signals - sanciones/apps.py

from django.apps import AppConfig


class SancionesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'sanciones'
    path = r'c:\Users\Once\Documents\trae_projects\sistema_administracion\sanciones'

    def ready(self):
        import sanciones.signals  # Importar signals al iniciar la app