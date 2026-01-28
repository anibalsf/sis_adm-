from rest_framework import viewsets, filters
from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from .models import Sancion
from .serializers import SancionSerializer
from historial.models import CambioEstado
from django.contrib.contenttypes.models import ContentType
from comunicacion.models import Notificacion
from comunicacion.whatsapp_templates import WhatsAppTemplates
from django.conf import settings
import urllib.request
import json
from pagos_qr.services import QRService


from django_filters.rest_framework import DjangoFilterBackend

class SancionViewSet(viewsets.ModelViewSet):
    queryset = Sancion.objects.select_related('afiliado', 'referencia_asistencia').all()
    serializer_class = SancionSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ['afiliado__ci', 'tipo', 'estado']
    ordering_fields = ['created_at', 'monto']
    filterset_fields = ['tipo', 'estado', 'afiliado']

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
            'pendiente': {'notificada', 'pagada', 'anulada'},
            'notificada': {'pagada', 'anulada'},
            'pagada': set(),
            'anulada': set(),
        }
        if nuevo not in allowed.get(obj.estado, set()):
            return Response({'detail': 'Transición no permitida'}, status=400)
        old = obj.estado
        obj.estado = nuevo
        with transaction.atomic():
            obj.save()
            CambioEstado.objects.create(
                content_type=ContentType.objects.get_for_model(Sancion),
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
        mensaje = request.data.get('mensaje') or f"Sanción {obj.tipo} {obj.estado} monto {obj.monto} para {obj.afiliado.apellidos} {obj.afiliado.nombres}"
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
        sancion = self.get_object()
        monto = float(sancion.monto)
        glosa = f"Pago Sanción {sancion.tipo} - ID: {sancion.id} - A nombre de: Anibal Choque Aguirre"
        
        qr_obj = QRService.generate_qr(
            monto=monto,
            glosa=glosa,
            content_object=sancion
        )
        
        return Response({
            'qr_string': qr_obj.qr_string,
            'imagen_base64': qr_obj.imagen_base64,
            'transaction_id': qr_obj.transaction_id,
            'monto': qr_obj.monto,
            'glosa': qr_obj.glosa
        })
    
    @action(detail=False, methods=['get'])
    def pendientes_afiliado(self, request):
        """Obtiene sanciones pendientes de un afiliado"""
        afiliado_id = request.query_params.get('afiliado')
        if not afiliado_id:
            return Response({'error': 'afiliado_id requerido'}, status=400)
        
        sanciones = Sancion.objects.filter(
            afiliado_id=afiliado_id,
            estado__in=['pendiente', 'notificada']
        ).select_related('afiliado')
        
        serializer = self.get_serializer(sanciones, many=True)
        
        total_adeudado = sum(float(s.monto) for s in sanciones)
        
        return Response({
            'tiene_sanciones': sanciones.exists(),
            'cantidad': sanciones.count(),
            'total_adeudado': total_adeudado,
            'sanciones': serializer.data
        })
    
    def perform_create(self, serializer):
        obj = serializer.save()
        try:
            from comunicacion.services import WhatsAppService
            # Calcular deuda total
            sanciones_pendientes = Sancion.objects.filter(
                afiliado=obj.afiliado,
                estado='pendiente'
            )
            total = sum(float(s.monto) for s in sanciones_pendientes)
            count = sanciones_pendientes.count()
            
            if obj.afiliado.telefono:
                WhatsAppService().send_message(
                    obj.afiliado.telefono, 
                    WhatsAppTemplates.alerta_deuda(
                        obj.afiliado.nombre_completo,
                        total,
                        count
                    )
                )
        except Exception:
            pass

    @action(detail=False, methods=['post'])
    def generar_por_inasistencia(self, request):
        """
        Generar sanción automática al marcar inasistencia.
        Espera: {
            "afiliado_id": 1,
            "asistencia_id": 5,
            "tipo": "Falta a Reunión",
            "monto": 50.00,
            "motivo": "Inasistencia a reunión del 04/12/2025"
        }
        """
        from afiliados.models import Afiliado
        from asistencias.models import Asistencia
        from comunicacion.services import WhatsAppService
        from comunicacion.whatsapp_templates import WhatsAppTemplates
        
        afiliado_id = request.data.get('afiliado_id')
        asistencia_id = request.data.get('asistencia_id')
        tipo_config = request.data.get('tipo_config', 'FALTA_REUNION')
        motivo = request.data.get('motivo', '')
        
        if not afiliado_id:
            return Response({'error': 'afiliado_id es requerido'}, status=400)
        
        try:
            afiliado = Afiliado.objects.get(id=afiliado_id)
            asistencia = Asistencia.objects.get(id=asistencia_id) if asistencia_id else None
            
            # Obtener configuración
            config = settings.SANCIONES_CONFIG.get(tipo_config, {})
            tipo = config.get('tipo', 'Sanción')
            monto = config.get('monto_default', 50.00)
            
            # Verificar si ya existe
            if asistencia:
                existe = Sancion.objects.filter(
                    afiliado=afiliado,
                    referencia_asistencia=asistencia,
                    tipo=tipo
                ).exists()
                
                if existe:
                    return Response({
                        'error': 'Ya existe una sanción para esta inasistencia'
                    }, status=400)
            
            # Crear sanción
            with transaction.atomic():
                sancion = Sancion.objects.create(
                    afiliado=afiliado,
                    tipo=tipo,
                    motivo=motivo,
                    monto=monto,
                    estado='pendiente',
                    referencia_asistencia=asistencia
                )
                
                # Notificar por WhatsApp
                try:
                    sanciones_pendientes = Sancion.objects.filter(
                        afiliado=afiliado,
                        estado='pendiente'
                    )
                    total = sum(float(s.monto) for s in sanciones_pendientes)
                    count = sanciones_pendientes.count()
                    
                    if afiliado.telefono:
                        WhatsAppService().send_message(
                            afiliado.telefono,
                            WhatsAppTemplates.alerta_deuda(
                                afiliado.nombre_completo,
                                total,
                                count
                            )
                        )
                except Exception as e:
                    print(f"Error notificando sanción: {e}")
                
                return Response({
                    'success': True,
                    'mensaje': f'Sanción generada: {tipo} por Bs. {monto}',
                    'sancion_id': sancion.id,
                    'afiliado': afiliado.nombre_completo,
                    'monto': float(sancion.monto)
                }, status=201)
                
        except Afiliado.DoesNotExist:
            return Response({'error': 'Afiliado no encontrado'}, status=404)
        except Asistencia.DoesNotExist:
            return Response({'error': 'Asistencia no encontrada'}, status=404)
        except Exception as e:
            return Response({'error': str(e)}, status=500)