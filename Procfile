web: gunicorn sistema.wsgi:application --bind 0.0.0.0:8000
worker: celery -A sistema worker -l info
beat: celery -A sistema beat -l info
