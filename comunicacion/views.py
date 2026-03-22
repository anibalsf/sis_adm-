from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Notificacion, AlertaSistema
from .serializers import NotificacionSerializer, AlertaSistemaSerializer

class NotificacionViewSet(viewsets.ModelViewSet):
    queryset = Notificacion.objects.all()
    serializer_class = NotificacionSerializer

class AlertaSistemaViewSet(viewsets.ModelViewSet):
    queryset = AlertaSistema.objects.all()
    serializer_class = AlertaSistemaSerializer

    @action(detail=False, methods=['get'])
    def no_leidas(self, request):
        count = AlertaSistema.objects.filter(leida=False).count()
        alertas = AlertaSistema.objects.filter(leida=False)[:10]
        return Response({
            'count': count,
            'alertas': AlertaSistemaSerializer(alertas, many=True).data
        })

    @action(detail=True, methods=['post'])
    def marcar_leida(self, request, pk=None):
        alerta = self.get_object()
        alerta.leida = True
        alerta.save()
        return Response({'status': 'ok'})

    @action(detail=False, methods=['post'])
    def marcar_todas_leidas(self, request):
        AlertaSistema.objects.filter(leida=False).update(leida=True)
        return Response({'status': 'ok'})
