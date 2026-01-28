from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EgresoViewSet

router = DefaultRouter()
router.register(r'egresos', EgresoViewSet)

urlpatterns = [
    path('', include(router.urls)),
]