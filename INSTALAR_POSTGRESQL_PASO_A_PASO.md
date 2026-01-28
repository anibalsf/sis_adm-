# 🔧 GUÍA DE INSTALACIÓN DE POSTGRESQL 16

## ⚠️ IMPORTANTE: Necesitas instalar PostgreSQL manualmente

Chocolatey requiere permisos de administrador. Es más fácil usar el instalador oficial.

---

## 📥 PASO 1: DESCARGAR EL INSTALADOR

### A. Abrir la página de descarga:

1. Abre tu navegador
2. Ve a: **https://www.enterprisedb.com/downloads/postgres-postgresql-downloads**
3. O busca en Google: "PostgreSQL Windows download"

### B. Seleccionar la versión:

- **Versión:** PostgreSQL 16.6 (o la más reciente de la serie 16)
- **Sistema Operativo:** Windows x86-64
- Click en **"Download"**

El archivo se llamará algo como: `postgresql-16.6-1-windows-x64.exe`  
Tamaño aproximado: 350-450 MB

---

## 💿 PASO 2: EJECUTAR EL INSTALADOR

1. **Localiza el archivo descargado** (usualmente en Descargas)
2. **Doble click** en `postgresql-16.x-x-windows-x64.exe`
3. Si Windows pregunta "¿Quieres permitir cambios?", click **"Sí"**

---

## ⚙️ PASO 3: CONFIGURACIÓN DEL INSTALADOR

### Pantalla 1: Setup - PostgreSQL

Click **"Next"**

---

### Pantalla 2: Installation Directory

**Directorio de instalación:**
```
C:\Program Files\PostgreSQL\16
```

✅ **Deja el valor por defecto**  
Click **"Next"**

---

### Pantalla 3: Select Components

**Componentes a instalar:**
- ✅ **PostgreSQL Server** (Requerido)
- ✅ **pgAdmin 4** (Herramienta gráfica - Recomendado)
- ✅ **Stack Builder** (Opcional - puedes desmarcarlo)
- ✅ **Command Line Tools** (Requerido)

Click **"Next"**

---

### Pantalla 4: Data Directory

**Directorio de datos:**
```
C:\Program Files\PostgreSQL\16\data
```

✅ **Deja el valor por defecto**  
Click **"Next"**

---

### Pantalla 5: Password

**⚠️ IMPORTANTE: ANOTA ESTA CONTRASEÑA**

Esta es la contraseña del superusuario **postgres**.

**Contraseña recomendada:** `Postgres2025!`

- Escribe la contraseña
- Confírmala en el segundo campo
- **📝 ANÓTALA** en algún lugar seguro

Click **"Next"**

---

### Pantalla 6: Port

**Puerto:**
```
5432
```

✅ **Deja el valor por defecto (5432)**  
Este es el puerto estándar de PostgreSQL

Click **"Next"**

---

### Pantalla 7: Advanced Options - Locale

**Locale:**
```
Spanish, Bolivia
```

O puedes dejar:
```
[Default locale]
```

Click **"Next"**

---

### Pantalla 8: Pre Installation Summary

**Revisa que todo esté correcto:**
- Installation Directory: C:\Program Files\PostgreSQL\16
- Data Directory: C:\Program Files\PostgreSQL\16\data
- Port: 5432
- Components: Server, pgAdmin 4, Command Line Tools

Click **"Next"**

---

### Pantalla 9: Ready to Install

Click **"Next"** para iniciar la instalación

**⏱️ Tiempo estimado: 5-10 minutos**

Verás una barra de progreso mientras instala:
- PostgreSQL Server
- pgAdmin 4
- Command Line Tools

---

### Pantalla 10: Completing the PostgreSQL Setup Wizard

✅ **Instalación completada**

- **DESMARCA** la casilla "Stack Builder" (no es necesario)
- Click **"Finish"**

---

## ✅ PASO 4: VERIFICAR LA INSTALACIÓN

### A. Verificar el servicio

1. Presiona **Windows + R**
2. Escribe: `services.msc`
3. Presiona Enter
4. Busca **"postgresql-x64-16"** en la lista
5. Debe decir **"En ejecución"** (Running)

### B. Verificar desde PowerShell

Abre una **NUEVA** ventana de PowerShell (importante para que reconozca los nuevos comandos):

```powershell
# Verificar versión
psql --version

# Debe mostrar algo como:
# psql (PostgreSQL) 16.6
```

Si aparece un error "comando no reconocido", **cierra y abre una nueva PowerShell**.

---

## 🎉 PASO 5: ¡LISTO!

PostgreSQL está instalado. Ahora continuamos con:

1. ✅ PostgreSQL instalado y corriendo
2. ⏭️ Crear base de datos (lo haremos juntos)
3. ⏭️ Ejecutar migración automática

---

## 🆘 SOLUCIÓN DE PROBLEMAS

### El instalador no se ejecuta
- Click derecho → "Ejecutar como administrador"

### Ya existe otra instalación de PostgreSQL
- Es normal si tenías una versión anterior
- El nuevo instalador actualizará o creará una nueva versión

### El servicio no inicia
```powershell
# Iniciar manualmente:
net start postgresql-x64-16
```

### "psql" no se reconoce después de instalar
- **Cierra completamente PowerShell**
- Abre una **nueva ventana** de PowerShell
- Intenta de nuevo: `psql --version`

---

## 📞 SIGUIENTE PASO

Una vez que veas que `psql --version` funciona, avísame y continuaremos con:

**PASO 6: Crear la base de datos** ✨

---

**Tiempo total de instalación:** 15-20 minutos  
**¡Mucho éxito!** 🚀
