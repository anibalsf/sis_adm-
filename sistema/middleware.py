import threading

_thread_locals = threading.local()


def get_current_request():
    return getattr(_thread_locals, 'request', None)


def get_current_user():
    """Usuario autenticado de la petición en curso (o None).

    Se resuelve de forma perezosa a propósito: DRF autentica el token JWT
    *después* de que se ejecuten los middlewares, así que leer request.user
    dentro del middleware devolvía siempre AnonymousUser y la bitácora quedaba
    sin autor. Leyendo el atributo en el momento del log ya está poblado.
    """
    request = get_current_request()
    if request is not None:
        user = getattr(request, 'user', None)
        return user if getattr(user, 'is_authenticated', False) else None

    user = getattr(_thread_locals, 'user', None)
    return user if getattr(user, 'is_authenticated', False) else None


def get_client_ip():
    """IP del cliente, teniendo en cuenta el proxy inverso (nginx)."""
    request = get_current_request()
    if request is None:
        return None

    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip()

    return request.META.get('REMOTE_ADDR') or None


class CurrentUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_locals.request = request
        _thread_locals.user = getattr(request, 'user', None)
        try:
            return self.get_response(request)
        finally:
            # Limpiar al finalizar la petición
            for attr in ('request', 'user'):
                if hasattr(_thread_locals, attr):
                    delattr(_thread_locals, attr)
