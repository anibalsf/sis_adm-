from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.contenttypes.models import ContentType
from .models import CambioEstado, LogAuditoria
from .serializers import CambioEstadoSerializer, LogAuditoriaSerializer


class HistorialView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        app_label = request.GET.get('app')
        model = request.GET.get('model')
        object_id = request.GET.get('object_id')
        desde = request.GET.get('desde')
        hasta = request.GET.get('hasta')
        usuario_id = request.GET.get('usuario_id')
        if not (app_label and model and object_id):
            return Response({'detail': 'Parámetros requeridos: app, model, object_id'}, status=400)
        try:
            ct = ContentType.objects.get(app_label=app_label, model=model.lower())
        except ContentType.DoesNotExist:
            return Response({'detail': 'Modelo inválido'}, status=400)
        qs = CambioEstado.objects.filter(content_type=ct, object_id=object_id).order_by('-timestamp')
        if desde:
            qs = qs.filter(timestamp__gte=desde)
        if hasta:
            qs = qs.filter(timestamp__lte=hasta)
        if usuario_id:
            qs = qs.filter(usuario_id=usuario_id)
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        start = (page - 1) * page_size
        end = start + page_size
        items = qs[start:end]
        return Response({
            'count': qs.count(),
            'results': CambioEstadoSerializer(items, many=True).data,
        })

class BitacoraView(APIView):
    permission_classes = [IsAuthenticated] # En producción debería ser IsAdminUser o similar

    def get(self, request):
        desde = request.GET.get('desde')
        hasta = request.GET.get('hasta')
        usuario_id = request.GET.get('usuario_id')
        tabla = request.GET.get('tabla')
        accion = request.GET.get('accion')
        
        qs = LogAuditoria.objects.all().select_related('usuario').order_by('-fecha_hora')
        
        if desde:
            qs = qs.filter(fecha_hora__gte=desde)
        if hasta:
            qs = qs.filter(fecha_hora__lte=hasta)
        if usuario_id:
            qs = qs.filter(usuario_id=usuario_id)
        if tabla:
            qs = qs.filter(tabla=tabla.lower())
        if accion:
            qs = qs.filter(accion=accion)
            
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 50))
        start = (page - 1) * page_size
        end = start + page_size
        items = qs[start:end]
        
        return Response({
            'count': qs.count(),
            'results': LogAuditoriaSerializer(items, many=True).data,
        })