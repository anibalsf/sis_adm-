import os
import django
from datetime import date
import sys

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sistema.settings")
django.setup()

from reservas.models import Reserva
from hojasruta.models import HojaRuta
from rutas.models import Ruta
from vehiculos.models import Vehiculo
from afiliados.models import Afiliado
from comunicacion.models import Notificacion
from django.utils import timezone

def verify_whatsapp():
    print("--- Iniciando Verificación de WhatsApp (Modo Simulación) ---")

    # 1. Crear datos de prueba
    afiliado, _ = Afiliado.objects.get_or_create(
        ci="1234567", 
        defaults={
            'nombres': 'Chofer', 
            'apellidos': 'Prueba', 
            'telefono': '70000000',
            'fecha_ingreso': date.today()
        }
    )
    
    ruta, _ = Ruta.objects.get_or_create(
        nombre="Ruta Test WhatsApp", 
        defaults={'origen': 'La Paz', 'destino': 'Taipiplaya', 'tarifa_base': 50}
    )
    
    vehiculo, _ = Vehiculo.objects.get_or_create(
        placa="WSP-100", 
        defaults={'afiliado': afiliado, 'tipo': 'Minivan', 'capacidad': 7}
    )
    
    # Crear Hoja de Ruta para hoy
    hoja, _ = HojaRuta.objects.get_or_create(
        ruta=ruta,
        fecha_salida=date.today(),
        vehiculo=vehiculo,
        afiliado=afiliado,
        fecha_emision=date.today(),
        defaults={'estado': 'emitida'}
    )
    
    # Datos de reserva
    cliente = "Juan Pérez Tester"
    telefono = "71234567" # Número de prueba
    
    print(f"Creando reserva para {cliente} (Tel: {telefono})...")
    
    # 2. Crear Reserva (esto debería disparar el WhatsAppService)
    # Usamos el serializer para simular el flujo real de la API, 
    # pero llamar directamente al modelo + servicio es más directo para un script rápido.
    # Sin embargo, la lógica está en ReservaViewSet.perform_create. 
    # Para probar la integración real del ViewSet, deberíamos usar APIClient, 
    # pero para probar la *lógica*, simulamos lo que hace perform_create.
    
    reserva = Reserva.objects.create(
        ruta=ruta,
        fecha_viaje=date.today(),
        cliente=cliente,
        telefono=telefono,
        cantidad=1,
        asiento=1,
        estado='pendiente'
    )
    
    # Simular la llamada que haría el ViewSet
    from comunicacion.services import WhatsAppService
    print("Enviando notificación...")
    WhatsAppService().send_reserva_confirmation(reserva)
    
    # 3. Verificar Notificación
    last_notif = Notificacion.objects.filter(destinatario=telefono).order_by('-created_at').first()
    
    if last_notif:
        print(f"\n✅ ÉXITO: Notificación encontrada.")
        print(f"ID: {last_notif.id}")
        print(f"Estado: {last_notif.estado}")
        print(f"Destinatario: {last_notif.destinatario}")
        print(f"Mensaje generado:\n{'-'*20}\n{last_notif.mensaje}\n{'-'*20}")
        print(f"Respuesta sistema: {last_notif.response_body}")
    else:
        print("\n❌ ERROR: No se generó ninguna notificación.")

if __name__ == "__main__":
    try:
        verify_whatsapp()
    except Exception as e:
        print(f"Error durante la verificación: {e}")
