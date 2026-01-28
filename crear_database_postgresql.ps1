# Script PowerShell para crear la base de datos PostgreSQL
# Sistema: Sindicato Mixto de Transporte Integración Taipiplaya

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  CREAR BASE DE DATOS POSTGRESQL" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar si PostgreSQL 16 existe
$PSQL_PATH = "C:\Program Files\PostgreSQL\16\bin\psql.exe"

if (-not (Test-Path $PSQL_PATH)) {
    Write-Host "PostgreSQL 16 no encontrado en la ruta por defecto." -ForegroundColor Yellow
    Write-Host "Buscando otras versiones..." -ForegroundColor Yellow
    
    $PSQL_PATH = "C:\Program Files\PostgreSQL\15\bin\psql.exe"
    if (-not (Test-Path $PSQL_PATH)) {
        $PSQL_PATH = "C:\Program Files\PostgreSQL\14\bin\psql.exe"
    }
}

if (-not (Test-Path $PSQL_PATH)) {
    Write-Host ""
    Write-Host "Error: No se encontro psql.exe" -ForegroundColor Red
    Write-Host ""
    Write-Host "SOLUCION ALTERNATIVA:" -ForegroundColor Yellow
    Write-Host "1. Abre pgAdmin 4 (busca en el menu de Windows)" -ForegroundColor White
    Write-Host "2. Conecta al servidor PostgreSQL" -ForegroundColor White
    Write-Host "3. Abre Query Tool (Tools -> Query Tool)" -ForegroundColor White
    Write-Host "4. Copia el contenido de: crear_database_postgresql.sql" -ForegroundColor White
    Write-Host "5. Pega y ejecuta (F5)" -ForegroundColor White
    Write-Host ""
    Read-Host "Presiona Enter para salir"
    exit 1
}

Write-Host "PostgreSQL encontrado en: $PSQL_PATH" -ForegroundColor Green
Write-Host ""

$scriptPath = Join-Path $PSScriptRoot "crear_database_postgresql.sql"

if (-not (Test-Path $scriptPath)) {
    Write-Host "Error: No se encontro el script SQL" -ForegroundColor Red
    Write-Host "Ruta esperada: $scriptPath" -ForegroundColor Red
    exit 1
}

Write-Host "Ejecutando script SQL..." -ForegroundColor Yellow
Write-Host "Se te pedira la contraseña del usuario 'postgres'" -ForegroundColor Yellow
Write-Host ""

# Ejecutar el script SQL
& $PSQL_PATH -U postgres -f $scriptPath

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  BASE DE DATOS CREADA EXITOSAMENTE" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Credenciales de conexion:" -ForegroundColor Cyan
    Write-Host "  Base de datos: sindicato_taipiplaya" -ForegroundColor White
    Write-Host "  Usuario: admin_sindicato" -ForegroundColor White
    Write-Host "  Password: Taipiplaya2025!" -ForegroundColor White
    Write-Host "  Host: localhost" -ForegroundColor White
    Write-Host "  Puerto: 5432" -ForegroundColor White
    Write-Host ""
    Write-Host "Siguiente paso:" -ForegroundColor Yellow
    Write-Host "  python migrar_a_postgresql.py" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "Error al crear la base de datos" -ForegroundColor Red
    Write-Host ""
    Write-Host "Posibles causas:" -ForegroundColor Yellow
    Write-Host "  1. La base de datos ya existe" -ForegroundColor Gray
    Write-Host "  2. Contraseña incorrecta" -ForegroundColor Gray
    Write-Host "  3. PostgreSQL no esta corriendo" -ForegroundColor Gray
    Write-Host ""
}

Write-Host ""
Read-Host "Presiona Enter para salir"
