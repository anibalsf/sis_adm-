"""
Módulo de gestión para tareas programadas del scheduler
Permite ver y administrar los jobs programados
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from apscheduler.schedulers.background import BackgroundScheduler
import logging

logger = logging.getLogger(__name__)


class SchedulerViewSet(viewsets.ViewSet):
    """
    ViewSet para administrar el scheduler de notificaciones
    """
    permission_classes = [IsAdminUser]
    
    @action(detail=False, methods=['get'])
    def jobs(self, request):
        """Lista todos los jobs programados"""
        try:
            from sistema.scheduler import scheduler
            if not scheduler:
                return Response({
                    'detail': 'Scheduler no está activo'
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
            jobs_info = []
            for job in scheduler.get_jobs():
                jobs_info.append({
                    'id': job.id,
                    'name': job.name,
                    'next_run': str(job.next_run_time) if job.next_run_time else None,
                    'trigger': str(job.trigger)
                })
            
            return Response({
                'jobs': jobs_info,
                'status': 'running' if scheduler.running else 'stopped'
            })
        except Exception as e:
            return Response({
                'detail': f'Error obteniendo jobs: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def test_pagos(self, request):
        """Ejecuta manualmente el recordatorio de pagos (para pruebas)"""
        try:
            from sistema.scheduler import enviar_recordatorios_pagos
            cantidad = enviar_recordatorios_pagos()
            return Response({
                'detail': f'Recordatorios de pago enviados: {cantidad}',
                'cantidad': cantidad
            })
        except Exception as e:
            return Response({
                'detail': f'Error: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def test_sanciones(self, request):
        """Ejecuta manualmente el recordatorio de sanciones (para pruebas)"""
        try:
            from sistema.scheduler import enviar_recordatorios_sanciones
            cantidad = enviar_recordatorios_sanciones()
            return Response({
                'detail': f'Recordatorios de sanciones enviados: {cantidad}',
                'cantidad': cantidad
            })
        except Exception as e:
            return Response({
                'detail': f'Error: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def test_reporte_diario(self, request):
        """Ejecuta manualmente el reporte diario"""
        try:
            from sistema.scheduler import enviar_reporte_diario_ingresos
            resultado = enviar_reporte_diario_ingresos()
            return Response({'detail': f'Reporte diario enviado a {resultado} admins'})
        except Exception as e:
            return Response({'detail': str(e)}, status=500)

    @action(detail=False, methods=['post'])
    def test_alerta_morosos(self, request):
        """Ejecuta manualmente el reporte de morosos"""
        try:
            from sistema.scheduler import enviar_alertas_morosos_semanal
            resultado = enviar_alertas_morosos_semanal()
            return Response({'detail': 'Reporte de morosos ejecutado'})
        except Exception as e:
            return Response({'detail': str(e)}, status=500)
