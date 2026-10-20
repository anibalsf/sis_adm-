from datetime import date

from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.permissions import BasePermission, SAFE_METHODS, IsAuthenticated
from rest_framework.response import Response
from dateutil.relativedelta import relativedelta

from .models import MiembroDirectorio, VIGENCIA_ANIOS
from .serializers import MiembroDirectorioSerializer


def _parse_fecha(valor):
    if not valor:
        return None
    try:
        return date.fromisoformat(valor)
    except ValueError:
        return None


class MiembroDirectorioViewSet(viewsets.ModelViewSet):
    queryset = MiembroDirectorio.objects.select_related('afiliado').all()
    serializer_class = MiembroDirectorioSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['afiliado__ci', 'afiliado__apellidos', 'afiliado__nombres', 'cargo', 'estado']
    ordering_fields = ['fecha_inicio', 'fecha_fin', 'cargo']
    class IsSecretariaOrDirectivaOrReadOnly(BasePermission):
        def has_permission(self, request, view):
            if request.method in SAFE_METHODS:
                return True
            user = request.user
            if not user or not user.is_authenticated:
                return False
            if getattr(user, 'is_superuser', False) or getattr(user, 'is_staff', False):
                return True
            return user.groups.filter(name__in=['Secretaria', 'Sistemas']).exists()
    permission_classes = [IsAuthenticated, IsSecretariaOrDirectivaOrReadOnly]

    @action(detail=False, methods=['get'])
    def vigente(self, request):
        """Directorio vigente + estado de la gestión (vencida / por vencer)."""
        hoy = date.today()
        miembros = list(MiembroDirectorio.directorio_vigente(hoy))
        vencidos = False
        if miembros:
            fecha_inicio = min(m.fecha_inicio for m in miembros)
            fin_gestion = fecha_inicio + relativedelta(years=VIGENCIA_ANIOS)
            dias_restantes = (fin_gestion - hoy).days
        else:
            # Sin vigente: mostramos si hay uno vencido por concluir
            vencidos = MiembroDirectorio.objects.filter(estado='activo').exists()
            fecha_inicio = None
            fin_gestion = None
            dias_restantes = None
        datos = MiembroDirectorioSerializer(miembros, many=True).data
        return Response({
            'miembros': datos,
            'fecha_inicio_gestion': fecha_inicio,
            'fecha_fin_gestion': fin_gestion,
            'dias_restantes': dias_restantes,
            'vencida': bool(dias_restantes is not None and dias_restantes <= 0) or not miembros,
            'por_vencer': bool(dias_restantes is not None and 0 < dias_restantes <= 30),
            'hay_vencidos_sin_concluir': vencidos,
            'vigencia_anios': VIGENCIA_ANIOS,
        })

    @action(detail=False, methods=['get'])
    def gestiones(self, request):
        """Histórico de gestiones del directorio (una por año de inicio)."""
        resultado = []
        for g in MiembroDirectorio.gestiones():
            resultado.append({
                'anio': g['anio'],
                'fecha_inicio': g['fecha_inicio'],
                'fecha_fin': g['fecha_fin'],
                'total_miembros': g['total_miembros'],
                'activos': g['activos'],
            })
        return Response(resultado)

    @action(detail=False, methods=['post'])
    def cambio_gestion(self, request):
        """Cierre del directorio saliente + inauguración del entrante.

        Concluye el directorio vencido, crea los miembros electos y devuelve
        el resumen de transferencia de caja. La numeración de recibos continúa.
        """
        from .services import cambio_gestion as servicio_cambio

        nuevos = request.data.get('miembros') or []
        if not nuevos:
            return Response({'detail': 'Debe indicar los miembros del nuevo directorio'},
                            status=status.HTTP_400_BAD_REQUEST)
        fecha_inicio = _parse_fecha(request.data.get('fecha_inicio')) or date.today()
        try:
            resultado = servicio_cambio(nuevos, fecha_inicio=fecha_inicio, user=request.user)
        except ValueError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        t = resultado['transferencia']
        return Response({
            'detalle': f"Directorio concluido. Nuevo directorio vigente desde {fecha_inicio.isoformat()}.",
            'saliente': MiembroDirectorioSerializer(resultado['saliente'], many=True).data,
            'entrante': MiembroDirectorioSerializer(resultado['entrante'], many=True).data,
            'transferencia': {
                'desde': t['desde'],
                'hasta': t['hasta'],
                'total_ingresos': t['total_ingresos'],
                'total_egresos': t['total_egresos'],
                'saldo': t['saldo'],
                'nro_recibo_actual': t['nro_recibo_actual'],
                'nota_numeracion': 'La numeración de recibos continúa sin reiniciarse.',
            },
            'fecha_cambio': resultado['fecha_cambio'],
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def reporte(self, request):
        """Reporte PDF de directorio; acepta filtro de gestión por fechas."""
        import io
        from django.http import FileResponse
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet

        desde = _parse_fecha(request.query_params.get('desde'))
        hasta = _parse_fecha(request.query_params.get('hasta'))
        anio = request.query_params.get('anio')
        solo_vigente = request.query_params.get('vigente') == 'true'

        qs = self.get_queryset()
        titulo = 'Reporte de Directorio'
        if solo_vigente:
            hoy = date.today()
            qs = qs.filter(pk__in=[m.pk for m in MiembroDirectorio.directorio_vigente(hoy)])
            titulo = 'Directorio Vigente'
        elif anio:
            try:
                qs = qs.filter(fecha_inicio__year=int(anio))
                titulo = f'Directorio Gestión {anio}'
            except (TypeError, ValueError):
                pass
        elif desde and hasta:
            qs = qs.filter(fecha_inicio__lte=hasta).filter(
                models_q_fin_posterior(desde)
            )
            titulo = f'Directorio Gestión {desde.year}-{hasta.year}'
        elif desde:
            qs = qs.filter(fecha_inicio__gte=desde)
            titulo = f'Directorio desde {desde}'

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()

        elements.append(Paragraph(titulo, styles['Title']))
        elements.append(Spacer(1, 12))

        data = [['Afiliado', 'Cargo', 'Inicio', 'Fin', 'Estado']]
        for miembro in qs.order_by('cargo'):
            afiliado_nombre = f"{miembro.afiliado.apellidos} {miembro.afiliado.nombres}" if miembro.afiliado else "Sin Afiliado"
            data.append([
                afiliado_nombre,
                miembro.cargo.replace('_', ' ').title(),
                str(miembro.fecha_inicio),
                str(miembro.fecha_fin) if miembro.fecha_fin else '-',
                miembro.estado.capitalize()
            ])

        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(table)

        doc.build(elements)
        buffer.seek(0)
        return FileResponse(buffer, as_attachment=True, filename='directorio.pdf')

    def get_queryset(self):
        qs = super().get_queryset()
        cargo = self.request.query_params.get('cargo')
        estado = self.request.query_params.get('estado')
        activo = self.request.query_params.get('activo')
        anio = self.request.query_params.get('anio')
        if anio:
            try:
                qs = qs.filter(fecha_inicio__year=int(anio))
            except (TypeError, ValueError):
                pass
        if cargo:
            canon = (cargo or '').strip().lower()
            label_map = {
                'secretario_general': ['secretario_general', 'secretario general'],
                'secretario_relaciones': ['secretario_relaciones', 'secretario de relaciones'],
                'secretario_hacienda': ['secretario_hacienda', 'secretario de hacienda'],
                'secretario_actas': ['secretario_actas', 'secretario de actas'],
                'secretario_conflictos': ['secretario_conflictos', 'secretario de conflictos'],
                'secretario_deportes': ['secretario_deportes', 'secretario de deportes'],
                'vocal': ['vocal'],
            }
            aliases = label_map.get(canon, [canon])
            qs = qs.filter(cargo__iexact=canon) | qs.filter(cargo__in=aliases) | qs.filter(cargo__in=[a.replace('_', ' ') for a in aliases])
        if estado:
            qs = qs.filter(estado=estado)
        if activo == 'true':
            qs = qs.filter(estado='activo', fecha_fin__isnull=True)
        if activo == 'false':
            qs = qs.exclude(estado='activo')
        return qs


def models_q_fin_posterior(desde):
    """Membresías cuya vigencia alcanza la fecha 'desde' (gestión que la abarca)."""
    from django.db.models import Q
    return Q(fecha_fin__isnull=True) | Q(fecha_fin__gte=desde)
