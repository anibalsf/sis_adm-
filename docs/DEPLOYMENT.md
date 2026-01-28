# Guía de Deployment - Sistema Sindicato Taipiplaya

Esta guía proporciona instrucciones paso a paso para desplegar el sistema en diferentes ambientes.

## 📋 Tabla de Contenidos

- [Requisitos del Servidor](#requisitos-del-servidor)
- [Deployment en Servidor Linux (Ubuntu/Debian)](#deployment-en-servidor-linux)
- [Configuración con Nginx](#configuración-con-nginx)
- [Configuración con Docker](#configuración-con-docker)
- [Variables de Entorno de Producción](#variables-de-entorno-de-producción)
- [SSL/HTTPS](#sslhttps)
- [Backup y Restauración](#backup-y-restauración)
- [Monitoreo](#monitoreo)

---

## 🖥️ Requisitos del Servidor

### Hardware Mínimo Recomendado

- **CPU**: 2 cores
- **RAM**: 4 GB
- **Disco**: 20 GB SSD
- **Ancho de banda**: 100 Mbps

### Software Requerido

- Ubuntu 20.04 LTS o superior / Debian 11+
- Python 3.10+
- MySQL 8.0+ o PostgreSQL 13+
- Nginx 1.18+
- Supervisor (para gestión de procesos)
- Git

---

## 🚀 Deployment en Servidor Linux

### 1. Actualizar el Sistema

```bash
sudo apt update && sudo apt upgrade -y
```

### 2. Instalar Dependencias del Sistema

```bash
sudo apt install -y python3 python3-pip python3-venv \
    mysql-server mysql-client libmysqlclient-dev \
    nginx supervisor git
```

### 3. Configurar MySQL

```bash
# Ejecutar script de seguridad
sudo mysql_secure_installation

# Crear base de datos y usuario
sudo mysql -u root -p
```

```sql
CREATE DATABASE sindicato_taipiplaya CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'sindicato_user'@'localhost' IDENTIFIED BY 'tu_password_seguro';
GRANT ALL PRIVILEGES ON sindicato_taipiplaya.* TO 'sindicato_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### 4. Crear Usuario de Sistema

```bash
sudo adduser --system --group --home /opt/sindicato sindicato
sudo su - sindicato
```

### 5. Clonar el Repositorio

```bash
cd /opt/sindicato
git clone <url-del-repositorio> app
cd app
```

### 6. Configurar Entorno Virtual

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 7. Configurar Variables de Entorno

```bash
cp .env.example .env
nano .env
```

Configurar con valores de producción (ver sección [Variables de Entorno](#variables-de-entorno-de-producción)).

### 8. Ejecutar Migraciones y Collectstatic

```bash
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

### 9. Probar Gunicorn

```bash
gunicorn sistema.wsgi:application --bind 0.0.0.0:8000
# Verificar que funciona, luego Ctrl+C para detener
```

---

## 🌐 Configuración con Nginx

### 1. Crear Configuración de Nginx

```bash
sudo nano /etc/nginx/sites-available/sindicato
```

```nginx
upstream sindicato_app {
    server 127.0.0.1:8000 fail_timeout=0;
}

server {
    listen 80;
    server_name tu-dominio.com www.tu-dominio.com;
    
    client_max_body_size 20M;
    
    # Logs
    access_log /var/log/nginx/sindicato_access.log;
    error_log /var/log/nginx/sindicato_error.log;
    
    # Static files
    location /static/ {
        alias /opt/sindicato/app/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    # Media files
    location /media/ {
        alias /opt/sindicato/app/media/;
        expires 7d;
    }
    
    # Proxy to Django
    location / {
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Host $http_host;
        proxy_redirect off;
        proxy_pass http://sindicato_app;
    }
}
```

### 2. Activar Sitio

```bash
sudo ln -s /etc/nginx/sites-available/sindicato /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## 🔧 Configuración de Supervisor

### 1. Crear Configuración de Supervisor

```bash
sudo nano /etc/supervisor/conf.d/sindicato.conf
```

```ini
[program:sindicato]
command=/opt/sindicato/app/venv/bin/gunicorn sistema.wsgi:application --bind 127.0.0.1:8000 --workers 3 --timeout 120
directory=/opt/sindicato/app
user=sindicato
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/opt/sindicato/app/logs/gunicorn.log
stderr_logfile=/opt/sindicato/app/logs/gunicorn_error.log
environment=PATH="/opt/sindicato/app/venv/bin"
```

### 2. Activar Supervisor

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start sindicato
sudo supervisorctl status sindicato
```

---

## 🐳 Configuración con Docker

### 1. Crear Dockerfile

Ver archivo `Dockerfile` en el proyecto.

### 2. Crear docker-compose.yml

Ver archivo `docker-compose.yml` en el proyecto.

### 3. Desplegar

```bash
docker-compose up -d
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
docker-compose exec web python manage.py collectstatic --noinput
```

---

## 🔐 Variables de Entorno de Producción

Ejemplo de `.env` para producción:

```env
# Django
SECRET_KEY=<generar-key-segura-con-comando-python>
DEBUG=False
ENVIRONMENT=production
ALLOWED_HOSTS=tu-dominio.com,www.tu-dominio.com

# Database
DB_ENGINE=mysql
DB_NAME=sindicato_taipiplaya
DB_USER=sindicato_user
DB_PASSWORD=<password-seguro>
DB_HOST=localhost
DB_PORT=3306

# CORS
CORS_ENABLED=True
CORS_ALLOWED_ORIGINS=https://frontend.tu-dominio.com
CORS_ALLOW_CREDENTIALS=True

# Static/Media
STATIC_URL=/static/
STATIC_ROOT=/opt/sindicato/app/staticfiles
MEDIA_URL=/media/
MEDIA_ROOT=/opt/sindicato/app/media

# Logging
LOG_LEVEL=WARNING
LOG_DIR=/opt/sindicato/app/logs

# Business
SANCTION_ABSENCE_AMOUNT=50
PAGE_SIZE=20
```

---

## 🔒 SSL/HTTPS con Let's Encrypt

### 1. Instalar Certbot

```bash
sudo apt install certbot python3-certbot-nginx -y
```

### 2. Obtener Certificado

```bash
sudo certbot --nginx -d tu-dominio.com -d www.tu-dominio.com
```

### 3. Auto-renovación

El certificado se renueva automáticamente. Verificar:

```bash
sudo certbot renew --dry-run
```

---

## 💾 Backup y Restauración

### Backup de Base de Datos

```bash
# MySQL
mysqldump -u sindicato_user -p sindicato_taipiplaya > backup_$(date +%Y%m%d).sql

# Comprimir
gzip backup_$(date +%Y%m%d).sql
```

### Restaurar Base de Datos

```bash
# Descomprimir
gunzip backup_20231201.sql.gz

# Restaurar
mysql -u sindicato_user -p sindicato_taipiplaya < backup_20231201.sql
```

### Script de Backup Automático

```bash
sudo nano /opt/sindicato/backup.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/opt/sindicato/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup DB
mysqldump -u sindicato_user -p'PASSWORD' sindicato_taipiplaya | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Backup Media
tar -czf $BACKUP_DIR/media_$DATE.tar.gz /opt/sindicato/app/media/

# Eliminar backups antiguos (más de 30 días)
find $BACKUP_DIR -type f -mtime +30 -delete
```

### Configurar Cron

```bash
sudo crontab -e
```

```
# Backup diario a las 2 AM
0 2 * * * /opt/sindicato/backup.sh
```

---

## 📊 Monitoreo

### Logs del Sistema

```bash
# Logs de Nginx
sudo tail -f /var/log/nginx/sindicato_access.log
sudo tail -f /var/log/nginx/sindicato_error.log

# Logs de Django
tail -f /opt/sindicato/app/logs/django.log
tail -f /opt/sindicato/app/logs/errors.log

# Logs de Gunicorn
tail -f /opt/sindicato/app/logs/gunicorn.log
```

### Supervisor

```bash
sudo supervisorctl status
sudo supervisorctl restart sindicato
sudo supervisorctl tail -f sindicato
```

### Verificar Estado del Sistema

```bash
# Estado de servicios
sudo systemctl status nginx
sudo systemctl status mysql
sudo systemctl status supervisor

# Uso de recursos
htop
df -h
free -h
```

---

## 🔄 Actualización del Sistema

### 1. Hacer Backup

```bash
/opt/sindicato/backup.sh
```

### 2. Actualizar Código

```bash
cd /opt/sindicato/app
git pull origin main
source venv/bin/activate
pip install -r requirements.txt --upgrade
```

### 3. Migrar y Collectstatic

```bash
python manage.py migrate
python manage.py collectstatic --noinput
```

### 4. Reiniciar Servicios

```bash
sudo supervisorctl restart sindicato
sudo systemctl reload nginx
```

---

## 🆘 Troubleshooting

### Error 502 Bad Gateway

```bash
# Verificar que Gunicorn esté corriendo
sudo supervisorctl status sindicato

# Revisar logs
tail -f /opt/sindicato/app/logs/gunicorn_error.log
```

### Error de Base de Datos

```bash
# Verificar conexión
mysql -u sindicato_user -p sindicato_taipiplaya

# Revisar configuración en .env
cat /opt/sindicato/app/.env
```

### Permisos de Archivos

```bash
sudo chown -R sindicato:sindicato /opt/sindicato/app
sudo chmod -R 755 /opt/sindicato/app
```

---

## 📞 Soporte

Para problemas de deployment, crear un issue en el repositorio con:
- Logs relevantes
- Pasos para reproducir el problema
- Configuración del servidor (sin passwords)

---

Desarrollado con ❤️ para el Sindicato Mixto de Transporte Integración Taipiplaya
