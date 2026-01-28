from django.contrib import admin
from .models import Reunion


@admin.register(Reunion)
class ReunionAdmin(admin.ModelAdmin):
    list_display = ('id', 'fecha', 'tema', 'tipo', 'quorum')
    search_fields = ('tema', 'tipo')
    list_filter = ('tipo',)