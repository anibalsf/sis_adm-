from django.contrib import admin
from .models import MiembroDirectorio


@admin.register(MiembroDirectorio)
class MiembroDirectorioAdmin(admin.ModelAdmin):
    list_display = ('id', 'afiliado', 'get_cargo_display', 'fecha_inicio', 'fecha_fin', 'get_estado_display')
    search_fields = ('afiliado__ci', 'afiliado__apellidos', 'afiliado__nombres', 'cargo')
    list_filter = ('cargo', 'estado')