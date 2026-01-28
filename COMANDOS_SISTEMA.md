# ⚡ Comandos Rápidos del Sistema

## 🚀 Iniciar el Sistema

### Backend
```powershell
python manage.py runserver
```

### Frontend
```powershell
cd frontend
npm run dev
```

### Celery Worker (Procesa mensajes de WhatsApp y tareas)
```powershell
celery -A sistema worker -l info
```

### Celery Beat (Programa reportes automáticos)
```powershell
celery -A sistema beat -l info
```

## 🔧 Comandos de Desarrollo

### Migraciones
```powershell
# Crear migraciones
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate

# Ver estado de migraciones
python manage.py showmigrations
```

### Usuarios
```powershell
# Crear superusuario
python manage.py createsuperuser

# Crear usuario de prueba
python crear_superusuario.py
```

### Base de Datos
```powershell
# Verificar conexión
python manage.py check

# Shell de Django
python manage.py shell
```

## 🧪 Comandos de Prueba

### Probar Celery
```powershell
# Probar todas las tareas
python test_celery_tasks.py

# Probar una tarea específica desde shell
python manage.py shell
>>> from reportes_auto.tasks import send_daily_report_task
>>> send_daily_report_task.delay()
```

### Verificar WhatsApp
```powershell
python verify_whatsapp.py
```

### Verificar Reportes
```powershell
python verify_reports.py
```

## 📊 Comandos de Datos

### Crear Datos de Prueba
```powershell
# Rutas
python crear_rutas.py

# Tipos de pago
python crear_tipos_pago.py

# Plantillas de WhatsApp
python crear_plantillas_whatsapp.py
```

### Backup
```powershell
# Backup de PostgreSQL
.\backup_postgresql.ps1

# Backup manual
python manage.py dumpdata > backup.json
```

## 🔍 Comandos de Monitoreo

### Ver Logs
```powershell
# Logs de Django
type logs\django.log

# Logs de errores
type logs\errors.log
```

### Estado de Celery
```powershell
# Ver tareas activas
celery -A sistema inspect active

# Ver tareas programadas
celery -A sistema inspect scheduled

# Ver workers registrados
celery -A sistema inspect registered
```

## 🛠️ Comandos de Mantenimiento

### Limpiar Sistema
```powershell
python limpiar_sistema.py
```

### Actualizar Dependencias
```powershell
# Backend
pip install -r requirements.txt --upgrade

# Frontend
cd frontend
npm update
```

### Recolectar Archivos Estáticos
```powershell
python manage.py collectstatic --noinput
```

## 🌐 URLs Importantes

- **Frontend:** http://localhost:5173
- **Backend API:** http://127.0.0.1:8000
- **Admin:** http://127.0.0.1:8000/admin
- **API Docs:** http://127.0.0.1:8000/api/schema/swagger-ui/

## 🔐 Credenciales por Defecto

**Admin:**
- Usuario: admin
- Password: (configurar con createsuperuser)

## 📝 Notas Importantes

1. **Redis debe estar corriendo** antes de iniciar Celery
2. **PostgreSQL debe estar activo** para el backend
3. Para **desarrollo rápido**, solo necesitas Backend + Frontend
4. Para **funcionalidad completa**, necesitas los 4 servicios (Backend, Frontend, Worker, Beat)

## 🆘 Comandos de Emergencia

### Resetear Migraciones
```powershell
# ⚠️ CUIDADO: Esto borra la base de datos
python manage.py flush
python manage.py migrate
```

### Reiniciar Celery
```powershell
# Detener todos los workers
taskkill /F /IM celery.exe

# Reiniciar
celery -A sistema worker -l info
```

### Limpiar Cache de Redis
```powershell
redis-cli FLUSHALL
```
