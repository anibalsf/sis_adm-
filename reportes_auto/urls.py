from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ReporteGeneradoViewSet, ConfiguracionReporteViewSet

router = DefaultRouter()
router.register(r'reportes', ReporteGeneradoViewSet, basename='reporte')
router.register(r'configuracion', ConfiguracionReporteViewSet, basename='configuracion')

urlpatterns = [
    path('', include(router.urls)),
]
