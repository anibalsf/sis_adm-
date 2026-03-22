from PIL import Image, ImageDraw, ImageFont
import os

def crear_poster_mejorado():
    # Dimensiones (Proporción A4)
    w, h = 1240, 1754
    poster = Image.new('RGB', (w, h), 'white')
    draw = ImageDraw.Draw(poster)
    
    # Colores
    emerald = "#10b981"
    navy = "#1e293b"
    white = "#ffffff"
    
    # 1. Fondo Superior (Navy)
    draw.rectangle([0, 0, w, h*0.4], fill=navy)
    
    # 2. Línea divisoria
    draw.rectangle([0, h*0.4, w, h*0.41], fill=emerald)
    
    # 3. Tipografía
    try:
        font_titulo = ImageFont.truetype("arialbd.ttf", 100)
        font_sub = ImageFont.truetype("arial.ttf", 45)
        font_footer = ImageFont.truetype("arialbd.ttf", 55)
        font_modelo = ImageFont.truetype("arialbd.ttf", 35)
    except:
        font_titulo = ImageFont.load_default()
        font_sub = ImageFont.load_default()
        font_footer = ImageFont.load_default()
        font_modelo = ImageFont.load_default()

    # Título (Centrado)
    txt_titulo = "RESERVA TU\nPASAJE ONLINE"
    draw.text((w/2, 220), txt_titulo, fill=white, font=font_titulo, anchor="mm", align="center")
    
    # Subtítulo (CORREGIDO: Centrado)
    txt_sub = "Escanea el código para ver salidas\ny elegir tu asiento en tiempo real"
    draw.multiline_text((w/2, 480), txt_sub, fill=white, font=font_sub, anchor="mm", align="center", spacing=10)
    
    # 4. QR Centrado con Borde
    qr_path = "QR_RESERVAS_TAIPIPLAYA.png"
    if os.path.exists(qr_path):
        qr_img = Image.open(qr_path)
        qr_size = 700
        qr_img = qr_img.resize((qr_size, qr_size), Image.LANCZOS)
        
        # Recuadro blanco para el QR
        border = 25
        qr_y_pos = int(h*0.35)
        draw.rectangle([w/2 - qr_size/2 - border, qr_y_pos - border, 
                        w/2 + qr_size/2 + border, qr_y_pos + qr_size + border], 
                       fill=white, outline=emerald, width=8)
        
        poster.paste(qr_img, (int(w/2 - qr_size/2), qr_y_pos))
    
    # 5. Dibujo de Vehículos (Siluetas Estéticas en lugar de rectángulos vacíos)
    def draw_minibus(x, y):
        # Cuerpo principal
        draw.rounded_rectangle([x, y, x+300, y+130], radius=15, fill="#f1f5f9", outline=navy, width=3)
        # Ventanas
        draw.rectangle([x+20, y+20, x+100, y+60], fill="#cbd5e1")
        draw.rectangle([x+110, y+20, x+190, y+60], fill="#cbd5e1")
        draw.rectangle([x+200, y+20, x+280, y+60], fill="#cbd5e1")
        # Ruedas
        draw.ellipse([x+40, y+110, x+80, y+150], fill=navy)
        draw.ellipse([x+220, y+110, x+260, y+150], fill=navy)
        # Detalle Emerald
        draw.rectangle([x, y+80, x+300, y+90], fill=emerald)

    def draw_ipsum(x, y):
        # Cuerpo (forma de auto/vagoneta)
        draw.polygon([(x, y+130), (x+50, y+60), (x+200, y+60), (x+280, y+130)], fill="#f1f5f9", outline=navy)
        draw.rounded_rectangle([x-20, y+80, x+300, y+130], radius=10, fill="#f1f5f9", outline=navy, width=3)
        # Ventanas
        draw.polygon([(x+10, y+90), (x+55, y+70), (x+140, y+70), (x+140, y+90)], fill="#cbd5e1")
        draw.polygon([(x+150, y+90), (x+150, y+70), (x+195, y+70), (x+240, y+90)], fill="#cbd5e1")
        # Ruedas
        draw.ellipse([x+30, y+110, x+70, y+150], fill=navy)
        draw.ellipse([x+210, y+110, x+250, y+150], fill=navy)
        # Detalle Emerald
        draw.rectangle([x-20, y+100, x+300, y+105], fill=emerald)

    # Dibujar los vehículos
    draw_ipsum(w*0.15, h*0.78)
    draw_minibus(w*0.6, h*0.78)
    
    # Etiquetas de modelos
    draw.text((w*0.27, h*0.89), "🚗 TOYOTA IPSUM\n(6 PASAJEROS)", fill=navy, font=font_modelo, anchor="mm", align="center")
    draw.text((w*0.73, h*0.89), "🚐 MINIBUS\n(15 PASAJEROS)", fill=navy, font=font_modelo, anchor="mm", align="center")
    
    # 6. Footer (Centrado)
    draw.rectangle([0, h-160, w, h], fill=emerald)
    # Sombra del texto para legibilidad
    txt_sindicato = "SINDICATO MIXTO INTEGRACIÓN TAIPIPLAYA"
    draw.text((w/2, h-80), txt_sindicato, fill=white, font=font_footer, anchor="mm")
    
    # Guardar
    output_path = "POSTER_RESERVAS_TAIPIPLAYA.png"
    poster.save(output_path)
    print(f"Poster corregido guardado en: {output_path}")

if __name__ == "__main__":
    crear_poster_mejorado()
