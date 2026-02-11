#!/bin/bash

# ==============================================================================
# SCRIPT DE DESPLIEGUE AUTOMÁTICO - SINDICATO TAIPIPLAYA
# ==============================================================================
# Este script prepara el código para ser subido a GitHub y desplegado en Railway.

echo "🚀 Iniciando preparación para el despliegue..."

# 1. Actualizar requirements.txt
echo "📦 Actualizando lista de dependencias..."
pip freeze > requirements.txt

# 2. Configuración del Frontend
echo "⚛️ Preparando el Frontend..."
cd frontend
if [ ! -f .env ]; then
    echo "VITE_API_URL=/api" > .env
    echo "✅ Archivo frontend/.env creado."
fi
npm install
npm run build
cd ..

# 3. Verificación de Git
if [ ! -d .git ]; then
    echo "Initializing Git repository..."
    git init
fi

# 4. Asegurar que .gitignore incluya archivos sensibles
if ! grep -q ".env" .gitignore; then
    echo ".env" >> .gitignore
    echo "db.sqlite3" >> .gitignore
    echo "media/" >> .gitignore
    echo "staticfiles/" >> .gitignore
    echo "✅ .gitignore actualizado."
fi

# 5. Commit de cambios
echo "💾 Guardando cambios en Git..."
git add .
git commit -m "🚀 Preparación para despliegue: iconos coloridos, reportes mensuales y limpieza de bitácora"

echo ""
echo "=================================================================="
echo "✅ ¡SISTEMA PREPARADO PARA SUBIR!"
echo "=================================================================="
echo "Sigue estos pasos finales:"
echo "1. Crea un repositorio PRIVADO en GitHub."
echo "2. Ejecuta los siguientes comandos en tu terminal:"
echo "   git remote add origin https://github.com/tu-usuario/nombre-repo.git"
echo "   git branch -M main"
echo "   git push -u origin main"
echo "3. Conecta el repositorio a Railway.app"
echo "=================================================================="
