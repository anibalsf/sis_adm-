import React from 'react';
import PropTypes from 'prop-types';
import './StatusBadge.css';

/**
 * Componente de Badge reutilizable para mostrar estados
 */
const StatusBadge = ({ status, type = 'default', size = 'md', icon, children }) => {
    const getStatusClass = () => {
        const statusMap = {
            // Estados de pago
            'pendiente': 'badge-warning',
            'pagado': 'badge-success',
            'vencido': 'badge-danger',
            'parcial': 'badge-info',

            // Estados generales
            'activo': 'badge-success',
            'inactivo': 'badge-secondary',
            'confirmado': 'badge-success',
            'cancelado': 'badge-danger',

            // Estados de reportes
            'generado': 'badge-info',
            'enviado': 'badge-success',
            'fallido': 'badge-danger',

            // Prioridades
            'alta': 'badge-danger',
            'media': 'badge-warning',
            'baja': 'badge-info',
        };

        return statusMap[status?.toLowerCase()] || 'badge-default';
    };

    const getIcon = () => {
        if (icon) return icon;

        const iconMap = {
            'pendiente': '⏳',
            'pagado': '✅',
            'vencido': '❌',
            'activo': '✓',
            'inactivo': '○',
            'confirmado': '✓',
            'cancelado': '✗',
            'generado': '📄',
            'enviado': '📤',
            'fallido': '⚠️',
            'alta': '🔴',
            'media': '🟡',
            'baja': '🟢',
        };

        return iconMap[status?.toLowerCase()] || '';
    };

    return (
        <span className={`status-badge ${getStatusClass()} badge-${size} badge-${type}`}>
            {getIcon() && <span className="badge-icon">{getIcon()}</span>}
            <span className="badge-text">{children || status}</span>
        </span>
    );
};

StatusBadge.propTypes = {
    status: PropTypes.string.isRequired,
    type: PropTypes.oneOf(['default', 'outline', 'soft']),
    size: PropTypes.oneOf(['sm', 'md', 'lg']),
    icon: PropTypes.string,
    children: PropTypes.node,
};

export default StatusBadge;
