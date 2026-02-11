import os
from pathlib import Path
from datetime import timedelta
from decouple import config, Csv

from urllib.parse import urlparse
import sentry_sdk
import dj_database_url
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn=config('SENTRY_DSN', default=""),
    integrations=[DjangoIntegration()],
    traces_sample_rate=1.0,
    send_default_pii=True
)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-w-aud#lx#x5s=8$4t(%tsz03#bvpt9ol=-n#22*z&f*0jqx!-4')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

# Environment (development, staging, production)
ENVIRONMENT = config('ENVIRONMENT', default='development')

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='*', cast=Csv())

# RAILWAY_STATIC_URL o RAILWAY_PUBLIC_DOMAIN suelen venir en Railway
RAILWAY_DOMAIN = config('RAILWAY_PUBLIC_DOMAIN', default='')
if RAILWAY_DOMAIN and RAILWAY_DOMAIN not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(RAILWAY_DOMAIN)

CSRF_TRUSTED_ORIGINS = config('CSRF_TRUSTED_ORIGINS', default='http://localhost:5173,http://127.0.0.1:5173', cast=Csv())
if RAILWAY_DOMAIN:
    CSRF_TRUSTED_ORIGINS.append(f"https://{RAILWAY_DOMAIN}")

# Configuración necesaria para HTTPS detrás de un proxy (Railway)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

FRONTEND_URL = config('FRONTEND_URL', default='http://localhost:5173')


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third-party apps
    'rest_framework',
    'rest_framework.authtoken',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'django_apscheduler',
    'drf_spectacular',
    'django_filters',
    # Local apps
    'afiliados',
    'vehiculos',
    'hojasruta',
    'cuotas',
    'usuarios',
    'reuniones',
    'asistencias',
    'sanciones',
    'rutas',
    'reservas',
    'reportes',
    'comunicacion',
    'historial',
    'directorio',
    'tesoreria',
    'whatsapp_notif',
    'pagos_qr',
    'web_publica',
    'mantenimiento',
    'reportes_auto',
]

# Twilio Configuration
TWILIO_ACCOUNT_SID = config('TWILIO_ACCOUNT_SID', default='')
TWILIO_AUTH_TOKEN = config('TWILIO_AUTH_TOKEN', default='')
TWILIO_WHATSAPP_FROM = config('TWILIO_WHATSAPP_FROM', default='whatsapp:+14155238886')
ADMIN_PHONE_NUMBER = config('ADMIN_PHONE_NUMBER', default='70000000')

WHATSAPP_WEBHOOK_URL = None
TWILIO_WEBHOOK_URL = None

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',  # CORS debe estar antes de CommonMiddleware
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'sistema.middleware.CurrentUserMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'sistema.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'frontend' / 'dist'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'sistema.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

# Configuración dinámica de base de datos (prioridad: DATABASE_URL > DB_ENGINE)
DATABASE_URL = config('DATABASE_URL', default='')

if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
elif config('DB_ENGINE', default='sqlite') == 'postgresql':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('DB_NAME', default='sindicato_taipiplaya'),
            'USER': config('DB_USER', default='postgres'),
            'PASSWORD': config('DB_PASSWORD', default=''),
            'HOST': config('DB_HOST', default='localhost'),
            'PORT': config('DB_PORT', default='5432'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'es'

TIME_ZONE = 'America/La_Paz'

USE_I18N = True

USE_TZ = True

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.TokenAuthentication',  # Mantener para compatibilidad temporal
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': config('PAGE_SIZE', default=20, cast=int),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '10000/hour',
        'user': '100000/day'
    }
}

# JWT Configuration
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,

    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,

    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',

    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',

    'JTI_CLAIM': 'jti',
}

# DRF Spectacular Settings (API Documentation)
SPECTACULAR_SETTINGS = {
    'TITLE': 'Sistema Sindicato Mixto Integración Taipiplaya API',
    'DESCRIPTION': 'API REST para gestión administrativa del Sindicato de Transporte',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
}

# CORS Configuration
CORS_ALLOWED_ORIGINS = config('CORS_ALLOWED_ORIGINS', default='http://localhost:3000,http://localhost:5173,http://localhost:5174', cast=Csv())
CORS_ALLOW_CREDENTIALS = config('CORS_ALLOW_CREDENTIALS', default=True, cast=bool)

# Configuraciones de negocio
SANCTION_ABSENCE_AMOUNT = config('SANCTION_ABSENCE_AMOUNT', default=50, cast=int)

# ==============================================================================
# AUTOMATIZACIÓN: CONFIGURACIÓN DE SANCIONES
# ==============================================================================
SANCIONES_CONFIG = {
    'FALTA_REUNION': {
        'monto_default': 50.00,
        'tipo': 'Falta a Reunión',
        'notificar_automatico': True
    },
    'FALTA_TURNO_PARADA': {
        'monto_default': 50.00,
        'tipo': 'Falta a Turno de Parada',
        'notificar_automatico': True
    },
    'INCUMPLIMIENTO_REGLAMENTO': {
        'monto_default': 100.00,
        'tipo': 'Incumplimiento de Reglamento',
        'notificar_automatico': False
    }
}



# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = config('STATIC_URL', default='/static/')
STATIC_ROOT = BASE_DIR / config('STATIC_ROOT', default='staticfiles')
STATICFILES_DIRS = [
    BASE_DIR / 'frontend' / 'dist',
]

# Configuración de WhiteNoise para compresión y cache
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# Media files (User uploaded files)
MEDIA_URL = config('MEDIA_URL', default='/media/')
MEDIA_ROOT = BASE_DIR / config('MEDIA_ROOT', default='media')

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ==============================================================================
# LOGGING CONFIGURATION
# ==============================================================================

# Crear directorio de logs si no existe
LOG_DIR = BASE_DIR / config('LOG_DIR', default='logs')
LOG_DIR.mkdir(exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {module} {process:d} {thread:d} - {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
        'simple': {
            'format': '[{levelname}] {asctime} - {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    },
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'level': config('LOG_LEVEL', default='INFO'),
            'class': 'logging.FileHandler' if os.name == 'nt' else 'logging.handlers.RotatingFileHandler',
            'filename': LOG_DIR / 'django.log',
            'formatter': 'verbose',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler' if os.name == 'nt' else 'logging.handlers.RotatingFileHandler',
            'filename': LOG_DIR / 'errors.log',
            'formatter': 'verbose',
        },
        'debug_file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler' if os.name == 'nt' else 'logging.handlers.RotatingFileHandler',
            'filename': LOG_DIR / 'debug.log',
            'formatter': 'verbose',
            'filters': ['require_debug_true'],
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file', 'error_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['error_file', 'console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        # Loggers personalizados para cada app
        'afiliados': {
            'handlers': ['console', 'file'],
            'level': config('LOG_LEVEL', default='INFO'),
            'propagate': False,
        },
        'vehiculos': {
            'handlers': ['console', 'file'],
            'level': config('LOG_LEVEL', default='INFO'),
            'propagate': False,
        },
        'cuotas': {
            'handlers': ['console', 'file'],
            'level': config('LOG_LEVEL', default='INFO'),
            'propagate': False,
        },
        'usuarios': {
            'handlers': ['console', 'file'],
            'level': config('LOG_LEVEL', default='INFO'),
            'propagate': False,
        },
    },
    'root': {
        'handlers': ['console', 'file', 'error_file'],
        'level': config('LOG_LEVEL', default='INFO'),
    },
}

# Add rotation arguments only if NOT on Windows
if os.name != 'nt':
    LOGGING['handlers']['file']['maxBytes'] = 1024 * 1024 * 10
    LOGGING['handlers']['file']['backupCount'] = 5
    LOGGING['handlers']['error_file']['maxBytes'] = 1024 * 1024 * 10
    LOGGING['handlers']['error_file']['backupCount'] = 5
    LOGGING['handlers']['debug_file']['maxBytes'] = 1024 * 1024 * 5
    LOGGING['handlers']['debug_file']['backupCount'] = 3

# ==============================================================================
# SECURITY SETTINGS
# ==============================================================================

if not DEBUG:
    # Producción - Configuraciones de seguridad estrictas
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_HSTS_SECONDS = 31536000  # 1 año
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# ==============================================================================
# CELERY / REDIS CONFIGURATION (MODO SEGURO SIN REDIS)
# ==============================================================================
# Configuración original (Comentada temporalmente por fallo en Redis)
# Configuración dinámica de Celery (Prioridad: REDIS_URL > Eager Mode)
REDIS_URL = config('REDIS_URL', default='')

if REDIS_URL:
    CELERY_BROKER_URL = REDIS_URL
    CELERY_RESULT_BACKEND = REDIS_URL
    CELERY_TASK_ALWAYS_EAGER = False
else:
    # Fallback a modo síncrono para desarrollo sin Redis
    CELERY_BROKER_URL = 'memory://'
    CELERY_RESULT_BACKEND = 'db+sqlite:///results.sqlite'
    CELERY_TASK_ALWAYS_EAGER = True

CELERY_TASK_EAGER_PROPAGATES = True  # Propagar errores si ocurren

CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutos

# CELERY BEAT SCHEDULE
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    # Reporte diario a las 8:00 AM
    'send-daily-report-morning': {
        'task': 'reportes_auto.tasks.send_daily_report_task',
        'schedule': crontab(hour=8, minute=0),
    },
    # Reporte semanal los lunes a las 8:00 AM
    'send-weekly-report-monday': {
        'task': 'reportes_auto.tasks.send_weekly_report_task',
        'schedule': crontab(hour=8, minute=0, day_of_week=1),  # 1 = Lunes
    },
    # Reporte mensual el día 1 de cada mes a las 8:00 AM
    'send-monthly-report-first-day': {
        'task': 'reportes_auto.tasks.send_monthly_report_task',
        'schedule': crontab(hour=8, minute=0, day_of_month=1),
    },
    # Recordatorios de turno a las 18:00 (6 PM)
    'send-shift-reminders-evening': {
        'task': 'whatsapp_notif.tasks.send_shift_reminders',
        'schedule': crontab(hour=18, minute=0),
    },
    # Recordatorios de reunión a las 8:00 AM
    'send-meeting-reminders-morning': {
        'task': 'whatsapp_notif.tasks.send_meeting_reminders',
        'schedule': crontab(hour=8, minute=0),
    },
    # Recordatorios de deuda los lunes a las 9:00 AM
    'send-debt-reminders-weekly': {
        'task': 'whatsapp_notif.tasks.send_debt_reminders',
        'schedule': crontab(hour=9, minute=0, day_of_week=1),
    },
}
