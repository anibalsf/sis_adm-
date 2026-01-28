#!/usr/bin/env python
"""Script para verificar usuarios en la base de datos"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema.settings')
django.setup()

from usuarios.models import Usuario

print("\n" + "="*60)
print("USUARIOS EN LA BASE DE DATOS")
print("="*60)

usuarios = Usuario.objects.all()
print(f"\nTotal de usuarios: {usuarios.count()}\n")

for usuario in usuarios:
    print(f"Usuario: {usuario.usuario}")
    print(f"  - Nombre: {usuario.nombre} {usuario.apellido}")
    print(f"  - Rol: {usuario.rol}")
    print(f"  - Superusuario: {usuario.is_superuser}")
    print(f"  - Activo: {usuario.is_active}")
    print(f"  - Staff: {usuario.is_staff}")
    print()

print("="*60)
