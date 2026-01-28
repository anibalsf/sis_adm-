"""
Fase 7: Reportes Adicionales
Código para crear nuevos reportes analíticos
"""

# ========================================
# ARCHIVO: reportes/views.py (crear si no existe)
# ========================================
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Count, Avg, Q
from datetime import datetime, timedelta
"""

# ========================================
# REPORTE 1: Afiliados Morosos
# ========================================
"""
class AfiliadosMorososView(APIView):
    '''
    Reporte de afiliados con pagos pendientes.
    URL: GET /api/reportes/afiliados-morosos/?meses=3
    '''
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        from afiliados.models import Afiliado
        from tesoreria.models import Pago
        from sanciones.models import Sancion
        
        meses_atras = int(request.GET.get('meses', 3))
        fecha_limite = datetime.now() - timedelta(days=30 * meses_atras)
        
        # Obtener todos los afiliados activos
        afiliados = Afiliado.objects.filter(estado='activo', is_active=True)
        
        morosos = []
        for afiliado in afiliados:
            # Calcular deuda total de cuotas pendientes
            cuotas_pendientes = afiliado.cuotas.filter(
                estado='pendiente'
            )
            deuda_cuotas = cuotas_pendientes.aggregate(
                total=Sum('monto')
            )['total'] or 0
            
            # Calcular deuda de sanciones pendientes
            sanciones_pendientes = afiliado.sanciones.filter(
                estado='pendiente'
            )
            deuda_sanciones = sanciones_pendientes.aggregate(
                total=Sum('monto')
            )['total'] or 0
            
            deuda_total = deuda_cuotas + deuda_sanciones
            
            # Si tiene deuda, agregar a la lista
            if deuda_total > 0:
                # Obtener último pago
                ultimo_pago = Pago.objects.filter(
                    afiliado=afiliado
                ).order_by('-fecha_pago').first()
                
                dias_sin_pagar = (datetime.now().date() - ultimo_pago.fecha_pago).days if ultimo_pago and hasattr(ultimo_pago, 'fecha_pago') else 999
                
                # Determinar nivel de morosidad
                if dias_sin_pagar > 90:
                    nivel = 'CRÍTICO'
                elif dias_sin_pagar > 60:
                    nivel = 'ALTO'
                elif dias_sin_pagar > 30:
                    nivel = 'MODERADO'
                else:
                    nivel = 'BAJO'
                
                morosos.append({
                    'afiliado_id': afiliado.id,
                    'nombre_completo': afiliado.nombre_completo,
                    'ci': afiliado.ci,
                    'telefono': afiliado.telefono,
                    'deuda_cuotas': float(deuda_cuotas),
                    'deuda_sanciones': float(deuda_sanciones),
                    'deuda_total': float(deuda_total),
                    'cantidad_cuotas_pendientes': cuotas_pendientes.count(),
                    'cantidad_sanciones_pendientes': sanciones_pendientes.count(),
                    'ultimo_pago': str(ultimo_pago.fecha_pago) if ultimo_pago and hasattr(ultimo_pago, 'fecha_pago') else 'Nunca',
                    'dias_sin_pagar': dias_sin_pagar,
                    'nivel_morosidad': nivel
                })
        
        # Ordenar por deuda total descendente
        morosos.sort(key=lambda x: x['deuda_total'], reverse=True)
        
        # Calcular totales
        total_deuda = sum(m['deuda_total'] for m in morosos)
        
        return Response({
            'total_morosos': len(morosos),
            'deuda_total_sistema': float(total_deuda),
            'morosos': morosos,
            'resumen_por_nivel': {
                'critico': len([m for m in morosos if m['nivel_morosidad'] == 'CRÍTICO']),
                'alto': len([m for m in morosos if m['nivel_morosidad'] == 'ALTO']),
                'moderado': len([m for m in morosos if m['nivel_morosidad'] == 'MODERADO']),
                'bajo': len([m for m in morosos if m['nivel_morosidad'] == 'BAJO'])
            }
        })
"""

# ========================================
# REPORTE 2: Rutas Más Rentables
# ========================================
"""
class RutasRentablesView(APIView):
    '''
    Análisis de rentabilidad por ruta.
    URL: GET /api/reportes/rutas-rentables/?meses=6
    '''
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        from hojasruta.models import HojaRuta
        from rutas.models import Ruta
        
        meses = int(request.GET.get('meses', 6))
        fecha_inicio = datetime.now() - timedelta(days=30 * meses)
        
        # Obtener todas las rutas
        rutas = Ruta.objects.all()
        
        resultados = []
        for ruta in rutas:
            # Hojas de ruta de esta ruta en el período
            hojas = HojaRuta.objects.filter(
                ruta=ruta,
                fecha_emision__gte=fecha_inicio
            )
            
            total_hojas = hojas.count()
            
            if total_hojas == 0:
                continue
            
            # Calcular ingresos totales
            ingresos_totales = hojas.aggregate(
                total=Sum('precio')
            )['total'] or 0
            
            # Promedio de ingresos por viaje
            promedio_por_viaje = ingresos_totales / total_hojas if total_hojas > 0 else 0
            
            # Obtener reservas asociadas a estas hojas
            from reservas.models import Reserva
            total_reservas = Reserva.objects.filter(
                hoja_ruta__in=hojas
            ).count()
            
            resultados.append({
                'ruta_id': ruta.id,
                'ruta_nombre': ruta.nombre,
                'origen': getattr(ruta, 'origen', 'N/A'),
                'destino': getattr(ruta, 'destino', 'N/A'),
                'total_viajes': total_hojas,
                'ingresos_totales': float(ingresos_totales),
                'promedio_por_viaje': float(promedio_por_viaje),
                'total_reservas': total_reservas,
                'promedio_reservas_por_viaje': round(total_reservas / total_hojas, 2) if total_hojas > 0 else 0
            })
        
        # Ordenar por ingresos totales
        resultados.sort(key=lambda x: x['ingresos_totales'], reverse=True)
        
        # Calcular totales
        total_ingresos = sum(r['ingresos_totales'] for r in resultados)
        total_viajes = sum(r['total_viajes'] for r in resultados)
        
        return Response({
            'periodo_meses': meses,
            'fecha_desde': fecha_inicio.date(),
            'total_rutas_analizadas': len(resultados),
            'total_viajes_sistema': total_viajes,
            'ingresos_totales_sistema': float(total_ingresos),
            'promedio_por_viaje_sistema': float(total_ingresos / total_viajes) if total_viajes > 0 else 0,
            'rutas': resultados
        })
"""

# ========================================
# REPORTE 3: Ocupación Histórica
# ========================================
"""
class OcupacionHistoricaView(APIView):
    '''
    Análisis de ocupación de vehículos por mes.
    URL: GET /api/reportes/ocupacion-historica/?meses=12
    '''
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        from hojasruta.models import HojaRuta
        from reservas.models import Reserva
        from django.db.models.functions import TruncMonth
        
        meses = int(request.GET.get('meses', 12))
        fecha_inicio = datetime.now() - timedelta(days=30 * meses)
        
        # Agrupar hojas de ruta por mes
        hojas_por_mes = HojaRuta.objects.filter(
            fecha_emision__gte=fecha_inicio
        ).annotate(
            mes=TruncMonth('fecha_emision')
        ).values('mes').annotate(
            total_hojas=Count('id'),
            total_cupos=Sum('capacidad_total'),
            total_reservados=Sum('cupos_reservados')
        ).order_by('mes')
        
        resultados_mensuales = []
        for item in hojas_por_mes:
            total_cupos = item['total_cupos'] or 0
            total_reservados = item['total_reservados'] or 0
            
            porcentaje_ocupacion = (total_reservados / total_cupos * 100) if total_cupos > 0 else 0
            
            resultados_mensuales.append({
                'mes': item['mes'].strftime('%Y-%m'),
                'mes_nombre': item['mes'].strftime('%B %Y'),
                'total_hojas': item['total_hojas'],
                'total_cupos_disponibles': total_cupos,
                'total_cupos_reservados': total_reservados,
                'cupos_libres': total_cupos - total_reservados,
                'porcentaje_ocupacion': round(porcentaje_ocupacion, 2)
            })
        
        # Promedios generales
        if resultados_mensuales:
            promedio_ocupacion = sum(r['porcentaje_ocupacion'] for r in resultados_mensuales) / len(resultados_mensuales)
        else:
            promedio_ocupacion = 0
        
        return Response({
            'periodo_meses': meses,
            'fecha_desde': fecha_inicio.date(),
            'promedio_ocupacion_general': round(promedio_ocupacion, 2),
            'meses': resultados_mensuales
        })
"""

# ========================================
# INTEGRACIÓN EN urls.py
# ========================================
"""
# En reportes/urls.py o urls.py principal:
from django.urls import path
from reportes.views import AfiliadosMorososView, RutasRentablesView, OcupacionHistoricaView

urlpatterns = [
    path('reportes/afiliados-morosos/', AfiliadosMorososView.as_view()),
    path('reportes/rutas-rentables/', RutasRentablesView.as_view()),
    path('reportes/ocupacion-historica/', OcupacionHistoricaView.as_view()),
]
"""

# ========================================
# INTEGRACIÓN EN FRONTEND
# ========================================
"""
// En api.js:
getAfiliadosMorosos: (params) => axios.get('/reportes/afiliados-morosos/', { params }),
getRutasRentables: (params) => axios.get('/reportes/rutas-rentables/', { params }),
getOcupacionHistorica: (params) => axios.get('/reportes/ocupacion-historica/', { params }),

// Componente de ejemplo para mostrar morosos:
import { useState, useEffect } from 'react';
import { api } from '../services/api';

const ReporteMorosos = () => {
    const [data, setData] = useState(null);
    
    useEffect(() => {
        const loadData = async () => {
            const res = await api.getAfiliadosMorosos({ meses: 3 });
            setData(res.data);
        };
        loadData();
    }, []);
    
    if (!data) return <div>Cargando...</div>;
    
    return (
        <div>
            <h2>Afiliados Morosos</h2>
            <div className="stats">
                <p>Total Morosos: {data.total_morosos}</p>
                <p>Deuda Total: Bs. {data.deuda_total_sistema.toFixed(2)}</p>
            </div>
            
            <table>
                <thead>
                    <tr>
                        <th>Afiliado</th>
                        <th>CI</th>
                        <th>Deuda Total</th>
                        <th>Días sin Pagar</th>
                        <th>Nivel</th>
                    </tr>
                </thead>
                <tbody>
                    {data.morosos.map(m => (
                        <tr key={m.afiliado_id} className={`nivel-${m.nivel_morosidad.toLowerCase()}`}>
                            <td>{m.nombre_completo}</td>
                            <td>{m.ci}</td>
                            <td>Bs. {m.deuda_total.toFixed(2)}</td>
                            <td>{m.dias_sin_pagar}</td>
                            <td><span className="badge">{m.nivel_morosidad}</span></td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
};
"""

print("Código de Reportes Adicionales listo para integrar")
