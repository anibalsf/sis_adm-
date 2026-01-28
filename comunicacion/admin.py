from django.contrib import admin
from .models import Notificacion


@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = ('id', 'canal', 'destinatario', 'estado', 'created_at')
    search_fields = ('destinatario', 'canal', 'estado')