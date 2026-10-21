from datetime import date, timedelta
from decimal import Decimal

import pytest

from afiliados.models import Afiliado
from hojasruta.models import HojaRuta
from pagos_qr.models import QRTransaccion
from reservas.models import Reserva
from rutas.models import Ruta
from vehiculos.models import Vehiculo


@pytest.fixture(autouse=True)
def silenciar_whatsapp(monkeypatch):
    enviados = []

    monkeypatch.setattr(
        'whatsapp_notif.signals.whatsapp_service.send_from_template',
        lambda *args, **kwargs: None,
    )

    import whatsapp_notif.services as whatsapp_services

    monkeypatch.setattr(
        whatsapp_services.whatsapp_service,
        'send_message',
        lambda *args, **kwargs: enviados.append(kwargs) or None,
    )
    return enviados


@pytest.fixture
def ruta(db):
    return Ruta.objects.create(
        nombre='La Paz',
        origen='Taipiplaya',
        destino='La Paz',
        tarifa_base=Decimal('100.00'),
    )


@pytest.fixture
def afiliado(db):
    return Afiliado.objects.create(
        nombres='Juan',
        apellidos='Perez',
        ci='1234567',
        telefono='71234567',
        fecha_ingreso=date.today(),
    )


@pytest.fixture
def vehiculo(db, afiliado):
    return Vehiculo.objects.create(
        placa='ABC-1234',
        tipo='minibus',
        capacidad=6,
        afiliado=afiliado,
    )


@pytest.fixture
def hoja(db, ruta, afiliado, vehiculo):
    return HojaRuta.objects.create(
        nro='HR-TEST-001',
        fecha_emision=date.today(),
        fecha_salida=date.today() + timedelta(days=1),
        afiliado=afiliado,
        estado='emitida',
        precio=Decimal('100.00'),
        vehiculo=vehiculo,
        ruta=ruta,
    )


def payload(ruta, fecha, **extra):
    data = {
        'cliente': 'Pasajero Prueba',
        'telefono': '71234567',
        'ruta': ruta.id,
        'fecha_viaje': fecha.isoformat(),
    }
    data.update(extra)
    return data


@pytest.mark.django_db
class TestCreacionReservas:
    def test_crea_una_reserva_por_asiento_y_calcula_montos(self, api_client, hoja):
        fecha = hoja.fecha_salida
        response = api_client.post(
            '/api/reservas/',
            payload(hoja.ruta, fecha, asientos=[1, 2]),
            format='json',
        )

        assert response.status_code == 201
        assert len(response.data) == 2
        assert {r['asiento'] for r in response.data} == {1, 2}
        assert len({r['grupo_id'] for r in response.data}) == 1
        for item in response.data:
            assert item['estado'] == 'pendiente'
            assert item['monto_unitario'] == '100.00'
            assert item['monto_total'] == '100.00'

    def test_rechaza_asiento_ocupado_con_409(self, api_client, hoja):
        api_client.post('/api/reservas/', payload(hoja.ruta, hoja.fecha_salida, asientos=[3]), format='json')

        response = api_client.post(
            '/api/reservas/',
            payload(hoja.ruta, hoja.fecha_salida, asientos=[3]),
            format='json',
        )

        assert response.status_code == 409
        assert '3' in str(response.data)

    def test_rechaza_cuando_no_hay_hoja_de_ruta(self, api_client, ruta):
        response = api_client.post(
            '/api/reservas/',
            payload(ruta, date.today() + timedelta(days=30)),
            format='json',
        )

        assert response.status_code == 400
        assert 'hoja de ruta' in str(response.data).lower()

    def test_rechaza_capacidad_excedida(self, api_client, hoja):
        response = api_client.post(
            '/api/reservas/',
            payload(hoja.ruta, hoja.fecha_salida, asientos=[1, 2, 3, 4, 5, 6]),
            format='json',
        )
        assert response.status_code == 201

        response = api_client.post(
            '/api/reservas/',
            payload(hoja.ruta, hoja.fecha_salida, asientos=[1]),
            format='json',
        )
        assert response.status_code == 400
        assert 'cupos' in str(response.data).lower()


@pytest.mark.django_db
class TestPermisosReservas:
    def test_listado_exige_autenticacion(self, api_client):
        response = api_client.get('/api/reservas/')
        assert response.status_code in (401, 403)

    def test_listado_disponible_para_personal(self, authenticated_client):
        response = authenticated_client.get('/api/reservas/')
        assert response.status_code == 200

    def test_voucher_publico_no_expone_datos_privados(self, api_client, hoja):
        creada = api_client.post(
            '/api/reservas/',
            payload(hoja.ruta, hoja.fecha_salida, asientos=[1]),
            format='json',
        )
        reserva_id = creada.data[0]['id']

        response = api_client.get(f'/api/reservas/{reserva_id}/public-retrieve/')

        assert response.status_code == 200
        assert 'telefono' not in response.data
        assert 'afiliado_direccion' not in response.data


@pytest.mark.django_db
class TestGestionReservas:
    def test_no_permite_cambiar_fecha_de_reserva_activa(self, authenticated_client, hoja):
        creada = authenticated_client.post(
            '/api/reservas/',
            payload(hoja.ruta, hoja.fecha_salida, asientos=[1]),
            format='json',
        )
        reserva_id = creada.data[0]['id']

        response = authenticated_client.patch(
            f'/api/reservas/{reserva_id}/',
            {'fecha_viaje': (hoja.fecha_salida + timedelta(days=2)).isoformat()},
            format='json',
        )

        assert response.status_code == 400
        assert 'fecha' in str(response.data).lower()

    def test_cancelar_libera_el_asiento(self, api_client, authenticated_client, hoja):
        creada = api_client.post(
            '/api/reservas/',
            payload(hoja.ruta, hoja.fecha_salida, asientos=[4]),
            format='json',
        )
        reserva_id = creada.data[0]['id']

        response = authenticated_client.delete(f'/api/reservas/{reserva_id}/')
        assert response.status_code == 204

        reserva = Reserva.objects.get(id=reserva_id)
        assert reserva.estado == 'cancelada'
        assert reserva.fecha_anulacion is not None

        response = api_client.post(
            '/api/reservas/',
            payload(hoja.ruta, hoja.fecha_salida, asientos=[4]),
            format='json',
        )
        assert response.status_code == 201

    def test_update_no_permite_asiento_ocupado(self, api_client, authenticated_client, hoja):
        primera = api_client.post(
            '/api/reservas/',
            payload(hoja.ruta, hoja.fecha_salida, asientos=[1]),
            format='json',
        )
        segunda = api_client.post(
            '/api/reservas/',
            payload(hoja.ruta, hoja.fecha_salida, asientos=[2]),
            format='json',
        )

        response = authenticated_client.patch(
            f"/api/reservas/{segunda.data[0]['id']}/",
            {'asiento': primera.data[0]['asiento']},
            format='json',
        )

        assert response.status_code == 409

    def test_confirmar_reserva_pendiente(self, api_client, authenticated_client, hoja):
        creada = api_client.post(
            '/api/reservas/',
            payload(hoja.ruta, hoja.fecha_salida, asientos=[5]),
            format='json',
        )
        reserva_id = creada.data[0]['id']

        response = authenticated_client.post(f'/api/reservas/{reserva_id}/confirmar/')
        assert response.status_code == 200
        assert response.data['estado'] == 'confirmada'

        repetida = authenticated_client.post(f'/api/reservas/{reserva_id}/confirmar/')
        assert repetida.status_code == 400

    def test_cancelar_desde_accion_registra_motivo(self, api_client, authenticated_client, hoja):
        creada = api_client.post(
            '/api/reservas/',
            payload(hoja.ruta, hoja.fecha_salida, asientos=[6]),
            format='json',
        )
        reserva_id = creada.data[0]['id']

        response = authenticated_client.post(
            f'/api/reservas/{reserva_id}/cancelar/',
            {'motivo': 'Cliente desistió del viaje'},
            format='json',
        )

        assert response.status_code == 200
        assert response.data['estado'] == 'cancelada'
        assert response.data['motivo_anulacion'] == 'Cliente desistió del viaje'
        assert response.data['fecha_anulacion'] is not None


@pytest.mark.django_db
class TestPagoQrReservas:
    def test_genera_qr_grupal_y_confirma_todas_las_reservas(
        self, api_client, silenciar_whatsapp, hoja
    ):
        creadas = api_client.post(
            '/api/reservas/',
            payload(hoja.ruta, hoja.fecha_salida, asientos=[1, 2]),
            format='json',
        )
        ids = [r['id'] for r in creadas.data]

        response = api_client.post(
            f'/api/reservas/{ids[0]}/generar_pago_qr/',
            {'reservas': ids},
            format='json',
        )

        assert response.status_code == 200
        assert response.data['monto'] == 200.0
        assert response.data['cantidad_total'] == 2
        assert set(response.data['reserva_ids']) == set(ids)
        assert response.data['titular']

        qr = QRTransaccion.objects.get(transaction_id=response.data['transaction_id'])
        assert qr.estado == 'pendiente'
        assert qr.response_data['reserva_ids'] == ids

        silenciar_whatsapp.clear()
        verificacion = api_client.post(
            '/api/pagos-qr/transactions/verify-public/',
            {'transaction_id': response.data['transaction_id']},
            format='json',
        )

        assert verificacion.status_code == 200
        assert set(Reserva.objects.filter(id__in=ids).values_list('estado', flat=True)) == {
            'confirmada'
        }
        assert len(silenciar_whatsapp) == 1
        assert silenciar_whatsapp[0]['related_reservation_id'] == ids[0]

    def test_no_permite_qr_grupal_con_pasajeros_distintos(self, api_client, hoja):
        uno = api_client.post(
            '/api/reservas/',
            payload(hoja.ruta, hoja.fecha_salida, asientos=[1], cliente='Ana Uno'),
            format='json',
        )
        dos = api_client.post(
            '/api/reservas/',
            payload(hoja.ruta, hoja.fecha_salida, asientos=[2], cliente='Luis Dos'),
            format='json',
        )

        response = api_client.post(
            f"/api/reservas/{uno.data[0]['id']}/generar_pago_qr/",
            {'reservas': [uno.data[0]['id'], dos.data[0]['id']]},
            format='json',
        )

        assert response.status_code == 400
        assert 'mismo pasajero' in str(response.data).lower()
