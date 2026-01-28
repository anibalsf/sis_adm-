# ==========================================
# STAGE 1: Build Frontend (React)
# ==========================================
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# Instalar dependencias
COPY frontend/package*.json ./
RUN npm install

# Copiar código y construir
COPY frontend/ ./
RUN npm run build

# ==========================================
# STAGE 2: Backend & Production (Django)
# ==========================================
FROM python:3.12-slim

# Variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBUG=False

WORKDIR /app

# Instalar dependencias del sistema para psycopg2 y reportlab
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código del backend
COPY . .

# Copiar los archivos construidos del frontend a la carpeta que Django servirá
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Preparar archivos estáticos de Django (WhiteNoise)
RUN python manage.py collectstatic --noinput

# Puerto expuesto
EXPOSE 8000

# Comando para iniciar con Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "sistema.wsgi:application"]
