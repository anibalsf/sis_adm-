#!/bin/bash

# Script de optimización para producción
# Ejecutar antes del deployment

echo "🔧 Iniciando optimización para producción..."

# 1. Limpiar archivos innecesarios
echo "📦 Limpiando archivos de desarrollo..."
find . -type f -name "*.pyc" -delete
find . -type d -name "__pycache__" -delete
find . -type d -name ".pytest_cache" -delete
find . -type f -name ".DS_Store" -delete

# 2. Verificar requirements.txt
echo "📋 Verificando dependencias..."
pip list --outdated

# 3. Ejecutar tests (si existen)
if [ -d "tests" ]; then
    echo "🧪 Ejecutando tests..."
    python manage.py test
fi

# 4. Verificar migraciones pendientes
echo "🗄️  Verificando migraciones..."
python manage.py makemigrations --check --dry-run

# 5. Colectar archivos estáticos
echo "📁 Recolectando archivos estáticos..."
python manage.py collectstatic --noinput --clear

# 6. Comprimir archivos estáticos (opcional)
if command -v gzip &> /dev/null; then
    echo "🗜️  Comprimiendo archivos estáticos..."
    find staticfiles -type f \( -name "*.js" -o -name "*.css" \) -exec gzip -k {} \;
fi

# 7. Verificar configuración de seguridad
echo "🔒 Verificando configuración de seguridad..."
python manage.py check --deploy

# 8. Generar reporte de tamaño
echo "📊 Generando reporte de tamaño..."
du -sh staticfiles/ media/ 2>/dev/null || echo "Directorios no encontrados"

echo "✅ Optimización completada!"
echo ""
echo "⚠️  RECORDATORIOS IMPORTANTES:"
echo "  1. Cambiar SECRET_KEY en producción"
echo "  2. Configurar DEBUG=False"
echo "  3. Actualizar ALLOWED_HOSTS"
echo "  4. Configurar base de datos PostgreSQL"
echo "  5. Configurar backups automáticos"
echo "  6. Habilitar SSL/HTTPS"
