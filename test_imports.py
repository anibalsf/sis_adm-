import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema.settings')
django.setup()

from reportes.views import ReportesGraficosView
print("Successfully imported ReportesGraficosView")

from reportes.views import ReportesOperativosView
print("Successfully imported ReportesOperativosView")

from reportes.views import TransaccionesView
print("Successfully imported TransaccionesView")
