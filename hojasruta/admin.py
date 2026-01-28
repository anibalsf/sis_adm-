from django.contrib import admin
from .models import HojaRuta


@admin.register(HojaRuta)
class HojaRutaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nro', 'fecha_emision', 'afiliado', 'estado', 'precio')
    search_fields = ('nro', 'afiliado__ci')
    list_filter = ('estado',)
