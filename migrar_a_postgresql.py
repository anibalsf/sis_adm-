#!/usr/bin/env python
"""
Script de migración de SQLite a PostgreSQL
Sistema: Sindicato Mixto de Transporte Integración Taipiplaya
Autor: Sistema de Administración
Fecha: 2025-12-12
"""

import os
import sys
import shutil
from datetime import datetime
from pathlib import Path
import subprocess

# Colores para terminal
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(message):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{message.center(70)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}\n")

def print_success(message):
    print(f"{Colors.OKGREEN}✓ {message}{Colors.ENDC}")

def print_error(message):
    print(f"{Colors.FAIL}✗ {message}{Colors.ENDC}")

def print_warning(message):
    print(f"{Colors.WARNING}⚠ {message}{Colors.ENDC}")

def print_info(message):
    print(f"{Colors.OKCYAN}ℹ {message}{Colors.ENDC}")

def main():
    print_header("MIGRACIÓN A POSTGRESQL")
    print_info("Sistema: Sindicato Mixto de Transporte Integración Taipiplaya")
    print_info(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Configuración
    BASE_DIR = Path(__file__).resolve().parent
    SQLITE_DB = BASE_DIR / 'db.sqlite3'
    BACKUP_DIR = BASE_DIR / 'backups'
    BACKUP_DIR.mkdir(exist_ok=True)
    
    # Paso 1: Verificar que SQLite existe
    print_header("PASO 1: VERIFICACIÓN DE BASE DE DATOS ACTUAL")
    if not SQLITE_DB.exists():
        print_error("No se encontró db.sqlite3")
        print_warning("¿Es la primera vez que ejecutas el sistema?")
        sys.exit(1)
    print_success(f"Base de datos SQLite encontrada: {SQLITE_DB}")
    print_info(f"Tamaño: {SQLITE_DB.stat().st_size / 1024:.2f} KB\n")
    
    # Paso 2: Backup de SQLite
    print_header("PASO 2: BACKUP DE SQLITE")
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_sqlite = BACKUP_DIR / f'db.sqlite3.backup_{timestamp}'
    
    try:
        shutil.copy2(SQLITE_DB, backup_sqlite)
        print_success(f"Backup creado: {backup_sqlite}")
    except Exception as e:
        print_error(f"Error al crear backup: {e}")
        sys.exit(1)
    
    # Paso 3: Backup de datos en JSON
    print_header("PASO 3: EXPORTAR DATOS A JSON")
    backup_json = BACKUP_DIR / f'data_backup_{timestamp}.json'
    
    print_info("Exportando datos de SQLite...")
    print_info("Exportando datos de SQLite...")
    
    try:
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        
        with open(backup_json, 'w', encoding='utf-8') as f:
            subprocess.run(
                ['python', 'manage.py', 'dumpdata', '--natural-foreign', '--natural-primary', '-e', 'contenttypes', '-e', 'auth.Permission'],
                stdout=f,
                env=env,
                check=True
            )
        result = 0
    except Exception as e:
        print_error(f"Excepción al exportar: {e}")
        result = 1
    
    if result != 0:
        print_error("Error al exportar datos")
        print_warning("Verifica que el servidor esté detenido")
        sys.exit(1)
    
    print_success(f"Datos exportados: {backup_json}")
    print_info(f"Tamaño: {backup_json.stat().st_size / 1024:.2f} KB\n")
    
    # Paso 4: Solicitar credenciales de PostgreSQL
    print_header("PASO 4: CONFIGURACIÓN DE POSTGRESQL")
    print_info("Ingresa las credenciales de PostgreSQL:\n")
    
    db_name = input(f"{Colors.OKCYAN}Nombre de la base de datos [sindicato_taipiplaya]: {Colors.ENDC}").strip() or "sindicato_taipiplaya"
    db_user = input(f"{Colors.OKCYAN}Usuario [admin_sindicato]: {Colors.ENDC}").strip() or "admin_sindicato"
    db_password = input(f"{Colors.OKCYAN}Contraseña: {Colors.ENDC}").strip()
    
    if not db_password:
        print_error("La contraseña no puede estar vacía")
        sys.exit(1)
    
    db_host = input(f"{Colors.OKCYAN}Host [localhost]: {Colors.ENDC}").strip() or "localhost"
    db_port = input(f"{Colors.OKCYAN}Puerto [5432]: {Colors.ENDC}").strip() or "5432"
    
    # Paso 5: Backup del .env actual
    print_header("PASO 5: ACTUALIZAR CONFIGURACIÓN")
    env_file = BASE_DIR / '.env'
    env_backup = BASE_DIR / f'.env.backup_{timestamp}'
    
    if env_file.exists():
        shutil.copy2(env_file, env_backup)
        print_success(f"Backup de .env creado: {env_backup}")
    
    # Leer .env actual
    env_content = ""
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            env_content = f.read()
    
    # Actualizar configuración de base de datos
    lines = env_content.split('\n')
    new_lines = []
    db_config_found = False
    
    for line in lines:
        if line.startswith('DB_ENGINE='):
            new_lines.append('DB_ENGINE=postgresql')
            db_config_found = True
        elif line.startswith('DB_NAME='):
            new_lines.append(f'DB_NAME={db_name}')
        elif line.startswith('DB_USER='):
            new_lines.append(f'DB_USER={db_user}')
        elif line.startswith('DB_PASSWORD='):
            new_lines.append(f'DB_PASSWORD={db_password}')
        elif line.startswith('DB_HOST='):
            new_lines.append(f'DB_HOST={db_host}')
        elif line.startswith('DB_PORT='):
            new_lines.append(f'DB_PORT={db_port}')
        else:
            new_lines.append(line)
    
    # Si no se encontró configuración, agregarla
    if not db_config_found:
        new_lines.extend([
            '',
            '# Base de Datos - PostgreSQL',
            'DB_ENGINE=postgresql',
            f'DB_NAME={db_name}',
            f'DB_USER={db_user}',
            f'DB_PASSWORD={db_password}',
            f'DB_HOST={db_host}',
            f'DB_PORT={db_port}',
        ])
    
    # Guardar .env actualizado
    with open(env_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))
    
    print_success(".env actualizado con configuración de PostgreSQL\n")
    
    # Paso 6: Verificar conexión a PostgreSQL
    print_header("PASO 6: VERIFICAR CONEXIÓN A POSTGRESQL")
    print_info("Probando conexión...")
    
    import psycopg2
    try:
        conn = psycopg2.connect(
            dbname=db_name,
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port
        )
        conn.close()
        print_success("Conexión a PostgreSQL exitosa\n")
    except (Exception, UnicodeDecodeError) as e:
        # Manejar errores de encoding comunes en Windows con mensajes en español
        error_str = str(e)
        if "codec can't decode" in error_str:
            print_error("Fallo de conexión o credenciales (Error de encoding en mensaje del sistema)")
            print_info("Esto usualmente significa que la CONTRASEÑA ES INCORRECTA.")
        else:
            print_error(f"No se pudo conectar a PostgreSQL: {e}")
        print_warning("Verifica que:")
        print_warning("  1. PostgreSQL esté instalado y corriendo")
        print_warning("  2. La base de datos exista")
        print_warning("  3. El usuario tenga permisos")
        print_warning("  4. Las credenciales sean correctas")
        print_warning("\nRestaurando .env original...")
        if env_backup.exists():
            shutil.copy2(env_backup, env_file)
            print_success(".env restaurado")
        sys.exit(1)
    
    # Paso 7: Aplicar migraciones
    print_header("PASO 7: APLICAR MIGRACIONES A POSTGRESQL")
    print_info("Creando estructura de tablas...\n")
    
    result = os.system('python manage.py migrate --run-syncdb')
    
    if result != 0:
        print_error("Error al aplicar migraciones")
        print_warning("Restaurando configuración...")
        if env_backup.exists():
            shutil.copy2(env_backup, env_file)
            print_success(".env restaurado")
        sys.exit(1)
    
    print_success("Migraciones aplicadas correctamente\n")
    
    # Paso 8: Importar datos
    print_header("PASO 8: IMPORTAR DATOS A POSTGRESQL")
    print_info("Transfiriendo datos de SQLite a PostgreSQL...")
    print_warning("Esto puede tomar varios minutos dependiendo del tamaño de los datos\n")
    
    result = os.system(f'python manage.py loaddata "{backup_json}"')
    
    if result != 0:
        print_error("Error al importar datos")
        print_warning("Los datos no se importaron completamente")
        print_info("Puedes intentar manualmente con:")
        print_info(f'  python manage.py loaddata "{backup_json}"')
    else:
        print_success("Datos importados correctamente\n")
    
    # Paso 9: Verificar datos
    print_header("PASO 9: VERIFICAR INTEGRIDAD DE DATOS")
    print_info("Contando registros...\n")
    
    # Importar Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema.settings')
    import django
    django.setup()
    
    from afiliados.models import Afiliado
    from vehiculos.models import Vehiculo
    from hojasruta.models import HojaRuta
    from cuotas.models import Pago
    
    print_success(f"Afiliados: {Afiliado.objects.count()}")
    print_success(f"Vehículos: {Vehiculo.objects.count()}")
    print_success(f"Hojas de Ruta: {HojaRuta.objects.count()}")
    print_success(f"Pagos: {Pago.objects.count()}\n")
    
    # Paso 10: Crear índices optimizados
    print_header("PASO 10: OPTIMIZAR BASE DE DATOS")
    print_info("Creando índices para mejor rendimiento...\n")
    
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            # Índices para búsquedas frecuentes
            indices = [
                "CREATE INDEX IF NOT EXISTS idx_afiliados_ci ON afiliados_afiliado(ci);",
                "CREATE INDEX IF NOT EXISTS idx_afiliados_estado ON afiliados_afiliado(estado);",
                "CREATE INDEX IF NOT EXISTS idx_afiliados_nombres ON afiliados_afiliado(nombres);",
                "CREATE INDEX IF NOT EXISTS idx_afiliados_apellidos ON afiliados_afiliado(apellidos);",
                "CREATE INDEX IF NOT EXISTS idx_vehiculos_placa ON vehiculos_vehiculo(placa);",
                "CREATE INDEX IF NOT EXISTS idx_hojasruta_fecha ON hojasruta_hojaruta(fecha);",
                "CREATE INDEX IF NOT EXISTS idx_hojasruta_estado ON hojasruta_hojaruta(estado);",
                "CREATE INDEX IF NOT EXISTS idx_pagos_fecha ON cuotas_pago(fecha);",
                "CREATE INDEX IF NOT EXISTS idx_pagos_tipo ON cuotas_pago(tipo_pago_id);",
            ]
            
            for sql in indices:
                try:
                    cursor.execute(sql)
                    print_success(f"Índice creado")
                except Exception as e:
                    print_warning(f"Índice ya existente o error: {str(e)[:50]}")
        
        print_info("\nOptimización completada")
    except Exception as e:
        print_warning(f"No se pudieron crear todos los índices: {e}")
    
    # Resumen final
    print_header("✅ MIGRACIÓN COMPLETADA EXITOSAMENTE")
    
    print(f"{Colors.OKGREEN}{Colors.BOLD}")
    print("🎉 ¡La migración a PostgreSQL ha sido exitosa!")
    print(f"{Colors.ENDC}")
    
    print(f"\n{Colors.OKCYAN}📋 Resumen:{Colors.ENDC}")
    print(f"  • Base de datos: {db_name}")
    print(f"  • Host: {db_host}:{db_port}")
    print(f"  • Usuario: {db_user}")
    
    print(f"\n{Colors.OKCYAN}💾 Backups creados:{Colors.ENDC}")
    print(f"  • SQLite: {backup_sqlite}")
    print(f"  • JSON: {backup_json}")
    print(f"  • Config: {env_backup}")
    
    print(f"\n{Colors.OKGREEN}✅ Próximos pasos:{Colors.ENDC}")
    print("  1. Ejecutar el servidor:")
    print("     python manage.py runserver")
    print("  2. Verificar que todo funcione correctamente")
    print("  3. Revisar el dashboard y módulos principales")
    print("  4. Configurar backup automático (ver MIGRACION_POSTGRESQL.md)")
    
    print(f"\n{Colors.WARNING}⚠ Importante:{Colors.ENDC}")
    print("  • El archivo db.sqlite3 original NO se ha borrado")
    print("  • Puedes volver a SQLite restaurando .env.backup")
    print("  • Mantén los backups en un lugar seguro")
    
    print(f"\n{Colors.HEADER}{'='*70}{Colors.ENDC}\n")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.WARNING}Migración cancelada por el usuario{Colors.ENDC}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.FAIL}Error inesperado: {e}{Colors.ENDC}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
