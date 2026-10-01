import logging
from datetime import timedelta

from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import ConfiguracionReporte, ReporteGenerado
from .report_generator import ReportGenerator
from .serializers import ConfiguracionReporteSerializer, ReporteGeneradoSerializer
from .tasks import TAREAS_POR_TIPO, _ejecutar_reporte

logger = logging.getLogger(__name__)


class ReporteGeneradoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Historial de reportes generados.

    Se cambió a ReadOnly: los reportes se crean únicamente a través de las
    tareas (programadas o manuales), nunca por un POST arbitrario.
    """
    queryset = ReporteGenerado.objects.all().order_by('-fecha_generacion')
    serializer_class = ReporteGeneradoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()

        tipo = self.request.query_params.get('tipo')
        estado = self.request.query_params.get('estado')
        origen = self.request.query_params.get('origen')
        fecha_desde = self.request.query_params.get('fecha_desde')
        fecha_hasta = self.request.query_params.get('fecha_hasta')
        solo_fallidos = self.request.query_params.get('solo_fallidos')

        if tipo:
            queryset = queryset.filter(tipo=tipo)
        if estado:
            queryset = queryset.filter(estado=estado)
        if origen:
            queryset = queryset.filter(origen=origen)
        if fecha_desde:
            queryset = queryset.filter(fecha_generacion__date__gte=fecha_desde)
        if fecha_hasta:
            queryset = queryset.filter(fecha_generacion__date__lte=fecha_hasta)
        if solo_fallidos in ('1', 'true', 'True'):
            queryset = queryset.filter(estado='fallido')

        return queryset

    @action(detail=False, methods=['post'], url_path='generar-manual')
    def generar_manual(self, request):
        """
        Genera un reporte bajo demanda.

        `enviar: false` devuelve una vista previa con el contenido y los
        adjuntos en base64, sin enviar nada. Por defecto (`enviar: true`)
        ejecuta el envío de forma síncrona para que el usuario vea el
        resultado de inmediato.
        """
        tipo = request.data.get('tipo', 'diario')
        enviar = _booleano(request.data.get('enviar', True))

        if tipo not in TAREAS_POR_TIPO:
            return Response(
                {'error': f'Tipo de reporte inválido: {tipo}',
                 'tipos_validos': sorted(TAREAS_POR_TIPO.keys())},
                status=status.HTTP_400_BAD_REQUEST,
            )

        config = ConfiguracionReporte.objects.filter(tipo=tipo).first()

        if not enviar:
            return self._previsualizar(tipo, config)

        try:
            resultado = _ejecutar_reporte(tipo, origen='manual', config=config)
        except Exception as exc:
            logger.exception('Error en generación manual del reporte %s', tipo)
            return Response(
                {'error': str(exc), 'tipo': tipo},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response({'mensaje': 'Reporte generado y enviado.', **resultado})

    def _previsualizar(self, tipo, config):
        """Genera el contenido sin enviarlo (vista previa en la UI)."""
        from .tasks import GENERADORES

        try:
            texto, datos = GENERADORES[tipo]()
        except Exception as exc:
            logger.exception('Error previsualizando el reporte %s', tipo)
            return Response({'error': str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        adjuntos = []
        from .tasks import _formatos
        formatos = _formatos(config)
        if formatos:
            from .documentos import generar_excel, generar_pdf
            if 'pdf' in formatos:
                adjuntos.append({
                    'nombre': 'reporte.pdf',
                    'mime': 'application/pdf',
                    'contenido_base64': _b64(generar_pdf(datos)),
                })
            if 'excel' in formatos:
                adjuntos.append({
                    'nombre': 'reporte.xlsx',
                    'mime': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    'contenido_base64': _b64(generar_excel(datos)),
                })

        return Response({
            'tipo': tipo,
            'contenido': texto,
            'datos': datos,
            'adjuntos': adjuntos,
            'programacion': config.descripcion_programacion() if config else None,
        })

    @action(detail=True, methods=['get'], url_path='descargar')
    def descargar(self, request, pk=None):
        """Descarga el reporte en el formato pedido (pdf, excel o txt)."""
        reporte = self.get_object()
        formato = (request.query_params.get('formato') or 'txt').lower()

        if formato in ('pdf', 'excel'):
            return self._descargar_documento(reporte, formato)

        respuesta = HttpResponse(reporte.contenido, content_type='text/plain; charset=utf-8')
        respuesta['Content-Disposition'] = (
            f'attachment; filename="reporte_{reporte.tipo}_'
            f'{reporte.fecha_periodo.strftime("%Y%m%d")}.txt"'
        )
        return respuesta

    def _descargar_documento(self, reporte, formato):
        import io
        import os

        from django.conf import settings
        from django.http import FileResponse, Http404

        nombre = f'{reporte.tipo}_{reporte.fecha_periodo.strftime("%Y%m%d")}.{formato}'
        ruta_relativa = f'reportes_auto/{nombre}'
        ruta_absoluta = os.path.join(settings.MEDIA_ROOT, ruta_relativa)

        # 1) adjunto ya generado al enviar el reporte
        for adjunto in reporte.adjuntos or []:
            if adjunto.get('nombre', '').endswith(f'.{formato}'):
                ruta_relativa = adjunto['ruta']
                ruta_absoluta = os.path.join(settings.MEDIA_ROOT, ruta_relativa)
                break

        if not os.path.exists(ruta_absoluta):
            # 2) fallback: se genera al vuelo desde los datos estructurados
            if not reporte.datos:
                raise Http404('Este reporte no tiene datos para generar el archivo.')
            from .documentos import generar_excel, generar_pdf
            contenido = generar_pdf(reporte.datos) if formato == 'pdf' else generar_excel(reporte.datos)
            mime = ('application/pdf' if formato == 'pdf' else
                    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            return FileResponse(
                io.BytesIO(contenido),
                as_attachment=True,
                filename=nombre,
                content_type=mime,
            )

        return FileResponse(
            open(ruta_absoluta, 'rb'), as_attachment=True, filename=os.path.basename(ruta_absoluta)
        )

    @action(detail=True, methods=['post'], url_path='reintentar')
    def reintentar(self, request, pk=None):
        """
        Reenvía a quien no recibió el reporte.

        Acepta tanto reportes 'fallido' como 'enviado' con destinatarios
        pendientes: el reintento escribe solo a esos, sin duplicar los que
        ya recibieron el mensaje.
        """
        reporte = self.get_object()
        if reporte.estado not in ('fallido', 'enviado') or (
            reporte.estado == 'enviado' and not reporte.pendientes
        ):
            return Response(
                {'error': 'Este reporte no tiene destinatarios pendientes de envío.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        config = ConfiguracionReporte.objects.filter(tipo=reporte.tipo).first()
        try:
            # Se conserva el origen del reporte original para reintentar el
            # mismo registro en vez de crear uno nuevo en el historial.
            resultado = _ejecutar_reporte(
                reporte.tipo,
                origen=reporte.origen,
                config=config,
                permitir_repetido=True,
            )
        except Exception as exc:
            logger.exception('Error reintentando el reporte %s', reporte.id)
            return Response({'error': str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        reporte.refresh_from_db()
        return Response({
            'mensaje': 'Reintento ejecutado.',
            'reporte_anterior': reporte.id,
            **resultado,
        })

    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """Métricas de salud del envío automático."""
        from django.db.models import Count, Sum

        total = ReporteGenerado.objects.count()
        por_estado = dict(
            ReporteGenerado.objects.values_list('estado').annotate(n=Count('id'))
        )
        por_tipo = {
            tipo: total_tipo
            for tipo, total_tipo in ReporteGenerado.objects.values_list('tipo')
            .annotate(n=Count('id')).values_list('tipo', 'n')
        }

        enviados = (ReporteGenerado.objects.aggregate(
            m=Sum('mensajes_enviados'), f=Sum('destinatarios_fallidos')
        ))
        m = enviados['m'] or 0
        f = enviados['f'] or 0

        ultimos_7 = ReporteGenerado.objects.filter(
            fecha_generacion__gte=timezone.now() - timedelta(days=7)
        )
        fallos_7 = ultimos_7.filter(estado='fallido').count()

        return Response({
            'total': total,
            'enviados': por_estado.get('enviado', 0),
            'fallidos': por_estado.get('fallido', 0),
            'generados': por_estado.get('generado', 0),
            'omitidos': por_estado.get('omitido', 0),
            'por_tipo': por_tipo,
            'mensajes_enviados': m,
            'mensajes_fallidos': f,
            'tasa_exito': round(m / (m + f) * 100, 1) if (m + f) else None,
            'fallos_ultimos_7_dias': fallos_7,
            'configuraciones_activas': ConfiguracionReporte.objects.filter(activo=True).count(),
        })


def _booleano(valor):
    """
    Interpreta el valor de `enviar`. Sin esto, el string "false" que llega
    desde un formulario se evalúa como True y el reporte se envía.
    """
    if isinstance(valor, bool):
        return valor
    if valor is None:
        return True
    return str(valor).strip().lower() not in ('false', '0', 'no', 'off', '')


def _b64(contenido):
    import base64
    return base64.b64encode(contenido).decode('ascii')


class ConfiguracionReporteViewSet(viewsets.ModelViewSet):
    """
    Configuración de reportes automáticos.

    `hora_envio`, `dia_semana` y `dia_mes` son leídos por
    `dispatch_reportes_programados` en cada tick, así que los cambios
    surten efecto sin tocar CELERY_BEAT_SCHEDULE.
    """
    queryset = ConfiguracionReporte.objects.all().order_by('tipo')
    serializer_class = ConfiguracionReporteSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def activas(self, request):
        return Response(self.get_serializer(self.queryset.filter(activo=True), many=True).data)

    @action(detail=False, methods=['get'], url_path='programacion')
    def programacion(self, request):
        """
        Vista de un vistazo de la programación real: qué se enviará, cuándo
        y si tiene destinatarios válidos.
        """
        ahora = timezone.localtime()
        items = []
        for config in self.queryset:
            serializer = self.get_serializer(config)
            data = serializer.data
            data['corresponde_hoy'] = config.corresponde_hoy(ahora.date())
            items.append(data)
        return Response({'ahora': ahora, 'configuraciones': items})
