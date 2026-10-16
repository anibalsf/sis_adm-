from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import BasePermission, SAFE_METHODS, IsAuthenticated

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
        from sanciones.services import get_sancion_config_para_reunion
        
        # Resolver tipo y monto de multa según el tipo de reunión/actividad
        # (el monto de la reunión es editable; si es 0 se usa el monto por defecto)
        cfg = get_sancion_config_para_reunion(reunion.tipo, reunion.monto_multa)
        
        # 1. Asegurar que todos los que tengan 'falta' tengan su sanción
        asistencias_falta = reunion.asistencias.filter(estado='falta')
        sanciones_creadas = 0
        
        for asist in asistencias_falta:
            sancion, created = Sancion.objects.get_or_create(
                afiliado=asist.afiliado,
                tipo=cfg['tipo'],
                referencia_asistencia=asist,
                defaults={
                    'motivo': f"Inasistencia: {reunion.tema}"[:255],
                    'monto': cfg['monto'],
                    'estado': 'pendiente',
                }
            )
            if created:
                sanciones_creadas += 1
                
        # 2. Cambiar estado de la reunión
        reunion.estado = 'cerrada'
        reunion.save()
        
        return Response({
            'detail': (
                f"Reunión cerrada exitosamente. Se generaron {sanciones_creadas} "
                f"nuevas sanciones de {cfg['tipo']} por Bs. {cfg['monto']}."
            ),
            'sanciones_creadas': sanciones_creadas,
            'tipo_sancion': cfg['tipo'],
            'monto': cfg['monto'],
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

    permission_classes = [IsAuthenticated, IsSecretariaOrDirectivaOrReadOnly]