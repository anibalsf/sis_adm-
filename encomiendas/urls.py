from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EncomiendaViewSet

router = DefaultRouter()
router.register(r'', EncomiendaViewSet, basename='encomienda')

urlpatterns = [
    path('', include(router.urls)),
]
