# 🚀 Guía Rápida de Inicio - Sistema Completo

## Prerrequisitos
- Python 3.8+
- Node.js 16+
- PostgreSQL (o SQLite para desarrollo)
- Redis

## 🔧 Instalación

### 1. Backend
```bash
# Activar entorno virtual
.venv\Scripts\activate  # Windows
# o
source .venv/bin/activate  # Linux/Mac

# Instalar dependencias
pip install -r requirements.txt

# Aplicar migraciones
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser
```

### 2. Frontend
```bash
cd frontend
npm install
```

### 3. Redis
Asegúrate de tener Redis corriendo en `localhost:6379`

## ▶️ Ejecutar el Sistema

### Opción 1: Desarrollo Completo (4 terminales)

**Terminal 1 - Backend:**
```bash
python manage.py runserver
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

**Terminal 3 - Celery Worker:**
```bash
celery -A sistema worker -l info
```

**Terminal 4 - Celery Beat:**
```bash
celery -A sistema beat -l info
```

### Opción 2: Solo Backend y Frontend (sin tareas programadas)

**Terminal 1:**
```bash
python manage.py runserver
```

**Terminal 2:**
```bash
cd frontend
npm run dev
```

## 🧪 Probar el Sistema

### Verificar Backend
```bash
python manage.py check
```

### Probar Tareas de Celery
```bash
python test_celery_tasks.py
```

### Acceder a la Aplicación
- **Frontend:** http://localhost:5173
- **Backend API:** http://127.0.0.1:8000
- **Admin:** http://127.0.0.1:8000/admin

## 📝 Configuración Inicial

### 1. Configurar WhatsApp (Admin)
1. Ir a `/admin/whatsapp_notif/whatsappconfig/`
2. Activar el servicio
3. Seleccionar proveedor (Twilio)

### 2. Crear Plantillas de WhatsApp
1. Ir a `/admin/whatsapp_notif/whatsapptemplate/`
2. Crear plantillas para:
   - payment_confirmation
   - shift_reminder
   - meeting_reminder
   - debt_reminder

### 3. Configurar Reportes Automáticos
1. Ir a `/admin/reportes_auto/configuracionreporte/`
2. Crear configuraciones para reportes diario, semanal y mensual
3. Agregar números de teléfono de destinatarios

## 🔍 Verificar que Todo Funciona

### Check 1: Base de Datos
```bash
python manage.py showmigrations
```

### Check 2: Celery Worker
Debe mostrar las tareas registradas al iniciar

### Check 3: Celery Beat
Debe mostrar el schedule configurado

### Check 4: WhatsApp
Enviar un mensaje de prueba desde el admin

## 🆘 Solución de Problemas

### Error: Redis no conecta
```bash
# Verificar que Redis esté corriendo
redis-cli ping
# Debe responder: PONG
```

### Error: Celery no encuentra tareas
```bash
# Verificar que las apps estén en INSTALLED_APPS
python manage.py shell
>>> from django.conf import settings
>>> print(settings.INSTALLED_APPS)
```

### Error: Frontend no conecta con Backend
Verificar CORS en `settings.py`:
```python
CORS_ALLOWED_ORIGINS = [
    'http://localhost:5173',
    'http://localhost:3000',
]
```

## 📚 Documentación Adicional
- `PLAN_MEJORAS_FASE1.md` - Plan original
- `RESUMEN_IMPLEMENTACION_FASE1.md` - Resumen de lo implementado
- `CONFIGURACION_WHATSAPP.md` - Guía de configuración de WhatsApp
