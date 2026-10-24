import logging

from django.db import OperationalError, ProgrammingError
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        return response

    if isinstance(exc, (OperationalError, ProgrammingError)):
        logger.exception('Error de base de datos en %s', context.get('view'))
        return Response(
            {
                'detail': (
                    'La base de datos está desactualizada o no está disponible. '
                    'Ejecute las migraciones (python manage.py migrate) y vuelva a intentarlo.'
                ),
                'code': 'database_error',
            },
            status=503,
        )

    return None
