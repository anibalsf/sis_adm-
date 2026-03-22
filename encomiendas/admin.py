from django.contrib import admin
from .models import Encomienda

@admin.register(Encomienda)
class EncomiendaAdmin(admin.ModelAdmin):
    list_display = ['codigo_tracking', 'remitente_nombre', 'destinatario_nombre', 'descripcion', 'precio', 'estado', 'fecha_registro']
    list_filter = ['estado', 'pagado']
    search_fields = ['codigo_tracking', 'remitente_nombre', 'destinatario_nombre']
    readonly_fields = ['codigo_tracking', 'fecha_registro']
