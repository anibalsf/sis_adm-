from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import BasePermission, SAFE_METHODS

from .models import Reunion
from .serializers import ReunionSerializer


class ReunionViewSet(viewsets.ModelViewSet):
    queryset = Reunion.objects.all()
    serializer_class = ReunionSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['tema', 'tipo', 'acuerdos']
    ordering_fields = ['fecha', 'quorum']

    @action(detail=True, methods=['post'])
    def cerrar_reunion(self, request, pk=None):
        """Cierra la gestión de asistencia y genera sanciones para las faltas"""
        reunion = self.get_object()
        if reunion.estado == 'cerrada':
            return Response({'detail': 'La reunión ya está cerrada.'}, status=status.HTTP_400_BAD_REQUEST)
        
        from asistencias.models import Asistencia
        from sanciones.models import Sancion
        from django.conf import settings
        
        # 1. Asegurar que todos los que tengan 'falta' tengan su sanción
        asistencias_falta = reunion.asistencias.filter(estado='falta')
        sanciones_creadas = 0
        
        for asist in asistencias_falta:
            sancion, created = Sancion.objects.get_or_create(
                afiliado=asist.afiliado,
                tipo='falta_reunion',
                referencia_asistencia=asist,
                defaults={
                    'motivo': f'Inasistencia a reunión: {reunion.tema}',
                    'monto': getattr(settings, 'SANCTION_ABSENCE_AMOUNT', 50),
                    'estado': 'pendiente',
                }
            )
            if created:
                sanciones_creadas += 1
                
        # 2. Cambiar estado de la reunión
        reunion.estado = 'cerrada'
        reunion.save()
        
        return Response({
            'detail': f'Reunión cerrada exitosamente. Se generaron {sanciones_creadas} nuevas sanciones.',
            'sanciones_creadas': sanciones_creadas
        })

    class IsSecretariaOrDirectivaOrReadOnly(BasePermission):
        def has_permission(self, request, view):
            if request.method in SAFE_METHODS:
                return True
            user = request.user
            if not user or not user.is_authenticated:
                return False
            # Permitir a superusuarios, Secretaria, Directiva y Sistemas
            return user.is_superuser or user.groups.filter(name__in=['Secretaria', 'Directiva', 'Sistemas']).exists()

    permission_classes = [IsSecretariaOrDirectivaOrReadOnly]