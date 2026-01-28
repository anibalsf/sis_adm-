# 🚀 Comandos para Ejecutar el Sistema

Esta guía te muestra paso a paso cómo ejecutar el sistema completo (Backend Django + Frontend React).

---

## 📋 Requisitos Previos

Asegúrate de tener instalado:
- ✅ Python 3.10 o superior
- ✅ Node.js 16 o superior
- ✅ MySQL 8.0 o superior

---

## 🔧 BACKEND (Django)

### 1️⃣ Abrir una terminal en el directorio del proyecto

```powershell
cd C:\Users\Once\Documents\trae_projects\sistema_administracion
```

### 2️⃣ Activar el entorno virtual

```powershell
# Si ya existe el entorno virtual
.\.venv\Scripts\Activate.ps1

# Si NO existe, créalo primero:
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3️⃣ Instalar/Actualizar dependencias (solo la primera vez o si hay cambios)

```powershell
pip install -r requirements.txt
```

### 4️⃣ Configurar la base de datos (solo la primera vez)

```powershell
# Ejecutar migraciones
python manage.py migrate

# Crear superusuario (admin)
python manage.py createsuperuser
```

### 5️⃣ Ejecutar el servidor de desarrollo

```powershell
python manage.py runserver
```

✅ **El backend estará corriendo en:** `http://localhost:8000`
- API: `http://localhost:8000/api/`
- Admin: `http://localhost:8000/admin/`

---

## ⚛️ FRONTEND (React)

### 1️⃣ Abrir UNA NUEVA terminal (mantén la del backend abierta)

```powershell
cd C:\Users\Once\Documents\trae_projects\sistema_administracion\frontend
```

### 2️⃣ Instalar dependencias (solo la primera vez o si hay cambios)

```powershell
npm install
```

### 3️⃣ Ejecutar el servidor de desarrollo

```powershell
npm run dev
```

✅ **El frontend estará corriendo en:** `http://localhost:5173`

---

## 🎯 Resumen de Comandos Rápidos

### Para el BACKEND:
```powershell
cd C:\Users\Once\Documents\trae_projects\sistema_administracion
.\.venv\Scripts\Activate.ps1
python manage.py runserver
```

### Para el FRONTEND:
```powershell
cd C:\Users\Once\Documents\trae_projects\sistema_administracion\frontend
npm run dev
```

---

## 🔍 URLs Importantes

| Servicio | URL | Descripción |
|----------|-----|-------------|
| **Frontend** | http://localhost:5173 | Aplicación React |
| **Backend API** | http://localhost:8000/api/ | API REST |
| **Admin Django** | http://localhost:8000/admin/ | Panel de administración |
| **API Afiliados** | http://localhost:8000/api/afiliados/ | Endpoint de afiliados |
| **API Vehículos** | http://localhost:8000/api/vehiculos/ | Endpoint de vehículos |

---

## ❌ Detener los Servidores

### Detener Backend:
- Presiona `Ctrl + C` en la terminal del backend

### Detener Frontend:
- Presiona `Ctrl + C` en la terminal del frontend

---

## 🐛 Solución de Problemas Comunes

### Error: "No module named..."
```powershell
# Asegúrate de estar en el entorno virtual
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Error: "Database connection failed"
```powershell
# Verifica que MySQL esté corriendo
# Verifica las credenciales en el archivo .env
```

### Error: "Port already in use"
```powershell
# Backend en otro puerto:
python manage.py runserver 8001

# Frontend en otro puerto:
npm run dev -- --port 5174
```

### Error al activar entorno virtual
```powershell
# Si hay problemas de permisos en PowerShell:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## 📝 Notas Importantes

- **Siempre ejecuta el BACKEND primero** antes del frontend
- **Mantén AMBAS terminales abiertas** mientras trabajas
- El frontend se conecta automáticamente a `http://localhost:8000`
- Los cambios en el código se recargan automáticamente en ambos servidores

---

## 🎨 Próximos Pasos

1. Accede a http://localhost:5173 para ver el frontend
2. Accede a http://localhost:8000/admin/ para gestionar datos
3. Usa el API en http://localhost:8000/api/ para interactuar con el backend

## 🛡️ Mantenimiento y Seguridad (Producción)

### 1️⃣ Respaldos de Base de Datos
He incluido un script para respaldar automáticamente la base de datos PostgreSQL.

**Para ejecutar un respaldo manual:**
```powershell
python scripts/backup_db.py
```
*Los respaldos se guardarán en la carpeta `/backups` y se mantienen automáticamente los últimos 7 días.*

**Para programar respaldos automáticos en Windows:**
1. Abre "Programador de tareas" (Task Scheduler).
2. Crea una "Tarea Básica" llamada "Respaldo Sistema Transportes".
3. Gatillo: Diariamente a las 02:00 AM.
4. Acción: Iniciar un programa.
5. Programa/script: `C:\Users\Once\Documents\trae_projects\sistema_administracion\.venv\Scripts\python.exe`
6. Argumentos: `C:\Users\Once\Documents\trae_projects\sistema_administracion\scripts\backup_db.py`
7. Iniciar en: `C:\Users\Once\Documents\trae_projects\sistema_administracion`

---

✨ **¡Listo! El sistema ya debería estar funcionando correctamente con todas las mejoras de producción.**
