"""
Script para crear datos de prueba de pagos y egresos
Ejecutar: python crear_datos_prueba_tesoreria.py
"""
import os
import django
from datetime import date, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema.settings')
django.setup()

from tesoreria.models import Pago, Egreso, TipoPago
from afiliados.models import Afiliado

print("Verificando tipos de pago...")
tipos_pago = TipoPago.objects.all()
print(f"Tipos de pago disponibles: {tipos_pago.count()}")

if tipos_pago.count() == 0:
    print("ERROR: No hay tipos de pago. Ejecuta primero: python crear_tipos_pago.py")
    exit(1)

print("\nVerificando afiliados...")
afiliados = Afiliado.objects.all()[:5]
print(f"Afiliados disponibles: {afiliados.count()}")

if afiliados.count() == 0:
    print("ERROR: No hay afiliados en el sistema. Crea al menos un afiliado primero.")
    exit(1)

# Obtener tipos
tipo_cuota_mensual = TipoPago.objects.filter(tipo='ingreso', nombre__icontains='mensual').first()
tipo_servicios = TipoPago.objects.filter(tipo='egreso', nombre__icontains='servicios').first()

if not tipo_cuota_mensual:
    tipo_cuota_mensual = TipoPago.objects.filter(tipo='ingreso').first()
if not tipo_servicios:
    tipo_servicios = TipoPago.objects.filter(tipo='egreso').first()

print("\n=== Creando Pagos de Prueba ===")
hoy = date.today()

for i, afiliado in enumerate(afiliados, 1):
    pago_data = {
        'afiliado': afiliado,
        'tipo_pago': tipo_cuota_mensual,
        'monto': 100.00 * i,
        'fecha_pago': hoy - timedelta(days=i*7),
        'observaciones': f'Pago de prueba {i}'
    }
    pago, created = Pago.objects.get_or_create(
        afiliado=afiliado,
        fecha_pago=pago_data['fecha_pago'],
        defaults=pago_data
    )
    if created:
        print(f"✓ Pago creado: {afiliado.nombre_completo} - Bs. {pago.monto}")
    else:
        print(f"  Ya existe: {afiliado.nombre_completo} - {pago.fecha_pago}")

print("\n=== Creando Egresos de Prueba ===")
egresos_prueba = [
    {'descripcion': 'Pago de luz', 'monto': 150.00, 'dias_atras': 5},
    {'descripcion': 'Pago de agua', 'monto': 80.00, 'dias_atras': 10},
    {'descripcion': 'Material de oficina', 'monto': 120.00, 'dias_atras': 15},
]

for eg_data in egresos_prueba:
    egreso, created = Egreso.objects.get_or_create(
        descripcion=eg_data['descripcion'],
        fecha=hoy - timedelta(days=eg_data['dias_atras']),
        defaults={
            'tipo_pago': tipo_servicios,
            'monto': eg_data['monto']
        }
    )
    if created:
        print(f"✓ Egreso creado: {egreso.descripcion} - Bs. {egreso.monto}")
    else:
        print(f"  Ya existe: {egreso.descripcion}")

print(f"\n=== Resumen ===")
print(f"Total Pagos: {Pago.objects.count()}")
print(f"Total Egresos: {Egreso.objects.count()}")
print("\n¡Datos de prueba creados! Ahora puedes ver el módulo de Pagos y Egresos.")
