from django.apps import AppConfig


class SistemaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'sistema'
    verbose_name = 'Sistema de Administración'

    def ready(self):
        """
        Se ejecuta cuando Django está listo
        Inicia el scheduler de notificaciones automáticas
        """
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            from sistema.scheduler import start_scheduler
            start_scheduler()
            logger.info("✅ Notificaciones automáticas habilitadas")
        except Exception as e:
            logger.warning(f"⚠️ Scheduler no iniciado: {str(e)}")
