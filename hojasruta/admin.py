from django.contrib import admin
from .models import HojaRuta, TurnoSalida


@admin.register(HojaRuta)
class HojaRutaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nro', 'fecha_emision', 'afiliado', 'estado', 'precio')
    search_fields = ('nro', 'afiliado__ci')
    list_filter = ('estado',)


@admin.register(TurnoSalida)
class TurnoSalidaAdmin(admin.ModelAdmin):
    list_display = ('id', 'fecha', 'ruta', 'afiliado', 'orden')
    list_filter = ('fecha', 'ruta')
    search_fields = ('afiliado__apellidos', 'afiliado__nombres')
