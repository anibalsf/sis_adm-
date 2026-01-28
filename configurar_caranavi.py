"""
Script para configurar Hoja de Ruta Caranavi con plazo y multa.
Ejecutar con: python configurar_caranavi.py
"""

from datetime import time
import django
import os
import sys

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema.settings')
django.setup()

from tesoreria.models import TipoPago

def configurar_caranavi():
    """
    Configura el tipo de pago 'Hoja de Ruta Caranavi' con:
    - Plazo: Lunes de 17:00 a 22:00
    - Multa: 50 Bs por pago fuera de plazo
    """
    
    # Buscar o crear el tipo de pago
    tipo_pago, created = TipoPago.objects.get_or_create(
        nombre="Hoja de Ruta Caranavi",
        defaults={
            'descripcion': 'Pago semanal Hoja de Ruta Caranavi',
            'tipo': 'ingreso'
        }
    )
    
    # Configurar plazo y multa
    tipo_pago.tiene_plazo = True
    tipo_pago.dia_plazo = 0  # 0 = Lunes
    tipo_pago.hora_inicio_plazo = time(17, 0)  # 5:00 PM
    tipo_pago.hora_fin_plazo = time(22, 0)  # 10:00 PM
    tipo_pago.monto_multa = 50.00
    tipo_pago.save()
    
    if created:
        print("✅ Tipo de pago 'Hoja de Ruta Caranavi' creado exitosamente")
    else:
        print("✅ Tipo de pago 'Hoja de Ruta Caranavi' actualizado exitosamente")
    
    print(f"\nConfiguración:")
    print(f"- Plazo: Lunes de {tipo_pago.hora_inicio_plazo} a {tipo_pago.hora_fin_plazo}")
    print(f"- Multa: {tipo_pago.monto_multa} Bs")

if __name__ == "__main__":
    configurar_caranavi()
