from django.contrib import admin
from .models import CambioEstado


@admin.register(CambioEstado)
class CambioEstadoAdmin(admin.ModelAdmin):
    list_display = ('id', 'content_type', 'object_id', 'estado_anterior', 'estado_nuevo', 'usuario', 'timestamp')
    search_fields = ('estado_anterior', 'estado_nuevo')