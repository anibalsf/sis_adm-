"""
WSGI config for sistema project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

from sistema.startup import aplicar_migraciones_pendientes

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema.settings')

application = get_wsgi_application()
aplicar_migraciones_pendientes()
