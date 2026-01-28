from django.contrib import admin
from .models import Cuota


@admin.register(Cuota)
class CuotaAdmin(admin.ModelAdmin):
    list_display = ('id', 'afiliado', 'periodo', 'tipo', 'monto', 'estado', 'fecha_pago')
    search_fields = ('afiliado__ci', 'tipo', 'estado')
    list_filter = ('tipo', 'estado')
