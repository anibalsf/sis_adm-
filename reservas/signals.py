from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Reserva
from comunicacion.models import AlertaSistema

@receiver(post_save, sender=Reserva)
def crear_alerta_reserva(sender, instance, created, **kwargs):
    if created:
        # Solo para nuevas reservas (especialmente las que vengan de la pizarra pública)
        # La lógica de si es "pizarra pública" o no se suele manejar con un campo adicional o simplemente avisando todas
        from rutas.models import Ruta
        ruta_nombre = instance.ruta.nombre if instance.ruta else "Ruta desconocida"
        
        AlertaSistema.objects.create(
            tipo='reserva',
            titulo=f"Nueva Reserva Online",
            mensaje=f"Pasajero: {instance.cliente}\nRuta: {ruta_nombre}\nFecha: {instance.fecha_viaje}",
            link=f"/reservas" # Link al módulo de reservas en el frontend
        )
