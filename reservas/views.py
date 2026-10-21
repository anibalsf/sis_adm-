import json
import urllib.request
import uuid
from decimal import Decimal
from io import BytesIO

import qrcode
from django.conf import settings
from django.db import IntegrityError, transaction
from django.db.models import Sum
from django.http import HttpResponse
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.permissions import SAFE_METHODS, BasePermission
from rest_framework.response import Response

from comunicacion.models import Notificacion
from hojasruta.models import HojaRuta
from pagos_qr.services import QRService

from .models import ESTADOS_ACTIVOS, Reserva
from .serializers import ReservaPublicaSerializer, ReservaSerializer
from .services import precio_de


class AsientoOcupado(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = 'El asiento ya está reservado.'
    default_code = 'asiento_ocupado'


class ReservaPermission(BasePermission):
    """Acciones públicas para pasajeros y escritura restringida al personal."""

    ACCIONES_PUBLICAS = {'create', 'generar_pago_qr', 'public_retrieve', 'generar_qr'}

    def has_permission(self, request, view):
        accion = getattr(view, 'action', None)
        if accion in self.ACCIONES_PUBLICAS:
            return True

        user = request.user
        if not user or not user.is_authenticated:
            return False

        if accion == 'notificar':
            return user.is_superuser or user.is_staff or user.groups.filter(name='Secretaria').exists()

        if request.method in SAFE_METHODS:
            return True

        if getattr(user, 'is_superuser', False) or getattr(user, 'is_staff', False):
            return True
        return user.groups.filter(name__in=['Secretaria', 'Directiva', 'Sistemas']).exists()


class ReservaViewSet(viewsets.ModelViewSet):
    queryset = Reserva.objects.select_related(
        'afiliado', 'ruta', 'hoja_ruta__vehiculo', 'hoja_ruta__afiliado'
    ).all()
    serializer_class = ReservaSerializer
    permission_classes = [ReservaPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['estado', 'ruta', 'fecha_viaje', 'hoja_ruta']
    search_fields = ['cliente', 'telefono', 'ruta__nombre', 'afiliado__ci']
    ordering_fields = ['fecha_viaje', 'cantidad', 'created_at', 'cliente', 'estado']

    # ------------------------------------------------------------------
    # Utilidades
    # ------------------------------------------------------------------
    def _hoja_para(self, ruta, fecha, bloquear=False):
        qs = HojaRuta.objects.select_related('vehiculo', 'afiliado').filter(
            ruta=ruta,
            fecha_salida=fecha,
            estado__in=['emitida', 'notificada', 'pagada'],
        )
        if bloquear:
            qs = qs.select_for_update()
        return qs.order_by('id').first()

    def _validar_cupos_y_asientos(self, hoja, ruta_id, fecha, total_pasajes, asientos, excluir_id=None):
        capacidad = hoja.vehiculo.capacidad if hoja and hoja.vehiculo else 0

        activas = Reserva.objects.filter(
            ruta_id=ruta_id,
            fecha_viaje=fecha,
            estado__in=ESTADOS_ACTIVOS,
        )
        if excluir_id:
            activas = activas.exclude(pk=excluir_id)

        reservados = activas.aggregate(total=Sum('cantidad'))['total'] or 0
        disponibles = capacidad - reservados
        if total_pasajes > disponibles:
            raise ValidationError({
                'detail': f'No hay suficientes cupos. Disponibles: {max(disponibles, 0)}, '
                          f'Solicitados: {total_pasajes}',
                'cupos_disponibles': max(disponibles, 0),
                'cantidad_solicitada': total_pasajes,
            })

        asientos = [a for a in asientos if a is not None]
        if not asientos:
            return

        if capacidad and any(a > capacidad for a in asientos):
            raise ValidationError({
                'detail': f'El vehículo solo tiene {capacidad} asientos.',
                'capacidad_total': capacidad,
            })

        ocupados = list(
            activas.filter(asiento__in=asientos).values_list('asiento', flat=True)
        )
        if ocupados:
            raise AsientoOcupado(
                f'Los asientos {", ".join(map(str, sorted(set(ocupados))))} ya están reservados.'
            )

    def _cancelar(self, instance, motivo=''):
        if instance.estado == 'cancelada':
            return instance
        instance.estado = 'cancelada'
        instance.fecha_anulacion = timezone.now()
        instance.motivo_anulacion = (motivo or 'Anulada desde el módulo de reservas')[:255]
        instance.save(update_fields=['estado', 'fecha_anulacion', 'motivo_anulacion', 'updated_at'])
        return instance

    def _monto_de(self, reserva):
        if reserva.monto_total is not None:
            return Decimal(reserva.monto_total)
        return precio_de(reserva.hoja_ruta, reserva.ruta) * reserva.cantidad

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)

        asientos_raw = request.data.get('asientos')
        if asientos_raw is not None:
            if not isinstance(asientos_raw, list) or not asientos_raw:
                raise ValidationError({'asientos': 'Debe enviar una lista con al menos un asiento.'})
            try:
                asientos = [int(a) for a in asientos_raw]
            except (TypeError, ValueError):
                raise ValidationError({'asientos': 'Los asientos deben ser números enteros.'})
            if any(a < 1 for a in asientos):
                raise ValidationError({'asientos': 'Los asientos deben ser mayores a cero.'})
            if len(set(asientos)) != len(asientos):
                raise ValidationError({'asientos': 'No se puede repetir un asiento en la misma reserva.'})
            asientos = sorted(set(asientos))
            total_pasajes = len(asientos)
        else:
            asientos = []
            if data.get('asiento') is not None:
                asientos = [data['asiento']]
            total_pasajes = data['cantidad']

        ruta = data['ruta']
        fecha = data['fecha_viaje']

        with transaction.atomic():
            hoja = self._hoja_para(ruta, fecha, bloquear=True)
            if not hoja:
                return Response(
                    {'detail': 'No hay hoja de ruta disponible para esta fecha'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            self._validar_cupos_y_asientos(
                hoja, ruta.id, fecha, total_pasajes, asientos
            )

            unitario = precio_de(hoja, ruta)
            base = {
                'cliente': data['cliente'],
                'telefono': data.get('telefono', ''),
                'ruta': ruta,
                'hoja_ruta': hoja,
                'fecha_viaje': fecha,
                'afiliado': data.get('afiliado') or hoja.afiliado,
                'estado': 'pendiente',
            }
            grupo_id = uuid.uuid4()
            creadas = []

            try:
                if asientos:
                    for asiento in asientos:
                        creadas.append(Reserva.objects.create(
                            **base,
                            cantidad=1,
                            asiento=asiento,
                            monto_unitario=unitario,
                            monto_total=unitario,
                            grupo_id=grupo_id,
                        ))
                else:
                    cantidad = data['cantidad']
                    creadas.append(Reserva.objects.create(
                        **base,
                        cantidad=cantidad,
                        asiento=None,
                        monto_unitario=unitario,
                        monto_total=unitario * cantidad,
                        grupo_id=grupo_id,
                    ))
            except IntegrityError:
                raise AsientoOcupado()

        output = self.get_serializer(creadas, many=True).data
        if asientos_raw is not None:
            return Response(output, status=status.HTTP_201_CREATED)
        return Response(output[0], status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if instance.estado in ESTADOS_ACTIVOS:
            if 'ruta' in data and data['ruta'].id != instance.ruta_id:
                return Response(
                    {'detail': 'No se puede cambiar la ruta de una reserva activa.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if 'fecha_viaje' in data and data['fecha_viaje'] != instance.fecha_viaje:
                return Response(
                    {'detail': 'No se puede cambiar la fecha de una reserva activa.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        with transaction.atomic():
            instance = self.get_object()
            nueva_cantidad = data.get('cantidad', instance.cantidad)
            nuevo_asiento = data.get('asiento', instance.asiento)
            cambia_cupos = 'cantidad' in data or 'asiento' in data

            if cambia_cupos and instance.estado in ESTADOS_ACTIVOS:
                hoja = instance.hoja_ruta or self._hoja_para(instance.ruta, instance.fecha_viaje, bloquear=True)
                if not hoja:
                    return Response(
                        {'detail': 'No hay hoja de ruta disponible para esta reserva.'},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                self._validar_cupos_y_asientos(
                    hoja,
                    instance.ruta_id,
                    instance.fecha_viaje,
                    nueva_cantidad,
                    [nuevo_asiento] if nuevo_asiento else [],
                    excluir_id=instance.id,
                )

            try:
                instance = serializer.save()
            except IntegrityError:
                raise AsientoOcupado()

            if cambia_cupos:
                unitario = instance.monto_unitario or precio_de(instance.hoja_ruta, instance.ruta)
                instance.monto_unitario = unitario
                instance.monto_total = unitario * instance.cantidad
                instance.save(update_fields=['monto_unitario', 'monto_total', 'updated_at'])

        return Response(self.get_serializer(instance).data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self._cancelar(instance, request.data.get('motivo', ''))
        return Response(status=status.HTTP_204_NO_CONTENT)

    # ------------------------------------------------------------------
    # Acciones de gestión
    # ------------------------------------------------------------------
    @action(detail=True, methods=['post'])
    def confirmar(self, request, pk=None):
        reserva = self.get_object()
        if reserva.estado != 'pendiente':
            return Response(
                {'detail': f'No se puede confirmar una reserva en estado {reserva.estado}.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        reserva.estado = 'confirmada'
        reserva.save(update_fields=['estado', 'updated_at'])
        return Response(self.get_serializer(reserva).data)

    @action(detail=True, methods=['post'])
    def cancelar(self, request, pk=None):
        reserva = self.get_object()
        if reserva.estado == 'cancelada':
            return Response(self.get_serializer(reserva).data)
        self._cancelar(reserva, request.data.get('motivo', ''))
        return Response(self.get_serializer(reserva).data)

    @action(detail=True, methods=['post'])
    def notificar(self, request, pk=None):
        obj = self.get_object()
        telefono = request.data.get('telefono')
        mensaje = request.data.get('mensaje')

        from comunicacion.services import WhatsAppService

        success, result = WhatsAppService().send_message(
            telefono, mensaje or f"Reserva {obj.id} actualizada"
        )

        return Response({
            'detail': 'Notificación procesada',
            'success': success,
            'result': result,
        })

    # ------------------------------------------------------------------
    # QR
    # ------------------------------------------------------------------
    @action(detail=True, methods=['get'])
    def generar_qr(self, request, pk=None):
        """Genera el QR de verificación del boleto digital."""
        reserva = self.get_object()
        frontend_url = getattr(settings, 'FRONTEND_URL', 'https://administracion.sindicatointegracion.com').rstrip('/')

        hoja = reserva.hoja_ruta or self._hoja_para(reserva.ruta, reserva.fecha_viaje)
        vehiculo_placa = hoja.vehiculo.placa if hoja and hoja.vehiculo else 'N/A'
        vehiculo_tipo = hoja.vehiculo.tipo if hoja and hoja.vehiculo else 'N/A'
        afiliado = reserva.afiliado or (hoja.afiliado if hoja else None)
        afiliado_nombre = str(afiliado) if afiliado else 'N/A'
        afiliado_telefono = afiliado.telefono if afiliado else 'N/A'
        afiliado_direccion = afiliado.direccion if afiliado else 'N/A'

        url_verificacion = f"{frontend_url}/voucher/{reserva.id}"
        qr_content = (
            f"{url_verificacion}\n"
            f"---\n"
            f"RESERVA: RES-{str(reserva.id).zfill(6)}\n"
            f"PASAJERO: {reserva.cliente}\n"
            f"RUTA: {reserva.ruta.nombre if reserva.ruta else 'N/A'}\n"
            f"FECHA: {str(reserva.fecha_viaje)}\n"
            f"ASIENTO: {reserva.asiento or 'S/A'} | CANT: {reserva.cantidad}\n"
            f"ESTADO: {reserva.estado.upper()}\n"
            f"---\n"
            f"CONDUCTOR: {afiliado_nombre}\n"
            f"CELULAR: {afiliado_telefono}\n"
            f"DIRECCION: {afiliado_direccion}\n"
            f"PLACA: {vehiculo_placa} ({vehiculo_tipo})\n"
            f"---\n"
            f"SINDICATO MIXTO INTEGRACION TAIPIPLAYA\n"
            f"{frontend_url}"
        )

        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_content)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)

        return HttpResponse(buffer.getvalue(), content_type='image/png')

    @action(detail=True, methods=['get'])
    def generar_confirmacion_pdf(self, request, pk=None):
        """Genera PDF de confirmación con QR integrado."""
        reserva = self.get_object()
        frontend_url = getattr(settings, 'FRONTEND_URL', 'https://administracion.sindicatointegracion.com').rstrip('/')
        hoja = reserva.hoja_ruta or self._hoja_para(reserva.ruta, reserva.fecha_viaje)
        afiliado = reserva.afiliado or (hoja.afiliado if hoja else None)

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2E7D32'),
            alignment=TA_CENTER,
            spaceAfter=20,
        )
        elements.append(Paragraph("CONFIRMACIÓN DE RESERVA", title_style))
        elements.append(Paragraph("Sindicato Taipiplaya", styles['Normal']))
        elements.append(Spacer(1, 0.3 * inch))

        conf_style = ParagraphStyle(
            'Confirmation',
            parent=styles['Normal'],
            fontSize=14,
            textColor=colors.HexColor('#1976D2'),
            alignment=TA_CENTER,
            spaceAfter=20,
        )
        elements.append(Paragraph(
            f"<b>Nº Confirmación: RES-{str(reserva.id).zfill(6)}</b>",
            conf_style,
        ))
        elements.append(Spacer(1, 0.2 * inch))

        data = [
            ['Cliente:', reserva.cliente],
            ['Ruta:', reserva.ruta.nombre if reserva.ruta else 'N/A'],
            ['Fecha de Viaje:', reserva.fecha_viaje.strftime('%d/%m/%Y')],
            ['Cantidad de Pasajes:', str(reserva.cantidad)],
            ['Asiento:', str(reserva.asiento) if reserva.asiento else 'Por asignar'],
            ['Conductor:', str(afiliado) if afiliado else 'N/A'],
            ['Vehículo:', hoja.vehiculo.placa if hoja and hoja.vehiculo else 'N/A'],
            ['Total:', f"Bs. {self._monto_de(reserva):.2f}"],
            ['Estado:', reserva.estado.upper()],
        ]

        table = Table(data, colWidths=[2 * inch, 4 * inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#E8F5E9')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 0.3 * inch))

        qr_buffer = BytesIO()
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(f"{frontend_url}/voucher/{reserva.id}")
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_img.save(qr_buffer, format='PNG')
        qr_buffer.seek(0)

        qr_image = Image(qr_buffer, width=2 * inch, height=2 * inch)
        elements.append(qr_image)
        elements.append(Spacer(1, 0.3 * inch))

        note_style = ParagraphStyle(
            'Note',
            parent=styles['Italic'],
            fontSize=10,
            textColor=colors.grey,
            alignment=TA_CENTER,
        )
        elements.append(Paragraph(
            "Escanee este código QR para abrir el boleto digital.",
            note_style,
        ))
        elements.append(Paragraph(
            f"Documento generado el {reserva.created_at.strftime('%d/%m/%Y %H:%M') if reserva.created_at else 'N/A'}",
            note_style,
        ))

        doc.build(elements)
        buffer.seek(0)

        return HttpResponse(
            buffer.getvalue(),
            content_type='application/pdf',
            headers={
                'Content-Disposition': f'attachment; filename="confirmacion_RES-{str(reserva.id).zfill(6)}.pdf"'
            },
        )

    @action(detail=True, methods=['post'])
    def enviar_confirmacion_whatsapp(self, request, pk=None):
        """Envía confirmación de reserva por WhatsApp."""
        reserva = self.get_object()
        telefono = request.data.get('telefono') or reserva.telefono

        if not telefono:
            return Response(
                {'detail': 'Debe proporcionar un número de teléfono'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        frontend_url = getattr(settings, 'FRONTEND_URL', 'https://administracion.sindicatointegracion.com').rstrip('/')
        mensaje = f"""✅ CONFIRMACIÓN DE RESERVA

Nº: RES-{str(reserva.id).zfill(6)}
Cliente: {reserva.cliente}
Ruta: {reserva.ruta.nombre if reserva.ruta else 'N/A'}
Fecha: {reserva.fecha_viaje.strftime('%d/%m/%Y')}
Pasajes: {reserva.cantidad}
Asiento: {reserva.asiento if reserva.asiento else 'Por asignar'}
Boleto digital: {frontend_url}/voucher/{reserva.id}

🚌 Sindicato Taipiplaya
Por favor conserve este mensaje."""

        notif = Notificacion.objects.create(
            canal='whatsapp',
            destinatario=telefono,
            mensaje=mensaje,
            estado='pendiente',
        )

        url = getattr(settings, 'WHATSAPP_WEBHOOK_URL', None)
        if url:
            try:
                payload = json.dumps({'to': telefono, 'message': mensaje}).encode('utf-8')
                req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'})
                urllib.request.urlopen(req, timeout=5)
                notif.estado = 'enviado'
                notif.save()
            except Exception as exc:
                notif.estado = 'error'
                notif.save()
                return Response(
                    {'detail': 'Error al enviar WhatsApp', 'error': str(exc)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        return Response({
            'detail': 'Confirmación enviada por WhatsApp',
            'notificacion_id': notif.id,
            'mensaje': mensaje,
        })

    @action(detail=True, methods=['post'])
    def generar_pago_qr(self, request, pk=None):
        """Genera un único QR de pago para una reserva o un grupo de reservas."""
        reserva = self.get_object()
        ids_solicitados = request.data.get('reservas') or request.data.get('reserva_ids')

        if ids_solicitados is None:
            reservas = [reserva]
        else:
            if not isinstance(ids_solicitados, list) or not ids_solicitados:
                raise ValidationError({'reservas': 'Debe enviar una lista de reservas.'})
            try:
                ids = list(dict.fromkeys(int(i) for i in ids_solicitados))
            except (TypeError, ValueError):
                raise ValidationError({'reservas': 'Los IDs de reserva deben ser números enteros.'})

            encontradas = list(
                Reserva.objects.select_related('ruta', 'hoja_ruta', 'hoja_ruta__vehiculo')
                .filter(id__in=ids)
                .order_by('id')
            )
            if len(encontradas) != len(ids):
                raise ValidationError({'reservas': 'Una o más reservas no existen.'})
            reservas = encontradas

        if any(r.estado == 'cancelada' for r in reservas):
            return Response(
                {'detail': 'No se puede cobrar una reserva cancelada.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if any(r.estado == 'confirmada' for r in reservas):
            return Response(
                {'detail': 'Una o más reservas ya están confirmadas.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if len({r.cliente for r in reservas}) > 1:
            return Response(
                {'detail': 'Todas las reservas del pago deben ser del mismo pasajero.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        total = sum((self._monto_de(r) for r in reservas), Decimal('0'))
        if total <= 0:
            return Response(
                {'detail': 'No se pudo determinar el monto a cobrar.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ids_reservas = [r.id for r in reservas]
        cantidad_total = sum(r.cantidad for r in reservas)
        titular = getattr(settings, 'QR_TITULAR_NOMBRE', 'Anibal Choque Aguirre')
        glosa = f"Pago Reserva {', '.join(str(i) for i in ids_reservas)} - A nombre de: {titular}"

        try:
            qr_obj = QRService.generate_qr(
                monto=total,
                glosa=glosa,
                valid_hours=24,
                content_object=reservas[0],
                metadata={
                    'tipo': 'reserva',
                    'reserva_ids': ids_reservas,
                    'grupo_id': str(reservas[0].grupo_id) if reservas[0].grupo_id else None,
                },
            )
        except Exception as exc:
            return Response(
                {'detail': f'Error al generar QR: {str(exc)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        frontend_url = getattr(settings, 'FRONTEND_URL', 'https://administracion.sindicatointegracion.com').rstrip('/')
        return Response({
            'id': qr_obj.id,
            'qr_string': qr_obj.qr_string,
            'imagen_base64': qr_obj.imagen_base64,
            'monto': float(qr_obj.monto),
            'transaction_id': qr_obj.transaction_id,
            'expires_at': qr_obj.expiration_date.isoformat(),
            'metodo': 'Yape',
            'titular': titular,
            'glosa': glosa,
            'reserva_ids': ids_reservas,
            'cantidad_total': cantidad_total,
            'voucher_url': f"{frontend_url}/voucher/{reservas[0].id}",
        })

    # ------------------------------------------------------------------
    # Consulta pública
    # ------------------------------------------------------------------
    @action(detail=True, methods=['get'], url_path='public-retrieve')
    def public_retrieve(self, request, pk=None):
        """Versión pública de retrieve para el voucher del pasajero."""
        instance = self.get_object()
        serializer = ReservaPublicaSerializer(instance)
        return Response(serializer.data)
