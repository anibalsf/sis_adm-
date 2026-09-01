"""
Script para generar el QR de Movilidades de Turno a La Paz.
Al escanear, el pasajero verá: nombre completo, placa y teléfono
de las movilidades (ipsum y minibus) de turno para hacer la reserva.

Ejecutar: python generar_qr_movilidades_lapaz.py
"""
import qrcode
from PIL import Image, ImageDraw, ImageFont
import os

def generate_qr_movilidades():
    # URL pública exacta para el QR de reservas.
    base_url = "https://administracion.sindicatointegracion.com"
    url = f"{base_url}/reservas"

    print(f"Generando QR para: {url}")

    # Configurar el código QR
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)

    # Color principal: azul sindicato
    qr_img = qr.make_image(fill_color="#1a3a5c", back_color="white").convert('RGB')

    # Intentar integrar logo del sindicato
    logo_paths = [
        r"d:/Users/Once/Documents/trae_projects/sistema_administracion/frontend/public/logo_smit.jpg",
        r"d:/Users/Once/Documents/trae_projects/sistema_administracion/public/logo_smit.jpg",
        "logo_smit.jpg",
    ]

    for logo_path in logo_paths:
        if os.path.exists(logo_path):
            try:
                logo = Image.open(logo_path).convert("RGBA")
                size = 70
                logo = logo.resize((size, size), Image.LANCZOS)
                pos = ((qr_img.size[0] - size) // 2, (qr_img.size[1] - size) // 2)
                qr_img.paste(logo, pos, logo if logo.mode == 'RGBA' else None)
                print(f"Logo integrado desde: {logo_path}")
            except Exception as e:
                print(f"No se pudo integrar el logo: {e}")
            break
    else:
        print("No se encontró el logo. El QR se generará sin él.")

    # Crear imagen final con bordes y texto
    qr_w, qr_h = qr_img.size
    padding = 30
    footer_h = 80
    final_w = qr_w + padding * 2
    final_h = qr_h + padding * 2 + footer_h

    final = Image.new('RGB', (final_w, final_h), '#0a0f1e')
    draw = ImageDraw.Draw(final)

    # Fondo blanco para el QR con borde redondeado simulado
    bg = Image.new('RGB', (qr_w + 20, qr_h + 20), 'white')
    final.paste(bg, (padding - 10, padding - 10))
    final.paste(qr_img, (padding, padding))

    # Intentar usar fuente personalizada
    try:
        font_title = ImageFont.truetype("arial.ttf", 18)
        font_sub   = ImageFont.truetype("arial.ttf", 13)
    except Exception:
        font_title = ImageFont.load_default()
        font_sub   = font_title

    # Texto de instrucción
    title_text = "📱 RESERVA TU PASAJE A LA PAZ"
    sub_text   = "Escanea para ver afiliado, placa, celular y hora"

    # Calcular posición centrada del texto
    text_y = qr_h + padding * 2 - 5
    draw.text((final_w // 2, text_y), title_text, font=font_title, fill="#10b981", anchor="mm")
    draw.text((final_w // 2, text_y + 28), sub_text, font=font_sub, fill="#94a3b8", anchor="mm")

    # Guardar
    output_path = "qr_movilidades_lapaz.png"
    final.save(output_path)
    print(f"\n[OK] QR generado: '{output_path}'")
    print(f"     URL: {url}")
    print("\nPega este QR en la oficina o en la parada para que los pasajeros")
    print("escaneen y vean las movilidades de turno con telefono para reservar.")



if __name__ == "__main__":
    generate_qr_movilidades()
