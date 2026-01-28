@echo off
REM Script de optimización para producción (Windows)
REM Ejecutar antes del deployment

echo 🔧 Iniciando optimización para producción...

REM 1. Limpiar archivos innecesarios
echo 📦 Limpiando archivos de desarrollo...
for /r %%i in (*.pyc) do del "%%i"
for /d /r %%i in (__pycache__) do rd /s /q "%%i"
for /d /r %%i in (.pytest_cache) do rd /s /q "%%i"

REM 2. Activar entorno virtual
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else (
    echo ⚠️  Entorno virtual no encontrado
)

REM 3. Verificar requirements.txt
echo 📋 Verificando dependencias...
pip list --outdated

REM 4. Ejecutar tests (si existen)
if exist tests (
    echo 🧪 Ejecutando tests...
    python manage.py test
)

REM 5. Verificar migraciones pendientes
echo 🗄️  Verificando migraciones...
python manage.py makemigrations --check --dry-run

REM 6. Colectar archivos estáticos
echo 📁 Recolectando archivos estáticos...
python manage.py collectstatic --noinput --clear

REM 7. Verificar configuración de seguridad
echo 🔒 Verificando configuración de seguridad...
python manage.py check --deploy

echo.
echo ✅ Optimización completada!
echo.
echo ⚠️  RECORDATORIOS IMPORTANTES:
echo   1. Cambiar SECRET_KEY en producción
echo   2. Configurar DEBUG=False
echo   3. Actualizar ALLOWED_HOSTS
echo   4. Configurar base de datos PostgreSQL
echo   5. Configurar backups automáticos
echo   6. Habilitar SSL/HTTPS
echo.
pause
