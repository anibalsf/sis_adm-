from django.conf import settings
from django.db import connection
from django.http import JsonResponse
from django.utils import timezone


def health_check(request):
    health_status = {
        "status": "ok",
        "timestamp": timezone.now().isoformat(),
        "database": "disconnected",
        "environment": getattr(settings, 'ENVIRONMENT', 'development'),
        "debug": bool(settings.DEBUG),
    }

    try:
        connection.ensure_connection()
        health_status["database"] = "connected"
    except Exception as exc:
        health_status["status"] = "error"
        health_status["database_error"] = str(exc)
        return JsonResponse(health_status, status=503)

    try:
        from django.db.migrations.executor import MigrationExecutor

        executor = MigrationExecutor(connection)
        pendientes = executor.migration_plan(executor.loader.graph.leaf_nodes())
        health_status["pending_migrations"] = len(pendientes)
        if pendientes:
            health_status["status"] = "degraded"
            health_status["database"] = "migrations_pending"
    except Exception as exc:
        health_status["status"] = "degraded"
        health_status["migrations_error"] = str(exc)

    return JsonResponse(health_status)
