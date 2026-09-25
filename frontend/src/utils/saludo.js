/**
 * Utilidades de saludo según la hora
 *
 * La hora se calcula siempre en la zona horaria de Bolivia (America/La_Paz),
 * no en la del dispositivo, para que el saludo coincida con el horario real
 * de la oficina aunque el equipo o el navegador estén en otra zona.
 */

const ZONA_HORARIA = 'America/La_Paz';

const formatoHora = new Intl.DateTimeFormat('en-GB', {
    timeZone: ZONA_HORARIA,
    hour: '2-digit',
    minute: '2-digit',
    hourCycle: 'h23',
});

/**
 * Hora de Bolivia (0-23) en el momento indicado.
 */
export const getHoraBolivia = (fecha = new Date()) => {
    const [hora] = formatoHora.format(fecha).split(':');
    return Number(hora);
};

/**
 * Saludo correspondiente a la hora de Bolivia:
 * 00:00 - 11:59  ¡Buenos días!
 * 12:00 - 18:59  ¡Buenas tardes!
 * 19:00 - 23:59  ¡Buenas noches!
 */
export const getSaludo = (fecha = new Date()) => {
    const hora = getHoraBolivia(fecha);

    if (hora < 12) return '¡Buenos días!';
    if (hora < 19) return '¡Buenas tardes!';
    return '¡Buenas noches!';
};

/**
 * Saludo con el nombre del usuario: "¡Buenas tardes!, Juan"
 */
export const getSaludoConNombre = (nombre = '', fecha = new Date()) => {
    const saludo = getSaludo(fecha);
    return nombre ? `${saludo}, ${nombre}` : saludo;
};
