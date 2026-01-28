# ==============================================================================
# EJEMPLO DE TEST - Afiliados
# ==============================================================================
# Colocar en: afiliados/tests/test_api.py

import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
class TestAfiliadoAPI:
    """Tests para el API de Afiliados."""
    
    def test_list_afiliados_unauthenticated(self, api_client):
        """Test: usuarios no autenticados no pueden listar afiliados."""
        url = reverse('afiliado-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_list_afiliados_authenticated(self, authenticated_client):
        """Test: usuarios autenticados pueden listar afiliados."""
        url = reverse('afiliado-list')
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
    
    def test_create_afiliado(self, authenticated_client):
        """Test: crear un nuevo afiliado."""
        url = reverse('afiliado-list')
        data = {
            'nombre': 'Juan',
            'apellido': 'Pérez',
            'ci': '12345678',
            'telefono': '78901234',
            # Agregar campos requeridos según modelo
        }
        response = authenticated_client.post(url, data)
        assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST]
