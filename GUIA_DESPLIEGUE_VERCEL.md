# GUIA DE DESPLIEGUE: ARQUITECTURA MODERNA (VERCEL + RAILWAY)

Para sistemas como este (Django + React), la mejor estrategia de despliegue es una arquitectura hibrida:

1.  **Frontend (React)** -> **Vercel** (Lider en velocidad para React).
2.  **Backend (Django) y Base de Datos** -> **Railway** (Excelente soporte para Python y PostgreSQL).

---

## PASO 1: Subir tu codigo a GitHub
1.  Crea un repositorio en GitHub (ej: `sistema-sindicato`).
2.  Sube todo tu codigo actual a ese repositorio.

## PASO 2: Desplegar Backend en Railway
1.  Entra a [railway.app](https://railway.app) y logueate con GitHub.
2.  Click en **"New Project"** -> **"Deploy from GitHub repo"**.
3.  Selecciona tu repositorio `sistema-sindicato`.
4.  **Importante:** Anade una Base de Datos PostgreSQL al proyecto en Railway.
5.  En la configuracion del servicio Django ("Variables"), agrega:
    *   `SECRET_KEY`: (Crea una clave segura)
    *   `DEBUG`: `False`
    *   `ALLOWED_HOSTS`: `*` (o tu dominio final)
    *   `DATABASE_URL`: (Usa la variable `${{Postgres.DATABASE_URL}}` que te da Railway)
6.  Railway detectara tu `requirements.txt` y desplegara automaticamente.
    *   *Nota: Copia la URL que te da Railway (ej: `https://web-production-1234.up.railway.app`).*

## PASO 3: Desplegar Frontend en Vercel
1.  Entra a [vercel.com](https://vercel.com) y logueate con GitHub.
2.  Click en **"Add New..."** -> **"Project"**.
3.  Selecciona el mismo repositorio `sistema-sindicato`.
4.  **Configuracion del Proyecto:**
    *   **Root Directory:** Dale click a "Edit" y selecciona la carpeta **`frontend`**.
    *   **Framework Preset:** Vite (lo detectara automatico).
5.  **Variables de Entorno:**
    *   Nombre: `VITE_API_URL`
    *   Valor: La URL de tu backend en Railway (ej: `https://web-production-1234.up.railway.app/api`) **(¡Ojo! Anade /api al final)**.
6.  Click en **"Deploy"**.

## Resultado Final
- Tu Frontend estara en `https://sistema-sindicato.vercel.app`.
- Tu Backend estara seguro y estable en Railway.
- Ambos se comunicaran correctamente.
