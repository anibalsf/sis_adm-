import os
import django
import sys
from django.utils import timezone
from datetime import date

# Configurar el entorno de Django
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema.settings')
django.setup()

from reportes_auto.report_generator import ReportGenerator
from hojasruta.models import HojaRuta
from afiliados.models import Afiliado
from rutas.models import Ruta

def previsualizar_reporte_lunes():
    print("📋 Generando Previsualización de Lista Oficial de Control (Lunes)...")
    
    # Asegurar que existan datos para el reporte de hoy
    # (Si no es lunes, igual lo forzamos para la vista previa)
    today = date.today()
    
    afiliados = Afiliado.objects.all()[:3]
    ruta = Ruta.objects.first()
    
    if not afiliados or not ruta:
        print("❌ Error: Faltan datos (afiliados o rutas) para generar la vista previa.")
        return

    # Crear algunas hojas de prueba para hoy
    print("🔨 Creando datos de prueba para hoy...")
    
    # Una pagada
    h1, _ = HojaRuta.objects.get_or_create(
        nro="TEST-001",
        fecha_emision=today,
        defaults={
            'afiliado': afiliados[0],
            'ruta': ruta,
            'precio': 50.00,
            'estado': 'pagada'
        }
    )
    
    # Una pendiente
    if len(afiliados) > 1:
        h2, _ = HojaRuta.objects.get_or_create(
            nro="TEST-002",
            fecha_emision=today,
            defaults={
                'afiliado': afiliados[1],
                'ruta': ruta,
                'precio': 50.00,
                'estado': 'emitida'
            }
        )

    # Generar el reporte
    reporte_texto = ReportGenerator.get_monday_hojas_pagadas_report()
    
    print("\n--- INICIO DEL MENSAJE DE WHATSAPP ---")
    print(reporte_texto)
    print("--- FIN DEL MENSAJE ---\n")
    
    print("✅ El reporte se enviará automáticamente cada lunes a las 10:00 PM.")
    
    # Limpiar datos de prueba si se desea (opcional)
    # h1.delete()
    # h2.delete()

if __name__ == "__main__":
    previsualizar_reporte_lunes()
