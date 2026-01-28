import React, { useEffect } from 'react';
import './Toast.css';
import {
    IconCheck,
    IconBan,
    IconAlertTriangle,
    IconInfo
} from './Icons';

const Toast = ({ message, type, id, onRemove, duration }) => {
    useEffect(() => {
        const timer = setTimeout(() => {
            onRemove(id);
        }, duration);
        return () => clearTimeout(timer);
    }, [id, onRemove, duration]);

    const getIcon = () => {
        switch (type) {
            case 'success': return <IconCheck />;
            case 'error': return <IconBan />;
            case 'warning': return <IconAlertTriangle />;
            default: return <IconInfo />;
        }
    };

    return (
        <div className={`toast-item toast-${type}`} onClick={() => onRemove(id)}>
            <div className="toast-icon">
                {getIcon()}
            </div>
            <div className="toast-content">
                <p>{message}</p>
            </div>
            <button className="toast-close">✕</button>
            <div className="toast-progress">
                <div
                    className="toast-progress-bar"
                    style={{ animationDuration: `${duration}ms` }}
                />
            </div>
        </div>
    );
};

const ToastContainer = ({ toasts, removeToast }) => {
    return (
        <div className="toast-container">
            {toasts.map((toast) => (
                <Toast
                    key={toast.id}
                    {...toast}
                    onRemove={removeToast}
                />
            ))}
        </div>
    );
};

export default ToastContainer;
