import qrcode
from pathlib import Path

# CONFIGURACIÓN
BASE_URL = "https://administracion.sindicatointegracion.com"
TARGET_URL = f"{BASE_URL}/reservas"

def generate_reservation_qr():
    # Resolver la salida desde el repositorio para que funcione en cualquier equipo.
    output_dir = Path(__file__).resolve().parents[1] / 'frontend' / 'public'
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / 'QR_RESERVAS_TAIPIPLAYA.png'
    
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
