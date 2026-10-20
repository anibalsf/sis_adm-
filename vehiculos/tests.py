from django.test import TestCase
from datetime import date
from afiliados.models import Afiliado
from vehiculos.models import Vehiculo
from vehiculos.serializers import VehiculoSerializer


class VehiculoSerializerTests(TestCase):
    def setUp(self):
        self.afiliado = Afiliado.objects.create(
            nombres='Juan',
            apellidos='Perez',
            ci='1234567',
            fecha_ingreso=date.today(),
        )

    def test_capacidad_debe_ser_mayor_a_cero(self):
        data = {
            'placa': 'ABC123',
            'tipo': 'Minibus',
            'capacidad': 0,
            'afiliado': self.afiliado.id,
            'estado': 'activo',
        }
        s = VehiculoSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn('capacidad', s.errors)

    def test_estado_invalido(self):
        data = {
            'placa': 'DEF456',
            'tipo': 'Bus',
            'capacidad': 30,
            'afiliado': self.afiliado.id,
            'estado': 'mantenimiento',
        }
        s = VehiculoSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn('estado', s.errors)

    def test_placa_unica(self):
        Vehiculo.objects.create(
            placa='GHI789',
            tipo='Minibus',
            capacidad=15,
            afiliado=self.afiliado,
            estado='activo',
        )
        data = {
            'placa': 'GHI789',
            'tipo': 'Minibus',
            'capacidad': 15,
            'afiliado': self.afiliado.id,
            'estado': 'activo',
        }
        s = VehiculoSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn('placa', s.errors)

    def test_tipo_invalido(self):
        data = {
            'placa': 'JKL000',
            'tipo': 'camioneta',
            'capacidad': 12,
            'afiliado': self.afiliado.id,
            'estado': 'activo',
        }
        s = VehiculoSerializer(data=data)
        self.assertTrue(s.is_valid())
    def test_tipo_permitido_micro(self):
        data = {
            'placa': 'MIC001',
            'tipo': 'micro',
            'capacidad': 20,
            'afiliado': self.afiliado.id,
            'estado': 'activo',
        }
        s = VehiculoSerializer(data=data)
        self.assertTrue(s.is_valid())


class VehiculoIndocumentadoTests(TestCase):
    def setUp(self):
        self.afiliado = Afiliado.objects.create(
            nombres='Ana', apellidos='Mamani', ci='9988776', fecha_ingreso=date.today()
        )

    def test_placa_requerida_si_no_indocumentado(self):
        s = VehiculoSerializer(data={
            'placa': '', 'tipo': 'minibus', 'capacidad': 15,
            'afiliado': self.afiliado.id, 'estado': 'activo', 'indocumentado': False,
        })
        self.assertFalse(s.is_valid())
        self.assertIn('placa', s.errors)

    def test_indocumentado_sin_placa_genera_referencia(self):
        s = VehiculoSerializer(data={
            'placa': '', 'tipo': 'ipsum', 'capacidad': 15,
            'afiliado': self.afiliado.id, 'estado': 'activo', 'indocumentado': True,
        })
        self.assertTrue(s.is_valid(), s.errors)
        obj = s.save()
        self.assertTrue(obj.indocumentado)
        self.assertTrue(obj.placa.startswith('S/P'))

    def test_dos_indocumentados_placas_distintas(self):
        s1 = VehiculoSerializer(data={
            'placa': '', 'tipo': 'ipsum', 'capacidad': 15,
            'afiliado': self.afiliado.id, 'estado': 'activo', 'indocumentado': True,
        })
        s1.is_valid(); v1 = s1.save()
        s2 = VehiculoSerializer(data={
            'placa': '', 'tipo': 'minibus', 'capacidad': 12,
            'afiliado': self.afiliado.id, 'estado': 'activo', 'indocumentado': True,
        })
        s2.is_valid(); v2 = s2.save()
        self.assertNotEqual(v1.placa, v2.placa)

    def test_convenio_caranavi_se_guarda(self):
        s = VehiculoSerializer(data={
            'placa': '1234XYZ', 'tipo': 'ipsum', 'capacidad': 15,
            'afiliado': self.afiliado.id, 'estado': 'activo', 'es_convenio_caranavi': True,
        })
        self.assertTrue(s.is_valid(), s.errors)
        self.assertTrue(s.save().es_convenio_caranavi)


class VehiculoAPITests(TestCase):
    def setUp(self):
        from django.contrib.auth.models import User
        from rest_framework.test import APIClient
        self.client = APIClient()
        self.user = User.objects.create_superuser('jefe2', 'jefe2@x.com', 'pw')
        self.client.force_authenticate(user=self.user)
        self.afiliado = Afiliado.objects.create(
            nombres='Luis', apellidos='Rojas', ci='5566778', fecha_ingreso=date.today()
        )

    def test_crear_indocumentado_sin_placa(self):
        resp = self.client.post('/api/vehiculos/', data={
            'placa': '', 'tipo': 'ipsum', 'capacidad': 15,
            'afiliado': self.afiliado.id, 'estado': 'activo', 'indocumentado': True,
        }, format='json')
        self.assertEqual(resp.status_code, 201, resp.content)
        self.assertTrue(resp.json()['indocumentado'])
        self.assertTrue(resp.json()['placa'].startswith('S/P'))


