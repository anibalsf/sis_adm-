@echo off
:: ==============================================================================
:: SCRIPT DE DESPLIEGUE AUTOMÁTICO (WINDOWS) - SINDICATO TAIPIPLAYA
:: ==============================================================================

echo 🚀 Iniciando preparacion para el despliegue...

:: 1. Actualizar requirements.txt
echo 📦 Actualizando lista de dependencias...
.\.venv\Scripts\python -m pip freeze > requirements.txt

:: 2. Configuración del Frontend
echo ⚛️ Preparando el Frontend...
cd frontend
if not exist .env (
    echo VITE_API_URL=/api > .env
    echo ✅ Archivo frontend/.env creado.
)
call npm install
call npm run build
cd ..

:: 3. Verificación de Git
if not exist .git (
    echo Initializing Git repository...
    git init
)

:: 4. Commit de cambios
echo 💾 Guardando cambios en Git...
git add .
git commit -m "🚀 Prep para despliegue: iconos color, reportes mensuales y limpieza"

echo.
echo ==================================================================
echo ✅ ¡SISTEMA PREPARADO PARA SUBIR!
echo ==================================================================
echo Sigue estos pasos finales:
echo 1. Crea un repositorio PRIVADO en GitHub.
echo 2. Ejecuta los siguientes comandos en tu terminal:
echo    git remote add origin https://github.com/TU_USUARIO/TU_REPOSITORIO.git
echo    git branch -M main
echo    git push -u origin main
echo 3. Conecta el repositorio a Railway.app
echo ==================================================================
pause
