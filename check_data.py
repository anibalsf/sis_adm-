import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema.settings')
django.setup()

from rutas.models import Ruta
from vehiculos.models import Vehiculo

print("Rutas existentes:")
for r in Ruta.objects.all():
    print(f"- {r.nombre} (ID: {r.id})")

print("\nTipos de Vehículo existentes:")
tipos = Vehiculo.objects.values_list('tipo', flat=True).distinct()
for t in tipos:
    print(f"- {t}")
