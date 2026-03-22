import os
import django
import sys
from datetime import date

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema.settings')
django.setup()

from afiliados.models import Afiliado

try:
    afiliado, created = Afiliado.objects.get_or_create(
        ci="CONVENIO-1",
        defaults={
            'nombres': 'Convenio',
            'apellidos': 'Integración Caranavi',
            'fecha_ingreso': date.today(),
            'estado': 'activo',
            'is_active': True,
            'telefono': '00000000' # default to prevent validation errors
        }
    )
    if created:
        print("Afiliado Creado exitosamente: Convenio Integración Caranavi")
    else:
        print("El Afiliado de Convenio ya existe.")
except Exception as e:
    print(f"Error: {e}")
