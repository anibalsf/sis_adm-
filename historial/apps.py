from django.apps import AppConfig


class HistorialConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'historial'

    def ready(self):
        from .signals import conectar_signals

        # La bitácora se conecta a todos los modelos de todos los módulos para
        # que ningún cambio quede fuera del registro.
        conectar_signals()
