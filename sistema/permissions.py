from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsSecretariaOrDirectivaOrReadOnly(BasePermission):
    """
    Permite lectura a todos (o solo autenticados si se combina con IsAuthenticated).
    Permite escritura a 'Secretaria', 'Directiva' y 'Sistemas'.
    """
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if getattr(user, 'is_superuser', False) or getattr(user, 'is_staff', False):
            return True
        return user.groups.filter(name__in=['Secretaria', 'Sistemas', 'Directiva']).exists()

class IsDirectivaOrSistemas(BasePermission):
    """
    Solo permite acceso a 'Directiva' y 'Sistemas'.
    """
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if getattr(user, 'is_superuser', False):
            return True
        return user.groups.filter(name__in=['Directiva', 'Sistemas']).exists()
