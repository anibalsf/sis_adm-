from django.http import JsonResponse
from django.db import connection
from django.utils import timezone

def health_check(request):
    """
    Endpoint para verificar el estado del sistema.
    Verifica la conexión a la base de datos y provee información básica.
    """
    health_status = {
        "status": "ok",
        "timestamp": timezone.now().isoformat(),
        "database": "disconnected",
        "environment": "development"
    }
    
    # Verificar base de datos
    try:
        connection.ensure_connection()
        health_status["database"] = "connected"
    except Exception as e:
        health_status["status"] = "error"
        health_status["database_error"] = str(e)
        
    return JsonResponse(health_status)
