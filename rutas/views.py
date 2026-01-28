from rest_framework import viewsets, filters
from rest_framework.permissions import BasePermission, SAFE_METHODS
from .models import Ruta
from .serializers import RutaSerializer


class RutaViewSet(viewsets.ModelViewSet):
    queryset = Ruta.objects.all()
    serializer_class = RutaSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nombre', 'origen', 'destino']
    ordering_fields = ['nombre', 'tarifa_base']

    class IsSecretariaOrDirectivaOrReadOnly(BasePermission):
        def has_permission(self, request, view):
            if request.method in SAFE_METHODS:
                return True
            user = request.user
            if not user or not user.is_authenticated:
                return False
            # Permitir a superusuarios, staff o miembros de grupos específicos
            return (
                user.is_superuser or 
                user.is_staff or 
                user.groups.filter(name__in=['Secretaria', 'Directiva', 'Sistemas']).exists()
            )

    permission_classes = [IsSecretariaOrDirectivaOrReadOnly]