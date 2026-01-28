from django.contrib import admin
from .models import Vehiculo


@admin.register(Vehiculo)
class VehiculoAdmin(admin.ModelAdmin):
    list_display = ('id', 'placa', 'tipo', 'capacidad', 'afiliado', 'estado')
    search_fields = ('placa', 'tipo', 'afiliado__ci')
    list_filter = ('estado',)
