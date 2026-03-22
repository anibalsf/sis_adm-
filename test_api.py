import os
import django
import sys

# Set up Django environment manually
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema.settings')
sys.path.append('c:\\Users\\Once\\Documents\\trae_projects\\sistema_administracion')
django.setup()

from django.contrib.auth import get_user_model
from core.models import Bitacora
from rest_framework.test import APIClient

client = APIClient()
# Need to authenticate or just bypass auth for local test. We can force authenticate with a superuser
User = get_user_model()
su = User.objects.filter(is_superuser=True).first()
if su:
    client.force_authenticate(user=su)

res_users = client.get('/api/usuarios/')
print("Users:", res_users.json()[:1] if isinstance(res_users.json(), list) else str(res_users.json())[:200])

res_bitacora = client.get('/api/bitacora/')
print("Bitacora:", res_bitacora.json()[:1] if isinstance(res_bitacora.json(), list) else str(res_bitacora.json())[:200])

res_wa = client.get('/api/whatsapp/messages/')
print("WhatsApp:", res_wa.json()[:1] if isinstance(res_wa.json(), list) else str(res_wa.json())[:200])
