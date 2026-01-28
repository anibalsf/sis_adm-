from django.apps import AppConfig


class WhatsappNotifConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'whatsapp_notif'
    verbose_name = 'Notificaciones WhatsApp'

    def ready(self):
        """Importar señales y iniciar scheduler cuando la app esté lista"""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            # Importar señales
            import whatsapp_notif.signals  # noqa
            logger.info("Señales de WhatsApp cargadas")
            
            # Iniciar scheduler solo en proceso principal (no en reload)
            import os
            import sys
            
            # Evitar iniciar scheduler en migrations o tests
            if 'runserver' in sys.argv or 'gunicorn' in sys.argv[0]:
                # Solo iniciar en el proceso principal, no en el reloader
                if os.environ.get('RUN_MAIN') == 'true' or 'gunicorn' in sys.argv[0]:
                    from .scheduler import start_scheduler
                    start_scheduler()
                    logger.info("Scheduler de WhatsApp iniciado")
        
        except Exception as e:
            logger.warning(f"No se pudo inicializar completamente WhatsApp: {str(e)}")
