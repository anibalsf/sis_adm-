import os
import django
import sys

# Configurar el entorno de Django
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema.settings')
django.setup()

from reportes_auto.models import ConfiguracionReporte

def actualizar_destinatarios():
    numero = "71275002"
    reportes = [
        ('diario', 'Reporte Diario de Ingresos'),
        ('semanal', 'Reporte Semanal Financiero'),
        ('mensual', 'Reporte Mensual General'),
        ('lunes_control', 'Lista de Control Oficial (Lunes)')
    ]
    
    print(f"🔄 Actualizando destinatarios al número: {numero}")
    
    for tipo, nombre in reportes:
        config, created = ConfiguracionReporte.objects.update_or_create(
            tipo=tipo,
            defaults={
                'nombre': nombre,
                'destinatarios_whatsapp': numero,
                'activo': True
            }
        )
        status = "Creado" if created else "Actualizado"
        print(f"✅ {status}: {nombre} ({tipo})")

if __name__ == "__main__":
    actualizar_destinatarios()
