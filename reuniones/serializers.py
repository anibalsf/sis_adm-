from rest_framework import serializers
from .models import Reunion


class ReunionSerializer(serializers.ModelSerializer):
    asistentes_count = serializers.SerializerMethodField()
    faltas_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Reunion
        fields = ['id', 'fecha', 'tema', 'tipo', 'quorum', 'estado', 'acta_texto', 'acuerdos', 'documento_adjunto', 'created_at', 'updated_at', 'asistentes_count', 'faltas_count']
        read_only_fields = ['id', 'estado', 'created_at', 'updated_at', 'asistentes_count', 'faltas_count']
    
    def get_asistentes_count(self, obj):
        """Cuenta cuántos afiliados asistieron a la reunión"""
        return obj.asistencias.filter(estado='presente').count()
    
    def get_faltas_count(self, obj):
        """Cuenta cuántas faltas hubo en la reunión"""
        return obj.asistencias.filter(estado='falta').count()