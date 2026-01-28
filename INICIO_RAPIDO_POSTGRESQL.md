# 🚀 INICIO RÁPIDO - MIGRACIÓN A POSTGRESQL

## 📌 PASOS EXACTOS A SEGUIR

### **1️⃣ INSTALAR POSTGRESQL (15-20 minutos)**

#### Descargar e Instalar:
1. Ve a: https://www.postgresql.org/download/windows/
2. Descarga el instalador de PostgreSQL 16
3. Ejecuta el instalador
4. **IMPORTANTE:** Anota la contraseña que establezcas para el usuario `postgres`
5. Acepta todos los valores por defecto:
   - Puerto: 5432
   - Ubicación: C:\Program Files\PostgreSQL\16
   - Componentes: Todos seleccionados

#### Verificar Instalación:
```powershell
# Abrir PowerShell y ejecutar:
psql --version

# Debe mostrar: psql (PostgreSQL) 16.x
```

---

### **2️⃣ CREAR BASE DE DATOS (5 minutos)**

#### Usando pgAdmin 4 (Más fácil - Recomendado):

1. **Abrir pgAdmin 4** (se instaló con PostgreSQL)
2. **Conectar al servidor local:**
   - Expandir "Servers" → "PostgreSQL 16"
   - Ingresar la contraseña que anotaste
3. **Crear base de datos:**
   - Click derecho en "Databases"
   - "Create" → "Database"
   - **Database:** `sindicato_taipiplaya`
   - Click "Save"
4. **Crear usuario:**
   - Click derecho en "Login/Group Roles"
   - "Create" → "Login/Group Role"
   - Tab "General": **Name:** `admin_sindicato`
   - Tab "Definition": **Password:** `Taipiplaya2025!` (o la que prefieras)
   - Tab "Privileges": Marcar "Can login?"
   - Click "Save"
5. **Dar permisos:**
   - Click derecho en base de datos `sindicato_taipiplaya`
   - "Properties" → "Security"
   - Click "+"
   - **Grantee:** admin_sindicato
   - **Privileges:** ALL
   - Click "Save"

✅ **Listo!** Base de datos creada.

---

### **3️⃣ EJECUTAR MIGRACIÓN AUTOMÁTICA (10 minutos)**

```powershell
# 1. Navegar al proyecto
cd C:\Users\Once\Documents\trae_projects\sistema_administracion

# 2. Activar entorno virtual
.\.venv\Scripts\Activate.ps1

# 3. DETENER el servidor si está corriendo
# Presiona Ctrl + C en la terminal donde corre el backend

# 4. Ejecutar script de migración
python migrar_a_postgresql.py
```

#### Durante la ejecución te pedirá:
- **Nombre de base de datos:** Presiona ENTER (usa `sindicato_taipiplaya`)
- **Usuario:** Presiona ENTER (usa `admin_sindicato`)
- **Contraseña:** Escribe `Taipiplaya2025!` (o la que elegiste)
- **Host:** Presiona ENTER (usa `localhost`)
- **Puerto:** Presiona ENTER (usa `5432`)

El script hará automáticamente:
- ✅ Backup de SQLite
- ✅ Exportar datos a JSON
- ✅ Actualizar .env
- ✅ Conectar a PostgreSQL
- ✅ Crear tablas
- ✅ Importar todos los datos
- ✅ Crear índices optimizados

---

### **4️⃣ VERIFICAR QUE TODO FUNCIONA (5 minutos)**

```powershell
# 1. Ejecutar el servidor
python manage.py runserver

# 2. Abrir navegador en:
http://localhost:8000/admin/

# 3. Verificar que:
# - Puedes iniciar sesión
# - Los afiliados están presentes
# - Los vehículos están presentes
# - Todo funciona normal
```

---

## 🎉 ¡LISTO!

Tu sistema ahora usa PostgreSQL. 

### **Beneficios obtenidos:**
✅ Mejor rendimiento  
✅ Mayor seguridad para datos financieros  
✅ Soporte para múltiples usuarios simultáneos  
✅ Funciones avanzadas de búsqueda  
✅ Mejor escalabilidad  

---

## 🔄 ¿Algo salió mal?

### Volver a SQLite:
```powershell
# 1. Restaurar configuración
Copy-Item .env.backup_* .env -Force

# 2. Reiniciar servidor
python manage.py runserver
```

Tu base de datos SQLite original **NO se borró**, está intacta.

---

## 📞 Problemas Comunes

### No puedo conectar a PostgreSQL
**Solución:** Verifica que el servicio esté corriendo:
```powershell
Get-Service -Name postgresql*
Start-Service postgresql-x64-16
```

### Error de contraseña
**Solución:** Verifica que la contraseña en el script coincida con la que configuraste en pgAdmin.

### Error "role does not exist"
**Solución:** Asegúrate de haber creado el usuario `admin_sindicato` en pgAdmin.

---

## 📚 Documentación Completa

Para más detalles, ver:
- `MIGRACION_POSTGRESQL.md` - Guía completa paso a paso
- `backup_postgresql.ps1` - Script de backup automático

---

**¡Éxito con tu migración!** 🚀
