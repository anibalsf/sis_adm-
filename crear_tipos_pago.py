"""
Script para crear tipos de pago iniciales en el sistema
Ejecutar: python crear_tipos_pago.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema.settings')
django.setup()

from tesoreria.models import TipoPago

# Tipos de Pago para Ingresos
tipos_ingreso = [
    {'nombre': 'Cuota Mensual', 'descripcion': 'Pago mensual de afiliación', 'tipo': 'ingreso'},
    {'nombre': 'Cuota Anual', 'descripcion': 'Pago anual de afiliación', 'tipo': 'ingreso'},
    {'nombre': 'Afiliación', 'descripcion': 'Pago por derecho de afiliación nueva', 'tipo': 'ingreso'},
    {'nombre': 'Sanción', 'descripcion': 'Pago de sanciones', 'tipo': 'ingreso'},
    {'nombre': 'Aporte Navidad', 'descripcion': 'Aporte especial de Navidad', 'tipo': 'ingreso'},
    {'nombre': 'Aporte Carnaval', 'descripcion': 'Aporte especial de Carnaval', 'tipo': 'ingreso'},
    {'nombre': 'Aporte Aniversario', 'descripcion': 'Aporte especial de Aniversario', 'tipo': 'ingreso'},
    {'nombre': 'Hoja de Ruta Caranavi', 'descripcion': 'Pago por hoja de ruta a Caranavi', 'tipo': 'ingreso'},
    {'nombre': 'Hoja de Ruta La Paz (Ipsum)', 'descripcion': 'Pago por hoja de ruta a La Paz (Ipsum)', 'tipo': 'ingreso'},
    {'nombre': 'Hoja de Ruta La Paz (Minibus)', 'descripcion': 'Pago por hoja de ruta a La Paz (Minibus)', 'tipo': 'ingreso'},
    {'nombre': 'Encomienda', 'descripcion': 'Pago por encomienda', 'tipo': 'ingreso'},
    {'nombre': 'Otros ingresos', 'descripcion': 'Otros tipos de ingresos', 'tipo': 'ingreso'},
]

# Tipos de Pago para Egresos
tipos_egreso = [
    {'nombre': 'Servicios Básicos', 'descripcion': 'Luz, agua, internet', 'tipo': 'egreso'},
    {'nombre': 'Mantenimiento', 'descripcion': 'Mantenimiento de oficina y equipos', 'tipo': 'egreso'},
    {'nombre': 'Pago Personal', 'descripcion': 'Salarios de secretaria y dirigentes', 'tipo': 'egreso'},
    {'nombre': 'Sueldo y Salario Secretaría', 'descripcion': 'Pago de sueldo y salario a la secretaria', 'tipo': 'egreso'},
    {'nombre': 'Gastos Aniversario', 'descripcion': 'Gastos de festejos y eventos de aniversario', 'tipo': 'egreso'},
    {'nombre': 'Gastos Navidad', 'descripcion': 'Gastos de festejos y canastones de navidad', 'tipo': 'egreso'},
    {'nombre': 'Gastos Carnaval', 'descripcion': 'Gastos de actividades y festejos de carnaval', 'tipo': 'egreso'},
    {'nombre': 'Papelería', 'descripcion': 'Material de oficina', 'tipo': 'egreso'},
    {'nombre': 'Gastos Administrativos', 'descripcion': 'Otros gastos administrativos', 'tipo': 'egreso'},
]

print("Creando tipos de pago...")

for tipo_data in tipos_ingreso + tipos_egreso:
    tipo, created = TipoPago.objects.get_or_create(
        nombre=tipo_data['nombre'],
        defaults={'descripcion': tipo_data['descripcion'], 'tipo': tipo_data['tipo']}
    )
    if created:
        print(f"[+] Creado: {tipo.nombre} ({tipo.tipo})")
    else:
        print(f"  Ya existe: {tipo.nombre}")

print(f"\nTotal de tipos de pago en el sistema: {TipoPago.objects.count()}")
print(f"  - Ingresos: {TipoPago.objects.filter(tipo='ingreso').count()}")
print(f"  - Egresos: {TipoPago.objects.filter(tipo='egreso').count()}")
print("\n¡Listo! Ya puedes usar el módulo de Pagos y Egresos.")
