from django.contrib import admin
from .models import Asistencia


@admin.register(Asistencia)
class AsistenciaAdmin(admin.ModelAdmin):
    list_display = ('id', 'reunion', 'afiliado', 'presente', 'created_at')
    search_fields = ('reunion__tema', 'afiliado__ci')
    list_filter = ('presente',)