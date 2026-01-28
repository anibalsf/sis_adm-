
try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    import os

    print("Reportlab imported successfully")

    # Check color
    try:
        c_color = colors.mediumseagreen
        print(f"Color mediumseagreen found: {c_color}")
    except AttributeError:
        print("Color mediumseagreen NOT FOUND")
        c_color = colors.green

    # Try to generate a PDF
    filename = "test_gen.pdf"
    c = canvas.Canvas(filename, pagesize=A4)
    w, h = A4
    c.drawString(100, 700, "Hello World - Test PDF")
    
    # Draw colored rect
    c.setFillColor(c_color)
    c.rect(100, 600, 200, 50, fill=1, stroke=0)
    
    c.showPage()
    c.save()
    
    print(f"PDF generated: {filename}, size: {os.path.getsize(filename)} bytes")

except Exception as e:
    print(f"Error: {e}")
