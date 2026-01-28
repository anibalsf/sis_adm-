import os
import django
import json
import base64

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sistema.settings")
django.setup()

from pagos_qr.services import QRService
from pagos_qr.models import QRTransaccion

def verify_qr_flow():
    print("--- Verificando Flujo de Pagos QR ---")
    
    # 1. Generar QR
    print("1. Generando QR de prueba (50Bs)...")
    try:
        qr_obj = QRService.generate_qr(monto=50.00, glosa="Prueba de concepto QR")
        print(f"[OK] QR Generado: {qr_obj.transaction_id}")
        print(f"   Estado inicial: {qr_obj.estado}")
        if qr_obj.imagen_base64:
            print("   [OK] Imagen Base64 generada correctamente")
            # Opcional: decodificar para verificar que sea imagen válida, pero por ahora confiamos
            
    except Exception as e:
        print(f"[ERROR] Error generando QR: {e}")
        return

    # 2. Simular Webhook (Pago realizado)
    print("\n2. Simulando callback del banco (Webhook)...")
    trx_id = qr_obj.transaction_id
    
    success, msg = QRService.verify_payment(trx_id)
    
    if success:
        print(f"[OK] Webhook procesado: {msg}")
    else:
        print(f"[ERROR] Webhook falló: {msg}")
        
    # 3. Verificar estado final
    print("\n3. Verificando persistencia en BD...")
    qr_final = QRTransaccion.objects.get(transaction_id=trx_id)
    print(f"   Estado final: {qr_final.estado}")
    
    if qr_final.estado == 'pagado':
        print("\n[EXITO] PRUEBA EXITOSA: El ciclo de pago QR funciona.")
    else:
        print("\n[ALERTA] El estado no cambió a pagado.")

if __name__ == "__main__":
    verify_qr_flow()
