import os
import django
from datetime import date

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sistema.settings")
django.setup()

from sistema.scheduler import enviar_reporte_diario_ingresos, enviar_alertas_morosos_semanal
from tesoreria.models import Pago, TipoPago
from afiliados.models import Afiliado
from sanciones.models import Sancion

def verify_reports():
    print("--- Verificando Reportes Automáticos ---")
    
    # 1. Preparar datos de prueba para hoy
    print("1. Creando datos de prueba...")
    tipo_pago, _ = TipoPago.objects.get_or_create(
        nombre="Aporte Diario", 
        defaults={
            'tipo': 'ingreso',
            'descripcion': 'Aportes diarios de prueba'
        }
    )
    
    afiliado = Afiliado.objects.first()
    if not afiliado:
        afiliado = Afiliado.objects.create(ci="999999", nombres="Test", apellidos="Reporte", estado='activo')
        
    # Crear un pago hoy (Para Reporte Diario)
    Pago.objects.create(
        afiliado=afiliado,
        tipo_pago=tipo_pago,
        monto=50.00,
        fecha_pago=date.today(),
        observaciones="Pago prueba reporte"
    )
    
    # Crear una sanción pendiente (Para Alerta Morosos)
    Sancion.objects.create(
        afiliado=afiliado,
        tipo="Multa Test",
        monto=300.00,
        estado='pendiente'
    )
    
    # 2. Probar Reporte Diario
    print("\n2. Ejecutando Reporte Diario...")
    count = enviar_reporte_diario_ingresos()
    print(f"   Resultado: Enviado a {count} admins")
    
    # 3. Probar Reporte Morosos
    print("\n3. Ejecutando Reporte Morosos...")
    res = enviar_alertas_morosos_semanal()
    print(f"   Resultado: Ejecución finalizada")
    
    print("\n[INFO] Verificar logs de consola/DB para confirmar envío simulado de WhatsApp.")

if __name__ == "__main__":
    verify_reports()
