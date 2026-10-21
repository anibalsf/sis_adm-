from decimal import Decimal


def precio_de(hoja, ruta):
    """Precio unitario único: hoja de ruta si existe, si no la tarifa de la ruta."""
    if hoja is not None and hoja.precio is not None:
        return Decimal(hoja.precio)
    if ruta is not None and ruta.tarifa_base is not None:
        return Decimal(ruta.tarifa_base)
    return Decimal('0')
