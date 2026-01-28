import os
import django
import sys

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema.settings')
django.setup()

from django.contrib.auth.models import User

def list_users():
    print(f"{'USERNAME':<20} | {'EMAIL':<30} | {'ROLES (GROUPS)':<30} | {'IS_ACTIVE'}")
    print("-" * 100)
    for user in User.objects.all():
        groups = ", ".join([g.name for g in user.groups.all()]) or "Ninguno"
        print(f"{user.username:<20} | {user.email:<30} | {groups:<30} | {user.is_active}")

if __name__ == '__main__':
    list_users()
