from rest_framework import serializers
from .models import Notificacion, AlertaSistema

class NotificacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notificacion
        fields = '__all__'

class AlertaSistemaSerializer(serializers.ModelSerializer):
    class Meta:
        model = AlertaSistema
        fields = '__all__'
