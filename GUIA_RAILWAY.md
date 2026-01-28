# 🚂 Guia Completa: Desplegar en Railway (Backend y Base de Datos)

Railway es la plataforma más facil para subir tu **Backend (Django)** y tu **Base de Datos (PostgreSQL)**. Aquí tienes los pasos detallados:

---

## 🔧 PASO 1: Preparar tu Proyecto (Antes de subir)

Necesitamos asegurarnos de que Railway sepa cómo ejecutar tu Django.

1.  **Verifica tu archivo `Procfile`**:
    *   Crea un archivo llamado `Procfile` (sin extensión) en la raíz de tu proyecto.
    *   Escribe esto dentro:
        ```text
        web: gunicorn sistema.wsgi --log-file -
        ```

2.  **Verifica tu `requirements.txt`**:
    *   Asegúrate de que `gunicorn`, `psycopg2-binary` y `dj-database-url` estén en tu archivo `requirements.txt`.
    *   Si no estan, agregalos manualmente.

3.  **Configura `settings.py` para Railway**:
    *   Abre `sistema/settings.py` y busca la parte de DATABASE.
    *   Asegúrate de tener esto (para que lea la URL de Railway automáticamente):
        ```python
        import dj_database_url
        
        # ... al final del archivo o donde está DATABASES ...
        
        DATABASE_URL = os.environ.get('DATABASE_URL')
        if DATABASE_URL:
            DATABASES['default'] = dj_database_url.config(default=DATABASE_URL, conn_max_age=600)
        ```

---

## ☁️ PASO 2: Subir a GitHub
(Si ya lo hiciste para Vercel, salta este paso).
1.  Crea un repositorio en GitHub.
2.  Sube todo tu codigo.

---

## 🚀 PASO 3: Desplegar en Railway

1.  **Crea tu cuenta**:
    *   Ve a [railway.app](https://railway.app) y regístrate con tu cuenta de GitHub.

2.  **Nuevo Proyecto**:
    *   Click en el botón grande **"New Project"**.
    *   Selecciona **"Deploy from GitHub repo"**.
    *   Busca y selecciona tu repositorio (ej: `sistema-sindicato`).
    *   Click en **"Deploy Now"**.

3.  **Agregar Base de Datos**:
    *   Una vez creado el proyecto, verás una caja con tu repositorio.
    *   Click derecho en el fondo vacío -> **"New Service"** -> **"Database"** -> **"PostgreSQL"**.
    *   Espera unos segundos a que se instale.

4.  **Conectar Django con PostgreSQL**:
    *   Click en tu **servicio de PostgreSQL** -> Pestaña **"Variables"**.
    *   Copia el valor de `DATABASE_URL` (se ve oculto, dale al ojo o botón copiar).
    *   Ahora ve a tu **servicio de Django (GitHub)** -> Pestaña **"Variables"**.
    *   Click en **"New Variable"** y agrega:
        *   **`DATABASE_URL`**: Pegar el valor que copiaste.
        *   **`SECRET_KEY`**: Inventa una clave larga y segura.
        *   **`DEBUG`**: `False`
        *   **`ALLOWED_HOSTS`**: `*`
        *   **`PORT`**: `8000`

5.  **Generar Dominio (URL Pública)**:
    *   Ve a la pestaña **"Settings"** de tu servicio Django.
    *   Baja a la sección **"Networking"**.
    *   Click en **"Generate Domain"**.
    *   ¡Listo! Te dará una URL como `sistema-sindicato-production.up.railway.app`.

---

## ✅ PASO 4: Comandos Finales (Migraciones)

Ahora que está corriendo, necesitamos crear las tablas en la base de datos nueva.

1.  En Railway, click en tu servicio Django.
2.  Ve a la pestaña **"Builds"** (o usa el Railway CLI si lo prefieres, pero esto es más fácil).
3.  En realidad, lo mejor es agregar un "Start Command" en **Settings**:
    *   Busca **"Deploy"** -> **"Start Command"**.
    *   Pon esto: `python manage.py migrate && gunicorn sistema.wsgi`
    *   Esto ejecutará las migraciones automáticamente cada vez que hagas un cambio.

---

## 🔗 PASO 5: Conectar con el Frontend

Copia esa URL generada en el paso 3 (`https://...up.railway.app`) y úsala en tu Frontend (Vercel) como la variable `VITE_API_URL`.

¡Y eso es todo! Tu backend está en la nube. 🚂
