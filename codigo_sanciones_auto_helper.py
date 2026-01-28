"""
Código para implementar Sanciones Automáticas
Agregar estos métodos a sanciones/views.py en SancionViewSet
"""

# ========================================
# MÉTODO 1: Generar sanción automática por inasistencia
# ========================================
"""
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction

@action(detail=False, methods=['post'])
def generar_por_inasistencia(self, request):
    '''
    Generar sanción automática al marcar inasistencia en una reunión.
    Espera: {
        "afiliado_id": 1,
        "asistencia_id": 5,
        "tipo": "Falta a Reunión",
        "monto": 50.00,
        "motivo": "Inasistencia a reunión ordinaria del 04/12/2025"
    }
    '''
    from sanciones.models import Sancion
    from afiliados.models import Afiliado
    from asistencias.models import Asistencia
    
    afiliado_id = request.data.get('afiliado_id')
    asistencia_id = request.data.get('asistencia_id')
    tipo = request.data.get('tipo', 'Falta a Reunión')
    monto = request.data.get('monto', 50.00)  # Monto por defecto
    motivo = request.data.get('motivo', '')
    
    if not afiliado_id:
        return Response({'error': 'afiliado_id es requerido'}, status=400)
    
    try:
        afiliado = Afiliado.objects.get(id=afiliado_id)
        asistencia = Asistencia.objects.get(id=asistencia_id) if asistencia_id else None
        
        # Verificar si ya existe una sanción para esta asistencia
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
        
        # Crear sanción automáticamente
        with transaction.atomic():
            sancion = Sancion.objects.create(
                afiliado=afiliado,
                tipo=tipo,
                motivo=motivo,
                monto=monto,
                estado='pendiente',
                referencia_asistencia=asistencia
            )
            
            # Opcional: Enviar notificación automática
            # self._enviar_notificacion_sancion(sancion)
            
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
"""

# ========================================
# MÉTODO 2: Listar afiliados con múltiples sanciones
# ========================================
"""
@action(detail=False, methods=['get'])
def afiliados_multiples_sanciones(self, request):
    '''
    Obtener lista de afiliados con 3 o más sanciones pendientes.
    Útil para generar alertas en el dashboard.
    '''
    from django.db.models import Count, Sum
    from sanciones.models import Sancion
    
    # Agrupar por afiliado y contar sanciones pendientes
    afiliados_con_sanciones = Sancion.objects.filter(
        estado='pendiente'
    ).values(
        'afiliado__id',
        'afiliado__nombres',
        'afiliado__apellidos',
        'afiliado__ci'
    ).annotate(
        total_sanciones=Count('id'),
        monto_total=Sum('monto')
    ).filter(
        total_sanciones__gte=3  # 3 o más sanciones
    ).order_by('-total_sanciones')
    
    # Formatear respuesta
    resultado = []
    for item in afiliados_con_sanciones:
        resultado.append({
            'afiliado_id': item['afiliado__id'],
            'nombre_completo': f"{item['afiliado__apellidos']} {item['afiliado__nombres']}",
            'ci': item['afiliado__ci'],
            'total_sanciones': item['total_sanciones'],
            'monto_total': float(item['monto_total'] or 0),
            'alerta_nivel': 'ALTA' if item['total_sanciones'] >= 5 else 'MEDIA'
        })
    
    return Response({
        'count': len(resultado),
        'afiliados': resultado
    })
"""

# ========================================
# MÉTODO 3: Método auxiliar para enviar notificaciones
# ========================================
"""
def _enviar_notificacion_sancion(self, sancion):
    '''
    Método auxiliar para enviar notificación WhatsApp de nueva sanción.
    '''
    try:
        if not sancion.afiliado.telefono:
            return
        
        mensaje = f'''
🚫 *SANCIÓN REGISTRADA*

Afiliado: {sancion.afiliado.nombre_completo}
CI: {sancion.afiliado.ci}

Tipo: {sancion.tipo}
Motivo: {sancion.motivo}
Monto: Bs. {sancion.monto}

Estado: {sancion.estado.upper()}

Por favor, regularice su situación a la brevedad posible.

_Sindicato Mixto Integración Taipiplaya_
        '''.strip()
        
        # Aquí iría la lógica de envío por WhatsApp
        # Por ahora solo registramos el intento
        print(f"Notificación enviada a {sancion.afiliado.telefono}")
        
    except Exception as e:
        print(f"Error enviando notificación: {e}")
"""

# ========================================
# CONFIGURACIÓN RECOMENDADA
# ========================================
"""
# En settings.py o como constantes del sistema:

SANCIONES_CONFIG = {
    'FALTA_REUNION': {
        'monto_default': 50.00,
        'tipo': 'Falta a Reunión',
        'notificar_automatico': True
    },
    'FALTA_TURNO_PARADA': {
        'monto_default': 50.00,
        'tipo': 'Falta a Turno de Parada',
        'notificar_automatico': True
    },
    'INCUMPLIMIENTO_REGLAMENTO': {
        'monto_default': 100.00,
        'tipo': 'Incumplimiento de Reglamento',
        'notificar_automatico': False
    }
}

# Uso:
from django.conf import settings
monto = settings.SANCIONES_CONFIG['FALTA_REUNION']['monto_default']
"""

# ========================================
# INTEGRACIÓN CON MÓDULO DE ASISTENCIAS
# ========================================
"""
# En asistencias/views.py, al marcar inasistencia:

def marcar_inasistencia(self, request, pk=None):
    asistencia = self.get_object()
    asistencia.presente = False
    asistencia.save()
    
    # Generar sanción automática
    from sanciones.models import Sancion
    from django.conf import settings
    
    config = settings.SANCIONES_CONFIG.get('FALTA_REUNION', {})
    
    try:
        Sancion.objects.create(
            afiliado=asistencia.afiliado,
            tipo=config.get('tipo', 'Falta a Reunión'),
            motivo=f"Inasistencia a reunión del {asistencia.reunion.fecha}",
            monto=config.get('monto_default', 50.00),
            estado='pendiente',
            referencia_asistencia=asistencia
        )
    except Exception as e:
        pass  # Log error but don't fail the operation
    
    return Response({'success': True})
"""

print("Código de sanciones automáticas listo para integrar")
print("Ver instrucciones en los comentarios del archivo")
