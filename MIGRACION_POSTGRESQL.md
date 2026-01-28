# 🔄 GUÍA DE MIGRACIÓN A POSTGRESQL

**Sistema:** Sindicato Mixto de Transporte Integración Taipiplaya  
**De:** SQLite  
**A:** PostgreSQL 16+  
**Tiempo estimado:** 30-45 minutos

---

## ✅ PRE-REQUISITOS

- [ ] PostgreSQL 16+ instalado
- [ ] Backup de datos actual (automático en este proceso)
- [ ] Backend detenido

---

## 📋 PASO 1: INSTALAR POSTGRESQL (Windows)

### Opción A: Instalador Oficial (Recomendado)

1. **Descargar PostgreSQL:**
   - Ir a: https://www.postgresql.org/download/windows/
   - Descargar instalador de EnterpriseDB
   - Versión recomendada: **PostgreSQL 16.x**

2. **Instalar:**
   - Ejecutar el instalador descargado
   - **Puerto:** 5432 (default)
   - **Contraseña del superusuario (postgres):** ⚠️ **ANOTAR ESTA CONTRASEÑA**
   - Componentes a instalar:
     - ✅ PostgreSQL Server
     - ✅ pgAdmin 4
     - ✅ Command Line Tools
     - ⬜ Stack Builder (opcional)

3. **Verificar instalación:**
```powershell
# Abrir PowerShell y ejecutar:
psql --version
# Debe mostrar: psql (PostgreSQL) 16.x
```

### Opción B: Con Chocolatey

```powershell
# Si tienes Chocolatey instalado:
choco install postgresql16

# Iniciar servicio
net start postgresql-x64-16
```

---

## 🗄️ PASO 2: CREAR BASE DE DATOS

### A. Usando pgAdmin 4 (Interfaz Gráfica)

1. **Abrir pgAdmin 4** (instalado con PostgreSQL)
2. **Conectar al servidor** (click en "PostgreSQL 16")
   - Contraseña: la que anotaste en la instalación
3. **Crear nueva base de datos:**
   - Click derecho en "Databases" → "Create" → "Database"
   - **Database name:** `sindicato_taipiplaya`
   - **Owner:** postgres
   - **Encoding:** UTF8
   - Click "Save"

4. **Crear usuario para la aplicación:**
   - Click derecho en "Login/Group Roles" → "Create" → "Login/Group Role"
   - **General tab:**
     - Name: `admin_sindicato`
   - **Definition tab:**
     - Password: `Taipiplaya2025!` (o la que prefieras)
   - **Privileges tab:**
     - ✅ Can login
     - ✅ Create databases
   - Click "Save"

5. **Dar permisos al usuario:**
   - Click derecho en la base de datos `sindicato_taipiplaya` → "Properties"
   - Tab "Security"
   - Click "+" para agregar
   - **Grantee:** admin_sindicato
   - **Privileges:** ALL
   - Click "Save"

### B. Usando SQL Shell (psql) - Línea de Comandos

```powershell
# 1. Abrir "SQL Shell (psql)" desde el menú de inicio
# 2. Presionar Enter para valores por defecto hasta llegar a Password
# 3. Ingresar la contraseña del usuario postgres

# 4. Ejecutar estos comandos SQL:
```

```sql
-- Crear la base de datos
CREATE DATABASE sindicato_taipiplaya 
    WITH 
    ENCODING 'UTF8' 
    LC_COLLATE='Spanish_Bolivia.1252' 
    LC_CTYPE='Spanish_Bolivia.1252'
    TEMPLATE=template0;

-- Crear usuario de la aplicación
CREATE USER admin_sindicato WITH PASSWORD 'Taipiplaya2025!';

-- Dar permisos completos
ALTER DATABASE sindicato_taipiplaya OWNER TO admin_sindicato;

-- Dar privilegios
GRANT ALL PRIVILEGES ON DATABASE sindicato_taipiplaya TO admin_sindicato;

-- Conectar a la nueva base de datos
\c sindicato_taipiplaya

-- Dar permisos sobre el esquema público
GRANT ALL ON SCHEMA public TO admin_sindicato;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO admin_sindicato;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO admin_sindicato;

-- Mostrar bases de datos para verificar
\l

-- Salir
\q
```

✅ **Verificación:** Deberías ver `sindicato_taipiplaya` en la lista de bases de datos.

---

## 🔧 PASO 3: EJECUTAR SCRIPT DE MIGRACIÓN

Ya tenemos un script que hará todo automáticamente:

```powershell
cd C:\Users\Once\Documents\trae_projects\sistema_administracion

# Activar entorno virtual
.\.venv\Scripts\Activate.ps1

# Ejecutar script de migración
python migrar_a_postgresql.py
```

**El script hará automáticamente:**
1. ✅ Backup de SQLite
2. ✅ Actualizar .env con PostgreSQL
3. ✅ Aplicar migraciones
4. ✅ Transferir todos los datos
5. ✅ Verificar integridad

---

## 🔍 PASO 4: VERIFICAR LA MIGRACIÓN

```powershell
# 1. Ejecutar el servidor
python manage.py runserver

# 2. Abrir el navegador en http://localhost:8000/admin/

# 3. Verificar que:
# - Puedes iniciar sesión
# - Todos los afiliados están presentes
# - Todos los vehículos están presentes
# - Las hojas de ruta están presentes
# - Los pagos y transacciones están presentes
```

---

## 📊 PASO 5: OPTIMIZAR POSTGRESQL

El script de migración ya incluye estas optimizaciones, pero puedes verificarlas:

### A. Índices Importantes

```sql
-- Conectar con psql a la base de datos
\c sindicato_taipiplaya

-- Ver índices creados
\di

-- Los índices importantes que deberías tener:
-- - afiliados_ci_idx (búsqueda por CI)
-- - vehiculos_placa_idx (búsqueda por placa)
-- - hojasruta_fecha_idx (búsqueda por fecha)
-- - pagos_fecha_idx (reportes financieros)
```

### B. Configuración de Performance

```sql
-- Ver configuración actual
SHOW shared_buffers;
SHOW work_mem;

-- Para un servidor con 8GB RAM (ajustar según tu sistema):
-- Editar postgresql.conf:
-- shared_buffers = 2GB
-- work_mem = 16MB
-- effective_cache_size = 6GB
```

---

## 🔄 PASO 6: CONFIGURAR BACKUPS AUTOMÁTICOS

### Script de Backup Diario

El archivo `backup_postgresql.ps1` ya está creado. Para programarlo:

```powershell
# 1. Abrir "Programador de tareas" (Task Scheduler)
# 2. Crear nueva tarea básica
# 3. Nombre: "Backup PostgreSQL Sindicato"
# 4. Desencadenador: Diariamente a las 2:00 AM
# 5. Acción: Iniciar programa
#    - Programa: powershell.exe
#    - Argumentos: -File "C:\Users\Once\Documents\trae_projects\sistema_administracion\backup_postgresql.ps1"
# 6. Finalizar
```

---

## ⚠️ SOLUCIÓN DE PROBLEMAS

### Error: "could not connect to server"

```powershell
# Verificar que PostgreSQL está corriendo
Get-Service -Name postgresql*

# Si no está corriendo, iniciarlo:
Start-Service postgresql-x64-16
```

### Error: "password authentication failed"

```powershell
# Verificar credenciales en .env
# Usuario: admin_sindicato
# Password: el que configuraste en Paso 2

# Si olvidaste la contraseña, resetearla:
# 1. Conectar como postgres
psql -U postgres

# 2. Cambiar contraseña
ALTER USER admin_sindicato WITH PASSWORD 'nueva_contraseña';
```

### Error: "permission denied for schema public"

```sql
-- Conectar como postgres
psql -U postgres -d sindicato_taipiplaya

-- Ejecutar:
GRANT ALL ON SCHEMA public TO admin_sindicato;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO admin_sindicato;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO admin_sindicato;
```

### Error al migrar datos: "duplicate key value"

```powershell
# Limpiar PostgreSQL y volver a intentar:
python manage.py migrate --run-syncdb
python manage.py flush --no-input
python migrar_a_postgresql.py
```

---

## 🔙 ROLLBACK (Si algo sale mal)

Si necesitas volver a SQLite:

```powershell
# 1. Detener el servidor
# Ctrl + C en la terminal del backend

# 2. Restaurar .env.backup
Copy-Item .env.backup .env -Force

# 3. Reiniciar el servidor
python manage.py runserver
```

Los datos de SQLite no se borran, se mantienen en `db.sqlite3` y `db.sqlite3.backup`.

---

## ✅ CHECKLIST POST-MIGRACIÓN

Después de migrar, verificar:

- [ ] Login funciona correctamente
- [ ] Dashboard muestra estadísticas correctas
- [ ] Módulo de Afiliados funciona
- [ ] Módulo de Vehículos funciona
- [ ] Hojas de Ruta se crean correctamente
- [ ] Pagos y transacciones funcionan
- [ ] Reportes se generan correctamente
- [ ] PDFs se generan sin errores
- [ ] Backup automático configurado

---

## 🎉 BENEFICIOS OBTENIDOS

Después de la migración a PostgreSQL:

✅ **Mejor rendimiento** en consultas complejas  
✅ **Mayor integridad** de datos financieros  
✅ **Full-text search** disponible  
✅ **JSON queries** nativas  
✅ **Mejor soporte** para concurrencia  
✅ **Escalabilidad** a largo plazo  
✅ **Backups** más confiables  

---

## 📞 SOPORTE

Si tienes problemas durante la migración:

1. Revisar logs: `logs/django.log`
2. Ver errores de PostgreSQL: `C:\Program Files\PostgreSQL\16\data\log`
3. Consultar documentación: https://www.postgresql.org/docs/

---

**Última actualización:** 12 de diciembre de 2025  
**Versión:** 1.0
