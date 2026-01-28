# Script para crear ruta La Paz
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema.settings')
django.setup()

from rutas.models import Ruta

# Crear ruta La Paz
ruta, created = Ruta.objects.get_or_create(
    nombre="La Paz",
    defaults={
        'origen': 'Taipiplaya',
        'destino': 'La Paz',
        'tarifa_base': 150.00,
        'prefijo': 'LP'
    }
)

if created:
    print(f"✅ Ruta '{ruta.nombre}' creada exitosamente")
    print(f"   - ID: {ruta.id}")
    print(f"   - Origen: {ruta.origen}")
    print(f"   - Destino: {ruta.destino}")
    print(f"   - Tarifa: {ruta.tarifa_base} Bs.")
    print(f"   - Prefijo: {ruta.prefijo}")
else:
    print(f"ℹ️  Ruta '{ruta.nombre}' ya existe")
    print(f"   - ID: {ruta.id}")
    print(f"   - Tarifa actual: {ruta.tarifa_base} Bs.")
