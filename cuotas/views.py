from rest_framework import viewsets
from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework import filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from .models import Cuota
from .serializers import CuotaSerializer
from historial.models import CambioEstado
from django.contrib.contenttypes.models import ContentType
from comunicacion.models import Notificacion
from django.conf import settings
import urllib.request
import json
from pagos_qr.services import QRService


class CuotaViewSet(viewsets.ModelViewSet):
    queryset = Cuota.objects.select_related('afiliado').all()
    serializer_class = CuotaSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['afiliado__ci', 'tipo', 'estado']
    ordering_fields = ['periodo', 'monto', 'tipo', 'estado']
    class IsSecretariaOrDirectivaOrReadOnly(BasePermission):
        def has_permission(self, request, view):
            if request.method in SAFE_METHODS:
                return True
            user = request.user
            if not user or not user.is_authenticated:
                return False
            return user.groups.filter(name__in=['Secretaria', 'Directiva']).exists()
    permission_classes = [IsSecretariaOrDirectivaOrReadOnly]

    def get_permissions(self):
        if getattr(self, 'action', None) == 'notificar':
            class OnlySecretaria(BasePermission):
                def has_permission(self, request, view):
                    user = request.user
                    if not user or not user.is_authenticated:
                        return False
                    return user.groups.filter(name='Secretaria').exists()
            return [OnlySecretaria()]
        return super().get_permissions()

    @action(detail=True, methods=['post'])
    def cambiar_estado(self, request, pk=None):
        obj = self.get_object()
        nuevo = request.data.get('estado')
        allowed = {
            'pendiente': {'pagada', 'anulada'},
            'pagada': set(),
            'anulada': set(),
        }
        if nuevo not in allowed.get(obj.estado, set()):
            return Response({'detail': 'Transición no permitida'}, status=400)
        old = obj.estado
        obj.estado = nuevo
        if nuevo == 'pagada' and not obj.fecha_pago:
            from datetime import date
            obj.fecha_pago = date.today()
        with transaction.atomic():
            obj.save()
            CambioEstado.objects.create(
                content_type=ContentType.objects.get_for_model(Cuota),
                object_id=obj.id,
                estado_anterior=old,
                estado_nuevo=nuevo,
                usuario=request.user,
            )
        return Response({'detail': 'Estado actualizado'})

    @action(detail=True, methods=['post'])
    def notificar(self, request, pk=None):
        obj = self.get_object()
        telefono = request.data.get('telefono')
        mensaje = request.data.get('mensaje') or f"Cuota {obj.afiliado.apellidos} {obj.afiliado.nombres} periodo {obj.periodo} {obj.estado} monto {obj.monto}"
        notif = Notificacion.objects.create(canal='whatsapp', destinatario=telefono or '', mensaje=mensaje, estado='pendiente')
        url = getattr(settings, 'WHATSAPP_WEBHOOK_URL', None)
        if url:
            try:
                data = json.dumps({'to': telefono, 'message': mensaje}).encode('utf-8')
                req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
                urllib.request.urlopen(req, timeout=5)
                notif.estado = 'enviado'
                notif.save()
            except Exception:
                pass
        return Response({'detail': 'Notificación enviada', 'notificacion_id': notif.id})

    @action(detail=True, methods=['post'])
    def generar_pago_qr(self, request, pk=None):
        cuota = self.get_object()
        monto = float(cuota.monto)
        glosa = f"Pago Cuota {cuota.periodo} - ID: {cuota.id} - A nombre de: Anibal Choque Aguirre"
        
        qr_obj = QRService.generate_qr(
            monto=monto,
            glosa=glosa,
            content_object=cuota
        )
        
        return Response({
            'qr_string': qr_obj.qr_string,
            'imagen_base64': qr_obj.imagen_base64,
            'transaction_id': qr_obj.transaction_id,
            'monto': qr_obj.monto,
            'glosa': qr_obj.glosa
        })
