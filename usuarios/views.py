from rest_framework.views import APIView
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User, Group
from django.contrib.auth import login, logout, update_session_auth_hash
from .serializers import RegisterSerializer, LoginSerializer, UserSerializer, UserCreateSerializer, ChangePasswordSerializer
from rest_framework.permissions import BasePermission
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
import uuid
import random


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        group, _ = Group.objects.get_or_create(name='Afiliado')
        user.groups.add(group)
        token, _ = Token.objects.get_or_create(user=user)
        return Response({'token': token.key, 'user': UserSerializer(user).data}, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [] # Desactivar throttling de DRF para permitir login siempre (manejamos bloqueos internos)

    def post(self, request):
        username = (request.data.get('username') or '').strip()
        # Captcha disabled as per user request
        
        ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
        cache_key = f'login_attempts:{username}:{ip}'
        info = cache.get(cache_key) or {'count': 0, 'blocked_until': None}
        now = timezone.now()
        if info.get('blocked_until') and now < info['blocked_until']:
            remaining = int((info['blocked_until'] - now).total_seconds() // 60) + 1
            return Response(
                {'detail': f'Demasiados intentos. Intenta nuevamente en {remaining} minutos.'},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        try:
            serializer = LoginSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
        except Exception:
            info['count'] = int(info.get('count', 0)) + 1
            if info['count'] >= 5:
                info['blocked_until'] = now + timedelta(minutes=15)
                info['count'] = 0
            cache.set(cache_key, info, timeout=60 * 60)
            raise
        user = serializer.validated_data['user']
        if not user.is_active:
            return Response({'detail': 'Usuario inactivo'}, status=status.HTTP_403_FORBIDDEN)
        
        # Generar JWT tokens
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        
        login(request, user)
        remember = bool(request.data.get('remember'))
        request.session.set_expiry(1209600 if remember else 0)
        cache.delete(cache_key)
        
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data,
            'remember': remember
        })


class CaptchaView(APIView):
    permission_classes = [permissions.AllowAny]
    def get(self, request):
        a = random.randint(1, 9)
        b = random.randint(1, 9)
        total = a + b
        cid = uuid.uuid4().hex
        cache.set(f'captcha:{cid}', total, timeout=300)
        return Response({'id': cid, 'pregunta': f'{a} + {b} = ?'})


class MeView(APIView):
    def get(self, request):
        return Response(UserSerializer(request.user).data)


class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            update_session_auth_hash(request, user)  # Mantener la sesión activa
            return Response({"detail": "Contraseña actualizada correctamente."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    def post(self, request):
        try:
            # Blacklist el refresh token si se proporciona
            refresh_token = request.data.get('refresh')
            if refresh_token:
                from rest_framework_simplejwt.tokens import RefreshToken
                token = RefreshToken(refresh_token)
                token.blacklist()
        except Exception as e:
            # Si hay error al blacklistear, continuar con logout normal
            pass
        
        # Eliminar token estático (compatibilidad)
        Token.objects.filter(user=request.user).delete()
        logout(request)
        return Response({'detail': 'Sesión cerrada'})


class IsDirectiva(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return user.groups.filter(name='Directiva').exists()


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('username')
    serializer_class = UserSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['username', 'first_name', 'last_name', 'email']
    ordering_fields = ['date_joined', 'username']

    class IsDirectivaOrSistemas(BasePermission):
        def has_permission(self, request, view):
            user = request.user
            if not user or not user.is_authenticated:
                return False
            # Permitir a Directiva y Sistemas (o superuser)
            return user.is_superuser or user.groups.filter(name__in=['Directiva', 'Sistemas']).exists()

    permission_classes = [IsDirectivaOrSistemas]

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer

    @action(detail=True, methods=['post'])
    def reset_password(self, request, pk=None):
        user = self.get_object()
        new_password = request.data.get('new_password')
        if not new_password:
            return Response({'detail': 'Nueva contraseña requerida'}, status=400)
        
        user.set_password(new_password)
        user.save()
        return Response({'detail': f'Contraseña de @{user.username} restablecida con éxito'})

    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        user = self.get_object()
        # No permitir desactivarse a sí mismo
        if user.id == request.user.id:
            return Response({'detail': 'No puedes desactivar tu propia cuenta'}, status=400)
        
        user.is_active = not user.is_active
        user.save()
        return Response({'detail': f'Usuario {"activado" if user.is_active else "desactivado"}'})

    @action(detail=True, methods=['post'])
    def assign_role(self, request, pk=None):
        user = self.get_object()
        role = request.data.get('role')
        if not role:
            return Response({'detail': 'Rol requerido'}, status=400)
        
        # Limpiar grupos anteriores (opcional, dependiendo de si un usuario puede tener múltiples roles)
        # En este sistema parece que es un rol principal
        user.groups.clear()
        
        group, _ = Group.objects.get_or_create(name=role)
        user.groups.add(group)
        
        return Response({'detail': f'Rol {role} asignado'})
