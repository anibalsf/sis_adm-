import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema.settings')
django.setup()

from tesoreria.models import TipoPago

def seed_expense_categories():
    categories = [
        {'nombre': 'Luz', 'descripcion': 'Pago de energía eléctrica'},
        {'nombre': 'Internet', 'descripcion': 'Servicio de internet y wifi'},
        {'nombre': 'Agua', 'descripcion': 'Pago de servicio de agua potable'},
        {'nombre': 'Aportes Federación', 'descripcion': 'Aportes mensuales a la federación'},
        {'nombre': 'Limpieza', 'descripcion': 'Gastos de limpieza de oficinas'},
        {'nombre': 'Material de Escritorio', 'descripcion': 'Papelería, tinta, etc.'},
        {'nombre': 'Mantenimiento Local', 'descripcion': 'Reparaciones menores en sede'},
        {'nombre': 'Viáticos', 'descripcion': 'Viajes y representación de la directiva'},
        {'nombre': 'Multa Federación', 'descripcion': 'Sanciones impuestas por la matriz'},
        {'nombre': 'Gastos Aniversario', 'descripcion': 'Gastos de festejos y eventos de aniversario'},
        {'nombre': 'Gastos Navidad', 'descripcion': 'Gastos de festejos y canastones de navidad'},
        {'nombre': 'Gastos Carnaval', 'descripcion': 'Gastos de actividades y festejos de carnaval'},
        {'nombre': 'Sueldo y Salario Secretaría', 'descripcion': 'Pago de sueldo y salario a la secretaria'},
        {'nombre': 'Otros Egresos', 'descripcion': 'Gastos varios no categorizados'},
    ]

    print("--- Sembrando Categorías de Egreso ---")
    created_count = 0
    for cat in categories:
        obj, created = TipoPago.objects.get_or_create(
            nombre=cat['nombre'],
            defaults={
                'descripcion': cat['descripcion'],
                'tipo': 'egreso'
            }
        )
        if created:
            print(f"Creado: {cat['nombre']}")
            created_count += 1
        else:
            print(f"Ya existe: {cat['nombre']}")
    
    print(f"--- Fin: {created_count} nuevas categorias creadas ---")

if __name__ == "__main__":
    seed_expense_categories()
