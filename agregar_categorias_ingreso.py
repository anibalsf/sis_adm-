"""
Script para agregar nuevas categorías de ingreso al sistema:
  - Cambio de Movilidad
  - Venta de Luminaria

Ejecutar: python agregar_categorias_ingreso.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema.settings')
django.setup()

from tesoreria.models import TipoPago

nuevas_categorias = [
    {
        'nombre': 'Cambio de Movilidad',
        'descripcion': 'Ingreso por cambio de movilidad',
        'tipo': 'ingreso',
    },
    {
        'nombre': 'Venta de Luminaria',
        'descripcion': 'Ingreso por venta de luminaria',
        'tipo': 'ingreso',
    },
]

print("Agregando nuevas categorías de ingreso...")
print("-" * 45)

for data in nuevas_categorias:
    obj, created = TipoPago.objects.get_or_create(
        nombre=data['nombre'],
        defaults={
            'descripcion': data['descripcion'],
            'tipo': data['tipo'],
        }
    )
    if created:
        print(f"[+] Creado: {obj.nombre}")
    else:
        print(f"  Ya existe: {obj.nombre} (id={obj.id})")

print("-" * 45)
print(f"\nTotal categorías de ingreso en el sistema: "
      f"{TipoPago.objects.filter(tipo='ingreso').count()}")
print("\nCategorías de ingreso actuales:")
for tp in TipoPago.objects.filter(tipo='ingreso').order_by('nombre'):
    print(f"  - [{tp.id}] {tp.nombre}")

print("\n¡Listo!")
