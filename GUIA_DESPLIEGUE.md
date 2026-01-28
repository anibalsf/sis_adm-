# 🚀 Guía de Despliegue - Sistema Sindicato Taipiplaya

Esta guía detalla los pasos necesarios para desplegar el sistema en un entorno de producción.

## 🐳 Opción A: Despliegue con Docker (Recomendado)

Esta es la forma más rápida y segura de desplegar. Docker instalará automáticamente la base de datos PostgreSQL, el servidor Python y el frontend.

### Requisitos
- **Docker** y **Docker Compose** instalados.

### Pasos para el Despliegue
1. **Preparar el entorno:** Asegúrate de estar en la carpeta raíz del proyecto.
2. **Ejecutar el comando de construcción:**
   ```bash
   docker compose up -d --build
   ```
3. **Verificar que todo esté corriendo:**
   ```bash
   docker ps
   ```
4. **Acceder al sistema:** Abre tu navegador en `http://tu-ip-o-dominio:8000`.

> [!TIP]
> Los archivos de medios (fotos, etc.) se guardarán en la carpeta `media/` de tu servidor y la base de datos se guardará en un volumen persistente gestionado por Docker, por lo que tus datos estarán seguros aunque reinicies los contenedores.

---

## Opción B: Despliegue Manual (Tradicional)

## 📋 Requisitos del Servidor
- **S.O.:** Linux (Ubuntu 22.04+ recomendado)
- **Base de Datos:** PostgreSQL 14+ o MySQL 8.0+
- **Python:** 3.10+
- **Node.js:** 18+
- **Servidor Web:** Nginx + Gunicorn

---

## 🔧 1. Preparación del Backend (Django)

### Clonar y Configurar Entorno
```bash
git clone <url-del-repositorio>
cd sistema_administracion
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Configurar Variables de Entorno
Crea un archivo `.env` basado en `.env.example`:
```bash
SECRET_KEY=un-secreto-muy-seguro
DEBUG=False
ALLOWED_HOSTS=tusindicato.com,www.tusindicato.com
DB_ENGINE=postgresql
DB_NAME=sindicato_db
...
```

### Migraciones y Archivos Estáticos
```bash
python manage.py migrate
python manage.py collectstatic --noinput
```

### Configurar Gunicorn
Se recomienda usar un archivo de servicio de systemd para mantener Gunicorn corriendo.

---

## ⚛️ 2. Preparación del Frontend (React)

### Configurar Variables de Entorno
En la carpeta `frontend/`, crea un archivo `.env`:
```env
VITE_API_URL=https://api.tusindicato.com/api
```

### Construir para Producción
```bash
cd frontend
npm install
npm run build
```
Esto generará una carpeta `dist/` que contiene los archivos estáticos listos para ser servidos por Nginx.

---

## 🌐 3. Configuración de Nginx

Ejemplo de configuración para `/etc/nginx/sites-available/sindicato`:

```nginx
server {
    listen 80;
    server_name tusindicato.com;

    # Frontend
    location / {
        root /var/www/sindicato/frontend/dist;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Static & Media
    location /static/ {
        alias /var/www/sindicato/staticfiles/;
    }

    location /media/ {
        alias /var/www/sindicato/media/;
    }
}
```

---

## 🔒 4. Seguridad (SSL)
Se recomienda encarecidamente usar Certbot para habilitar HTTPS:
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d tusindicato.com
```

---

## 📁 5. Backups Automáticos
Configura un cronjob para respaldar la base de datos diariamente:
```bash
# Ejemplo para PostgreSQL
crontab -e
0 3 * * * pg_dump -U user_db sindicato_db > /backups/db_$(date +\%F).sql
```

---

✨ **¡Listo! El sistema ya debería estar funcionando en producción.**
