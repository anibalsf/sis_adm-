import logging
import os
import tempfile
from contextlib import contextmanager

logger = logging.getLogger('sistema.startup')

_VALORES_ACTIVOS = {'1', 'true', 'yes', 'si', 'sí', 'on'}


def auto_migrate_habilitado():
    valor = os.environ.get('AUTO_MIGRATE', 'true')
    return str(valor).strip().lower() in _VALORES_ACTIVOS


def _ruta_lock():
    from django.conf import settings

    candidatos = []
    base_dir = getattr(settings, 'BASE_DIR', None)
    if base_dir:
        candidatos.append(os.path.join(str(base_dir), 'logs'))
    candidatos.append(tempfile.gettempdir())

    for directorio in candidatos:
        try:
            os.makedirs(directorio, exist_ok=True)
            ruta = os.path.join(directorio, 'sindicato_auto_migrate.lock')
            with open(ruta, 'a'):
                pass
            return ruta
        except OSError:
            continue
    return None


@contextmanager
def _bloqueo(ruta):
    if not ruta:
        yield
        return

    archivo = open(ruta, 'a+')
    try:
        try:
            import fcntl
            fcntl.flock(archivo.fileno(), fcntl.LOCK_EX)
        except (ImportError, OSError):
            pass
        yield
    finally:
        try:
            import fcntl
            fcntl.flock(archivo.fileno(), fcntl.LOCK_UN)
        except (ImportError, OSError):
            pass
        archivo.close()


def migraciones_pendientes():
    from django.db import connection
    from django.db.migrations.executor import MigrationExecutor

    executor = MigrationExecutor(connection)
    return executor.migration_plan(executor.loader.graph.leaf_nodes())


def aplicar_migraciones_pendientes():
    if not auto_migrate_habilitado():
        logger.info('AUTO_MIGRATE deshabilitado: no se revisan migraciones al iniciar.')
        return False

    try:
        if not migraciones_pendientes():
            return False

        with _bloqueo(_ruta_lock()):
            pendientes = migraciones_pendientes()
            if not pendientes:
                return False

            logger.warning(
                'Base de datos desactualizada: aplicando %s migracion(es) pendiente(s).',
                len(pendientes),
            )
            from django.core.management import call_command

            call_command('migrate', interactive=False, verbosity=1)
            logger.warning('Migraciones aplicadas correctamente.')
            return True
    except Exception:
        logger.exception('No se pudieron aplicar las migraciones pendientes al iniciar.')
    return False
