import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { Link } from 'react-router-dom';
import QRScanner from './QRScanner';
import { IconQrCode } from './Icons';

const Header = ({ toggleSidebar }) => {
    const { user, logout } = useAuth();
    const { darkMode, toggleDarkMode } = useTheme();
    const [showScanner, setShowScanner] = useState(false);

    return (
        <header className="header flex items-center justify-between px-4 sm:px-6 py-4 bg-surface dark:bg-gray-800 border-b border-subtle dark:border-gray-700 sticky top-0 z-50">
            <div className="flex items-center">
                <button
                    className="lg:hidden text-primary text-2xl mr-4 hover:bg-primary/10 p-2 rounded-xl transition-colors"
                    onClick={toggleSidebar}
                >
                    ☰
                </button>
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
                    title="Escanear Hoja de Ruta"
                >
                    <IconQrCode className="w-5 h-5" />
                    <span className="hidden sm:inline">Escanear QR</span>
                </button>
                <button
                    onClick={toggleDarkMode}
                    className="p-2.5 rounded-xl bg-gray-100 dark:bg-gray-700 text-lg hover:scale-110 active:scale-95 transition-all shadow-sm"
                    title={darkMode ? "Modo Claro" : "Modo Oscuro"}
                >
                    {darkMode ? '☀️' : '🌙'}
                </button>
                {showScanner && <QRScanner onClose={() => setShowScanner(false)} />}
                <div className="relative group">
                    <button className="flex items-center gap-3 pl-2 pr-1 py-1 rounded-2xl hover:bg-gray-100 dark:hover:bg-gray-700 transition-all border border-transparent hover:border-gray-200 dark:hover:border-gray-600">
                        <div className="w-9 h-9 bg-primary flex items-center justify-center rounded-xl text-white font-bold shadow-lg shadow-primary/30">
                            {user?.username?.charAt(0).toUpperCase() || 'A'}
                        </div>
                        <div className="hidden lg:block text-left">
                            <p className="text-sm font-bold text-main dark:text-gray-100 leading-none mb-1">
                                {user?.username || 'Admin'}
                            </p>
                            <p className="text-[10px] text-muted dark:text-gray-400 font-semibold uppercase tracking-wider">
                                {user?.role || 'SISTEMAS'}
                            </p>
                        </div>
                        <span className="text-[10px] text-muted ml-1 opacity-50 group-hover:rotate-180 transition-transform">▼</span>
                    </button>
                    <div className="absolute right-0 mt-2 w-56 opacity-0 translate-y-2 pointer-events-none group-hover:opacity-100 group-hover:translate-y-0 group-hover:pointer-events-auto transition-all duration-200 z-50">
                        <div className="bg-surface dark:bg-gray-800 border border-subtle dark:border-gray-700 rounded-2xl shadow-2xl p-2 overflow-hidden">
                            <Link to="/usuarios" className="flex items-center gap-3 px-4 py-3 text-sm font-semibold rounded-xl hover:bg-primary/10 hover:text-primary transition-all text-main dark:text-gray-200">
                                👥 Gestionar Usuarios
                            </Link>
                            <button onClick={logout} className="w-full flex items-center gap-3 px-4 py-3 text-sm font-semibold rounded-xl hover:bg-red-50 dark:hover:bg-red-900/20 hover:text-red-500 transition-all text-main dark:text-gray-200">
                                🚪 Cerrar Sesión
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </header>
    );

};

export default Header;
