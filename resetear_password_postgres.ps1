# Script para resetear la contraseña de PostgreSQL
# IMPORTANTE: Ejecutar como Administrador

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  RESETEAR CONTRASEÑA POSTGRES" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar si se ejecuta como administrador
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
$isAdmin = $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "ERROR: Este script debe ejecutarse como Administrador" -ForegroundColor Red
    Write-Host ""
    Write-Host "Como ejecutar como Administrador:" -ForegroundColor Yellow
    Write-Host "1. Click derecho en PowerShell" -ForegroundColor White
    Write-Host "2. Selecciona 'Ejecutar como administrador'" -ForegroundColor White
    Write-Host "3. Ejecuta de nuevo este script" -ForegroundColor White
    Write-Host ""
    Read-Host "Presiona Enter para salir"
    exit 1
}

# Rutas de PostgreSQL
$PG_DATA = "C:\Program Files\PostgreSQL\16\data"
$PG_HBA_CONF = Join-Path $PG_DATA "pg_hba.conf"
$PG_HBA_BACKUP = Join-Path $PG_DATA "pg_hba.conf.backup"

# Verificar que existe
if (-not (Test-Path $PG_HBA_CONF)) {
    Write-Host "ERROR: No se encontro el archivo pg_hba.conf" -ForegroundColor Red
    Write-Host "Ruta esperada: $PG_HBA_CONF" -ForegroundColor Red
    exit 1
}

Write-Host "PASO 1: Hacer backup de pg_hba.conf" -ForegroundColor Yellow
Copy-Item $PG_HBA_CONF $PG_HBA_BACKUP -Force
Write-Host "Backup creado en: $PG_HBA_BACKUP" -ForegroundColor Green
Write-Host ""

Write-Host "PASO 2: Modificar pg_hba.conf para permitir acceso sin contraseña" -ForegroundColor Yellow

# Leer el archivo
$content = Get-Content $PG_HBA_CONF

# Reemplazar scram-sha-256 y md5 con trust
$newContent = $content -replace 'scram-sha-256', 'trust' -replace 'md5', 'trust'

# Guardar
Set-Content $PG_HBA_CONF $newContent

Write-Host "Archivo modificado" -ForegroundColor Green
Write-Host ""

Write-Host "PASO 3: Reiniciar servicio PostgreSQL" -ForegroundColor Yellow
try {
    Restart-Service postgresql-x64-16 -ErrorAction Stop
    Write-Host "Servicio reiniciado" -ForegroundColor Green
    Start-Sleep -Seconds 3
} catch {
    Write-Host "Error al reiniciar servicio: $_" -ForegroundColor Red
    Write-Host "Intenta manualmente: services.msc" -ForegroundColor Yellow
    exit 1
}
Write-Host ""

Write-Host "PASO 4: Cambiar contraseña del usuario postgres" -ForegroundColor Yellow
$PSQL_PATH = "C:\Program Files\PostgreSQL\16\bin\psql.exe"

if (-not (Test-Path $PSQL_PATH)) {
    Write-Host "ERROR: No se encontro psql.exe" -ForegroundColor Red
    exit 1
}

Write-Host "Ingresa la nueva contraseña para el usuario postgres:" -ForegroundColor Cyan
$newPassword = Read-Host "Nueva contraseña" -AsSecureString
$newPasswordPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($newPassword))

# Cambiar contraseña
$sqlCommand = "ALTER USER postgres WITH PASSWORD '$newPasswordPlain';"
$tempSqlFile = Join-Path $env:TEMP "change_password.sql"
Set-Content $tempSqlFile $sqlCommand

& $PSQL_PATH -U postgres -d postgres -f $tempSqlFile

Remove-Item $tempSqlFile -Force

Write-Host "Contraseña cambiada exitosamente" -ForegroundColor Green
Write-Host ""

Write-Host "PASO 5: Restaurar pg_hba.conf" -ForegroundColor Yellow
Copy-Item $PG_HBA_BACKUP $PG_HBA_CONF -Force
Write-Host "Archivo restaurado" -ForegroundColor Green
Write-Host ""

Write-Host "PASO 6 Reiniciar servicio PostgreSQL nuevamente" -ForegroundColor Yellow
try {
    Restart-Service postgresql-x64-16 -ErrorAction Stop
    Write-Host "Servicio reiniciado" -ForegroundColor Green
    Start-Sleep -Seconds 3
} catch {
    Write-Host "Error al reiniciar servicio: $_" -ForegroundColor Red
    exit 1
}
Write-Host ""

Write-Host "==========================================" -ForegroundColor Green
Write-Host "  CONTRASEÑA CAMBIADA EXITOSAMENTE" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Nueva contraseña para usuario 'postgres': $newPasswordPlain" -ForegroundColor Cyan
Write-Host ""
Write-Host "IMPORTANTE: Anota esta contraseña en un lugar seguro" -ForegroundColor Yellow
Write-Host ""

Read-Host "Presiona Enter para salir"
