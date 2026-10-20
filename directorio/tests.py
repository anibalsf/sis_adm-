from django.test import TestCase
from datetime import date
from dateutil.relativedelta import relativedelta
from afiliados.models import Afiliado
from directorio.models import MiembroDirectorio
from directorio.serializers import MiembroDirectorioSerializer
from directorio.services import cambio_gestion


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


class VigenciaDirectorioTests(TestCase):
    def setUp(self):
        self.afiliado = Afiliado.objects.create(
            nombres='Ana', apellidos='Quispe', ci='CI100', fecha_ingreso=date.today()
        )

    def test_vigencia_hasta_es_un_anio(self):
        m = MiembroDirectorio.objects.create(
            afiliado=self.afiliado, cargo='secretario_general',
            fecha_inicio=date(2024, 3, 15), estado='activo',
        )
        self.assertEqual(m.vigencia_hasta, date(2025, 3, 15))

    def test_esta_vencido(self):
        vencido = MiembroDirectorio(
            afiliado=self.afiliado, cargo='vocal',
            fecha_inicio=date.today() - relativedelta(years=2), estado='activo',
        )
        vigente = MiembroDirectorio(
            afiliado=self.afiliado, cargo='vocal',
            fecha_inicio=date.today(), estado='activo',
        )
        self.assertTrue(vencido.esta_vencido)
        self.assertFalse(vigente.esta_vencido)

    def test_concluir_vencidos_marca_concluido(self):
        m = MiembroDirectorio.objects.create(
            afiliado=self.afiliado, cargo='secretario_general',
            fecha_inicio=date.today() - relativedelta(years=2), estado='activo',
        )
        cerrados = MiembroDirectorio.concluir_vencidos()
        m.refresh_from_db()
        self.assertEqual(len(cerrados), 1)
        self.assertEqual(m.estado, 'concluido')
        self.assertEqual(m.fecha_fin, m.vigencia_hasta)

    def test_directorio_vigente_excluye_vencidos(self):
        MiembroDirectorio.objects.create(
            afiliado=self.afiliado, cargo='secretario_general',
            fecha_inicio=date.today() - relativedelta(years=2), estado='activo',
        )
        self.assertEqual(MiembroDirectorio.directorio_vigente().count(), 0)


class CambioGestionTests(TestCase):
    def setUp(self):
        self.saliente = Afiliado.objects.create(
            nombres='Luis', apellidos='Rojas', ci='CI200', fecha_ingreso=date.today()
        )
        self.entrante = Afiliado.objects.create(
            nombres='Carla', apellidos='Mamani', ci='CI201', fecha_ingreso=date.today()
        )
        MiembroDirectorio.objects.create(
            afiliado=self.saliente, cargo='secretario_general',
            fecha_inicio=date.today() - relativedelta(years=2), estado='activo',
        )

    def test_cambio_gestion_concluye_y_crea(self):
        resultado = cambio_gestion(
            [{'afiliado': self.entrante.id, 'cargo': 'secretario_general'}],
        )
        self.assertEqual(len(resultado['saliente']), 1)
        self.assertEqual(resultado['saliente'][0].estado, 'concluido')
        self.assertIsNotNone(resultado['saliente'][0].fecha_fin)
        self.assertEqual(len(resultado['entrante']), 1)
        self.assertEqual(resultado['entrante'][0].estado, 'activo')
        self.assertEqual(MiembroDirectorio.directorio_vigente().count(), 1)

    def test_cambio_gestion_rechaza_cargos_duplicados(self):
        with self.assertRaises(ValueError):
            cambio_gestion([
                {'afiliado': self.entrante.id, 'cargo': 'vocal'},
                {'afiliado': self.saliente.id, 'cargo': 'vocal'},
            ])

    def test_cambio_gestion_rechaza_lista_vacia(self):
        with self.assertRaises(ValueError):
            cambio_gestion([])

    def test_nro_recibo_continua_tras_cambio_gestion(self):
        from tesoreria.models import Pago, TipoPago
        tipo = TipoPago.objects.create(nombre='Cuota Test', tipo='ingreso')
        primer = Pago.objects.create(
            afiliado=self.saliente, tipo_pago=tipo, monto=10, fecha_pago=date.today()
        )
        self.assertEqual(primer.nro_recibo, 1)

        cambio_gestion([{'afiliado': self.entrante.id, 'cargo': 'secretario_general'}])

        segundo = Pago.objects.create(
            afiliado=self.entrante, tipo_pago=tipo, monto=10, fecha_pago=date.today()
        )
        self.assertEqual(segundo.nro_recibo, 2)


class DirectorioAPITests(TestCase):
    def setUp(self):
        from django.contrib.auth.models import User
        from rest_framework.test import APIClient
        self.client = APIClient()
        self.user = User.objects.create_superuser('jefe', 'jefe@x.com', 'pw')
        self.client.force_authenticate(user=self.user)
        self.afiliado = Afiliado.objects.create(
            nombres='Ana', apellidos='Quispe', ci='CI300', fecha_ingreso=date.today()
        )

    def test_endpoint_vigente(self):
        MiembroDirectorio.objects.create(
            afiliado=self.afiliado, cargo='secretario_general',
            fecha_inicio=date.today(), estado='activo',
        )
        resp = self.client.get('/api/directorio/vigente/')
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.json()['vencida'])
        self.assertEqual(len(resp.json()['miembros']), 1)

    def test_endpoint_cambio_gestion(self):
        MiembroDirectorio.objects.create(
            afiliado=self.afiliado, cargo='secretario_general',
            fecha_inicio=date.today() - relativedelta(years=2), estado='activo',
        )
        otro = Afiliado.objects.create(
            nombres='Carla', apellidos='Mamani', ci='CI301', fecha_ingreso=date.today()
        )
        resp = self.client.post(
            '/api/directorio/cambio_gestion/',
            data={'miembros': [{'afiliado': otro.id, 'cargo': 'secretario_general'}]},
            format='json',
        )
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(MiembroDirectorio.directorio_vigente().count(), 1)
