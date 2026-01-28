from django.test import TestCase
from datetime import date
from afiliados.models import Afiliado
from directorio.models import MiembroDirectorio
from directorio.serializers import MiembroDirectorioSerializer


class MiembroDirectorioSerializerTests(TestCase):
    def setUp(self):
        self.afiliado = Afiliado.objects.create(
            nombres='Maria',
            apellidos='Lopez',
            ci='CI001',
            fecha_ingreso=date.today(),
        )

    def test_cargo_invalido(self):
        data = {
            'afiliado': self.afiliado.id,
            'cargo': 'tesorero',
            'fecha_inicio': date(2024,1,1),
            'estado': 'activo',
        }
        s = MiembroDirectorioSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn('cargo', s.errors)

    def test_unico_activo_por_cargo(self):
        MiembroDirectorio.objects.create(
            afiliado=self.afiliado,
            cargo='secretario_general',
            fecha_inicio=date(2024,1,1),
            estado='activo',
        )
        otro = Afiliado.objects.create(
            nombres='Pedro', apellidos='Gomez', ci='CI002', fecha_ingreso=date.today()
        )
        data = {
            'afiliado': otro.id,
            'cargo': 'secretario_general',
            'fecha_inicio': date(2024,2,1),
            'estado': 'activo',
        }
        s = MiembroDirectorioSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn('cargo', s.errors)

    def test_fecha_fin_no_antes_de_inicio(self):
        data = {
            'afiliado': self.afiliado.id,
            'cargo': 'vocal',
            'fecha_inicio': date(2024,1,10),
            'fecha_fin': date(2024,1,5),
            'estado': 'concluido',
        }
        s = MiembroDirectorioSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn('fecha_fin', s.errors)