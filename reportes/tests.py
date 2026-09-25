"""Tests para asistencia y reportes financieros."""
import pytest
from datetime import date

from tesoreria.models import Pago, Egreso, TipoPago
from afiliados.models import Afiliado


@pytest.fixture
def tipo_ingreso(db):
    return TipoPago.objects.create(
        nombre='Cuota Mensual Test', descripcion='Cuota', tipo='ingreso'
    )


@pytest.fixture
def tipo_egreso(db):
    return TipoPago.objects.create(
        nombre='Mantenimiento Test', descripcion='Mant.', tipo='egreso'
    )


@pytest.fixture
def afiliado(db):
    return Afiliado.objects.create(
        nombres='Juan Perez',
        apellidos='Prueba Uno',
        ci='12345678',
        fecha_ingreso=date(2026, 1, 1),
        estado='activo',
    )


@pytest.mark.django_db
def test_resumen_periodo_solo_transacciones_validas(afiliado, tipo_ingreso, tipo_egreso):
    from reportes.query_helpers import resumen_periodo

    Pago.objects.create(
        afiliado=afiliado, tipo_pago=tipo_ingreso,
        monto=100, fecha_pago=date(2026, 9, 1), estado='completado',
    )
    Pago.objects.create(
        afiliado=afiliado, tipo_pago=tipo_ingreso,
        monto=500, fecha_pago=date(2026, 9, 2), estado='anulado',
        motivo_anulacion='Error',
    )
    Egreso.objects.create(
        fecha=date(2026, 9, 3), monto=50, descripcion='Gasto valido',
        tipo_pago=tipo_egreso, estado='aprobado',
    )
    Egreso.objects.create(
        fecha=date(2026, 9, 4), monto=999, descripcion='Gasto anulado',
        tipo_pago=tipo_egreso, estado='anulado',
    )

    resumen = resumen_periodo()

    # Solo el pago completado y el egreso aprobado cuentan
    assert resumen['total_ingresos'] == 100.0
    assert resumen['total_egresos'] == 50.0
    assert resumen['saldo'] == 50.0
    assert resumen['count_ingresos'] == 1
    assert resumen['count_egresos'] == 1

    # Los anulados quedan explícitamente excluidos y reportados
    excluidos = resumen['anulados_cancelados']
    assert excluidos['count_ingresos'] == 1
    assert excluidos['monto_ingresos'] == 500.0
    assert excluidos['count_egresos'] == 1
    assert excluidos['monto_egresos'] == 999.0


@pytest.mark.django_db
def test_pagos_validos_ignora_cancelados(afiliado, tipo_ingreso):
    from reportes.query_helpers import pagos_validos, pagos_excluidos

    Pago.objects.create(
        afiliado=afiliado, tipo_pago=tipo_ingreso,
        monto=10, fecha_pago=date(2026, 9, 1), estado='completado',
    )
    Pago.objects.create(
        afiliado=afiliado, tipo_pago=tipo_ingreso,
        monto=20, fecha_pago=date(2026, 9, 2), estado='cancelado',
    )

    assert pagos_validos().count() == 1
    assert pagos_excluidos().count() == 1


@pytest.mark.django_db
def test_balance_endpoint_solo_transacciones_validas(authenticated_client, afiliado, tipo_ingreso, tipo_egreso):
    Pago.objects.create(
        afiliado=afiliado, tipo_pago=tipo_ingreso,
        monto=100, fecha_pago=date(2026, 9, 1), estado='completado',
    )
    Pago.objects.create(
        afiliado=afiliado, tipo_pago=tipo_ingreso,
        monto=700, fecha_pago=date(2026, 9, 2), estado='anulado',
    )
    Egreso.objects.create(
        fecha=date(2026, 9, 3), monto=40, descripcion='Gasto',
        tipo_pago=tipo_egreso, estado='aprobado',
    )

    response = authenticated_client.get('/api/reportes/balance')
    assert response.status_code == 200

    data = response.data
    assert data['total_ingresos'] == 100.0
    assert data['total_egresos'] == 40.0
    assert data['saldo'] == 60.0
    assert data['excluidos_por_estado']['count_ingresos'] == 1
    assert data['excluidos_por_estado']['monto_ingresos'] == 700.0


@pytest.mark.django_db
def test_transacciones_endpoint_resumen(authenticated_client, afiliado, tipo_ingreso):
    Pago.objects.create(
        afiliado=afiliado, tipo_pago=tipo_ingreso,
        monto=25, fecha_pago=date(2026, 9, 1), estado='completado',
    )
    Pago.objects.create(
        afiliado=afiliado, tipo_pago=tipo_ingreso,
        monto=60, fecha_pago=date(2026, 9, 2), estado='cancelado',
    )

    response = authenticated_client.get('/api/reportes/transacciones')
    assert response.status_code == 200

    data = response.data
    assert data['count'] == 1
    assert data['resumen']['total_ingresos'] == 25.0
    assert data['resumen']['count_ingresos'] == 1
    assert data['excluidos_por_estado']['ingresos']['count'] == 1