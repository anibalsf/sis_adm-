from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import DocumentacionVehiculo, MantenimientoHistorial
from .serializers import DocumentacionVehiculoSerializer, MantenimientoHistorialSerializer

class DocumentacionVehiculoViewSet(viewsets.ModelViewSet):
    queryset = DocumentacionVehiculo.objects.all()
    serializer_class = DocumentacionVehiculoSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['vehiculo', 'tipo']
    search_fields = ['vehiculo__placa', 'observaciones']
    ordering_fields = ['fecha_vencimiento', 'created_at']

class MantenimientoHistorialViewSet(viewsets.ModelViewSet):
    queryset = MantenimientoHistorial.objects.all()
    serializer_class = MantenimientoHistorialSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['vehiculo', 'tipo_servicio']
    search_fields = ['vehiculo__placa', 'descripcion', 'taller']
    ordering_fields = ['fecha', 'kilometraje', 'costo']
