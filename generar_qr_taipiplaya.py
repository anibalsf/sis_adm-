import qrcode
from PIL import Image, ImageDraw, ImageFont
import os

def generate_taipiplaya_qr():
    # Página pública de reservas y asignaciones a La Paz.
    url_reservas = "https://administracion.sindicatointegracion.com/reservas"
    
    print(f"Generando QR para la oficina de TAIPIPLAYA: {url_reservas}")
    
    # Configurar el QR con alta corrección de errores para poder poner el logo
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=15,
        border=4,
    )
    qr.add_data(url_reservas)
    qr.make(fit=True)

    # Crear la imagen del QR (Verde Estético del Sindicato)
    qr_img = qr.make_image(fill_color="#10b981", back_color="white").convert('RGB')
    
    # Intentar integrar el logo en el centro
    logo_path = "c:/Users/Once/Documents/trae_projects/sistema_administracion/public/logo_smit.jpg"
    if not os.path.exists(logo_path):
        logo_path = "logo_smit.jpg"
        
    try:
        if os.path.exists(logo_path):
            logo = Image.open(logo_path)
            # El logo no debe ocupar más del 20% del QR
            size = qr_img.size[0]
            logo_size = int(size * 0.2)
            logo = logo.resize((logo_size, logo_size), Image.LANCZOS)
            
            # Crear un fondo blanco circular o cuadrado detrás del logo para que resalte
            pos = ((size - logo_size) // 2, (size - logo_size) // 2)
            mask = Image.new('L', (logo_size, logo_size), 255)
            qr_img.paste(logo, pos, mask)
            print("Logo integrado con éxito en el centro.")
    except Exception as e:
        print(f"Nota: No se pudo integrar el logo ({e}). Se generó el QR estándar.")

    # Guardar el archivo final
    filename = "QR_RESERVAS_TAIPIPLAYA.png"
    qr_img.save(filename)
    print(f"\n[OK] ¡EXITO! Se ha generado el archivo: {filename}")
    print("--------------------------------------------------")
    print("Instrucciones para la oficina:")
    print("1. Imprime este código en tamaño grande.")
    print("2. Colócalo en la ventanilla o pared de la oficina de Taipiplaya.")
    print("3. Funciona para reservar tanto en IPSUM (6 asientos) como en MINIBUS (15 asientos).")

if __name__ == "__main__":
    generate_taipiplaya_qr()
