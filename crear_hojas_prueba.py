import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema.settings')
django.setup()

from hojasruta.models import HojaRuta
from rutas.models import Ruta
from afiliados.models import Afiliado
from vehiculos.models import Vehiculo
from datetime import date, timedelta

# Obtener datos existentes
rutas = Ruta.objects.all()
afiliados = Afiliado.objects.all()
vehiculos = Vehiculo.objects.all()

if rutas.exists() and afiliados.exists():
    hoy = date.today()
    
    # Crear 3 hojas de ruta para los próximos días
    for i in range(3):
        fecha_salida = hoy + timedelta(days=i+1)
        
        ruta = rutas[i % rutas.count()]
        afiliado = afiliados[i % afiliados.count()]
        vehiculo = vehiculos[i % vehiculos.count()] if vehiculos.exists() else None
        
        hoja, created = HojaRuta.objects.get_or_create(
            fecha_salida=fecha_salida,
            ruta=ruta,
            defaults={
                'nro': f'HR-TEST-{i+1:03d}',
                'fecha_emision': hoy,
                'afiliado': afiliado,
                'vehiculo': vehiculo,
                'estado': 'emitida',
                'precio': ruta.tarifa_base if ruta else 150
            }
        )
        
        if created:
            print(f'Creada: {hoja.nro} - {ruta.nombre} - {fecha_salida}')
        else:
            print(f'Ya existe: {hoja.nro}')
    
    # Mostrar hojas disponibles
    hojas_disponibles = HojaRuta.objects.filter(
        estado='emitida',
        fecha_salida__gte=hoy
    ).count()
    
    print(f'\nTotal hojas disponibles: {hojas_disponibles}')
else:
    print('Error: No hay rutas o afiliados en la base de datos')

