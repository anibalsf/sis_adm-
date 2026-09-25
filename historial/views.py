from django.db.models import Count, Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.contenttypes.models import ContentType
from .constants import MODULOS, nombre_modulo
from .models import CambioEstado, LogAuditoria
from .serializers import CambioEstadoSerializer, LogAuditoriaSerializer


def paginar(qs, request, default_size=50):
    try:
        page = max(int(request.GET.get('page', 1)), 1)
    except (TypeError, ValueError):
        page = 1
    try:
        page_size = min(max(int(request.GET.get('page_size', default_size)), 1), 200)
    except (TypeError, ValueError):
        page_size = default_size
    inicio = (page - 1) * page_size
    return qs[inicio:inicio + page_size], page, page_size


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
        items, page, page_size = paginar(qs, request, default_size=20)
        return Response({
            'count': qs.count(),
            'page': page,
            'page_size': page_size,
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
        modulo = request.GET.get('modulo')
        busqueda = (request.GET.get('q') or '').strip()

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
            qs = qs.filter(accion__in=[a for a in accion.split(',') if a])
        if modulo:
            qs = qs.filter(app_label__in=[m for m in modulo.split(',') if m])
        if busqueda:
            qs = qs.filter(
                Q(descripcion__icontains=busqueda)
                | Q(tabla__icontains=busqueda)
                | Q(objeto_id__icontains=busqueda)
                | Q(usuario__username__icontains=busqueda)
            )

        count = qs.count()
        items, page, page_size = paginar(qs, request)

        # Módulos que realmente tienen movimientos (el filtro se arma con datos, no a mano)
        modulos = [
            {
                'app_label': row['app_label'],
                'nombre': nombre_modulo(row['app_label']),
                'total': row['total'],
            }
            for row in LogAuditoria.objects.values('app_label').annotate(total=Count('id')).order_by('-total')
        ]

        resumen_accion = {
            row['accion']: row['total']
            for row in LogAuditoria.objects.values('accion').annotate(total=Count('id'))
        }

        return Response({
            'count': count,
            'page': page,
            'page_size': page_size,
            'modulos': modulos,
            'resumen': {
                'total': LogAuditoria.objects.count(),
                'por_accion': resumen_accion,
                'sin_usuario': LogAuditoria.objects.filter(usuario__isnull=True).count(),
            },
            'results': LogAuditoriaSerializer(items, many=True).data,
        })
