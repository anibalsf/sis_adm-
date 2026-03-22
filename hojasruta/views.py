from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from django.utils import timezone
from .models import HojaRuta, TurnoSalida
from .serializers import HojaRutaSerializer, TurnoSalidaSerializer
from afiliados.models import Afiliado
from rutas.models import Ruta
from sanciones.models import Sancion
from sanciones.serializers import SancionSerializer
from comunicacion.models import Notificacion
from django.contrib.contenttypes.models import ContentType
from historial.models import CambioEstado
import json
import urllib.request
from datetime import date, timedelta


class HojaRutaViewSet(viewsets.ModelViewSet):
    queryset = HojaRuta.objects.select_related('afiliado', 'vehiculo', 'ruta').all()
    serializer_class = HojaRutaSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nro', 'afiliado__ci', 'afiliado__apellidos', 'afiliado__nombres', 'ruta__nombre', 'vehiculo__placa', 'agente_parada']
    ordering_fields = ['fecha_emision', 'fecha_salida', 'nro', 'precio']
    
from sistema.permissions import IsSecretariaOrDirectivaOrReadOnly

class HojaRutaViewSet(viewsets.ModelViewSet):
    queryset = HojaRuta.objects.select_related('afiliado', 'vehiculo', 'ruta').all()
    serializer_class = HojaRutaSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nro', 'afiliado__ci', 'afiliado__apellidos', 'afiliado__nombres', 'ruta__nombre', 'vehiculo__placa', 'agente_parada']
    ordering_fields = ['fecha_emision', 'fecha_salida', 'nro', 'precio']
    
    permission_classes = [IsSecretariaOrDirectivaOrReadOnly]

    def get_queryset(self):
        qs = super().get_queryset()
        desde = self.request.query_params.get('desde')
        hasta = self.request.query_params.get('hasta')
        ruta_id = self.request.query_params.get('ruta_id')
        afiliado_id = self.request.query_params.get('afiliado_id')
        destino = self.request.query_params.get('destino')
        if desde:
            qs = qs.filter(fecha_salida__gte=desde) | qs.filter(fecha_emision__gte=desde)
        if hasta:
            qs = qs.filter(fecha_salida__lte=hasta) | qs.filter(fecha_emision__lte=hasta)
        if ruta_id:
            qs = qs.filter(ruta_id=ruta_id)
        if afiliado_id:
            qs = qs.filter(afiliado_id=afiliado_id)
        if destino:
            canon = destino.strip().lower()
            qs = qs.filter(ruta__destino__iexact=canon) | qs.filter(ruta__nombre__iexact=canon)
        return qs

    def get_permissions(self):
        if getattr(self, 'action', None) == 'notificar':
            class OnlySecretaria(BasePermission):
                def has_permission(self, request, view):
                    user = request.user
                    if not user or not user.is_authenticated:
                        return False
                    if getattr(user, 'is_superuser', False) or getattr(user, 'is_staff', False):
                        return True
                    return user.groups.filter(name__in=['Secretaria', 'Sistemas']).exists()
            return [OnlySecretaria()]
        return super().get_permissions()

    @action(detail=True, methods=['post'])
    def cambiar_estado(self, request, pk=None):
        obj = self.get_object()
        nuevo = request.data.get('estado')
        allowed = {
            'emitida': {'anulada', 'notificada', 'pagada'},
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
                content_type=ContentType.objects.get_for_model(HojaRuta),
                object_id=obj.id,
                estado_anterior=old,
                estado_nuevo=nuevo,
                usuario=request.user,
            )
        return Response({'detail': 'Estado actualizado'})

    @action(detail=True, methods=['post'])
    def notificar(self, request, pk=None):
        """
        Notificar al agente de parada sobre su designación vía WhatsApp.
        Usa una plantilla predefinida si no se proporciona mensaje personalizado.
        """
        obj = self.get_object()
        telefono = request.data.get('telefono')
        
        # Plantilla de mensaje predefinida para designación de agente
        if not request.data.get('mensaje'):
            ruta_nombre = obj.ruta.nombre if obj.ruta else "Ruta no especificada"
            fecha_val = obj.fecha_salida or obj.fecha_emision
            fecha_str = None
            try:
                # Si es datetime/date, usar dd/mm/yyyy
                fecha_str = fecha_val.strftime('%d/%m/%Y')
            except Exception:
                # Si es string 'YYYY-MM-DD', reordenar
                if isinstance(fecha_val, str) and '-' in fecha_val:
                    parts = fecha_val.split('-')
                    if len(parts) == 3:
                        fecha_str = f"{parts[2]}/{parts[1]}/{parts[0]}"
                if not fecha_str:
                    fecha_str = str(fecha_val) if fecha_val else 'No especificada'
            
            mensaje = (
                f"🚌 *Designación de Agente de Parada*\n\n"
                f"Señor afiliado, usted fue asignado a la ruta: {ruta_nombre} en la fecha: {fecha_str}.\n"
                f"• Hoja Nº: {obj.nro}\n"
                f"• Multa por incumplimiento, de acuerdo a normativas internas\n\n"
                f"Por favor confirme su disponibilidad.\n\n"
                f"_Sindicato Mixto de Transporte Integración Taipiplaya_"
            )
            
            # Agregar link al PDF si está disponible
            if obj.archivo_url:
                mensaje += f"\n\n📄 Documento: {obj.archivo_url}"
        else:
            mensaje = request.data.get('mensaje')
        
        # Crear notificación
        notif = Notificacion.objects.create(
            canal='whatsapp',
            destinatario=telefono or '',
            mensaje=mensaje,
            estado='pendiente'
        )
        
        # Intentar enviar vía webhook si está configurado
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
        
        return Response({
            'detail': 'Notificación de designación enviada',
            'notificacion_id': notif.id,
            'mensaje': mensaje
        })

    @action(detail=True, methods=['post', 'get'])
    def generar_pdf(self, request, pk=None):
        obj = self.get_object()
        try:
            url = self._generate_pdf(obj)
            return Response({'detail': 'PDF generado', 'archivo_url': url})
        except Exception as e:
            return Response({'detail': f'Error al generar PDF: {str(e)}'}, status=500)

    def _generate_pdf(self, obj):
        try:
            from reportlab.pdfgen import canvas
        except Exception:
            raise Exception('Librería reportlab no instalada')
            
        import os
        from django.conf import settings
        folder = os.path.join(settings.MEDIA_ROOT, 'hojasruta')
        os.makedirs(folder, exist_ok=True)
        filename = f"hoja_{obj.id}.pdf"
        path = os.path.join(folder, filename)
        c = canvas.Canvas(path)
        c.setTitle(f"Hoja de Ruta #{obj.nro}")
        c.drawString(40, 800, f"Hoja de Ruta #{obj.nro}")
        y = 780
        c.drawString(40, y, f"Afiliado: {obj.afiliado.apellidos} {obj.afiliado.nombres}" if obj.afiliado_id else "Afiliado: -"); y-=16
        c.drawString(40, y, f"Vehículo: {obj.vehiculo.placa}" if obj.vehiculo_id else "Vehículo: -"); y-=16
        c.drawString(40, y, f"Destino: {obj.ruta.nombre}" if obj.ruta_id else "Destino: -"); y-=16
        c.drawString(40, y, f"Fecha salida: {obj.fecha_salida or obj.fecha_emision}"); y-=16
        c.drawString(40, y, f"Agente parada: {obj.agente_parada or '-'}"); y-=16
        c.drawString(40, y, f"Monto: {obj.precio}"); y-=16
        try:
            import qrcode
            qr_filename = f"qr_{obj.id}.png"
            qr_path = os.path.join(folder, qr_filename)
            
            # URL de validación
            frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')
            data = f"{frontend_url}/verificar-hoja/{obj.id}"
            
            img = qrcode.make(data)
            img.save(qr_path)
            c.drawImage(qr_path, 440, 720, width=120, height=120)
        except Exception:
            pass
        c.showPage()
        c.save()
        try:
            origin = self.request.build_absolute_uri('/').rstrip('/')
        except Exception:
            origin = getattr(settings, 'FRONTEND_URL', 'http://127.0.0.1:8000').replace('/','').rstrip('/')
        obj.archivo_url = f"{origin}{settings.MEDIA_URL}hojasruta/{filename}"
        obj.save(update_fields=['archivo_url'])
        return obj.archivo_url

    @action(detail=True, methods=['get'], permission_classes=[])
    def validar_qr(self, request, pk=None):
        """
        Endpoint público para validar QR. Retorna estado y datos básicos.
        """
        try:
            obj = self.get_object()
            data = {
                'id': obj.id,
                'nro': obj.nro,
                'estado': obj.estado,
                'fecha_salida': obj.fecha_salida,
                'ruta': obj.ruta.nombre if obj.ruta else '-',
                'vehiculo': obj.vehiculo.placa if obj.vehiculo else '-',
                'afiliado': f"{obj.afiliado.apellidos} {obj.afiliado.nombres}" if obj.afiliado else '-',
                'monto': str(obj.precio)
            }
            return Response(data)
        except Exception as e:
            return Response({'detail': 'Hoja de ruta no encontrada o inválida'}, status=404)

    def create(self, request, *args, **kwargs):
        afiliado_id = request.data.get('afiliado') or request.data.get('afiliado_id')
        force = request.data.get('force', False)
        
        if afiliado_id and not force:
            # Verificar sanciones pendientes
            sanciones = Sancion.objects.filter(
                afiliado_id=afiliado_id,
                estado__in=['pendiente', 'notificada']
            )
            
            if sanciones.exists():
                total = sum(float(s.monto) for s in sanciones)
                return Response({
                    'requires_confirmation': True,
                    'mensaje': f'El afiliado tiene {sanciones.count()} sanción(es) pendiente(s) por Bs. {total:.2f}',
                    'sanciones_count': sanciones.count(),
                    'total_adeudado': total,
                    'sanciones': SancionSerializer(sanciones, many=True).data
                }, status=409)  # HTTP 409 Conflict
        
        try:
            return super().create(request, *args, **kwargs)
        except Exception as e:
            from django.core.exceptions import ValidationError
            if isinstance(e, ValidationError):
                return Response({'detail': str(e)}, status=400)
            # Si es otro error, relanzarlo o devolver 500 con detalle
            import traceback
            traceback.print_exc()
            return Response({'detail': f'Error interno al guardar: {str(e)}'}, status=500)

    def perform_create(self, serializer):
        with transaction.atomic():
            instance = serializer.save()
            ct = ContentType.objects.get_for_model(HojaRuta)
            CambioEstado.objects.create(content_type=ct, object_id=instance.id, estado_anterior='', estado_nuevo=instance.estado)
            self._generate_pdf(instance)
            # Notificación automática al administrador cuando es Ruta La Paz
            try:
                es_la_paz = (
                    instance.ruta and (
                        'la paz' in (instance.ruta.nombre or '').lower() or
                        'la paz' in (instance.ruta.destino or '').lower()
                    )
                )
                if es_la_paz:
                    self._notificar_admin_la_paz(instance)
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"No se pudo enviar notif admin La Paz: {e}")

    def _notificar_admin_la_paz(self, hoja):
        """Enviar WhatsApp automático al administrador cuando se asigna ruta La Paz."""
        ADMIN_PHONE = '71275002'
        
        afiliado_nombre = f"{hoja.afiliado.apellidos} {hoja.afiliado.nombres}" if hoja.afiliado else 'N/A'
        placa = hoja.vehiculo.placa if hoja.vehiculo else 'Sin placa'
        tipo = (hoja.vehiculo.tipo or '').upper() if hoja.vehiculo else 'N/A'
        color = (hoja.vehiculo.color or 'No registrado') if hoja.vehiculo else 'N/A'
        fecha_salida = str(hoja.fecha_salida or hoja.fecha_emision or '')
        # Formatear fecha DD/MM/YYYY
        if fecha_salida and '-' in fecha_salida:
            parts = fecha_salida.split('-')
            if len(parts) == 3:
                fecha_salida = f"{parts[2]}/{parts[1]}/{parts[0]}"
        
        mensaje = (
            f"\U0001f6a8 *NUEVA SALIDA - RUTA LA PAZ*\n\n"
            f"\U0001f4cb Hoja N\u00ba: {hoja.nro}\n"
            f"\U0001f464 Afiliado: {afiliado_nombre}\n"
            f"\U0001f697 Modelo: {tipo}\n"
            f"\U0001f4cd Placa: {placa}\n"
            f"\U0001f3a8 Color: {color}\n"
            f"\U0001f4c5 Fecha de Salida: {fecha_salida}\n"
            f"\U0001f4b0 Monto: Bs. {hoja.precio}\n\n"
            f"_Sindicato Mixto de Transporte Integraci\u00f3n Taipiplaya_"
        )
        
        try:
            from whatsapp_notif.services import whatsapp_service
            whatsapp_service.send_message(
                phone=ADMIN_PHONE,
                message=mensaje,
                message_type='la_paz_salida',
                related_hoja_id=hoja.id,
                recipient_name='Administrador',
                use_celery=True,
            )
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error enviando WhatsApp admin: {e}")

    @action(detail=False, methods=['get'])
    def disponibles_hoy(self, request):
        """
        Retorna hojas de ruta disponibles para hoy y próximos días
        con estado 'emitida', incluyendo información del afiliado, vehículo, ruta
        y cupos disponibles
        """
        from datetime import date, timedelta
        from django.db.models import Sum, Q
        from reservas.models import Reserva
        
        hoy = date.today()
        # Obtener hojas de ruta de hoy y los próximos 7 días
        hasta = hoy + timedelta(days=7)
        
        destino = request.query_params.get('destino', 'La Paz')
        
        hojas = HojaRuta.objects.select_related(
            'afiliado', 'vehiculo', 'ruta'
        ).filter(
            ruta__nombre__iexact=destino,
            vehiculo__tipo__in=['minibus', 'ipsum'],
            estado='emitida',
            fecha_salida__gte=hoy,
            fecha_salida__lte=hasta
        ).order_by('ruta__nombre', 'fecha_salida')
        
        # Optimización: Obtener de una vez todas las reservas relevantes para evitar N+1
        rutas_ids = {h.ruta_id for h in hojas if h.ruta_id}
        fechas_salida = {h.fecha_salida for h in hojas if h.fecha_salida}
        
        from reservas.models import Reserva
        from django.db.models import Sum
        
        # 1. Agregado de cupos totales por ruta y fecha
        reservas_stats = Reserva.objects.filter(
            ruta_id__in=rutas_ids,
            fecha_viaje__in=fechas_salida,
            estado__in=['pendiente', 'confirmada']
        ).values('ruta_id', 'fecha_viaje').annotate(total=Sum('cantidad'))
        
        stats_map = {(r['ruta_id'], r['fecha_viaje']): r['total'] for r in reservas_stats}
        
        # 2. Mapa de asientos ocupados
        asientos_qs = Reserva.objects.filter(
            ruta_id__in=rutas_ids,
            fecha_viaje__in=fechas_salida,
            estado__in=['pendiente', 'confirmada']
        ).exclude(asiento__isnull=True).values('ruta_id', 'fecha_viaje', 'asiento')
        
        asientos_map = {}
        for r in asientos_qs:
            key = (r['ruta_id'], r['fecha_viaje'])
            if key not in asientos_map:
                asientos_map[key] = []
            asientos_map[key].append(r['asiento'])
        
        # Serializar con información pre-calculada
        data = []
        for hoja in hojas:
            key = (hoja.ruta_id, hoja.fecha_salida)
            
            cupos_reservados = stats_map.get(key, 0)
            asientos_ocupados = asientos_map.get(key, [])
            
            capacidad_total = hoja.vehiculo.capacidad if hoja.vehiculo else 0
            cupos_disponibles = max(0, capacidad_total - cupos_reservados)
            
            item = {
                'id': hoja.id,
                'nro': hoja.nro,
                'fecha_salida': hoja.fecha_salida,
                'ruta': {
                    'id': hoja.ruta.id if hoja.ruta else None,
                    'nombre': hoja.ruta.nombre if hoja.ruta else None,
                    'origen': hoja.ruta.origen if hoja.ruta else None,
                    'destino': hoja.ruta.destino if hoja.ruta else None,
                    'tarifa_base': str(hoja.ruta.tarifa_base) if hoja.ruta else None,
                },
                'afiliado': {
                    'id': hoja.afiliado.id if hoja.afiliado else None,
                    'nombre_completo': f"{hoja.afiliado.apellidos} {hoja.afiliado.nombres}" if hoja.afiliado else None,
                    'telefono': hoja.afiliado.telefono if hoja.afiliado else None,
                } if hoja.afiliado else None,
                'vehiculo': {
                    'id': hoja.vehiculo.id if hoja.vehiculo else None,
                    'placa': hoja.vehiculo.placa if hoja.vehiculo else None,
                    'tipo': hoja.vehiculo.tipo if hoja.vehiculo else None,
                } if hoja.vehiculo else None,
                'precio': str(hoja.precio),
                'capacidad_total': capacidad_total,
                'cupos_disponibles': cupos_disponibles,
                'cupos_reservados': cupos_reservados,
                'asientos_ocupados': asientos_ocupados,
            }
            data.append(item)
        
        return Response(data)

    @action(detail=False, methods=['get'])
    def pasajeros(self, request, pk=None):
        """Retorna la lista de pasajeros (reservas) para esta hoja de ruta"""
        hoja = self.get_object()
        from reservas.models import Reserva
        reservas = Reserva.objects.filter(
            ruta=hoja.ruta,
            fecha_viaje=hoja.fecha_salida,
            estado__in=['pendiente', 'confirmada']
        ).order_by('asiento', 'created_at')
        
        data = []
        for r in reservas:
            data.append({
                'id': r.id,
                'cliente': r.cliente,
                'asiento': r.asiento,
                'estado': r.estado,
                'telefono': r.telefono,
            })
        return Response(data)

    @action(detail=False, methods=['get'])
    def puntero_hoy(self, request):
        """Lista simplificada de hojas de ruta de hoy para los afiliados (Puntero del día)"""
        from django.utils import timezone
        hoy = timezone.now().date()
        
        hojas = HojaRuta.objects.filter(
            fecha_emision=hoy
        ).select_related('afiliado', 'ruta', 'vehiculo').order_by('nro')
        
        data = [{
            'id': h.id,
            'nro': h.nro,
            'afiliado': h.afiliado.nombre_completo if h.afiliado else 'N/A',
            'ruta': h.ruta.nombre if h.ruta else 'N/A',
            'vehiculo': h.vehiculo.placa if h.vehiculo else 'N/A',
            'estado': h.estado,
            'hora': h.created_at.strftime('%H:%M') if h.created_at else ''
        } for h in hojas]
        
        return Response(data)

    @action(detail=False, methods=['get'])
    def export_excel(self, request):
        """Exportar lista de hojas de ruta a Excel"""
        from openpyxl import Workbook
        from django.http import HttpResponse
        
        wb = Workbook()
        ws = wb.active
        ws.title = "Hojas de Ruta"
        
        headers = ['ID', 'Nro', 'Afiliado', 'Vehículo', 'Ruta', 'Fecha Emisión', 'Fecha Salida', 'Precio', 'Estado']
        ws.append(headers)
        
        for obj in self.get_queryset().order_by('-fecha_emision'):
            afiliado = f"{obj.afiliado.apellidos} {obj.afiliado.nombres}" if obj.afiliado else "N/A"
            vehiculo = obj.vehiculo.placa if obj.vehiculo else "N/A"
            ruta = obj.ruta.nombre if obj.ruta else "N/A"
            ws.append([
                obj.id,
                obj.nro,
                afiliado,
                vehiculo,
                ruta,
                obj.fecha_emision.strftime('%Y-%m-%d %H:%M') if obj.fecha_emision else '',
                obj.fecha_salida.strftime('%Y-%m-%d %H:%M') if obj.fecha_salida else '',
                obj.precio,
                obj.estado.capitalize()
            ])
            
        for cell in ws[1]:
            from openpyxl.styles import Font
            cell.font = Font(bold=True)
            
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=hojas_ruta.xlsx'
        wb.save(response)
        return response


    @action(detail=True, methods=['post', 'get'])
    def generar_planilla_la_paz(self, request, pk=None):
        """
        Genera una planilla (lista de pasajeros) con el diseño basado en la imagen proporcionada.
        """
        import os
        import time
        from django.conf import settings
        from django.http import FileResponse
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reservas.models import Reserva

        obj = self.get_object()
        
        try:
            folder = os.path.join(settings.MEDIA_ROOT, 'hojasruta')
            os.makedirs(folder, exist_ok=True)
            
            tipo_obj = obj.vehiculo.tipo if obj.vehiculo else 'minibus'
            tipo_v = str(tipo_obj or 'minibus').lower()
            timestamp = int(time.time())
            filename = f"planilla_{tipo_v}_{obj.id}_{timestamp}.pdf"
            path = os.path.join(folder, filename)
            
            c = canvas.Canvas(path, pagesize=A4)
            width, height = A4
            
            # Colores
            GREEN_THEME = colors.Color(0.1, 0.6, 0.3) # Verde aproximado
            
            # --- HEADER ---
            y = height - 40
            
            # Título Principal
            c.setFont("Helvetica-Bold", 16)
            c.setFillColor(GREEN_THEME)
            c.drawCentredString(width/2, y, "SINDICATO DE TRANSPORTE MIXTO")
            y -= 20
            c.setFont("Helvetica-Bold", 18)
            c.drawCentredString(width/2, y, '"INTEGRACION TAIPIPLAYA"')
            
            y -= 20
            c.setFont("Helvetica", 10)
            c.setFillColor(colors.black)
            c.drawCentredString(width/2, y, "SERVICIO RAPIDO Y CONFORTABLE")
            y -= 12
            c.setFont("Helvetica", 8)
            c.drawCentredString(width/2, y, 'Of. La Paz: Terminal Puente Minasa "Caseta Nº 12"')
            y -= 10
            c.drawCentredString(width/2, y, 'Telf. Cel. 63125350 - Fund. 22 - 09 - 2011')
            y -= 10
            c.drawCentredString(width/2, y, 'Of. Taipiplaya frente a la plaza 24 de junio')
            
            # Banner "LISTA DE PASAJEROS"
            y -= 25
            c.setFillColor(GREEN_THEME)
            c.roundRect(50, y, width - 100, 20, 5, fill=1, stroke=0)
            c.setFillColor(colors.white)
            c.setFont("Helvetica-Bold", 14)
            c.drawCentredString(width/2, y + 5, "L I S T A   D E   P A S A J E R O S")
            
            # --- CAMPOS DE DATOS (Recuadros) ---
            y -= 30
            c.setFillColor(colors.black) # Texto negro de aquí en adelante
            
            def draw_field_box(x, y, w, h, title, value):
                # Título del campo
                c.setFont("Helvetica-Bold", 8)
                c.setFillColor(GREEN_THEME)
                c.drawCentredString(x + w/2, y + h + 2, title)
                
                # Caja
                c.setStrokeColor(GREEN_THEME)
                c.setLineWidth(1)
                c.roundRect(x, y, w, h, 4, fill=0, stroke=1)
                
                # Valor
                c.setFont("Helvetica", 10)
                c.setFillColor(colors.black)
                if value:
                    c.drawCentredString(x + w/2, y + 8, str(value)[:30])

            # Fila 1: Conductor, Licencia, Placa
            row1_y = y
            full_w = width - 100
            w_placa = 100
            w_lic = 120
            w_cond = full_w - w_placa - w_lic - 10 # 5px gap each
            
            nombre_chofer = f"{obj.afiliado.apellidos} {obj.afiliado.nombres}" if obj.afiliado else ""
            placa = obj.vehiculo.placa if obj.vehiculo else ""
            
            draw_field_box(50, row1_y, w_cond, 25, "NOMBRE DEL CONDUCTOR", nombre_chofer)
            draw_field_box(50 + w_cond + 5, row1_y, w_lic, 25, "Nº DE LICENCIA", "") # No tenemos licencia en modelo
            draw_field_box(50 + w_cond + w_lic + 10, row1_y, w_placa, 25, "PLACA Nº", placa)
            
            # Fila 2: Destino, Hora, Fecha
            row2_y = row1_y - 40
            w_fecha = 120
            w_hora = 120
            w_dest = full_w - w_fecha - w_hora - 10
            
            destino = obj.ruta.nombre if obj.ruta else ""
            hora = obj.fecha_emision.strftime('%H:%M') if obj.fecha_emision else ""
            fecha = str(obj.fecha_salida) if obj.fecha_salida else ""
            
            draw_field_box(50, row2_y, w_dest, 25, "DESTINO", destino)
            draw_field_box(50 + w_dest + 5, row2_y, w_hora, 25, "HORA DE SALIDA", hora)
            draw_field_box(50 + w_dest + w_hora + 10, row2_y, w_fecha, 25, "FECHA", fecha)
            
            # Fila 3: Vehiculo, Marca, Color
            row3_y = row2_y - 40
            w_color = 150
            w_marca = 150
            w_veh = full_w - w_color - w_marca - 10
            
            tipo_veh = (obj.vehiculo.tipo or 'Minibús').upper() if obj.vehiculo else ""
            
            draw_field_box(50, row3_y, w_veh, 25, "VEHICULO", tipo_veh)
            draw_field_box(50 + w_veh + 5, row3_y, w_marca, 25, "MARCA", "") # No en modelo
            draw_field_box(50 + w_veh + w_marca + 10, row3_y, w_color, 25, "COLOR", "") # No en modelo
            
            # --- GRID DE ASIENTOS CON MARCO VERDE ---
            
            # Marco principal del área de asientos
            box_top = row3_y - 20
            box_height = 400
            c.setStrokeColor(GREEN_THEME)
            c.rect(50, box_top - box_height, full_w, box_height, stroke=1, fill=0)
            
            # Reservas
            reservas = Reserva.objects.filter(
                ruta=obj.ruta, 
                fecha_viaje=obj.fecha_salida, 
                estado__in=['confirmada', 'pendiente', 'pagada']
            )
            pasajeros_map = {res.asiento: f"{res.cliente}" for res in reservas if res.asiento}
            
            # Helper para dibujar cajas de asientos dentro del grid
            def draw_seat_cell(x, y, w, h, num, text, is_driver=False):
                # Marco de la celda
                c.setStrokeColor(GREEN_THEME)
                c.rect(x, y, w, h)
                
                # Etiqueta de número (pequeña caja en esquina superior izq)
                if not is_driver:
                    c.rect(x + 5, y + h - 20, 20, 15)
                    c.setFillColor(colors.black)
                    c.setFont("Helvetica-Bold", 10)
                    c.drawCentredString(x + 15, y + h - 16, str(num))
                else:
                    # Icono de volante (simple círculo y líneas)
                    cx, cy = x + w/2, y + h/2 + 10
                    c.setStrokeColor(GREEN_THEME)
                    c.setLineWidth(2)
                    c.circle(cx, cy, 15)
                    c.line(cx - 15, cy, cx + 15, cy)
                    c.line(cx, cy - 15, cx, cy + 15)
                    c.setLineWidth(1)
                    c.setFillColor(GREEN_THEME)
                    c.setFont("Helvetica-Bold", 10)
                    c.drawCentredString(x + w/2, y + h/2 - 20, "CONDUCTOR")

                # Contenido (Nombre pasajero)
                if text:
                    c.setFillColor(colors.blue)
                    c.setFont("Helvetica", 10) # Un poco más grande para simular escritura a mano
                    # Indentar un poco o centrar
                    c.drawString(x + 10, y + h/2 - 5, text[:25])
                
                # Lineas de renglón para escribir
                c.setStrokeColor(colors.gray)
                c.setLineWidth(0.5)
                c.setDash([2, 2], 0)
                c.line(x + 10, y + 15, x + w - 10, y + 15)
                c.line(x + 10, y + 35, x + w - 10, y + 35)
                c.setDash([], 0) # Reset dash

            # Layout Dinámico según tipo
            if tipo_v == 'ipsum':
                # Ipsum: 
                # [ Conductor ] [  1  ]
                # [  2  ] [  3  ] [  4  ] -> No, la imagen muestra 2 arriba
                # La imagen parece ser Ipsum:
                # Arriba: Conductor | Espacio (?)
                # Filas: 1 | 2-3-4? 
                # Vamos a hacer un layout Ipsum funcional y estético adaptado a la caja
                
                # Fila 1: Conductor (izq) y Asiento 1 (campo grande a la derecha?)
                # En la imagen se ve: Conductor a la izq, y a la derecha un bloque grande que parece el 1.
                # Luego abajo: 2, 3, 4 (tres columnas)
                # Luego abajo: 5, 6 (dos columnas)
                
                row_h = box_height / 3
                
                # Fila Superior
                row1_y = box_top - row_h
                w_half = full_w / 2
                draw_seat_cell(50, row1_y, w_half, row_h, 0, "", is_driver=True)
                draw_seat_cell(50 + w_half, row1_y, w_half, row_h, 1, pasajeros_map.get(1, ""))
                
                # Fila Medio (3 columnas)
                row2_y = box_top - 2*row_h
                w_third = full_w / 3
                draw_seat_cell(50, row2_y, w_third, row_h, 2, pasajeros_map.get(2, ""))
                draw_seat_cell(50 + w_third, row2_y, w_third, row_h, 3, pasajeros_map.get(3, ""))
                draw_seat_cell(50 + 2*w_third, row2_y, w_third, row_h, 4, pasajeros_map.get(4, ""))
                
                # Fila Inferior (2 columnas)
                row3_y = box_top - 3*row_h
                draw_seat_cell(50, row3_y, w_half, row_h, 5, pasajeros_map.get(5, ""))
                draw_seat_cell(50 + w_half, row3_y, w_half, row_h, 6, pasajeros_map.get(6, ""))

            else:
                # Minibús (14 pax)
                # Layout estándar de planilla minibús
                # 5 filas
                row_h = box_height / 5
                
                # Fila 1
                row1_y = box_top - row_h
                w_third = full_w / 3
                draw_seat_cell(50, row1_y, w_third, row_h, 0, "", is_driver=True)
                draw_seat_cell(50 + w_third, row1_y, w_third, row_h, 1, pasajeros_map.get(1, ""))
                draw_seat_cell(50 + 2*w_third, row1_y, w_third, row_h, 2, pasajeros_map.get(2, ""))
                
                # Resto filas
                curr_y = row1_y
                for r in range(4):
                    curr_y -= row_h
                    for c_idx in range(3):
                        seat_idx = 3 + r*3 + c_idx
                        if seat_idx > 14: break
                        draw_seat_cell(50 + c_idx*w_third, curr_y, w_third, row_h, seat_idx, pasajeros_map.get(seat_idx, ""))

            c.showPage()
            c.save()
            
            return FileResponse(open(path, 'rb'), content_type='application/pdf')

        except Exception as e:
            import traceback
            traceback.print_exc()
            from rest_framework.response import Response
            return Response({'detail': f'Error al generar PDF: {str(e)}'}, status=500)

class TurnoSalidaViewSet(viewsets.ModelViewSet):
    queryset = TurnoSalida.objects.select_related('afiliado', 'ruta').all()
    serializer_class = TurnoSalidaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        fecha = self.request.query_params.get('fecha')
        ruta_id = self.request.query_params.get('ruta_id')
        if fecha:
            qs = qs.filter(fecha=fecha)
        if ruta_id:
            qs = qs.filter(ruta_id=ruta_id)
        return qs

    @action(detail=False, methods=['post'])
    def generar_programacion(self, request):
        """
        Genera turnos de salida (puntero) automáticos para la ruta La Paz.
        """
        import datetime
        
        # 1. Obtener Ruta La Paz
        ruta_la_paz = Ruta.objects.filter(destino__iexact='la paz').first()
        if not ruta_la_paz:
             return Response({'detail': 'No se encontró la ruta a La Paz'}, status=400)
             
        # 2. Obtener Afiliados aptos para La Paz (Activos, con Minibus/Ipsum CON placa)
        afiliados = list(Afiliado.objects.filter(
            estado='activo',
            is_active=True,
            vehiculos__tipo__in=['minibus', 'ipsum'],
            vehiculos__indocumentado=False
        ).distinct().order_by('apellidos', 'nombres'))
        
        if not afiliados:
            return Response({'detail': 'No hay aliados aptos para la programación de La Paz'}, status=400)
            
        # 3. Determinar fecha de inicio
        ultimo = TurnoSalida.objects.filter(ruta=ruta_la_paz).order_by('-fecha').first()
        if ultimo:
            fecha_inicio = ultimo.fecha + timedelta(days=1)
        else:
            fecha_inicio = date.today()
            
        # 4. Índice de inicio
        total_previo = TurnoSalida.objects.filter(ruta=ruta_la_paz).count()
        idx = total_previo % len(afiliados)
        
        # 5. Generar para 30 días laborables
        dias_a_generar = 30
        dias_hechos = 0
        offset = 0
        creados = []
        
        while dias_hechos < dias_a_generar:
            fecha = fecha_inicio + timedelta(days=offset)
            offset += 1
            
            # Excluir Martes (1) y Jueves (3) que salen integración Caranavi
            if fecha.weekday() in [1, 3]:
                continue
                
            # Por ahora, 1 turno oficial por día en el puntero (pueden ser más si se requiere)
            af = afiliados[idx % len(afiliados)]
            
            ts = TurnoSalida.objects.create(
                fecha=fecha,
                afiliado=af,
                ruta=ruta_la_paz,
                orden=1
            )
            creados.append(f"{fecha}: {af.nombre_completo}")
            
            idx += 1
            dias_hechos += 1
            
        return Response({
            'detail': f'Se generaron {len(creados)} turnos nuevos para La Paz.',
            'total_afiliados': len(afiliados),
            'desde': fecha_inicio,
            'hasta': fecha
        })
