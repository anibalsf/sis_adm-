import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import sys

def create_database():
    print("Intentando conectar a PostgreSQL...")
    
    # Lista de contraseñas comunes para probar localmente
    passwords = ['root', 'postgres', 'admin', '123456', 'password', '']
    
    conn = None
    connected_password = None
    
    for pwd in passwords:
        try:
            print(f"Probando contraseña: '{pwd}'...")
            conn = psycopg2.connect(
                dbname='postgres',
                user='postgres',
                password=pwd,
                host='localhost',
                port='5432'
            )
            connected_password = pwd
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            print("¡Conexión exitosa!")
            break
        except Exception as e:
            pass
            
    if conn is None:
        print("No se pudo conectar a PostgreSQL con las contraseñas comunes.")
        print("Por favor, ejecuta el script manual: crear_database_postgresql.ps1")
        sys.exit(1)

    cursor = conn.cursor()
    
    # 1. Crear usuario si no existe
    try:
        cursor.execute("SELECT 1 FROM pg_roles WHERE rolname='admin_sindicato'")
        if not cursor.fetchone():
            print("Creando usuario 'admin_sindicato'...")
            cursor.execute("CREATE USER admin_sindicato WITH PASSWORD 'Taipiplaya2025!';")
            cursor.execute("ALTER USER admin_sindicato CREATEDB;")
        else:
            print("El usuario 'admin_sindicato' ya existe.")
    except Exception as e:
        print(f"Error gestionando usuario: {e}")

    # 2. Crear base de datos
    try:
        cursor.execute("SELECT 1 FROM pg_database WHERE datname='sindicato_taipiplaya'")
        if not cursor.fetchone():
            print("Creando base de datos 'sindicato_taipiplaya'...")
            cursor.execute("CREATE DATABASE sindicato_taipiplaya OWNER admin_sindicato;")
        else:
            print("La base de datos 'sindicato_taipiplaya' ya existe.")
    except Exception as e:
        print(f"Error creando base de datos: {e}")

    # 3. Dar permisos (redundante si es owner, pero por seguridad)
    try:
        cursor.execute("GRANT ALL PRIVILEGES ON DATABASE sindicato_taipiplaya TO admin_sindicato;")
    except Exception as e:
        print(f"Error asignando permisos: {e}")
        
    conn.close()
    print("=== Configuración de Base de Datos FINALIZADA ===")

if __name__ == "__main__":
    try:
        create_database()
    except ImportError:
        print("Error: psycopg2 no está instalado. Ejecuta pip install psycopg2-binary")
    except Exception as e:
        print(f"Error inesperado: {e}")
