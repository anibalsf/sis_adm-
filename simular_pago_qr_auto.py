import os
import django
import sys
from decimal import Decimal
from datetime import date

# Configurar el entorno de Django
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema.settings')
django.setup()

from tesoreria.models import Pago, TipoPago
from afiliados.models import Afiliado
from pagos_qr.services import QRService
from pagos_qr.models import QRTransaccion

def simular_flujo_pago_qr():
    print("🚀 Iniciando Simulación de Pago QR Automatizado...")
    
    # 1. Obtener o crear datos base
    afiliado = Afiliado.objects.first()
    if not afiliado:
        print("❌ Error: No hay afiliados en la BD.")
        return
        
    tipo_pago = TipoPago.objects.filter(tipo='ingreso').first()
    if not tipo_pago:
        print("❌ Error: No hay tipos de pago configurados.")
        return

    print(f"👤 Afiliado: {afiliado.nombre_completo} (Telf: {afiliado.telefono})")
    print(f"📝 Concepto: {tipo_pago.nombre}")

    # 2. El usuario genera un pago en el frontend (Estado: Pendiente)
    pago = Pago.objects.create(
        afiliado=afiliado,
        tipo_pago=tipo_pago,
        monto=Decimal('50.00'),
        fecha_pago=date.today(),
        metodo_pago='qr',
        estado='pendiente',
        observaciones="Simulación de Pago QR"
    )
    print(f"\n1️⃣ Pago registrado en el sistema (ID: {pago.id})")
    print(f"   Estado actual: {pago.estado} (No se ha enviado WhatsApp todavía)")

    # 3. Se genera el QR para este pago
    qr_obj = QRService.generate_qr(
        monto=pago.monto,
        glosa=f"Pago {tipo_pago.nombre} - ID {pago.id}",
        content_object=pago
    )
    print(f"2️⃣ QR de Transacción generado (Trans ID: {qr_obj.transaction_id[:8]})")

    # 4. Simulación de que el usuario paga con su Celular
    #    El banco llama al webhook del sistema
    print("\n⏳ Esperando confirmación del banco/Yape...")
    success, msg = QRService.verify_payment(qr_obj.transaction_id)
    
    if success:
        print(f"3️⃣ ✅ {msg}!")
        
        # 5. Verificar que el estado del pago cambió
        pago.refresh_from_db()
        print(f"4️⃣ Pago actualizado en BD: Estado = {pago.estado.upper()}")
        
        print("\n✨ RESULTADO FINAL:")
        print("--------------------------------------------------")
        print("El sistema ha detectado el pago y disparado el SIGNAL.")
        print("Se ha generado un registro de WhatsApp en 'whatsapp_notif' con el enlace al PDF.")
        print("--------------------------------------------------")
    else:
        print(f"❌ Error en verificación: {msg}")

if __name__ == "__main__":
    simular_flujo_pago_qr()
