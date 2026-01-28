# 🚀 COMANDOS RÁPIDOS - SINDICATO TAIPIPLAYA

## ⚡ EJECUTAR SISTEMA (Uso Diario)

### 🔹 BACKEND (Terminal 1)
```powershell
cd C:\Users\Once\Documents\trae_projects\sistema_administracion
.\.venv\Scripts\Activate.ps1
python manage.py runserver
```
✅ Backend: http://localhost:8000

---

### 🔹 FRONTEND (Terminal 2)
```powershell
cd C:\Users\Once\Documents\trae_projects\sistema_administracion\frontend
npm run dev
```
✅ Frontend: http://localhost:5173

---

## 🔧 COMANDOS DE DESARROLLO

### Migraciones
```powershell
# Crear migraciones
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate

# Ver SQL de migración
python manage.py sqlmigrate afiliados 0001
```

### Crear Superusuario
```powershell
python manage.py createsuperuser
```

### Shell Interactivo
```powershell
# Django shell
python manage.py shell

# Shell Plus (si tienes django-extensions)
python manage.py shell_plus
```

### Limpiar Base de Datos
```powershell
# Borrar todas las tablas y recrear
python manage.py flush

# Resetear migraciones de una app
python manage.py migrate afiliados zero
python manage.py migrate afiliados
```

---

## 📊 DATOS DE PRUEBA

### Crear Datos Iniciales
```powershell
# Tipos de pago
python crear_tipos_pago.py

# Rutas
python crear_rutas.py
python crear_ruta_la_paz.py

# Configurar Caranavi
python configurar_caranavi.py

# Datos de almacenamiento
python crear_hojas_prueba.py
python crear_datos_prueba_tesoreria.py

# Designar vehículos
python designar_vehiculos_la_paz.py
```

---

## 🛠️ INSTALACIÓN INICIAL (Primera vez)

### Backend
```powershell
# Crear entorno virtual
python -m venv .venv

# Activar entorno
.\.venv\Scripts\Activate.ps1

# Instalar dependencias
pip install -r requirements.txt

# Migraciones
python manage.py migrate

# Superusuario
python manage.py createsuperuser
```

### Frontend
```powershell
cd frontend

# Instalar dependencias
npm install
```

---

## 📦 ACTUALIZAR DEPENDENCIAS

### Backend
```powershell
# Actualizar todas las dependencias
pip install --upgrade -r requirements.txt

# Actualizar una específica
pip install --upgrade djangorestframework

# Listar outdated
pip list --outdated
```

### Frontend
```powershell
cd frontend

# Actualizar todas
npm update

# Actualizar una específica
npm update react

# Ver outdated
npm outdated
```

---

## 🐛 DEBUGGING

### Ver Logs
```powershell
# Ver logs en tiempo real
Get-Content -Path "logs\django.log" -Wait

# Ver últimas 50 líneas
Get-Content -Path "logs\django.log" -Tail 50

# Ver solo errores
Get-Content -Path "logs\errors.log" -Wait
```

### Modo Debug
```python
# En settings.py cambiar temporalmente:
DEBUG = True
```

---

## 🧪 TESTING

```powershell
# Ejecutar todos los tests
pytest

# Tests de una app específica
pytest afiliados/

# Con cobertura
pytest --cov=.

# Generar reporte HTML
pytest --cov=. --cov-report=html
```

---

## 📤 EXPORTAR/IMPORTAR DATOS

### Backup
```powershell
# Exportar todos los datos
python manage.py dumpdata > backup_completo.json

# Exportar datos de una app
python manage.py dumpdata afiliados > backup_afiliados.json

# Sin datos de sesiones
python manage.py dumpdata --exclude auth.permission --exclude contenttypes > backup.json
```

### Restore
```powershell
# Importar datos
python manage.py loaddata backup_completo.json

# Importar de una app específica
python manage.py loaddata backup_afiliados.json
```

---

## 🔒 SEGURIDAD

### Generar SECRET_KEY Nueva
```powershell
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### Cambiar Password
```powershell
python manage.py changepassword admin
```

---

## 🌐 PRODUCCIÓN

### Collect Static Files
```powershell
python manage.py collectstatic --noinput
```

### Build Frontend
```powershell
cd frontend
npm run build
```

### Run con Gunicorn
```powershell
gunicorn sistema.wsgi:application --bind 0.0.0.0:8000
```

---

## 🔍 INFORMACIÓN DEL SISTEMA

### Verificar Configuración
```powershell
python manage.py check

# Con deployment checks
python manage.py check --deploy
```

### Ver Migraciones
```powershell
# Todas las migraciones
python manage.py showmigrations

# De una app específica
python manage.py showmigrations afiliados
```

### Ver URLs
```powershell
# Listar todas las URLs
python manage.py show_urls
```

---

## 📝 ÚTILES

### Limpiar Cache
```powershell
# Python cache
Get-ChildItem -Include __pycache__ -Recurse -force | Remove-Item -Force -Recurse

# NPM cache
npm cache clean --force
```

### Git
```powershell
# Estado
git status

# Commit
git add .
git commit -m "Descripción del cambio"

# Push
git push origin main

# Ver log
git log --oneline -10
```

---

## 🆘 SOLUCIÓN DE PROBLEMAS

### Puerto en uso
```powershell
# Backend en otro puerto
python manage.py runserver 8001

# Frontend en otro puerto
npm run dev -- --port 5174
```

### Recrear node_modules
```powershell
cd frontend
Remove-Item -Recurse -Force node_modules
Remove-Item package-lock.json
npm install
```

### Recrear venv
```powershell
Remove-Item -Recurse -Force .venv
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Permisos PowerShell
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

✨ **Nota:** Mantén siempre 2 terminales abiertas (Backend + Frontend) mientras desarrollas
