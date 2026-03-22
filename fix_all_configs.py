import os

apps = [
    'afiliados', 'vehiculos', 'hojasruta', 'cuotas', 'usuarios', 
    'reuniones', 'asistencias', 'sanciones', 'rutas', 'reservas', 
    'reportes', 'comunicacion', 'historial', 'directorio', 'tesoreria', 
    'whatsapp_notif', 'pagos_qr', 'web_publica', 'mantenimiento', 
    'reportes_auto', 'encomiendas'
]

base_path = r'c:\Users\Once\Documents\trae_projects\sistema_administracion'

for app in apps:
    app_config_path = os.path.join(base_path, app, 'apps.py')
    if os.path.exists(app_config_path):
        with open(app_config_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if it already has path
        if 'path =' not in content and 'path=' not in content:
            # Look for the class definition and insert path after name
            import re
            fixed_content = re.sub(
                r"(name = ['\"]" + app + r"['\"])",
                r"\1\n    path = r'" + os.path.join(base_path, app) + r"'",
                content
            )
            
            with open(app_config_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            print(f"Fixed {app}")
        else:
            print(f"Skipped {app} (already has path)")
    else:
        print(f"File not found: {app_config_path}")
