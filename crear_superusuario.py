#!/usr/bin/env python
"""Script para crear un superusuario admin123"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema.settings')
django.setup()

from django.contrib.auth.models import User

# Datos del superusuario
username = 'admin123'
email = 'admin@taipiplaya.com'
password = 'admin123'

# Verificar si el usuario ya existe
if User.objects.filter(username=username).exists():
    print(f"\n❌ El usuario '{username}' ya existe.")
    user = User.objects.get(username=username)
    print(f"   - Superusuario: {user.is_superuser}")
    print(f"   - Activo: {user.is_active}")
    print(f"   - Staff: {user.is_staff}")
    
    # Actualizar contraseña
    user.set_password(password)
    user.is_superuser = True
    user.is_staff = True
    user.is_active = True
    user.save()
    print(f"\n✅ Contraseña actualizada para '{username}'")
else:
    # Crear el superusuario
    user = User.objects.create_superuser(
        username=username,
        email=email,
        password=password
    )
    print(f"\n✅ Superusuario '{username}' creado exitosamente!")

print(f"\nCredenciales:")
print(f"  Usuario: {username}")
print(f"  Contraseña: {password}")
print(f"\nPuedes iniciar sesión ahora en http://localhost:5173")
