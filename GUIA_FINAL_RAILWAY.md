# 🌐 Guía de Configuración Final en Railway.app

Una vez que hayas subido tu código a GitHub y conectado el repositorio a Railway, sigue estos pasos para que el sistema funcione perfectamente en internet.

## 1. Conectar PostgreSQL
Para que el sistema guarde datos de forma segura:
1. En tu proyecto de Railway, haz clic en **"New"** (o "Add Service").
2. Selecciona **"Database"** -> **"Add PostgreSQL"**.
3. Railway creará la base de datos y generará automáticamente una variable llamada `DATABASE_URL` que el sistema usará para conectarse.

## 2. Configurar Variables de Entorno
Ve a la pestaña **"Variables"** de tu servicio de Backend (el que viene de GitHub) y añade las siguientes:

| Nombre de Variable | Valor Sugerido | Descripción |
| :--- | :--- | :--- |
| `DATABASE_URL` | *Se llena sola* | Conexión a la base de datos. |
| `SECRET_KEY` | `p9k!&mj_@-%c_b1728pgwo!%s0=+nr%w(=+l391$8z+*-w77r=` | La clave de seguridad que generamos. |
| `DEBUG` | `False` | **IMPORTANTE** para seguridad en internet. |
| `ALLOWED_HOSTS` | `*` | Permite que el sistema responda en su nueva URL. |
| `ENVIRONMENT` | `production` | Indica al sistema que está en línea. |
| `CORS_ALLOWED_ORIGINS` | `https://tu-dominio.up.railway.app` | El enlace que te asigne Railway. |

## 3. Comandos de Inicialización (Deploy)
En la configuración del servicio en Railway, asegúrate de que el **"Start Command"** sea:
```bash
gunicorn sistema.wsgi --bind 0.0.0.0:$PORT
```
Y para preparar la base de datos la primera vez, puedes ejecutar desde la consola de Railway (o añadir al script de despliegue):
```bash
python manage.py migrate
python manage.py collectstatic --noinput
```

## 4. Crear tu primer Usuario Administrador
Como la base de datos en internet empezará vacía, deberás crear un nuevo superusuario. 
En la terminal de Railway (View Logs -> Terminal), escribe:
```bash
python manage.py createsuperuser
```
Sigue los pasos para crear tu usuario, correo y contraseña.

---
✨ **¡Listo! Con esto el Sindicato Taipiplaya tendrá su sistema funcionando oficialmente en la nube.**
