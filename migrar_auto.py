import os
import sys
import shutil
from pathlib import Path
import subprocess

def run_migration():
    print("=== INICIANDO MIGRACIÓN AUTOMÁTICA ===")
    
    BASE_DIR = Path(__file__).resolve().parent
    SQLITE_DB = BASE_DIR / 'db.sqlite3'
    JSON_DATA = BASE_DIR / 'data_migration.json'
    ENV_FILE = BASE_DIR / '.env'
    
    # 1. Exportar datos
    print("1. Exportando datos de SQLite...")
    if SQLITE_DB.exists():
        with open(JSON_DATA, 'w', encoding='utf-8') as f:
            subprocess.run(
                ['python', 'manage.py', 'dumpdata', '--natural-foreign', '--natural-primary', 
                 '-e', 'contenttypes', '-e', 'auth.Permission', '-e', 'admin.LogEntry'],
                stdout=f,
                check=True
            )
        print("Datos exportados correctamente.")
    else:
        print("Advertencia: No existe db.sqlite3, se omitirá la exportación.")

    # 2. Configurar .env
    print("2. Configurando .env para PostgreSQL...")
    env_content = ""
    if ENV_FILE.exists():
        with open(ENV_FILE, 'r', encoding='utf-8') as f:
            env_content = f.read()
            
    # Reemplazar configuración
    new_lines = []
    has_engine = False
    
    for line in env_content.split('\n'):
        if line.startswith('DB_ENGINE='):
            new_lines.append('DB_ENGINE=postgresql')
            has_engine = True
        elif any(line.startswith(p) for p in ['DB_NAME=', 'DB_USER=', 'DB_PASSWORD=', 'DB_HOST=', 'DB_PORT=']):
            continue # Skip old config
        else:
            new_lines.append(line)
            
    if not has_engine:
        new_lines.append('DB_ENGINE=postgresql')

    # Agregar config nueva
    new_lines.extend([
        'DB_NAME=sindicato_taipiplaya',
        'DB_USER=admin_sindicato',
        'DB_PASSWORD=Taipiplaya2025!',
        'DB_HOST=localhost',
        'DB_PORT=5432'
    ])
    
    with open(ENV_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))
    print(".env actualizado.")

    # 3. Migrar estructura
    print("3. Creando tablas en PostgreSQL...")
    subprocess.run(['python', 'manage.py', 'migrate'], check=True)
    
    # 4. Cargar datos
    if JSON_DATA.exists():
        print("4. Importando datos a PostgreSQL...")
        # A veces loaddata falla por encoding en windows, usamos subprocess env
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        subprocess.run(['python', 'manage.py', 'loaddata', str(JSON_DATA)], env=env, check=True)
        print("Datos importados.")
        
        # Limpieza
        # os.remove(JSON_DATA)
    
    print("=== MIGRACIÓN COMPLETADA EXITOSAMENTE ===")

if __name__ == '__main__':
    run_migration()
