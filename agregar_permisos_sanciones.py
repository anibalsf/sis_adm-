"""
Script para agregar permisos al usuario para el módulo de Sanciones Asistencia
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema.settings')
django.setup()

from django.contrib.auth.models import User, Group

def agregar_permisos_usuario(username):
    """Agrega el usuario al grupo Secretaria para poder gestionar reuniones"""
    try:
        # Obtener o crear el grupo Secretaria
        grupo_secretaria, created = Group.objects.get_or_create(name='Secretaria')
        if created:
            print(f"✅ Grupo 'Secretaria' creado")
        
        # Obtener el usuario
        usuario = User.objects.get(username=username)
        
        # Agregar al grupo
        usuario.groups.add(grupo_secretaria)
        
        print(f"✅ Usuario '{usuario.username}' agregado al grupo 'Secretaria'")
        print(f"📋 Grupos del usuario: {', '.join([g.name for g in usuario.groups.all()])}")
        print("\n🎉 ¡Listo! Ahora puedes crear reuniones y gestionar asistencias.")
        
    except User.DoesNotExist:
        print(f"❌ Error: No se encontró el usuario '{username}'")
        print("\nUsuarios disponibles:")
        for user in User.objects.all():
            print(f"  - {user.username}")

if __name__ == '__main__':
    # Listar usuarios disponibles
    print("👥 Usuarios disponibles en el sistema:")
    for user in User.objects.all():
        grupos = ', '.join([g.name for g in user.groups.all()]) or 'Sin grupos'
        print(f"  - {user.username} ({grupos})")
    
    print("\n" + "="*50)
    username = input("Ingresa el nombre de usuario a dar permisos: ")
    agregar_permisos_usuario(username)
