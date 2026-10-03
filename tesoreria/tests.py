"""Tests del módulo de tesorería (pagos y egresos)."""
from datetime import date

import pytest

from tesoreria.models import Egreso, Pago, TipoPago
from afiliados.models import Afiliado


@pytest.fixture
def tipo_egreso(db):
    return TipoPago.objects.create(
        nombre='Mantenimiento Test', descripcion='Mant.', tipo='egreso'
    )


@pytest.fixture
def tipo_ingreso(db):
    return TipoPago.objects.create(
        nombre='Cuota Test', descripcion='Cuota', tipo='ingreso'
    )


@pytest.fixture
def afiliado(db):
    return Afiliado.objects.create(
        nombres='Juan', apellidos='Perez Prueba',
        ci='12345678', fecha_ingreso=date(2026, 1, 1), estado='activo',
    )


def _egreso(tipo_pago, monto, estado='aprobado', descripcion='Gasto'):
    return Egreso.objects.create(
        fecha=date(2026, 9, 1), monto=monto,
        descripcion=descripcion, tipo_pago=tipo_pago, estado=estado,
    )


@pytest.mark.django_db
def test_listado_egresos_devuelve_total_de_todos_los_registros(
    authenticated_client, tipo_egreso
):
    """El total debe sumar TODOS los egresos, no solo la página visible."""
    for _ in range(12):
        _egreso(tipo_egreso, 100)
    _egreso(tipo_egreso, 250, estado='pendiente_aprobacion')
    _egreso(tipo_egreso, 50, estado='anulado')

    response = authenticated_client.get('/api/egresos/?page=1&page_size=10')

    assert response.status_code == 200
    assert response.data['count'] == 14
    # Solo 10 filas en la página, pero el total cubre los 14 registros.
    assert len(response.data['results']) == 10

    totales = response.data['totales']
    assert totales['total_monto'] == 1500.0
    assert totales['total_aprobado'] == 1200.0
    assert totales['total_pendiente_aprobacion'] == 250.0
    assert totales['total_anulado'] == 50.0


@pytest.mark.django_db
def test_totales_egresos_en_0_si_no_hay_registros(authenticated_client, tipo_egreso):
    response = authenticated_client.get('/api/egresos/')

    assert response.status_code == 200
    assert response.data['count'] == 0
    assert response.data['totales']['total_monto'] == 0.0


@pytest.mark.django_db
def test_listado_pagos_no_rompe_la_paginacion(authenticated_client, afiliado, tipo_ingreso):
    for _ in range(3):
        Pago.objects.create(
            afiliado=afiliado, tipo_pago=tipo_ingreso,
            monto=50, fecha_pago=date(2026, 9, 1), estado='completado',
        )

    response = authenticated_client.get('/api/pagos/')

    assert response.status_code == 200
    assert response.data['count'] == 3
    assert len(response.data['results']) == 3