from rest_framework import serializers
from .models import QRTransaccion

class QRTransaccionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QRTransaccion
        fields = ['id', 'transaction_id', 'monto', 'glosa', 'estado', 'qr_string', 'imagen_base64', 'expiration_date', 'created_at']
        read_only_fields = ['id', 'transaction_id', 'qr_string', 'imagen_base64', 'estado', 'created_at']

class QRGenerationSerializer(serializers.Serializer):
    monto = serializers.DecimalField(max_digits=10, decimal_places=2)
    glosa = serializers.CharField(max_length=255)
    valid_hours = serializers.IntegerField(default=24, min_value=1)
