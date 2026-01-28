import os
import django
from django.db import transaction

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema.settings')
django.setup()

from django.contrib.auth.models import User
from afiliados.models import Afiliado
from vehiculos.models import Vehiculo
from hojasruta.models import HojaRuta
from cuotas.models import Cuota
from sanciones.models import Sancion
from asistencias.models import Asistencia
from tesoreria.models import Pago, Egreso
from reservas.models import Reserva
from reuniones.models import Reunion
from historial.models import CambioEstado
from directorio.models import MiembroDirectorio

def limpiar_sistema():
    print("🚀 Iniciando limpieza total del sistema...")
    
    try:
        with transaction.atomic():
            # 1. Eliminar Reservas (dependen de HojaRuta)
            print("- Limpiando Reservas...")
            Reserva.objects.all().delete()
            
            # 2. Eliminar Hojas de Ruta
            print("- Limpiando Hojas de Ruta...")
            HojaRuta.objects.all().delete()
            
            # 3. Eliminar Sanciones, Cuotas y Asistencias
            print("- Limpiando Sanciones, Cuotas y Asistencias...")
            Sancion.objects.all().delete()
            Cuota.objects.all().delete()
            Asistencia.objects.all().delete()
            Reunion.objects.all().delete()
            
            # 4. Eliminar Finanzas
            print("- Limpiando Pagos y Egresos...")
            Pago.objects.all().delete()
            Egreso.objects.all().delete()
            
            # 5. Eliminar Historial
            print("- Limpiando Historial de cambios...")
            CambioEstado.objects.all().delete()
            
            # 6. Eliminar Directorio
            print("- Limpiando Directorio...")
            MiembroDirectorio.objects.all().delete()
            
            # 7. Eliminar Vehículos
            print("- Limpiando Vehículos...")
            Vehiculo.objects.all().delete()
            
            # 8. Eliminar Afiliados y sus Usuarios asociados (que no sean superusuarios)
            print("- Limpiando Afiliados y Usuarios asociados...")
            
            # Obtenemos los IDs de los usuarios de afiliados antes de borrarlos
            usuarios_afiliados_ids = list(Afiliado.objects.exclude(user__isnull=True).values_list('user_id', flat=True))
            
            # Borramos los afiliados
            Afiliado.objects.all().delete()
            
            # Borramos los usuarios que pertenecían a los afiliados y no son superusers
            User.objects.filter(id__in=usuarios_afiliados_ids, is_superuser=False).delete()
            
            # También borrar cualquier usuario que no sea superuser y no tenga afiliado (por si acaso)
            User.objects.filter(is_superuser=False).exclude(username='admin').delete()

        print("\n✅ ¡Sistema reseteado exitosamente!")
        print("Conservado: Superusuarios, Rutas y Tipos de Pago.")
        
    except Exception as e:
        print(f"\n❌ Error durante la limpieza: {str(e)}")
        raise

if __name__ == "__main__":
    confirm = input("⚠️ ¿ESTÁS SEGURO? Esto borrará TODOS los datos operativos. (Escribe 'SÍ' para confirmar): ")
    if confirm.upper() == 'SÍ' or confirm.upper() == 'SI':
        limpiar_sistema()
    else:
        print("Operación cancelada.")
