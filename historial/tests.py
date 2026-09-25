from django.contrib.auth.models import Group, User
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from django.test import TestCase

from tesoreria.models import Egreso, TipoPago
from historial.models import LogAuditoria
from historial.signals import get_modelos_auditados


class BitacoraCoberturaTests(TestCase):
    """La bitácora debe registrar los cambios de todos los módulos, no solo de 6 modelos."""

    def setUp(self):
        self.tipo_pago = TipoPago.objects.create(nombre='Prueba', tipo='egreso')

    def _crear_egreso(self, **kwargs):
        datos = {'fecha': '2026-09-25', 'monto': 100, 'descripcion': 'Prueba', 'estado': 'aprobado'}
        datos.update(kwargs)
        return Egreso.objects.create(tipo_pago=self.tipo_pago, **datos)

    def test_se_auditan_todos_los_modulos_de_negocio(self):
        app_labels = {m._meta.app_label for m in get_modelos_auditados()}
        esperados = {
            'afiliados', 'asistencias', 'auth', 'cuotas', 'directorio', 'encomiendas',
            'hojasruta', 'pagos_qr', 'reservas', 'reuniones', 'rutas', 'sanciones',
            'tesoreria', 'vehiculos',
        }
        self.assertTrue(
            esperados.issubset(app_labels),
            f'Faltan módulos auditados: {esperados - app_labels}',
        )

    def test_no_se_audita_a_si_mismo(self):
        self.assertNotIn('historial', {m._meta.app_label for m in get_modelos_auditados()})

    def test_registra_creacion_y_edicion_con_detalle_de_campos(self):
        egreso = self._crear_egreso()

        log = LogAuditoria.objects.filter(tabla='egreso', objeto_id=str(egreso.pk)).first()
        self.assertIsNotNone(log, 'No se registró la creación del egreso')
        self.assertEqual(log.accion, 'crear')
        self.assertEqual(log.app_label, 'tesoreria')

        egreso.monto = 250
        egreso.save()

        edicion = (
            LogAuditoria.objects.filter(tabla='egreso', objeto_id=str(egreso.pk), accion='editar')
            .order_by('-fecha_hora')
            .first()
        )
        self.assertIsNotNone(edicion)
        self.assertIn('monto', edicion.cambios)
        self.assertEqual(edicion.cambios['monto']['antes'], '100.00')
        self.assertEqual(edicion.cambios['monto']['despues'], '250')
        self.assertEqual(edicion.cambios_labels.get('monto'), Egreso._meta.get_field('monto').verbose_name)

    def test_registra_eliminacion(self):
        egreso = self._crear_egreso(monto=50, descripcion='Temporal')
        pk = egreso.pk
        egreso.delete()

        log = LogAuditoria.objects.filter(tabla='egreso', objeto_id=str(pk), accion='eliminar').first()
        self.assertIsNotNone(log)
        self.assertEqual(log.app_label, 'tesoreria')

    def test_ignora_guardados_sin_cambios_reales(self):
        egreso = self._crear_egreso(monto=75, descripcion='Sin cambios')
        egreso.save()

        ediciones = LogAuditoria.objects.filter(tabla='egreso', objeto_id=str(egreso.pk), accion='editar')
        self.assertEqual(ediciones.count(), 0, 'Un guardado idéntico no debe generar un registro de edición')

    def test_no_escribe_el_hash_de_la_contrasena(self):
        usuario = User.objects.create_user(username='prueba_pass', password='secreto123')
        LogAuditoria.objects.all().delete()

        usuario.set_password('otro-secreto')
        usuario.save()

        log = LogAuditoria.objects.filter(tabla='user', accion='editar').order_by('-fecha_hora').first()
        self.assertIsNotNone(log, 'El cambio de contraseña debe quedar registrado')
        self.assertEqual(log.cambios['password']['despues'], '(oculto)')
        self.assertNotIn('secreto', str(log.cambios))
        self.assertNotIn('otro-secreto', str(log.cambios))

    def test_registra_cambio_de_estado_en_modelos_sin_registro_manual(self):
        egreso = self._crear_egreso(estado='pendiente_aprobacion')
        egreso.estado = 'aprobado'
        egreso.save()

        cambios = LogAuditoria.objects.filter(
            tabla='egreso', objeto_id=str(egreso.pk), accion='editar'
        ).first()
        self.assertIn('estado', cambios.cambios)
        self.assertEqual(cambios.cambios['estado']['antes'], 'pendiente_aprobacion')
        self.assertEqual(cambios.cambios['estado']['despues'], 'aprobado')


class BitacoraApiTests(APITestCase):
    def setUp(self):
        self.usuario = User.objects.create_user(username='auditor', password='x')
        grupo, _ = Group.objects.get_or_create(name='Directiva')
        self.usuario.groups.add(grupo)
        token = RefreshToken.for_user(self.usuario)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')

    def test_responde_json_en_ruta_con_y_sin_slash(self):
        for url in ('/api/bitacora', '/api/bitacora/'):
            with self.subTest(url=url):
                respuesta = self.client.get(url)
                self.assertEqual(respuesta.status_code, 200)
                self.assertIn('results', respuesta.json())
                self.assertIn('modulos', respuesta.json())
                self.assertIn('resumen', respuesta.json())

    def test_registra_el_usuario_que_hace_el_cambio(self):
        tipo_pago = TipoPago.objects.create(nombre='Efectivo', tipo='egreso')
        self.client.post(
            '/api/egresos/',
            {'fecha': '2026-09-25', 'monto': 30, 'descripcion': 'Prueba API', 'tipo_pago': tipo_pago.id},
            format='json',
        )

        log = LogAuditoria.objects.filter(tabla='egreso', accion='crear').order_by('-fecha_hora').first()
        self.assertIsNotNone(log)
        self.assertEqual(log.usuario, self.usuario, 'La bitácora debe atribuir el cambio al usuario autenticado')
        self.assertIsNotNone(log.ip_address, 'Debe registrar la IP del cliente')

    def test_filtra_por_modulo_accion_y_busqueda(self):
        tipo_pago = TipoPago.objects.create(nombre='Efectivo', tipo='egreso')
        egreso = Egreso.objects.create(
            fecha='2026-09-25', monto=10, descripcion='Filtro unico xyz', tipo_pago=tipo_pago
        )

        datos = self.client.get('/api/bitacora/', {'modulo': 'tesoreria', 'accion': 'crear'}).json()
        self.assertGreaterEqual(datos['count'], 1)
        self.assertTrue(all(r['app_label'] == 'tesoreria' for r in datos['results']))

        encontrados = self.client.get('/api/bitacora/', {'q': 'xyz'}).json()
        self.assertEqual(encontrados['count'], 1)
        self.assertEqual(encontrados['results'][0]['objeto_id'], str(egreso.pk))

    def test_lista_de_modulos_sale_de_los_datos(self):
        TipoPago.objects.create(nombre='Efectivo', tipo='egreso')
        Egreso.objects.create(fecha='2026-09-25', monto=1, descripcion='X', tipo_pago=TipoPago.objects.first())

        modulos = self.client.get('/api/bitacora/').json()['modulos']
        self.assertIn('tesoreria', [m['app_label'] for m in modulos])
        self.assertEqual(next(m for m in modulos if m['app_label'] == 'tesoreria')['nombre'], 'Tesorería')

    def test_requiere_autenticacion(self):
        self.client.credentials()
        self.assertEqual(self.client.get('/api/bitacora/').status_code, 401)
