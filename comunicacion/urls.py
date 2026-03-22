from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NotificacionViewSet, AlertaSistemaViewSet

router = DefaultRouter()
router.register(r'notificaciones', NotificacionViewSet)
router.register(r'alertas', AlertaSistemaViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
