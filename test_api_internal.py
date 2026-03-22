import os
import django
from django.test import Client
from django.contrib.auth import get_user_model

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema.settings')
django.setup()

User = get_user_model()
user = User.objects.filter(is_superuser=True).first()
if not user:
    user = User.objects.create_superuser('admin_temp', 'admin@example.com', 'admin')

client = Client()
client.force_login(user)

print("Calling /api/reportes/graficos?tipo=mensual")
response = client.get('/api/reportes/graficos?tipo=mensual')
print("Status Code:", response.status_code)
if response.status_code != 200:
    print("Response Content:", response.content.decode())

print("\nCalling /api/reportes/transacciones")
response = client.get('/api/reportes/transacciones')
print("Status Code:", response.status_code)
if response.status_code != 200:
    print("Response Content:", response.content.decode())
