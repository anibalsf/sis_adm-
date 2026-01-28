import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema.settings')
django.setup()

from comunicacion.services import WhatsAppService
from django.conf import settings

def enviar_alerta_backup(exito, detalle=""):
    service = WhatsAppService()
    admin_phone = getattr(settings, 'ADMIN_PHONE_NUMBER', '70000000')
    
    status = "✅ EXITOSO" if exito else "❌ FALLIDO"
    mensaje = f"""
    📊 *REPORTE DE BACKUP - SINDICATO TAIPIPLAYA*
    
    Estado: {status}
    Detalle: {detalle}
    Fecha: {django.utils.timezone.now().strftime('%Y-%m-%d %H:%M:%S')}
    
    _Este es un mensaje automático del sistema._
    """
    
    success, result = service.send_message(admin_phone, mensaje)
    if success:
        print(f"Alerta enviada correctamente a {admin_phone}")
    else:
        print(f"Error al enviar alerta: {result}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python alerta_backup.py [success|fail] [detalle]")
        sys.exit(1)
        
    exito = sys.argv[1].lower() == 'success'
    detalle = sys.argv[2] if len(sys.argv) > 2 else ""
    enviar_alerta_backup(exito, detalle)
