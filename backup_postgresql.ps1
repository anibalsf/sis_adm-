# Script de Backup Automático de PostgreSQL
# Sistema: Sindicato Mixto de Transporte Integración Taipiplaya
# Ejecutar diariamente con Programador de Tareas

# Configuración
$BACKUP_DIR = "C:\Users\Once\Documents\trae_projects\sistema_administracion\backups"
$DB_NAME = "sindicato_taipiplaya"
$DB_USER = "admin_sindicato"
$DB_HOST = "localhost"
$DB_PORT = "5432"
$TIMESTAMP = Get-Date -Format "yyyyMMdd_HHmmss"
$BACKUP_FILE = "$BACKUP_DIR\backup_${DB_NAME}_${TIMESTAMP}.sql"
$DAYS_TO_KEEP = 30  # Mantener backups de los últimos 30 días

# Crear directorio de backups si no existe
if (-not (Test-Path $BACKUP_DIR)) {
    New-Item -ItemType Directory -Path $BACKUP_DIR -Force | Out-Null
    Write-Host "✓ Directorio de backups creado: $BACKUP_DIR" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  BACKUP POSTGRESQL - SINDICATO TAIPIPLAYA" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Fecha: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Yellow
Write-Host "Base de datos: $DB_NAME" -ForegroundColor Yellow
Write-Host "Archivo: $BACKUP_FILE" -ForegroundColor Yellow
Write-Host ""

# Solicitar contraseña (o configurar PGPASSWORD en variables de entorno)
# Para automatización completa, configurar archivo .pgpass o variable de entorno
# $env:PGPASSWORD = "tu_contraseña"

try {
    # Ejecutar pg_dump
    Write-Host "Iniciando backup..." -ForegroundColor Yellow
    
    # Ruta a pg_dump (ajustar según instalación)
    $PG_DUMP = "C:\Program Files\PostgreSQL\16\bin\pg_dump.exe"
    
    # Verificar que pg_dump existe
    if (-not (Test-Path $PG_DUMP)) {
        Write-Host "✗ Error: No se encontró pg_dump en $PG_DUMP" -ForegroundColor Red
        Write-Host "  Ajusta la ruta en el script según tu instalación" -ForegroundColor Yellow
        exit 1
    }
    
    # Ejecutar backup
    $arguments = @(
        "-h", $DB_HOST,
        "-p", $DB_PORT,
        "-U", $DB_USER,
        "-F", "c",  # Formato custom (comprimido)
        "-b",       # Include blobs
        "-v",       # Verbose
        "-f", $BACKUP_FILE,
        $DB_NAME
    )
    
    & $PG_DUMP @arguments
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✓ Backup completado exitosamente" -ForegroundColor Green
        
        # Mostrar tamaño del archivo
        $fileSize = (Get-Item $BACKUP_FILE).Length / 1MB
        Write-Host "  Tamaño: $([math]::Round($fileSize, 2)) MB" -ForegroundColor Green
        
        # Limpiar backups antiguos
        Write-Host ""
        Write-Host "Limpiando backups antiguos (más de $DAYS_TO_KEEP días)..." -ForegroundColor Yellow
        
        $cutoffDate = (Get-Date).AddDays(-$DAYS_TO_KEEP)
        $oldBackups = Get-ChildItem -Path $BACKUP_DIR -Filter "backup_${DB_NAME}_*.sql" | 
                      Where-Object { $_.LastWriteTime -lt $cutoffDate }
        
        if ($oldBackups.Count -gt 0) {
            foreach ($file in $oldBackups) {
                Remove-Item $file.FullName -Force
                Write-Host "  ✓ Eliminado: $($file.Name)" -ForegroundColor Gray
            }
            Write-Host "  Total eliminados: $($oldBackups.Count)" -ForegroundColor Green
        } else {
            Write-Host "  No hay backups antiguos para eliminar" -ForegroundColor Gray
        }
        
        # Mostrar backups disponibles
        Write-Host ""
        Write-Host "Backups disponibles:" -ForegroundColor Cyan
        $allBackups = Get-ChildItem -Path $BACKUP_DIR -Filter "backup_${DB_NAME}_*.sql" | 
                      Sort-Object LastWriteTime -Descending |
                      Select-Object -First 5
        
        foreach ($backup in $allBackups) {
            $size = [math]::Round($backup.Length / 1MB, 2)
            Write-Host "  • $($backup.Name) - ${size} MB - $($backup.LastWriteTime)" -ForegroundColor Gray
        }
        
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Cyan
        Write-Host "  BACKUP FINALIZADO CORRECTAMENTE" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Cyan
        Write-Host ""
        
        # Enviar alerta WhatsApp
        python alerta_backup.py success "Tamaño: $([math]::Round($fileSize, 2)) MB"
        
    } else {
        Write-Host ""
        Write-Host "✗ Error al crear el backup" -ForegroundColor Red
        Write-Host "  Código de error: $LASTEXITCODE" -ForegroundColor Red
        python alerta_backup.py fail "Error en pg_dump. Código: $LASTEXITCODE"
        exit 1
    }
    
} catch {
    Write-Host ""
    Write-Host "✗ Error durante el backup: $_" -ForegroundColor Red
    exit 1
}

# Log del backup
$logFile = "$BACKUP_DIR\backup_log.txt"
$logEntry = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') - Backup exitoso: $BACKUP_FILE"
Add-Content -Path $logFile -Value $logEntry
