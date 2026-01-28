import os
import datetime
import subprocess
from decouple import config
from urllib.parse import urlparse

def run_backup():
    db_url = config('DATABASE_URL', default='')
    if not db_url:
        print("DATABASE_URL no configurada en .env. No se puede realizar el respaldo.")
        return

    parsed = urlparse(db_url)
    db_name = parsed.path.lstrip('/')
    db_user = parsed.username
    db_password = parsed.password
    db_host = parsed.hostname or 'localhost'
    db_port = parsed.port or '5432'

    # Directorio de respaldos
    backup_dir = os.path.join(os.getcwd(), 'backups')
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)

    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"backup_{db_name}_{timestamp}.sql"
    filepath = os.path.join(backup_dir, filename)

    print(f"Iniciando respaldo de {db_name} en {filepath}...")

    # Configurar contraseña para pg_dump
    os.environ['PGPASSWORD'] = db_password

    try:
        # Comando pg_dump
        cmd = [
            'pg_dump',
            '-h', db_host,
            '-p', str(db_port),
            '-U', db_user,
            '-F', 'c', # Formato personalizado (comprimido)
            '-b', # Incluir blobs
            '-v', # Verbosidad
            '-f', filepath,
            db_name
        ]

        subprocess.run(cmd, check=True)
        print(f"Respaldo completado exitosamente: {filename}")

        # Limpieza de respaldos antiguos (mantener últimos 7 días)
        clean_old_backups(backup_dir, days=7)

    except subprocess.CalledProcessError as e:
        print(f"Error al realizar el respaldo: {e}")
    except Exception as e:
        print(f"Error inesperado: {e}")
    finally:
        if 'PGPASSWORD' in os.environ:
            del os.environ['PGPASSWORD']

def clean_old_backups(directory, days):
    now = datetime.datetime.now()
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        if os.path.isfile(filepath):
            file_time = datetime.datetime.fromtimestamp(os.path.getmtime(filepath))
            if now - file_time > datetime.timedelta(days=days):
                try:
                    os.remove(filepath)
                    print(f"Respaldo antiguo eliminado: {filename}")
                except Exception as e:
                    print(f"Error al eliminar {filename}: {e}")

if __name__ == '__main__':
    run_backup()
