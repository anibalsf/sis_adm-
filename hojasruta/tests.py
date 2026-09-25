"""Tests del módulo de reservas: datos de la movilidad asignada a La Paz.

El pasajero escanea el QR de la oficina y debe ver, tanto para IPSUM como para
MINIBÚS: nombre del afiliado, placa, color de la movilidad y hora de salida.
"""
from datetime import date, time, timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from afiliados.models import Afiliado
from hojasruta.models import HojaRuta, TurnoSalida
from rutas.models import Ruta
from vehiculos.models import Vehiculo


class MovilidadesLaPazTests(TestCase):
    """Vista pública que alimenta el QR de la oficina."""

    def setUp(self):
        self.client = APIClient()
        self.url = reverse('turnosalida-movilidades-lapaz-hoy')
        self.fecha = timezone.localdate()
        # La vista siempre toma la primera ruta "La Paz" existente (la del seed).
        self.ruta_la_paz = Ruta.objects.filter(destino__iexact='la paz').first() or Ruta.objects.create(
            nombre='La Paz',
            origen='Taipiplaya',
            destino='La Paz',
            tarifa_base=50,
        )
        self.ruta_caranavi = Ruta.objects.filter(destino__iexact='caranavi').first() or Ruta.objects.create(
            nombre='Caranavi',
            origen='Taipiplaya',
            destino='Caranavi',
            tarifa_base=40,
        )

    def _afiliado(self, ci, nombres='Juan', apellidos='Pérez'):
        return Afiliado.objects.create(
            nombres=nombres,
            apellidos=apellidos,
            ci=ci,
            telefono='70000000',
            fecha_ingreso=date(2026, 1, 1),
            estado='activo',
            is_active=True,
        )

    def _vehiculo(self, afiliado, placa, tipo, color, capacidad):
        return Vehiculo.objects.create(
            placa=placa,
            tipo=tipo,
            color=color,
            capacidad=capacidad,
            afiliado=afiliado,
            estado='activo',
        )

    def _hoja(self, afiliado, vehiculo, hora_salida, ruta=None):
        return HojaRuta.objects.create(
            fecha_emision=self.fecha,
            fecha_salida=self.fecha,
            hora_salida=hora_salida,
            afiliado=afiliado,
            vehiculo=vehiculo,
            ruta=ruta or self.ruta_la_paz,
            estado='emitida',
        )

    def test_datos_de_ipsum_y_minibus_para_la_paz(self):
        afiliado_ipsum = self._afiliado('1111111', 'Mario', 'Quispe')
        vehiculo_ipsum = self._vehiculo(afiliado_ipsum, '1234ABC', 'ipsum', 'Blanco', 6)
        self._hoja(afiliado_ipsum, vehiculo_ipsum, time(6, 30))

        afiliado_minibus = self._afiliado('2222222', 'Rosa', 'Chávez')
        vehiculo_minibus = self._vehiculo(afiliado_minibus, '5678DEF', 'minibus', 'Verde', 14)
        self._hoja(afiliado_minibus, vehiculo_minibus, time(7, 0))

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['found'])
        self.assertEqual(data['total'], 2)

        por_tipo = {m['tipo']: m for m in data['movilidades']}

        ipsum = por_tipo['ipsum']
        self.assertEqual(ipsum['nombre_completo'], 'Mario Quispe')
        self.assertEqual(ipsum['placa'], '1234ABC')
        self.assertEqual(ipsum['color'], 'Blanco')
        self.assertEqual(ipsum['hora_salida'], '06:30')

        minibus = por_tipo['minibus']
        self.assertEqual(minibus['nombre_completo'], 'Rosa Chávez')
        self.assertEqual(minibus['placa'], '5678DEF')
        self.assertEqual(minibus['color'], 'Verde')
        self.assertEqual(minibus['hora_salida'], '07:00')

    def test_primera_movilidad_en_turno_y_siguiente_habilitada(self):
        afiliado_ipsum = self._afiliado('1111111', 'Mario', 'Quispe')
        vehiculo_ipsum = self._vehiculo(afiliado_ipsum, '1234ABC', 'ipsum', 'Blanco', 6)
        self._hoja(afiliado_ipsum, vehiculo_ipsum, time(6, 30))

        afiliado_minibus = self._afiliado('2222222', 'Rosa', 'Chávez')
        vehiculo_minibus = self._vehiculo(afiliado_minibus, '5678DEF', 'minibus', 'Verde', 14)
        self._hoja(afiliado_minibus, vehiculo_minibus, time(7, 0))

        movilidades = self.client.get(self.url).json()['movilidades']
        habilitadas = [m for m in movilidades if m['habilitada']]

        self.assertEqual(len(habilitadas), 1)
        self.assertEqual(habilitadas[0]['placa'], '1234ABC')
        self.assertEqual([m['cupos_disponibles'] for m in movilidades], [6, 14])

    def test_consulta_otra_fecha(self):
        afiliado = self._afiliado('1111111')
        vehiculo = self._vehiculo(afiliado, '1234ABC', 'ipsum', 'Negro', 6)
        self._hoja(afiliado, vehiculo, time(6, 30))

        otra_fecha = self.fecha + timedelta(days=1)
        response = self.client.get(self.url, {'fecha': otra_fecha.isoformat()})

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['found'])
        self.assertEqual(response.json()['movilidades'], [])

    def test_fecha_invalida_devuelve_400(self):
        response = self.client.get(self.url, {'fecha': 'ayer'})
        self.assertEqual(response.status_code, 400)

    def test_ignora_otras_rutas(self):
        afiliado = self._afiliado('1111111')
        vehiculo = self._vehiculo(afiliado, '1234ABC', 'minibus', 'Azul', 14)
        self._hoja(afiliado, vehiculo, time(6, 30), ruta=self.ruta_caranavi)

        data = self.client.get(self.url).json()
        self.assertFalse(data['found'])

    def test_ignora_vehiculos_no_aptos_para_la_paz(self):
        afiliado = self._afiliado('1111111')
        taxi = self._vehiculo(afiliado, '1234ABC', 'taxi', 'Blanco', 4)
        self._hoja(afiliado, taxi, time(6, 30))

        self.assertFalse(self.client.get(self.url).json()['found'])

    def test_ignora_afiliados_inactivos(self):
        afiliado = self._afiliado('1111111')
        vehiculo = self._vehiculo(afiliado, '1234ABC', 'minibus', 'Verde', 14)
        self._hoja(afiliado, vehiculo, time(6, 30))
        afiliado.estado = 'inactivo'
        afiliado.save()

        self.assertFalse(self.client.get(self.url).json()['found'])

    def test_usa_turnos_programados_cuando_no_hay_hojas(self):
        afiliado = self._afiliado('1111111', 'Mario', 'Quispe')
        vehiculo = self._vehiculo(afiliado, '1234ABC', 'minibus', 'Plata', 14)
        TurnoSalida.objects.create(
            fecha=self.fecha,
            hora_salida=time(5, 45),
            afiliado=afiliado,
            ruta=self.ruta_la_paz,
            orden=1,
        )

        movilidades = self.client.get(self.url).json()['movilidades']
        self.assertEqual(len(movilidades), 1)
        self.assertEqual(movilidades[0]['placa'], '1234ABC')
        self.assertEqual(movilidades[0]['color'], 'Plata')
        self.assertEqual(movilidades[0]['hora_salida'], '05:45')
        self.assertEqual(movilidades[0]['tipo'], 'minibus')

    def test_sin_asignaciones_devuelve_found_false(self):
        data = self.client.get(self.url).json()
        self.assertFalse(data['found'])
        self.assertEqual(data['movilidades'], [])


class QrOficinaLaPazTests(TestCase):
    """El QR de la oficina se descarga sin autenticación."""

    def setUp(self):
        self.client = APIClient()
        self.url = reverse('turnosalida-qr-lapaz')

    def test_qr_publico_devuelve_imagen_png(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'image/png')
        self.assertTrue(response.content.startswith(b'\x89PNG'))
