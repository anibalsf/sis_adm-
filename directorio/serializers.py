from rest_framework import serializers
from .models import MiembroDirectorio


class MiembroDirectorioSerializer(serializers.ModelSerializer):
    afiliado_nombre = serializers.SerializerMethodField()
    cargo_label = serializers.SerializerMethodField()
    estado_label = serializers.SerializerMethodField()
    class Meta:
        model = MiembroDirectorio
        fields = ['id', 'afiliado', 'afiliado_nombre', 'cargo', 'cargo_label', 'fecha_inicio', 'fecha_fin', 'estado', 'estado_label', 'created_at', 'updated_at']

    def get_afiliado_nombre(self, obj):
        if obj.afiliado_id and getattr(obj.afiliado, 'apellidos', None):
            return f"{obj.afiliado.apellidos} {obj.afiliado.nombres}"
        return None

    def get_cargo_label(self, obj):
        try:
            return obj.get_cargo_display()
        except Exception:
            return obj.cargo

    def get_estado_label(self, obj):
        try:
            return obj.get_estado_display()
        except Exception:
            return obj.estado

    def validate_cargo(self, value):
        permitido = {
            'secretario_general',
            'secretario_relaciones',
            'secretario_hacienda',
            'secretario_actas',
            'secretario_conflictos',
            'secretario_deportes',
            'vocal',
        }
        v = (value or '').strip().lower()
        if v not in permitido:
            raise serializers.ValidationError('Cargo inválido')
        return v

    def validate_estado(self, value):
        permitido = {'activo', 'concluido'}
        v = (value or '').strip().lower()
        if v not in permitido:
            raise serializers.ValidationError('Estado inválido')
        return v

    def validate(self, attrs):
        fi = attrs.get('fecha_inicio')
        ff = attrs.get('fecha_fin')
        if ff and fi and ff < fi:
            raise serializers.ValidationError({'fecha_fin': 'Fecha fin no puede ser anterior a inicio'})
        cargo = (attrs.get('cargo') or '').strip().lower()
        estado = (attrs.get('estado') or 'activo').strip().lower()
        qs = MiembroDirectorio.objects.filter(cargo=cargo, estado='activo', fecha_fin__isnull=True)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if estado == 'activo' and qs.exists():
            raise serializers.ValidationError({'cargo': 'Ya existe un miembro activo para este cargo'})
        return attrs