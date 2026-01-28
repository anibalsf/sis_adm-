# 🐳 Guía de Despliegue con Docker

Esta guía detalla los pasos para desplegar el sistema completo (Frontend + Backend + Base de Datos) utilizando Docker.

## 📋 Requisitos Previos

- Tener instalado **Docker Desktop** (en Windows/Mac) o **Docker Engine** y **Docker Compose** (en Linux).
- Tener el código fuente del proyecto descargado.

---

## 🚀 Pasos para el Despliegue

### 1. Preparación

Abre una terminal (PowerShell o CMD) en la carpeta raíz del proyecto:
```powershell
cd C:\Users\Once\Documents\trae_projects\sistema_administracion
```

### 2. Construcción y Ejecución

Ejecuta el siguiente comando para construir las imágenes e iniciar los contenedores en segundo plano:

```powershell
docker-compose up -d --build
```
> **Nota:** La primera vez puede tardar unos minutos mientras descarga las imágenes base y compila el frontend.

### 3. Verificar el Estado

Puedes ver si los contenedores están corriendo con:

```powershell
docker-compose ps
```
Deberías ver dos servicios activos: `db` (PostgreSQL) y `web` (Django/App).

### 4. Acceder al Sistema

Una vez iniciado, el sistema estará disponible en:

- **Sistema Completo:** [http://localhost:8000](http://localhost:8000)
- **Panel Administrativo:** [http://localhost:8000/admin/](http://localhost:8000/admin/)

---

## 🛠️ Comandos de Mantenimiento

### Ver Logs
Para ver qué está pasando dentro de los contenedores (útil si algo falla):
```powershell
docker-compose logs -f
```
(Presiona `Ctrl + C` para salir de los logs)

### Detener el Sistema
Para detener los contenedores sin borrar los datos:
```powershell
docker-compose stop
```

### Detener y Borrar Contenedores
Para detener y eliminar los contenedores (la base de datos se conserva en el volumen):
```powershell
docker-compose down
```

### Reconstruir (Actualizar Cambios)
Si haces cambios en el código, necesitas reconstruir la imagen:
```powershell
docker-compose up -d --build
```

---

## ⚙️ Detalles Técnicos

- **Frontend:** Se compila automáticamente y se sirve a través de Django. No necesitas correr `npm start` por separado.
- **Base de Datos:** Se usa un contenedor de PostgreSQL. Los datos se guardan en un volumen llamado `postgres_data`, por lo que **no se pierden** al reiniciar Docker.
- **Variables de Entorno:** Las variables críticas para Docker están definidas en el archivo `docker-compose.yml`.
