import os
import django

# Configuración del entorno de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema.settings')
django.setup()

from django.db import connection, transaction
from tesoreria.models import Pago, Egreso
from reservas.models import Reserva
from cuotas.models import Cuota
from sanciones.models import Sancion
from asistencias.models import Asistencia
from hojasruta.models import HojaRuta
from pagos_qr.models import QRTransaccion
from whatsapp_notif.models import WhatsAppMessage

def reset_sistema():
    """
    Limpia todos los datos de ingresos, gastos y operaciones
    y reinicia los contadores de identificación.
    """
    print("\n" + "="*50)
    print("🚀 INICIANDO REINICIO DEL SISTEMA A CERO")
    print("="*50)
    
    models_to_clear = [
        Pago, 
        Egreso, 
        Reserva, 
        Cuota, 
        Sancion, 
        Asistencia, 
        HojaRuta, 
        QRTransaccion, 
        WhatsAppMessage
    ]
    
    db_engine = connection.vendor
    print(f"📊 Base de datos detectada: {db_engine}\n")
    
    try:
        with transaction.atomic():
            for model in models_to_clear:
                table_name = model._meta.db_table
                count = model.objects.count()
                
                # Eliminar registros
                model.objects.all().delete()
                print(f"✅ {model.__name__:<20} | {count:>5} registros eliminados")
                
                # Resetear el contador de ID
                with connection.cursor() as cursor:
                    if db_engine == 'sqlite':
                        # Para SQLite
                        cursor.execute(f"UPDATE sqlite_sequence SET seq=0 WHERE name='{table_name}'")
                        # Si no existe en sqlite_sequence (tabla vacía desde el inicio), el comando no falla
                    elif db_engine == 'postgresql':
                        # Para PostgreSQL
                        cursor.execute(f"ALTER SEQUENCE IF EXISTS {table_name}_id_seq RESTART WITH 1")
        
        print("\n" + "="*50)
        print("✨ SISTEMA REINICIADO EXITOSAMENTE")
        print("="*50)
        print("👉 Todos los ingresos y gastos ahora están en 0.00")
        print("👉 Los nuevos recibos y facturas comenzarán desde el 001/000001.")
        print("👉 Se ha limpiado el historial de WhatsApp y transacciones QR.")
        print("="*50 + "\n")

    except Exception as e:
        print(f"\n❌ ERROR DURANTE EL REINICIO: {str(e)}")
        print("⚠️ No se realizaron cambios permanentes (Rollback ejecutado).")

if __name__ == "__main__":
    reset_sistema()
