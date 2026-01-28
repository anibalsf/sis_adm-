# ==============================================================================
# CONFTEST.PY - Configuración de tests para pytest
# ==============================================================================

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture
def api_client():
    """Cliente de API para tests."""
    return APIClient()


@pytest.fixture
def user(db):
    """Usuario de prueba."""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )


@pytest.fixture
def authenticated_client(api_client, user):
    """Cliente autenticado para tests."""
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def admin_user(db):
    """Usuario administrador de prueba."""
    return User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='admin123'
    )
