from django.apps import AppConfig


import os

class RutasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'rutas'
    path = os.path.dirname(os.path.abspath(__file__))