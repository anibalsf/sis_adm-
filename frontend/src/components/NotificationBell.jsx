import React, { useState, useEffect, useRef } from 'react';
import { api } from '../services/api';
import { Link } from 'react-router-dom';

const NotificationBell = () => {
    const [count, setCount] = useState(0);
    const [notifications, setNotifications] = useState([]);
    const [isOpen, setIsOpen] = useState(false);
    const dropdownRef = useRef(null);

    const fetchNotifications = async () => {
        try {
            const res = await api.getAlertasNoLeidas();
            setCount(res.data.count);
            setNotifications(res.data.alertas);
        } catch (err) {
            console.error('Error fetching notifications:', err);
        }
    };

    useEffect(() => {
        fetchNotifications();
        const interval = setInterval(fetchNotifications, 60000); // Poll cada 1 minuto
        return () => clearInterval(interval);
    }, []);

    useEffect(() => {
        const handleClickOutside = (event) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
                setIsOpen(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    const markAsRead = async (id) => {
        try {
            await api.marcarAlertaLeida(id);
            fetchNotifications();
        } catch (err) {
            console.error('Error marking as read:', err);
        }
    };

    const markAllAsRead = async () => {
        try {
            await api.marcarTodasAlertasLeidas();
            fetchNotifications();
        } catch (err) {
            console.error('Error marking all as read:', err);
        }
    };

    return (
        <div className="relative" ref={dropdownRef}>
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="relative p-2.5 rounded-xl bg-gray-100 dark:bg-gray-700 text-lg hover:scale-110 active:scale-95 transition-all shadow-sm"
                title="Notificaciones"
            >
                🔔
                {count > 0 && (
                    <span className="absolute -top-1 -right-1 flex h-5 w-5 items-center justify-center rounded-full bg-red-500 text-[10px] font-bold text-white shadow-lg animate-pulse">
                        {count > 9 ? '9+' : count}
                    </span>
                )}
            </button>

            {isOpen && (
                <div className="absolute right-0 mt-2 w-80 bg-white dark:bg-gray-800 rounded-2xl shadow-2xl border border-gray-200 dark:border-gray-700 z-[100] overflow-hidden animate-in fade-in slide-in-from-top-2">
                    <div className="p-4 border-b border-gray-100 dark:border-gray-700 flex justify-between items-center">
                        <h3 className="font-bold text-gray-800 dark:text-gray-100">Notificaciones</h3>
                        {count > 0 && (
                            <button 
                                onClick={markAllAsRead}
                                className="text-xs font-semibold text-primary hover:underline"
                            >
                                Marcar todas como leídas
                            </button>
                        )}
                    </div>

                    <div className="max-h-[400px] overflow-y-auto">
                        {notifications.length === 0 ? (
                            <div className="p-8 text-center text-gray-500 dark:text-gray-400">
                                <span className="text-3xl block mb-2">🎈</span>
                                <p className="text-sm">Todo al día. No hay alertas nuevas.</p>
                            </div>
                        ) : (
                            notifications.map((notif) => (
                                <div 
                                    key={notif.id}
                                    className="p-4 border-b border-gray-50 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors cursor-pointer group"
                                    onClick={() => markAsRead(notif.id)}
                                >
                                    <div className="flex gap-3">
                                        <div className={`w-10 h-10 rounded-full flex items-center justify-center shrink-0 ${
                                            notif.tipo === 'reserva' ? 'bg-blue-100 text-blue-600' : 
                                            notif.tipo === 'encomienda' ? 'bg-purple-100 text-purple-600' : 
                                            'bg-emerald-100 text-emerald-600'
                                        }`}>
                                            {notif.tipo === 'reserva' ? '📅' : notif.tipo === 'encomienda' ? '📦' : '🚨'}
                                        </div>
                                        <div className="flex-1">
                                            <p className="text-xs font-bold text-gray-900 dark:text-gray-100 mb-0.5">{notif.titulo}</p>
                                            <p className="text-xs text-gray-600 dark:text-gray-400 whitespace-pre-line">{notif.mensaje}</p>
                                            <div className="mt-2 flex justify-between items-center">
                                                <span className="text-[10px] text-gray-400">{new Date(notif.fecha).toLocaleString()}</span>
                                                {notif.link && (
                                                    <Link 
                                                        to={notif.link} 
                                                        className="text-[10px] font-bold text-primary hover:underline"
                                                        onClick={(e) => {
                                                            e.stopPropagation();
                                                            markAsRead(notif.id);
                                                            setIsOpen(false);
                                                        }}
                                                    >
                                                        Ver detalle →
                                                    </Link>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            ))
                        )}
                    </div>

                    {notifications.length > 0 && (
                        <div className="p-3 bg-gray-50 dark:bg-gray-700/30 text-center">
                            <Link 
                                to="/alertas" 
                                className="text-xs font-bold text-gray-500 hover:text-primary transition-colors"
                                onClick={() => setIsOpen(false)}
                            >
                                Ver historial completo
                            </Link>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default NotificationBell;
