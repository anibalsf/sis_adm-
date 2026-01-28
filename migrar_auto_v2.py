import os
import sys
import shutil
import subprocess
from pathlib import Path
import json

def run_smart_migration():
    print("=== MIGRACIÓN INTELIGENTE A POSTGRESQL ===")
    
    BASE_DIR = Path(__file__).resolve().parent
    BACKUP_DIR = BASE_DIR / 'migration_backups'
    BACKUP_DIR.mkdir(exist_ok=True)
    
    ENV_FILE = BASE_DIR / '.env'
    
    # Lista de apps ordenadas por dependencia (aproximada)
    # Primero las que no dependen de otras
    apps_order = [
        'auth.User', 
        'auth.Group',
        'rutas',
        'afiliados', 
        'vehiculos', 
        'usuarios',
        'directorio',
        'tesoreria',
        'cuotas',
        'sanciones',
        'reuniones',
        'asistencias',
        'hojasruta',
        'reservas',
        'reportes',
        'comunicacion',
        'historial'
    ]
    
    # 1. EXPORTACIÓN
    print("\n1. Exportando datos por aplicación...")
    exported_files = []
    
    for app in apps_order:
        print(f"  > Exportando {app}...", end=" ", flush=True)
        filename = BACKUP_DIR / f"{app.replace('.', '_')}.json"
        
        try:
            # Usamos subprocess capturing output
            with open(filename, 'w', encoding='utf-8') as f:
                subprocess.run(
                    ['python', 'manage.py', 'dumpdata', app, '--natural-foreign', '--natural-primary'],
                    stdout=f,
                    check=True
                )
            
            # Verificar si el archivo tiene datos (es una lista no vacía)
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
                if content.strip() == '[]':
                    print("Vacío (OK)")
                else:
                    print("OK")
                    exported_files.append(filename)
                    
        except subprocess.CalledProcessError:
            print("FALLÓ")
            # Si falla auth.User es crítico, pero otros no tanto
            if 'auth' in app:
                print("    ! Advertencia: Falló la exportación de usuarios. Las contraseñas podrían perderse.")
        except Exception as e:
            print(f"Error: {e}")

    # 2. CONFIGURACIÓN .ENV
    print("\n2. Configurando PostgreSQL...")
    
    # Hacemos backup del .env si existe
    if ENV_FILE.exists():
        shutil.copy2(ENV_FILE, BACKUP_DIR / '.env.old')
    
    env_content = ""
    if ENV_FILE.exists():
        with open(ENV_FILE, 'r', encoding='utf-8') as f:
            env_content = f.read()
            
    new_lines = []
    has_engine = False
    
    for line in env_content.split('\n'):
        if line.startswith('DB_ENGINE='):
            new_lines.append('DB_ENGINE=postgresql')
            has_engine = True
        elif any(line.startswith(p) for p in ['DB_NAME=', 'DB_USER=', 'DB_PASSWORD=', 'DB_HOST=', 'DB_PORT=']):
            continue 
        else:
            new_lines.append(line)
            
    if not has_engine:
        new_lines.append('DB_ENGINE=postgresql')

    new_lines.extend([
        'DB_NAME=sindicato_taipiplaya',
        'DB_USER=admin_sindicato',
        'DB_PASSWORD=Taipiplaya2025!',
        'DB_HOST=localhost',
        'DB_PORT=5432'
    ])
    
    with open(ENV_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))
    print("  > Archivo .env actualizado.")

    # 3. MIGRACIÓN
    print("\n3. Creando tablas en PostgreSQL...")
    try:
        subprocess.run(['python', 'manage.py', 'migrate'], check=True)
        print("  > Tablas creadas correctamente.")
    except subprocess.CalledProcessError:
        print("  > Error al crear tablas. Verifique que la BD exista.")
        return

    # 4. IMPORTACIÓN
    print("\n4. Importando datos...")
    
    # Configurar entorno para evitar problemas de encoding
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'
    
    # Importar en el mismo orden
    for filename in exported_files:
        print(f"  > Importando {filename.name}...", end=" ", flush=True)
        try:
            subprocess.run(
                ['python', 'manage.py', 'loaddata', str(filename)],
                env=env,
                check=True,
                stdout=subprocess.DEVNULL, # Ocultar output verboso
                stderr=subprocess.PIPE     # Capturar errores si los hay
            )
            print("OK")
        except subprocess.CalledProcessError as e:
            print("FALLÓ")
            print(f"    Error: {e.stderr.decode('utf-8') if e.stderr else 'Desconocido'}")

    print("\n=== MIGRACIÓN FINALIZADA ===")
    print(f"Los backups de datos están en: {BACKUP_DIR}")

if __name__ == '__main__':
    run_smart_migration()
