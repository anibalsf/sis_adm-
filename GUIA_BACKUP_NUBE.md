# Guía de Sincronización de Backups en la Nube

Para asegurar que los backups del Sindicato Taipiplaya estén seguros incluso si la computadora local falla, se recomienda sincronizar la carpeta de backups con la nube.

## Opción 1: Google Drive para Escritorio (Recomendado)
1. Descarga e instala [Google Drive para Escritorio](https://www.google.com/intl/es/drive/download/).
2. Inicia sesión con la cuenta del Sindicato.
3. Ve a **Preferencias** > **Computadora** > **Agregar carpeta**.
4. Selecciona la carpeta: `C:\Users\Once\Documents\trae_projects\sistema_administracion\backups`.
5. Selecciona "Sincronizar con Google Drive".
6. ¡Listo! Cada vez que el script de PowerShell genere un backup, se subirá automáticamente a la nube.

## Opción 2: Rclone (Avanzado)
Si prefieres una herramienta de línea de comandos:
1. Instala Rclone.
2. Configura un "remote" para Google Drive o Dropbox.
3. Agrega esta línea al final del archivo `backup_postgresql.ps1`:
   ```powershell
   & rclone sync "C:\Users\Once\Documents\trae_projects\sistema_administracion\backups" "remote:BackupsSindicato"
   ```

## Verificación
Recibirás un mensaje de WhatsApp cada vez que se cree un backup. Verifica periódicamente tu Google Drive para confirmar que los archivos `.sql` están allí.
