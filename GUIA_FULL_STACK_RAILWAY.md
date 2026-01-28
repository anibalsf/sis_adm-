# 🚂 Guía de Despliegue: Todo en Uno en Railway

Esta es la forma **más fácil** de desplegar tu sistema. Railway se encargará de todo: el Backend (Django), el Frontend (React) y la Base de Datos.

Tu proyecto ya está configurado para que Django sirva también el Fronend, así que solo necesitas desplegar **UN solo servicio**.

---

## 🛠️ PASO 1: Subir código a GitHub
1.  Crea un nuevo repositorio en GitHub (ej: `sistema-sindicato-completo`).
2.  Sube todos los archivos de tu proyecto a ese repositorio.

## ☁️ PASO 2: Crear Proyecto en Railway
1.  Ve a [railway.app](https://railway.app).
2.  Click en **"New Project"**.
3.  Selecciona **"Deploy from GitHub repo"**.
4.  Elige tu repositorio `sistema-sindicato-completo`.

## 🗄️ PASO 3: Agregar Base de Datos
1.  En la vista del proyecto en Railway, haz click derecho en el fondo vacío.
2.  Elige **"New Service"** -> **"Database"** -> **"PostgreSQL"**.
3.  Espera unos segundos a que se inicie.

## 🔑 PASO 4: Configurar Variables (Muy Importante)
Railway necesita saber cómo configurarse. Ve al servicio de tu código (el que tiene el logo de GitHub), pestaña **"Variables"** y agrega:

| Variable | Valor | Nota |
|----------|-------|------|
| `PORT` | `8000` | **Crucial** para que Railway sepa dónde escucha Django |
| `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` | Railway autorellenará esto con tu BD |
| `SECRET_KEY` | `(Inventa una clave larga y rara)` | Seguridad |
| `DEBUG` | `False` | Para producción |
| `ALLOWED_HOSTS` | `*` | Permite acceder desde la web |
| `DISABLE_COLLECTSTATIC` | `0` | Asegura que se ejecute collectstatic |

## 🌐 PASO 5: Generar Dominio
1.  En el servicio de tu código, ve a **"Settings"**.
2.  Baja a **"Networking"**.
3.  Click en **"Generate Domain"**.
4.  Te dará una URL (ej: `sistema-production.up.railway.app`).

---

## ✅ ¡Listo!
Ahora, cuando entres a esa URL:
- Verás tu **Frontend (React)** funcionando.
- Si vas a `/admin`, verás el **Admin de Django**.
- El sistema de Login y todo lo demás funcionará automáticamente.

> **Nota:** La primera vez que despliegues, el proceso de "Build" tardará unos 3-5 minutos porque tiene que compilar React y instalar Python. Ten paciencia en la pestaña "Deployments".
