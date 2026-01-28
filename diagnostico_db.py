
import sys
import os
import psycopg2
from getpass import getpass

# Configura encoding para consola Windows
if sys.platform == 'win32':
    import codecs
    try:
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    except:
        pass

def test_connection(dbname, user, password, host, port):
    print(f"\n--- Probando conexión a '{dbname}' con usuario '{user}' ---")
    try:
        conn = psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port
        )
        conn.close()
        print("✅ ¡CONEXIÓN EXITOSA!")
        return True
    except Exception as e:
        print("❌ FALLÓ LA CONEXIÓN:")
        # Intentar decodificar error de postgres si está en encoding local
        error_msg = str(e)
        print(f"   Mensaje: {error_msg}")
        return False

def main():
    print("DIAGNÓSTICO DE CONEXIÓN POSTGRESQL")
    print("===================================")
    
    print("\n1. Intento con usuario 'admin_sindicato' (Aplicación)")
    print("   Contraseña esperada: Taipiplaya2025!")
    password_app = input("   Ingresa la contraseña para admin_sindicato [Taipiplaya2025!]: ").strip() or "Taipiplaya2025!"
    
    # Probar con ambos nombres de base de datos probables
    test_connection("sindicato_taipiplaya", "admin_sindicato", password_app, "localhost", "5432")
    test_connection("sindicato_integracion", "admin_sindicato", password_app, "localhost", "5432")

    print("\n2. Intento con usuario 'postgres' (Superusuario)")
    password_pg = input("   Ingresa tu contraseña de postgres: ").strip()
    
    if password_pg:
        if test_connection("postgres", "postgres", password_pg, "localhost", "5432"):
            print("\n🔍 Buscando bases de datos existentes...")
            try:
                conn = psycopg2.connect(dbname="postgres", user="postgres", password=password_pg)
                cur = conn.cursor()
                cur.execute("SELECT datname FROM pg_database WHERE datistemplate = false;")
                dbs = cur.fetchall()
                print("   Bases de datos encontradas:")
                for db in dbs:
                    print(f"    - {db[0]}")
                
                cur.execute("SELECT usename FROM pg_user;")
                users = cur.fetchall()
                print("\n   Usuarios encontrados:")
                for user in users:
                    print(f"    - {user[0]}")
                conn.close()
            except Exception as e:
                print(f"   Error consultando datos: {e}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nCancelado.")
    input("\nPresiona Enter para salir...")
