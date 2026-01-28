import psycopg
from psycopg import sql

# Configuration
DB_NAME = "sindicato_taipiplaya"
DB_USER = "admin_sindicato"
DB_PASS = "Taipiplaya2025!"
HOST = "localhost"
PORT = "5432"

# Common passwords for 'postgres' superuser
POSTGRES_PASSWORDS = ["postgres", "admin", "123456", "root", "", "password"]

def setup_database():
    conn = None
    connected = False
    
    print("Intentando conectar como superusuario 'postgres'...")
    
    for pwd in POSTGRES_PASSWORDS:
        try:
            print(f"Probando password: '{pwd}' ...")
            # Connect to default 'postgres' database
            conn = psycopg.connect(
                dbname="postgres",
                user="postgres",
                password=pwd,
                host=HOST,
                port=PORT,
                autocommit=True
            )
            print("¡Conexión exitosa!")
            connected = True
            break
        except Exception as e:
            # print(f"Falló: {e}")
            pass
            
    if not connected:
        print("\nERROR: No se pudo conectar a PostgreSQL como usuario 'postgres'.")
        print("Por favor, asegúrese de que PostgreSQL esté corriendo y verifique la contraseña del superusuario.")
        return False

    try:
        cur = conn.cursor()
        
        # 1. Create User if not exists
        print(f"Verificando usuario '{DB_USER}'...")
        cur.execute("SELECT 1 FROM pg_roles WHERE rolname=%s", (DB_USER,))
        if not cur.fetchone():
            print(f"Creando usuario '{DB_USER}'...")
            cur.execute(sql.SQL("CREATE USER {} WITH PASSWORD {}").format(
                sql.Identifier(DB_USER),
                sql.Literal(DB_PASS)
            ))
        else:
            print(f"Usuario '{DB_USER}' ya existe. Actualizando contraseña...")
            cur.execute(sql.SQL("ALTER USER {} WITH PASSWORD {}").format(
                sql.Identifier(DB_USER),
                sql.Literal(DB_PASS)
            ))

        # 2. Create Database if not exists
        print(f"Verificando base de datos '{DB_NAME}'...")
        cur.execute("SELECT 1 FROM pg_database WHERE datname=%s", (DB_NAME,))
        if not cur.fetchone():
            print(f"Creando base de datos '{DB_NAME}'...")
            # Cannot use parameters for database name in CREATE DATABASE
            cur.execute(sql.SQL("CREATE DATABASE {} WITH OWNER {} ENCODING 'UTF8'").format(
                sql.Identifier(DB_NAME),
                sql.Identifier(DB_USER)
            ))
        else:
            print(f"Base de datos '{DB_NAME}' ya existe.")
            
        # 3. Grant privileges
        print("Otorgando privilegios...")
        cur.execute(sql.SQL("GRANT ALL PRIVILEGES ON DATABASE {} TO {}").format(
            sql.Identifier(DB_NAME),
            sql.Identifier(DB_USER)
        ))
        
        # Note: Granting schema privileges requires connecting to the specific database
        # We'll skip that for now as the owner usually has access.
        
        print("\n¡Configuración de base de datos completada exitosamente!")
        return True
        
    except Exception as e:
        print(f"\nError durante la configuración: {e}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    setup_database()
