from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'role']

    def get_role(self, obj):
        group = obj.groups.first()
        return group.name if group else 'N/A'


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    email = serializers.EmailField(required=False)
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)
    nombres = serializers.CharField(required=True)
    apellidos = serializers.CharField(required=True)
    ci = serializers.CharField(required=True)
    telefono = serializers.CharField(required=False)
    fecha_ingreso = serializers.DateField(required=True)

    def create(self, validated_data):
        from afiliados.models import Afiliado
        user = User.objects.create_user(
            username=validated_data.get('username'),
            password=validated_data.get('password'),
            email=validated_data.get('email', ''),
            first_name=validated_data.get('first_name') or validated_data.get('nombres', ''),
            last_name=validated_data.get('last_name') or validated_data.get('apellidos', ''),
        )
        Afiliado.objects.create(
            user=user,
            nombres=validated_data.get('nombres'),
            apellidos=validated_data.get('apellidos'),
            ci=validated_data.get('ci'),
            telefono=validated_data.get('telefono', ''),
            email=validated_data.get('email', ''),
            estado='activo',
            fecha_ingreso=validated_data.get('fecha_ingreso'),
            is_active=True,
        )
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(username=attrs.get('username'), password=attrs.get('password'))
        if not user:
            raise serializers.ValidationError('Credenciales inválidas')
        attrs['user'] = user
        return attrs


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    role = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['username', 'password', 'email', 'first_name', 'last_name', 'role']

    def create(self, validated_data):
        role = validated_data.pop('role')
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        
        from django.contrib.auth.models import Group
        group, _ = Group.objects.get_or_create(name=role)
        user.groups.add(group)
        return user


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("La contraseña actual es incorrecta.")
        return value