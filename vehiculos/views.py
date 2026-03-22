from rest_framework import viewsets
from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework import filters
from .models import Vehiculo
from .serializers import VehiculoSerializer


class VehiculoViewSet(viewsets.ModelViewSet):
    queryset = Vehiculo.objects.select_related('afiliado').all()
    serializer_class = VehiculoSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['placa', 'tipo', 'color', 'afiliado__ci', 'afiliado__apellidos']
    ordering_fields = ['placa', 'tipo', 'capacidad']
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
        """Generar reporte PDF de vehículos"""
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
        elements.append(Paragraph("Reporte General de Vehículos", styles['Title']))
        elements.append(Spacer(1, 12))

        # Datos
        data = [['Placa', 'Tipo', 'Capacidad', 'Afiliado', 'Estado']]
        for vehiculo in self.queryset.all().order_by('placa'):
            afiliado_nombre = f"{vehiculo.afiliado.apellidos} {vehiculo.afiliado.nombres}" if vehiculo.afiliado else "Sin Afiliado"
            data.append([
                vehiculo.placa,
                vehiculo.tipo,
                str(vehiculo.capacidad),
                afiliado_nombre,
                vehiculo.estado.capitalize()
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
        return FileResponse(buffer, as_attachment=True, filename='vehiculos.pdf')

    @action(detail=False, methods=['get'])
    def export_excel(self, request):
        """Exportar lista de vehículos a Excel"""
        from openpyxl import Workbook
        from django.http import HttpResponse
        
        wb = Workbook()
        ws = wb.active
        ws.title = "Vehículos"
        
        # Encabezados
        headers = ['ID', 'Placa', 'Tipo', 'Capacidad', 'Afiliado', 'Estado']
        ws.append(headers)
        
        # Datos
        for obj in self.get_queryset().order_by('placa'):
            afiliado = f"{obj.afiliado.apellidos} {obj.afiliado.nombres}" if obj.afiliado else "N/A"
            ws.append([
                obj.id,
                obj.placa,
                obj.tipo.capitalize() if obj.tipo else '',
                obj.capacidad,
                afiliado,
                obj.estado.capitalize() if obj.estado else ''
            ])
            
        for cell in ws[1]:
            cell.font = cell.font.copy(bold=True)
            
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=vehiculos.xlsx'
        wb.save(response)
        return response

    def get_queryset(self):
        qs = super().get_queryset()
        estado = self.request.query_params.get('estado')
        afiliado = self.request.query_params.get('afiliado')
        con_placa = self.request.query_params.get('con_placa')
        tipo_in = self.request.query_params.get('tipo_in')
        if estado:
            qs = qs.filter(estado=estado)
        if afiliado:
            qs = qs.filter(afiliado_id=afiliado)
        if con_placa and con_placa.lower() == 'true':
            qs = qs.filter(indocumentado=False)
        if tipo_in:
            tipos = [t.strip().lower() for t in tipo_in.split(',')]
            qs = qs.filter(tipo__in=tipos)
        return qs
