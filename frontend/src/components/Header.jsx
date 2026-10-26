import React, { useEffect, useRef, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { Link } from 'react-router-dom';
import QRScanner from './QRScanner';
import {
    IconChevronDown,
    IconKey,
    IconLogout,
    IconMail,
    IconQrCode,
    IconUser,
    IconUsers,
} from './Icons';
import NotificationBell from './NotificationBell';
import './UserMenu.css';

const Header = ({ toggleSidebar }) => {
    const { user, logout } = useAuth();
    const { darkMode, toggleDarkMode } = useTheme();
    const [showScanner, setShowScanner] = useState(false);
    const [userMenuOpen, setUserMenuOpen] = useState(false);
    const userMenuRef = useRef(null);
    const userMenuTriggerRef = useRef(null);

    const nombreCompleto = [user?.first_name, user?.last_name]
        .filter(Boolean)
        .join(' ')
        .trim();
    const nombreVisible = nombreCompleto || user?.username || 'Usuario';
    const inicial = (user?.username || user?.first_name || 'U').charAt(0).toUpperCase();
    const puedeGestionarUsuarios = Boolean(user?.is_staff)
        || ['Directiva', 'Sistemas'].includes(user?.role);

    useEffect(() => {
        if (!userMenuOpen) return undefined;

        const handleClickOutside = (event) => {
            if (userMenuRef.current && !userMenuRef.current.contains(event.target)) {
                setUserMenuOpen(false);
            }
        };

        const handleEscape = (event) => {
            if (event.key === 'Escape') {
                setUserMenuOpen(false);
                userMenuTriggerRef.current?.focus();
            }
        };

        document.addEventListener('mousedown', handleClickOutside);
        document.addEventListener('keydown', handleEscape);

        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
            document.removeEventListener('keydown', handleEscape);
        };
    }, [userMenuOpen]);

    const closeUserMenu = () => setUserMenuOpen(false);

    const handleLogout = () => {
        closeUserMenu();
        logout();
    };

    return (
        <header className="header flex items-center justify-between px-4 sm:px-6 py-4 bg-surface dark:bg-gray-800 border-b border-subtle dark:border-gray-700 sticky top-0 z-50">
            <div className="flex items-center">
                {user?.role !== 'Afiliado' && (
                    <button
                        className="lg:hidden text-primary text-2xl mr-4 hover:bg-primary/10 p-2 rounded-xl transition-colors"
                        onClick={toggleSidebar}
                    >
                        ☰
                    </button>
                )}
                <div className="hidden lg:flex flex-col ml-2">
                    <div className="max-w-fit">
                        <h1 className="text-2xl font-extrabold bg-gradient-to-r from-emerald-600 via-green-500 to-emerald-600 bg-clip-text text-transparent uppercase tracking-tight leading-none animate-typing-title">
                            Sistema de Administración
                        </h1>
                    </div>
                    <div className="max-w-fit">
                        <p className="text-sm font-bold text-emerald-700 dark:text-emerald-400 uppercase tracking-[0.15em] mt-1 opacity-100 animate-typing-subtitle">
                            Sindicato Mixto de Transporte Taipiplaya
                        </p>
                    </div>
                </div>
            </div>
            <div className="flex items-center gap-3 sm:gap-6">
                <button
                    onClick={() => setShowScanner(true)}
                    className="flex items-center gap-2 px-4 py-2 bg-primary/10 hover:bg-primary/20 text-primary rounded-xl transition-all font-semibold text-sm border border-primary/20"
                    title="Escanear QR de reservas, hoja de ruta o voucher"
                >
                    <IconQrCode className="w-5 h-5" />
                    <span className="hidden sm:inline">Escanear QR</span>
                </button>
                
                <NotificationBell />

                <button
                    onClick={toggleDarkMode}
                    className="p-2.5 rounded-xl bg-gray-100 dark:bg-gray-700 text-lg hover:scale-110 active:scale-95 transition-all shadow-sm"
                    title={darkMode ? "Modo Claro" : "Modo Oscuro"}
                >
                    {darkMode ? '☀️' : '🌙'}
                </button>
                {showScanner && <QRScanner onClose={() => setShowScanner(false)} />}
                <div className="um-shell" ref={userMenuRef}>
                    <button
                        ref={userMenuTriggerRef}
                        type="button"
                        className={`um-trigger${userMenuOpen ? ' is-open' : ''}`}
                        onClick={() => setUserMenuOpen((open) => !open)}
                        aria-haspopup="menu"
                        aria-expanded={userMenuOpen}
                        aria-controls="user-menu-panel"
                        aria-label={`Abrir menú de ${nombreVisible}`}
                    >
                        <span className="um-avatar">{inicial}</span>
                        <span className="um-identity">
                            <span className="um-name">{user?.username || 'Usuario'}</span>
                            <span className="um-role-label">{user?.role || 'SISTEMAS'}</span>
                        </span>
                        <span className="um-chevron" aria-hidden="true">
                            <IconChevronDown />
                        </span>
                    </button>

                    {userMenuOpen && (
                        <div
                            id="user-menu-panel"
                            className="um-panel"
                            role="menu"
                            aria-label="Opciones de usuario"
                        >
                            <div className="um-profile">
                                <span className="um-avatar um-avatar--lg">{inicial}</span>
                                <div className="um-profile-text">
                                    <p className="um-profile-name">{nombreVisible}</p>
                                    {nombreCompleto && (
                                        <p className="um-profile-handle">@{user?.username}</p>
                                    )}
                                    <span className="um-role">{user?.role || 'Usuario'}</span>
                                </div>
                            </div>

                            {user?.email && (
                                <div className="um-email">
                                    <IconMail />
                                    <span>{user.email}</span>
                                </div>
                            )}

                            <div className="um-divider" />

                            <Link
                                to="/mi-perfil"
                                className="um-item"
                                role="menuitem"
                                onClick={closeUserMenu}
                            >
                                <span className="um-item-icon">
                                    <IconUser />
                                </span>
                                <span className="um-item-text">
                                    <strong>Mi perfil</strong>
                                    <small>Datos personales y cuenta</small>
                                </span>
                            </Link>

                            <Link
                                to="/change-password"
                                className="um-item"
                                role="menuitem"
                                onClick={closeUserMenu}
                            >
                                <span className="um-item-icon">
                                    <IconKey />
                                </span>
                                <span className="um-item-text">
                                    <strong>Seguridad</strong>
                                    <small>Cambiar mi contraseña</small>
                                </span>
                            </Link>

                            {puedeGestionarUsuarios && (
                                <Link
                                    to="/usuarios"
                                    className="um-item"
                                    role="menuitem"
                                    onClick={closeUserMenu}
                                >
                                    <span className="um-item-icon">
                                        <IconUsers />
                                    </span>
                                    <span className="um-item-text">
                                        <strong>Gestión de usuarios</strong>
                                        <small>Roles y permisos de acceso</small>
                                    </span>
                                </Link>
                            )}

                            <div className="um-divider" />

                            <button
                                type="button"
                                className="um-item um-item--danger"
                                role="menuitem"
                                onClick={handleLogout}
                            >
                                <span className="um-item-icon">
                                    <IconLogout />
                                </span>
                                <span className="um-item-text">
                                    <strong>Cerrar sesión</strong>
                                    <small>Salir del sistema de forma segura</small>
                                </span>
                            </button>
                        </div>
                    )}
                </div>
            </div>
        </header>
    );

};

export default Header;
