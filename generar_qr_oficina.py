import qrcode
from PIL import Image, ImageDraw, ImageFont
import os

def generate_office_qr():
    # URL de la pizarra (El usuario debe cambiar esto por su dominio real)
    url_pizarra = "https://sindicato-taipiplaya.com/pizarra" # Placeholder
    
    print(f"Generando QR para: {url_pizarra}")
    
    # Configurar el QR
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(url_pizarra)
    qr.make(fit=True)

    # Crear la imagen del QR (Verde Sindicato)
    qr_img = qr.make_image(fill_color="#10b981", back_color="white").convert('RGB')
    
    # Intentar cargar el logo del sindicato para ponerlo en el centro
    logo_path = "c:/Users/Once/Documents/trae_projects/sistema_administracion/public/logo_smit.jpg"
    if not os.path.exists(logo_path):
        # Intentar en la ruta relativa si la absoluta falla
        logo_path = "logo_smit.jpg"
        
    try:
        if os.path.exists(logo_path):
            logo = Image.open(logo_path)
            # Ajustar tamaño del logo
            pos = ((qr_img.size[0] - 60) // 2, (qr_img.size[1] - 60) // 2)
            logo = logo.resize((60, 60))
            qr_img.paste(logo, pos)
            print("Logo integrado con éxito.")
    except Exception as e:
        print(f"No se pudo integrar el logo: {e}")

    # Guardar el QR
    qr_img.save("qr_pizarra_publica.png")
    print("Archivo 'qr_pizarra_publica.png' generado.")

if __name__ == "__main__":
    generate_office_qr()
