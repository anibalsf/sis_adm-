import os
import django
import sqlite3

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema.settings')
django.setup()

from tesoreria.models import Pago, Egreso
from django.db import connection

# Delete all records
Pago.objects.all().delete()
Egreso.objects.all().delete()

# Reset auto-increment sequence for these models
with connection.cursor() as cursor:
    try:
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='tesoreria_pago';")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='tesoreria_egreso';")
        print("Sequence reset successfully.")
    except Exception as e:
        print("Error resetting sequences:", e)

print("Ingresos and Egresos have been reset to 0.")
