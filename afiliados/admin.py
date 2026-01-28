from django.contrib import admin
from .models import Afiliado


@admin.register(Afiliado)
class AfiliadoAdmin(admin.ModelAdmin):
    list_display = ('id', 'ci', 'apellidos', 'nombres', 'telefono', 'direccion', 'estado', 'is_active')
    search_fields = ('ci', 'apellidos', 'nombres', 'telefono', 'direccion')
    list_filter = ('estado', 'is_active')
