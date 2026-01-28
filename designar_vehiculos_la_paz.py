"""
Script para marcar vehículos autorizados para La Paz
Ejecutar: python manage.py shell < designar_vehiculos_la_paz.py
"""
from vehiculos.models import Vehiculo

# Listar vehículos documentados (con placa registrada)
vehiculos_documentados = Vehiculo.objects.filter(
    indocumentado=False,
    estado='activo'
)

print(f"\n📋 Vehículos APTOS para La Paz (documentados):")
print(f"{'='*60}")
for v in vehiculos_documentados:
    convenio = "✓ CONVENIO" if v.es_convenio_caranavi else ""
    print(f"  • Placa: {v.placa:15} | Tipo: {v.tipo:20} | {convenio}")

print(f"\nTotal: {vehiculos_documentados.count()} vehículos")

# Si quieres marcar vehículos específicos como "Convenio Caranavi"
# (solo pueden ir a La Paz), descomenta y ajusta:

"""
# Ejemplo: Marcar placas específicas como convenio
placas_convenio = ['ABC-123', 'XYZ-789']  # Ajustar según tus placas

for placa in placas_convenio:
    try:
        vehiculo = Vehiculo.objects.get(placa=placa)
        vehiculo.es_convenio_caranavi = True
        vehiculo.save()
        print(f"✅ {placa} marcado como CONVENIO (solo La Paz)")
    except Vehiculo.DoesNotExist:
        print(f"❌ {placa} no encontrado")
"""
