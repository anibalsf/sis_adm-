# Script para crear usuario de prueba
# Ejecutar con: python manage.py shell < crear_usuario.py

from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

# Crear o actualizar usuario admin
username = 'admin123'
password = 'admin123'
email = 'admin@taipiplaya.com'

try:
    user = User.objects.get(username=username)
    print(f"Usuario '{username}' ya existe. Actualizando contraseña...")
    user.set_password(password)
    user.is_staff = True
    user.is_superuser = True
    user.save()
except User.DoesNotExist:
    user = User.objects.create_superuser(username, email, password)
    print(f"Usuario '{username}' creado exitosamente!")

# Crear token
token, created = Token.objects.get_or_create(user=user)

print("\n" + "="*50)
print("CREDENCIALES DE ACCESO")
print("="*50)
print(f"Username: {username}")
print(f"Password: {password}")
print(f"Token: {token.key}")
print("="*50)
