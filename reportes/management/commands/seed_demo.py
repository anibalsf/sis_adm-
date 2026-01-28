from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from afiliados.models import Afiliado
from vehiculos.models import Vehiculo
from rutas.models import Ruta
from hojasruta.models import HojaRuta
from cuotas.models import Cuota
from reservas.models import Reserva
from reuniones.models import Reunion
from asistencias.models import Asistencia
from datetime import date


class Command(BaseCommand):
    help = 'Crea datos de demostración para el Dashboard y módulos.'

    def handle(self, *args, **options):
                sec_group, _ = Group.objects.get_or_create(name='Secretaria')
                sis_group, _ = Group.objects.get_or_create(name='Sistemas')
                dir_group, _ = Group.objects.get_or_create(name='Directiva')
                afi_group, _ = Group.objects.get_or_create(name='Afiliado')

        admin_user, _ = User.objects.get_or_create(username='admin_demo', defaults={'email': 'admin@demo.local'})
        admin_user.set_password('Admin123!')
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.save()
                admin_user.groups.add(dir_group)
                admin_user.groups.add(sis_group)

        sec_user, _ = User.objects.get_or_create(username='secretaria_demo', defaults={'email': 'secretaria@demo.local'})
        sec_user.set_password('Secret123!')
        sec_user.save()
        sec_user.groups.add(sec_group)

        afiliados = []
        base = [
            ('Juan', 'Perez', 'CI1001'),
            ('Carlos', 'Cortez', 'CI1002'),
            ('Maria', 'Gonzalez', 'CI1003'),
            ('Ana', 'Lopez', 'CI1004'),
            ('Luis', 'Rojas', 'CI1005'),
        ]
        for nombres, apellidos, ci in base:
            a, _ = Afiliado.objects.get_or_create(ci=ci, defaults={
                'nombres': nombres,
                'apellidos': apellidos,
                'telefono': '70000000',
                'email': f'{nombres.lower()}@demo.local',
                'estado': 'activo',
                'fecha_ingreso': date(2024, 1, 1),
                'is_active': True,
            })
            afiliados.append(a)

        rutas = []
        for nombre, origen, destino, tarifa in [
            ('La Paz', 'Taipiplaya', 'La Paz', 30),
            ('Caranavi', 'Taipiplaya', 'Caranavi', 25),
            ('Rincón', 'Taipiplaya', 'Rincón', 25),
        ]:
            r, _ = Ruta.objects.get_or_create(nombre=nombre, defaults={'origen': origen, 'destino': destino, 'tarifa_base': tarifa})
            rutas.append(r)

        vehiculos = []
        for i, a in enumerate(afiliados[:3], start=1):
            v, _ = Vehiculo.objects.get_or_create(placa=f'ABC-{100+i}', defaults={'tipo': 'minibus', 'capacidad': 14, 'afiliado': a, 'estado': 'activo'})
            vehiculos.append(v)

        # Hojas de ruta
        for i in range(1, 8):
            af = afiliados[i % len(afiliados)]
            ve = vehiculos[i % len(vehiculos)]
            ru = rutas[i % len(rutas)]
            HojaRuta.objects.get_or_create(nro=f'HR-{i:03d}', fecha_emision=date(2024, 3, (i % 28) + 1), afiliado=af, defaults={
                'vehiculo': ve,
                'ruta': ru,
                'estado': 'emitida',
                'precio': ru.tarifa_base,
            })

        # Cuotas
        for af in afiliados:
            Cuota.objects.get_or_create(afiliado=af, periodo=date(2024, 3, 1), tipo='mensual', defaults={'monto': 20, 'estado': 'pendiente'})
            Cuota.objects.get_or_create(afiliado=af, periodo=date(2024, 4, 1), tipo='mensual', defaults={'monto': 20, 'estado': 'pagada', 'fecha_pago': date(2024, 4, 10)})

        # Reservas
        for i in range(1, 5):
            Reserva.objects.get_or_create(cliente=f'Cliente {i}', ruta=rutas[i % len(rutas)], fecha_viaje=date(2024, 4, (i % 28) + 1), defaults={'cantidad': 2, 'estado': 'pendiente'})

        # Reunión y asistencias
        reunion, _ = Reunion.objects.get_or_create(fecha=date(2024, 3, 15), defaults={'tema': 'Ordinaria marzo', 'tipo': 'ordinaria', 'quorum': 30})
        for i, af in enumerate(afiliados):
            Asistencia.objects.get_or_create(reunion=reunion, afiliado=af, defaults={'presente': i % 2 == 0})

        self.stdout.write(self.style.SUCCESS('Datos de demostración creados/actualizados.'))