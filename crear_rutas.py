"""
Script para crear las rutas La Paz y Caranavi.
Ejecutar con: python crear_rutas.py
"""

import django
import os
import sys

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema.settings')
django.setup()

from rutas.models import Ruta

def crear_rutas():
    """
    Crea las rutas principales del sindicato.
    """
    
    # Ruta 1: La Paz
    lapaz, created = Ruta.objects.get_or_create(
        nombre="La Paz",
        defaults={
            'origen': 'Taipiplaya',
            'destino': 'La Paz',
            'tarifa_base': 20.00,  # Ajustar según tarifa real
            'prefijo': 'LP'
        }
    )
    
    if created:
        print("✅ Ruta 'La Paz' creada exitosamente")
    else:
        print("ℹ️  Ruta 'La Paz' ya existe")
    
    # Ruta 2: Caranavi
    caranavi, created = Ruta.objects.get_or_create(
        nombre="Caranavi",
        defaults={
            'origen': 'Taipiplaya',
            'destino': 'Caranavi',
            'tarifa_base': 20.00,  # Ajustar según tarifa real
            'prefijo': 'CAR'
        }
    )
    
    if created:
        print("✅ Ruta 'Caranavi' creada exitosamente")
    else:
        print("ℹ️  Ruta 'Caranavi' ya existe")
    
    print("\n📍 Rutas configuradas:")
    for ruta in Ruta.objects.all():
        print(f"  - {ruta.nombre}: {ruta.origen} → {ruta.destino} (Bs. {ruta.tarifa_base})")

if __name__ == "__main__":
    crear_rutas()
