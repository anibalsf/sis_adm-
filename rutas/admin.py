from django.contrib import admin
from .models import Ruta


@admin.register(Ruta)
class RutaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'origen', 'destino', 'tarifa_base')
    search_fields = ('nombre', 'origen', 'destino')
    list_filter = ('origen', 'destino')