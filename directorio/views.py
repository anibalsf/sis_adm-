from rest_framework import viewsets, filters
from rest_framework.permissions import BasePermission, SAFE_METHODS
from .models import MiembroDirectorio
from .serializers import MiembroDirectorioSerializer


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
    permission_classes = [IsSecretariaOrDirectivaOrReadOnly]

    from rest_framework.decorators import action
    @action(detail=False, methods=['get'])
    def reporte(self, request):
        """Generar reporte PDF de directorio"""
        import io
        from django.http import FileResponse
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()

        # Título
        elements.append(Paragraph("Reporte de Directorio", styles['Title']))
        elements.append(Spacer(1, 12))

        # Datos
        data = [['Afiliado', 'Cargo', 'Inicio', 'Fin', 'Estado']]
        for miembro in self.queryset.all().order_by('cargo'):
            afiliado_nombre = f"{miembro.afiliado.apellidos} {miembro.afiliado.nombres}" if miembro.afiliado else "Sin Afiliado"
            data.append([
                afiliado_nombre,
                miembro.cargo.replace('_', ' ').title(),
                str(miembro.fecha_inicio),
                str(miembro.fecha_fin) if miembro.fecha_fin else '-',
                miembro.estado.capitalize()
            ])

        # Tabla
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