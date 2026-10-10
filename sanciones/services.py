from django.conf import settings


def get_sancion_config(tipo_config):
    """Resuelve la configuración de una sanción a partir de su clave.

    Retorna un dict con la clave, el nombre del tipo y el monto de la multa.
    Si la clave no existe se usa FALTA_REUNION como respaldo.
    """
    config = getattr(settings, 'SANCIONES_CONFIG', {})
    conf = config.get(tipo_config) or config.get('FALTA_REUNION', {})
    return {
        'config_key': tipo_config if tipo_config in config else 'FALTA_REUNION',
        'tipo': conf.get('tipo', 'Falta a Reunión'),
        'monto': conf.get('monto_default', getattr(settings, 'SANCTION_ABSENCE_AMOUNT', 50)),
        'notificar_automatico': conf.get('notificar_automatico', True),
    }


def get_sancion_config_para_reunion(tipo_reunion, monto_override=None):
    """Devuelve la configuración de sanción que corresponde al tipo de reunión.

    - asamblea_general -> FALTA_ASAMBLEA
    - trabajo          -> FALTA_TRABAJO
    - resto            -> FALTA_REUNION

    Si monto_override es mayor a 0, se usa ese monto (multa editable por reunión).
    """
    mapa = getattr(settings, 'REUNION_TIPO_A_SANCION', {})
    tipo_config = mapa.get(tipo_reunion, 'FALTA_REUNION')
    cfg = get_sancion_config(tipo_config)
    try:
        if monto_override is not None and float(monto_override) > 0:
            cfg['monto'] = float(monto_override)
    except (TypeError, ValueError):
        pass
    return cfg


def get_sancion_config_para_reunion_obj(reunion):
    """Igual que get_sancion_config_para_reunion pero a partir de una Reunion."""
    if reunion is None:
        return get_sancion_config_para_reunion(None)
    return get_sancion_config_para_reunion(reunion.tipo, getattr(reunion, 'monto_multa', None))



def monto_falta_reunion(tipo_reunion):
    """Monto de multa a aplicar por faltar a una reunión/actividad."""
    return get_sancion_config_para_reunion(tipo_reunion)['monto']
