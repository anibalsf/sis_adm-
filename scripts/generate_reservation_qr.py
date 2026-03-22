import qrcode
import os

# CONFIGURACIÓN
# Cambia esta URL por la URL real de tu sistema en producción
BASE_URL = "http://taipiplaya.com"
TARGET_URL = f"{BASE_URL}/pizarra"

def generate_reservation_qr():
    # Asegurar directorio
    output_dir = r"c:\Users\Once\Documents\trae_projects\sistema_administracion\frontend\public"
    output_path = os.path.join(output_dir, "QR_RESERVAS_TAIPIPLAYA.png")
    
    print(f"Generando QR para: {TARGET_URL}")
    
    # Crear objeto QR
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H, # Alta corrección para impresión
        box_size=20,
        border=4,
    )
    qr.add_data(TARGET_URL)
    qr.make(fit=True)

    # Crear imagen
    # Usando fondo blanco y QR verde (color del sindicato)
    img = qr.make_image(fill_color="#2E7D32", back_color="white")
    
    # Guardar
    img.save(output_path)
    print(f"QR guardado en: {output_path}")

if __name__ == "__main__":
    generate_reservation_qr()
