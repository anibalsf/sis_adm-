from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from .models import ReporteGenerado, ConfiguracionReporte
from .serializers import ReporteGeneradoSerializer, ConfiguracionReporteSerializer
from .tasks import send_daily_report_task, send_weekly_report_task, send_monthly_report_task
from .report_generator import ReportGenerator


class ReporteGeneradoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para ver reportes generados
    """
    queryset = ReporteGenerado.objects.all().order_by('-fecha_generacion')
    serializer_class = ReporteGeneradoSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post'] # Restringir otros si se desea, pero ModelViewSet abre post.
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtros opcionales
        tipo = self.request.query_params.get('tipo', None)
        estado = self.request.query_params.get('estado', None)
        fecha_desde = self.request.query_params.get('fecha_desde', None)
        fecha_hasta = self.request.query_params.get('fecha_hasta', None)
        
        if tipo:
            queryset = queryset.filter(tipo=tipo)
        if estado:
            queryset = queryset.filter(estado=estado)
        if fecha_desde:
            queryset = queryset.filter(fecha_generacion__gte=fecha_desde)
        if fecha_hasta:
            queryset = queryset.filter(fecha_generacion__lte=fecha_hasta)
            
        return queryset
    
    @action(detail=False, methods=['post'], url_path='generar-manual')
    def generar_manual(self, request):
        """
        Generar un reporte manualmente (Ejecución Directa Síncrona)
        """
        tipo = request.data.get('tipo', 'diario')
        
        try:
            # Ejecutamos DIRECTAMENTE la función de la tarea, saltándonos el broker de Celery
            # Al estar decorada con @shared_task, al llamarla sin .delay() se ejecuta localmente
            if tipo == 'diario':
                result = send_daily_report_task()
            elif tipo == 'semanal':
                result = send_weekly_report_task()
            elif tipo == 'mensual':
                result = send_monthly_report_task()
            else:
                return Response(
                    {'error': 'Tipo de reporte inválido'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            return Response({
                'message': f'Reporte {tipo} procesado. {result}',
                'task_id': 'manual-execution'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            import traceback
            print(f"Error generando reporte manual: {e}")
            print(traceback.format_exc())
            return Response(
                {'error': f"Error interno: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """
        Obtener estadísticas de reportes
        """
        total_reportes = ReporteGenerado.objects.count()
        reportes_enviados = ReporteGenerado.objects.filter(estado='enviado').count()
        reportes_fallidos = ReporteGenerado.objects.filter(estado='fallido').count()
        
        # Por tipo
        por_tipo = {}
        for tipo_key, tipo_label in ReporteGenerado.TIPO_CHOICES:
            por_tipo[tipo_key] = ReporteGenerado.objects.filter(tipo=tipo_key).count()
        
        return Response({
            'total': total_reportes,
            'enviados': reportes_enviados,
            'fallidos': reportes_fallidos,
            'por_tipo': por_tipo
        })


class ConfiguracionReporteViewSet(viewsets.ModelViewSet):
    """
    ViewSet para configurar reportes automáticos
    """
    queryset = ConfiguracionReporte.objects.all()
    serializer_class = ConfiguracionReporteSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def activas(self, request):
        """
        Obtener solo configuraciones activas
        """
        configs = self.queryset.filter(activo=True)
        serializer = self.get_serializer(configs, many=True)
        return Response(serializer.data)
