import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
    IconHome, IconUser, IconUsers, IconBus, IconLayout,
    IconMapPin, IconList, IconCalendar, IconCash,
    IconTrendingUp, IconBarChart, IconAlertTriangle,
    IconHistory, IconLock, IconShield
} from './Icons';

const Sidebar = ({ isOpen, toggleSidebar }) => {
    const location = useLocation();
    const { user } = useAuth();
    const userRole = user?.role || 'Afiliado';

    const fallbackSvg =
        'data:image/svg+xml;utf8,' +
        encodeURIComponent(
            `<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 80 80">
                <defs>
                    <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
                        <stop offset="0%" stop-color="#4a9d9c"/>
                        <stop offset="100%" stop-color="#3a7d7c"/>
                    </linearGradient>
                </defs>
                <circle cx="40" cy="40" r="38" fill="url(#g)" stroke="#e5e7eb" stroke-width="2"/>
                <text x="40" y="46" font-size="22" font-weight="700" text-anchor="middle" fill="#ffffff">SMIT</text>
            </svg>`
        );
    const handleLogoError = (e) => {
        e.currentTarget.src = fallbackSvg;
    };

    const menuGroups = [
        {
            title: 'PRINCIPAL',
            items: [
                { path: '/', icon: <IconHome />, label: 'Inicio', color: '#10b981' }, // Emerald
                { path: '/mi-perfil', icon: <IconUser />, label: 'Mi Perfil', color: '#3b82f6' }, // Blue
            ]
        },
        {
            title: 'OPERATIVO',
            items: [
                { path: '/afiliados', icon: <IconUsers />, label: 'Afiliados', roles: ['Directiva', 'Secretaria', 'Sistemas'], color: '#6366f1' }, // Indigo
                { path: '/vehiculos', icon: <IconBus />, label: 'Vehículos', roles: ['Directiva', 'Secretaria', 'Sistemas'], color: '#f43f5e' }, // Rose
                { path: '/directorio', icon: <IconLayout />, label: 'Directorio', roles: ['Directiva', 'Sistemas'], color: '#0ea5e9' }, // Sky
                { path: '/rutas', icon: <IconMapPin />, label: 'Rutas', roles: ['Directiva', 'Secretaria', 'Sistemas'], color: '#8b5cf6' }, // Violet
                { path: '/hojas-ruta', icon: <IconList />, label: 'Hojas de Ruta', roles: ['Directiva', 'Secretaria', 'Sistemas', 'Agente'], color: '#f59e0b' }, // Amber
                { path: '/reservas', icon: <IconCalendar />, label: 'Reservas', roles: ['Directiva', 'Secretaria', 'Sistemas', 'Agente'], color: '#ec4899' }, // Pink
            ]
        },
        {
            title: 'ADMINISTRACIÓN',
            items: [
                { path: '/pagos-y-egresos', icon: <IconCash />, label: 'Pagos y Egresos', roles: ['Directiva', 'Secretaria', 'Sistemas'], color: '#22c55e' }, // Green
                { path: '/balance', icon: <IconTrendingUp />, label: 'Balance Financiero', roles: ['Directiva', 'Sistemas'], color: '#f97316' }, // Orange
                { path: '/reportes', icon: <IconBarChart />, label: 'Reportes', roles: ['Directiva', 'Secretaria', 'Sistemas'], color: '#a855f7' }, // Purple
                { path: '/reportes-automaticos', icon: <IconBarChart />, label: 'Reportes Automáticos', roles: ['Directiva', 'Sistemas'], color: '#06b6d4' }, // Cyan
                { path: '/sanciones-asistencia', icon: <IconAlertTriangle />, label: 'Sanciones / Asistencia', roles: ['Directiva', 'Secretaria', 'Sistemas'], color: '#ef4444' }, // Red
            ]
        },
        {
            title: 'SISTEMA',
            items: [
                { path: '/usuarios', icon: <IconUser />, label: 'Gestión Usuarios', roles: ['Directiva', 'Sistemas'], color: '#6366f1' }, // Indigo
                { path: '/bitacora', icon: <IconHistory />, label: 'Bitácora', roles: ['Directiva', 'Sistemas'], color: '#8b5cf6' }, // Violet
                { path: '/change-password', icon: <IconLock />, label: 'Seguridad', color: '#f59e0b' }, // Amber
            ]
        }
    ];

    return (
        <aside className={`sidebar fixed inset-y-0 left-0 z-50 w-72 bg-surface/80 dark:bg-gray-900/90 backdrop-blur-xl border-r border-subtle dark:border-gray-800 transform transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0 ${isOpen ? 'translate-x-0' : '-translate-x-full'}`}>
            <div className="flex items-center justify-between h-48 px-6 border-b border-subtle dark:border-gray-800">
                <div className="w-full flex justify-center">
                    <div className="flex-shrink-0 w-32 h-32 logo-container rounded-full overflow-hidden shadow-2xl border-4 border-primary/30 bg-white animate-logo-premium">
                        <img
                            src="/logo_smit.jpg"
                            alt="Logo SMIT"
                            className="w-full h-full object-contain rounded-full scale-110"
                            onError={handleLogoError}
                        />
                        <div className="logo-shimmer-overlay"></div>
                    </div>
                </div>
                <button
                    className="lg:hidden p-2 text-muted hover:text-primary transition-colors absolute right-4"
                    onClick={toggleSidebar}
                >
                    ✕
                </button>
            </div>


            <nav className="flex-1 overflow-y-auto px-4 py-6 space-y-8 custom-scrollbar">
                {menuGroups.map((group, gIndex) => {
                    const filteredItems = group.items.filter(item => {
                        if (!item.roles) return true;
                        return item.roles.includes(userRole);
                    });

                    if (filteredItems.length === 0) return null;

                    return (
                        <div key={gIndex} className="space-y-2">
                            <h4 className="px-4 text-[10px] font-bold text-muted dark:text-gray-500 uppercase tracking-[0.2em]">
                                {group.title}
                            </h4>
                            <div className="space-y-1">
                                {filteredItems.map((item) => {
                                    const isActive = location.pathname === item.path;
                                    return (
                                        <Link
                                            key={item.path}
                                            to={item.path}
                                            className={`flex items-center gap-3 px-4 py-2.5 rounded-2xl transition-all duration-300 group ${isActive
                                                ? 'bg-gradient-to-r from-primary to-primary/80 text-white shadow-lg shadow-primary/25 translate-x-1'
                                                : 'text-main/80 dark:text-gray-300 hover:bg-gray-100/50 dark:hover:bg-gray-800/50 hover:translate-x-1'
                                                }`}
                                        >
                                            <span
                                                className={`p-2 rounded-xl transition-all duration-300 flex items-center justify-center ${isActive
                                                    ? 'bg-white/20 text-white shadow-none ring-1 ring-white/30'
                                                    : 'bg-white dark:bg-gray-800 shadow-sm border border-gray-100 dark:border-gray-700 group-hover:scale-110 group-hover:shadow-md'
                                                    }`}
                                                style={!isActive ? { color: item.color } : {}}
                                            >
                                                {item.icon}
                                            </span>
                                            <span className={`text-[13px] font-bold tracking-tight transition-colors ${isActive ? 'text-white font-extrabold' : 'group-hover:text-primary'}`}>
                                                {item.label}
                                            </span>
                                            {isActive && (
                                                <div className="ml-auto w-1.5 h-1.5 rounded-full bg-white shadow-[0_0_8px_white]"></div>
                                            )}
                                        </Link>
                                    );
                                })}
                            </div>
                        </div>
                    );
                })}
            </nav>

            <div className="p-4 mt-auto">
                <div className="flex items-center gap-3 p-4 bg-gray-50 dark:bg-gray-800/50 rounded-2xl border border-gray-100 dark:border-gray-700/50">
                    <div className="w-10 h-10 bg-primary/20 flex items-center justify-center rounded-xl text-primary font-bold">
                        {user?.username?.charAt(0).toUpperCase()}
                    </div>
                    <div className="overflow-hidden">
                        <p className="text-sm font-bold text-main dark:text-white truncate">
                            {user?.username}
                        </p>
                        <p className="text-[10px] text-muted dark:text-gray-500 font-bold uppercase truncate">
                            {userRole}
                        </p>
                    </div>
                </div>
            </div>
        </aside>
    );

};

export default Sidebar;
