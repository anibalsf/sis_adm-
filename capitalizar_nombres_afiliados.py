import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema.settings')
django.setup()

from afiliados.models import Afiliado

def capitalizar_afiliados():
    print("Iniciando capitalización de nombres y apellidos...")
    afiliados = Afiliado.objects.all()
    count = 0
    
    for a in afiliados:
        old_nombres = a.nombres
        old_apellidos = a.apellidos
        
        # El método .save() ahora se encargará de capitalizar gracias al override previo
        a.save()
        
        if old_nombres != a.nombres or old_apellidos != a.apellidos:
            print(f"Actualizado: {old_nombres} {old_apellidos} -> {a.nombres} {a.apellidos}")
            count += 1
            
    print(f"\nFinalizado. Se actualizaron {count} registros de {afiliados.count()} totales.")

if __name__ == "__main__":
    capitalizar_afiliados()
