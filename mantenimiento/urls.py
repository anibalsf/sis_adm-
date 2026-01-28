from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DocumentacionVehiculoViewSet, MantenimientoHistorialViewSet

router = DefaultRouter()
router.register(r'documentacion', DocumentacionVehiculoViewSet)
router.register(r'historial', MantenimientoHistorialViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
