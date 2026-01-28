from django.contrib import admin
from .models import Sancion


@admin.register(Sancion)
class SancionAdmin(admin.ModelAdmin):
    list_display = ('id', 'afiliado', 'tipo', 'monto', 'estado', 'created_at')
    search_fields = ('afiliado__ci', 'tipo', 'estado')
    list_filter = ('estado', 'tipo')