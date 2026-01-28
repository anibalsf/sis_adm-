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
