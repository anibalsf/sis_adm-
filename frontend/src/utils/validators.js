/**
 * Utilidades de validación para formularios
 */

export const validators = {
    /**
     * Valida CI boliviano
     * Formato: 6-10 dígitos, opcionalmente con extensión
     */
    ci: (value) => {
        if (!value) return '';
        const pattern = /^\d{6,10}(-[0-9A-Z]{1,2})?$/;
        if (!pattern.test(value.toUpperCase())) {
            return 'CI inválido. Formato: 12345678 o 12345678-1A';
        }
        return '';
    },

    /**
     * Valida teléfono boliviano
     * Formato: 8 dígitos comenzando con 6 o 7
     */
    telefono: (value) => {
        if (!value) return '';
        const cleaned = value.replace(/[\s-]/g, '');
        const pattern = /^[67]\d{7}$/;
        if (!pattern.test(cleaned)) {
            return 'Teléfono inválido. Debe tener 8 dígitos y comenzar con 6 o 7';
        }
        return '';
    },

    /**
     * Valida placa de vehículo boliviano
     * Formato: ABC-1234 o 1234-ABC
     */
    placa: (value) => {
        if (!value) return '';
        const cleaned = value.replace(/\s/g, '').toUpperCase();
        const pattern = /^([A-Z]{3}-?\d{4}|\d{4}-?[A-Z]{3})$/;
        if (!pattern.test(cleaned)) {
            return 'Placa inválida. Formato: ABC-1234 o 1234-ABC';
        }
        return '';
    },

    /**
     * Valida email
     */
    email: (value) => {
        if (!value) return '';
        const pattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
        if (!pattern.test(value)) {
            return 'Email inválido';
        }
        return '';
    },

    /**
     * Valida monto positivo
     */
    monto: (value) => {
        if (!value) return '';
        const num = parseFloat(value);
        if (isNaN(num) || num <= 0) {
            return 'El monto debe ser mayor a 0';
        }
        // Validar máximo 2 decimales
        if (!/^\d+(\.\d{1,2})?$/.test(value)) {
            return 'Máximo 2 decimales permitidos';
        }
        return '';
    },

    /**
     * Valida que la fecha no sea futura
     */
    fechaNoFutura: (value) => {
        if (!value) return '';
        const fecha = new Date(value);
        const hoy = new Date();
        hoy.setHours(0, 0, 0, 0);
        if (fecha > hoy) {
            return 'La fecha no puede ser futura';
        }
        return '';
    }
};

/**
 * Formateadores automáticos
 */
export const formatters = {
    /**
     * Formatea CI: solo números, letras y guión
     */
    ci: (value) => {
        return value.toUpperCase().replace(/[^0-9A-Z-]/g, '').slice(0, 12);
    },

    /**
     * Formatea teléfono: solo números, máximo 8
     */
    telefono: (value) => {
        return value.replace(/\D/g, '').slice(0, 8);
    },

    /**
     * Formatea placa: mayúsculas, letras, números y guión
     */
    placa: (value) => {
        return value.toUpperCase().replace(/[^A-Z0-9-]/g, '').slice(0, 8);
    },

    /**
     * Formatea monto: solo números y punto decimal
     */
    monto: (value) => {
        // Permitir solo números y un punto decimal
        let formatted = value.replace(/[^\d.]/g, '');
        // Permitir solo un punto decimal
        const parts = formatted.split('.');
        if (parts.length > 2) {
            formatted = parts[0] + '.' + parts.slice(1).join('');
        }
        // Limitar a 2 decimales
        if (parts.length === 2 && parts[1].length > 2) {
            formatted = parts[0] + '.' + parts[1].slice(0, 2);
        }
        return formatted;
    }
};

/**
 * Hook personalizado para validación
 */
export const useValidation = (validationType) => {
    const validate = (value) => {
        if (validators[validationType]) {
            return validators[validationType](value);
        }
        return '';
    };

    const format = (value) => {
        if (formatters[validationType]) {
            return formatters[validationType](value);
        }
        return value;
    };

    return { validate, format };
};
