from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    WhatsAppMessageViewSet,
    WhatsAppTemplateViewSet,
    WhatsAppConfigViewSet
)

router = DefaultRouter()
router.register(r'messages', WhatsAppMessageViewSet, basename='whatsapp-message')
router.register(r'templates', WhatsAppTemplateViewSet, basename='whatsapp-template')
router.register(r'config', WhatsAppConfigViewSet, basename='whatsapp-config')

urlpatterns = [
    path('', include(router.urls)),
]
