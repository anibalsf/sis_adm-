import os
import django
import sys

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema.settings')
django.setup()

from django.contrib.auth.models import User, Group

def promote_user(username, role_name='Directiva'):
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        print(f"❌ Error: El usuario '{username}' no existe.")
        return

    group, created = Group.objects.get_or_create(name=role_name)
    
    # Clear other roles if you want single-role system, or just add
    user.groups.clear()
    user.groups.add(group)
    
    # Make sure they are active and staff if needed (optional)
    user.is_active = True
    user.save()

    print(f"✅ ¡Éxito! El usuario '{username}' ahora tiene el rol de '{role_name}'.")
    print(f"   Ahora puede ingresar al menú 'Usuarios' y gestionar permisos.")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: python promote_to_admin.py <nombre_usuario>")
        print("Ejemplo: python promote_to_admin.py admin123")
    else:
        username = sys.argv[1]
        promote_user(username)
