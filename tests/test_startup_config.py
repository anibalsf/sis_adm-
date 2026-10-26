import logging
from unittest.mock import Mock, patch

import pytest
from apscheduler.util import obj_to_ref, ref_to_obj
from django.conf import settings
from django.utils import timezone

from sistema import startup


@patch('sistema.startup.auto_migrate_habilitado', return_value=True)
@patch('sistema.startup.migraciones_pendientes', return_value=[])
def test_sin_migraciones_pendientes_devuelve_true(_pendientes, _habilitado):
    assert startup.aplicar_migraciones_pendientes() is True


@patch('sistema.startup.auto_migrate_habilitado', return_value=True)
@patch('sistema.startup.migraciones_pendientes')
@patch('django.core.management.call_command')
def test_registra_migraciones_pendientes_sin_fallar(call_command, pendientes, _habilitado, caplog):
    """Regresión: las pendientes son tuplas (migración, retroceder)."""
    migracion = Mock(app_label='afiliados')
    migracion.name = '0001_initial'
    pendientes.side_effect = [[(migracion, False)], [(migracion, False)]]

    with caplog.at_level(logging.WARNING, logger='sistema.startup'):
        assert startup.aplicar_migraciones_pendientes() is True

    assert 'afiliados.0001_initial' in caplog.text
    call_command.assert_called_once_with('migrate', interactive=False, verbosity=1)


@patch('sistema.startup.auto_migrate_habilitado', return_value=True)
@patch('sistema.startup.migraciones_pendientes', side_effect=RuntimeError('boom'))
def test_error_al_revisar_migraciones_devuelve_false(_pendientes, _habilitado, caplog):
    with caplog.at_level(logging.ERROR, logger='sistema.startup'):
        assert startup.aplicar_migraciones_pendientes() is False
    assert 'No se pudieron aplicar las migraciones' in caplog.text


def test_backend_celery_no_requiere_sqlalchemy():
    """El fallback sin Redis debe funcionar sin SQLAlchemy instalado."""
    from sistema.celery import app

    assert 'db+' not in (settings.CELERY_RESULT_BACKEND or '')
    assert app.backend is not None


def test_wrappers_del_scheduler_son_serializables():
    from whatsapp_notif import scheduler

    for funcion in (
        scheduler.run_shift_reminders,
        scheduler.run_meeting_reminders,
        scheduler.run_debt_reminders,
    ):
        assert ref_to_obj(obj_to_ref(funcion)) is funcion


@pytest.mark.django_db
def test_limpiar_jobs_invalidos_elimina_referencias_celery_local():
    from django_apscheduler.models import DjangoJob

    from whatsapp_notif.scheduler import _limpiar_jobs_invalidos

    DjangoJob.objects.create(
        id='job_obsoleto',
        next_run_time=timezone.now(),
        job_state=b'\x80\x05whatsapp_notif.tasks:celery.local',
    )
    DjangoJob.objects.create(
        id='job_valido',
        next_run_time=timezone.now(),
        job_state=b'\x80\x05whatsapp_notif.scheduler:run_shift_reminders',
    )

    _limpiar_jobs_invalidos()

    assert not DjangoJob.objects.filter(id='job_obsoleto').exists()
    assert DjangoJob.objects.filter(id='job_valido').exists()
