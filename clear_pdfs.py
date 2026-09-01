import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema.settings')
django.setup()

from hojasruta.models import HojaRuta

hojas = HojaRuta.objects.exclude(archivo_url__exact='')
count = hojas.count()
print(f"Limpiando {count} PDFs cacheados...")
hojas.update(archivo_url='')
print("Terminado.")
