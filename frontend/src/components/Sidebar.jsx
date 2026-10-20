import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
    IconHome, IconUser, IconUsers, IconBus, IconLayout,
    IconMapPin, IconList, IconCalendar, IconCash,
    IconTrendingUp, IconBarChart, IconAlertTriangle,
    IconHistory, IconLock, IconShield, IconBook
} from './Icons';
import './Sidebar.css';

const Sidebar = ({ isOpen, toggleSidebar }) => {
    const location = useLocation();
    const { user } = useAuth();
    const userRole = user?.role || 'Afiliado';

    const menuGroups = [
        {
            title: 'PRINCIPAL',
            items: [
                { path: '/',          icon: <IconHome />,    label: 'Inicio',            color: '#10b981', bg: 'rgba(16,185,129,0.13)' },
                { path: '/mi-perfil', icon: <IconUser />,    label: 'Mi Perfil',         color: '#3b82f6', bg: 'rgba(59,130,246,0.13)' },
                { path: '/pizarra',   icon: <IconLayout />,  label: 'Pizarra de Salidas',color: '#10b981', bg: 'rgba(16,185,129,0.13)' },
                { path: '/kiosco',    icon: <IconLayout />,  label: 'Kiosco Digital',    color: '#f59e0b', bg: 'rgba(245,158,11,0.13)', roles: ['Directiva','Secretaria','Sistemas','Agente'] },
            ]
        },
        {
            title: 'OPERATIVO',
            items: [
                { path: '/afiliados',    icon: <IconUsers />,        label: 'Afiliados',          roles: ['Directiva','Secretaria','Sistemas'],            color: '#6366f1', bg: 'rgba(99,102,241,0.13)' },
                { path: '/vehiculos',    icon: <IconBus />,          label: 'Vehículos',          roles: ['Directiva','Secretaria','Sistemas'],            color: '#f43f5e', bg: 'rgba(244,63,94,0.13)' },
                { path: '/directorio',   icon: <IconLayout />,       label: 'Directorio',         roles: ['Directiva','Sistemas'],                        color: '#0ea5e9', bg: 'rgba(14,165,233,0.13)' },
                { path: '/rutas',        icon: <IconMapPin />,       label: 'Rutas',              roles: ['Directiva','Secretaria','Sistemas'],            color: '#8b5cf6', bg: 'rgba(139,92,246,0.13)' },
                { path: '/hojas-ruta',   icon: <IconList />,         label: 'Hojas de Ruta',      roles: ['Directiva','Secretaria','Sistemas','Agente'],  color: '#f59e0b', bg: 'rgba(245,158,11,0.13)' },
                { path: '/reservas',     icon: <IconCalendar />,     label: 'Reservas',           roles: ['Directiva','Secretaria','Sistemas','Agente'],  color: '#ec4899', bg: 'rgba(236,72,153,0.13)' },
            ]
        },
        {
            title: 'ADMINISTRACIÓN',
            items: [
                { path: '/pagos-y-egresos',      icon: <IconCash />,          label: 'Pagos y Egresos',       roles: ['Directiva','Secretaria','Sistemas'],  color: '#22c55e', bg: 'rgba(34,197,94,0.13)' },
                { path: '/arqueo-caja',          icon: <IconCash />,          label: 'Arqueo de Caja',        roles: ['Directiva','Secretaria','Sistemas'],  color: '#10b981', bg: 'rgba(16,185,129,0.13)' },
                { path: '/balance',              icon: <IconTrendingUp />,    label: 'Balance Financiero',    roles: ['Directiva','Sistemas'],               color: '#f97316', bg: 'rgba(249,115,22,0.13)' },
                { path: '/encomiendas',          icon: <IconList />,          label: 'Encomiendas',           roles: ['Directiva','Secretaria','Sistemas','Agente'], color: '#f59e0b', bg: 'rgba(245,158,11,0.13)' },
                { path: '/reportes',             icon: <IconBarChart />,      label: 'Reportes',              roles: ['Directiva','Secretaria','Sistemas'],  color: '#a855f7', bg: 'rgba(168,85,247,0.13)' },
                { path: '/reportes-automaticos', icon: <IconBarChart />,      label: 'Reportes Automáticos',  roles: ['Directiva','Sistemas'],               color: '#06b6d4', bg: 'rgba(6,182,212,0.13)' },
                { path: '/sanciones-asistencia', icon: <IconAlertTriangle />, label: 'Sanciones / Asistencia',roles: ['Directiva','Secretaria','Sistemas'],  color: '#ef4444', bg: 'rgba(239,68,68,0.13)' },
                { path: '/libro-actas',          icon: <IconBook />,          label: 'Libro de Actas',        roles: ['Directiva','Secretaria','Sistemas'],  color: '#8b5cf6', bg: 'rgba(139,92,246,0.13)' },
            ]
        },
        {
            title: 'COMUNICACIÓN',
            items: [
                { path: '/whatsapp', icon: <IconLayout />, label: 'WhatsApp', roles: ['Directiva','Secretaria','Sistemas'], color: '#25d366', bg: 'rgba(37,211,102,0.13)' },
            ]
        },
        {
            title: 'SISTEMA',
            items: [
                { path: '/usuarios',        icon: <IconUser />,    label: 'Gestión Usuarios', roles: ['Directiva','Sistemas'], color: '#6366f1', bg: 'rgba(99,102,241,0.13)' },
                { path: '/bitacora',        icon: <IconHistory />, label: 'Bitácora',         roles: ['Directiva','Sistemas'], color: '#8b5cf6', bg: 'rgba(139,92,246,0.13)' },
                { path: '/change-password', icon: <IconLock />,    label: 'Seguridad',                                        color: '#f59e0b', bg: 'rgba(245,158,11,0.13)' },
            ]
        }
    ];

    return (
        <aside className={`sb-root${isOpen ? ' sb-open' : ''}`}>

            {/* ── HEADER ── */}
            <div className="sb-header">
                <div className="sb-logo-wrap">
                    <div className="sb-logo-icon">
                        <IconShield />
                    </div>
                    <div className="sb-logo-text">
                        <span className="sb-logo-title">S.M.I.T.</span>
                        <span className="sb-logo-sub">Sistema Administrativo</span>
                    </div>
                </div>
                <button className="sb-close-btn" onClick={toggleSidebar}>✕</button>
            </div>

            {/* ── NAV ── */}
            <nav className="sb-nav">
                {menuGroups.map((group, gIndex) => {
                    const filteredItems = group.items.filter(item =>
                        !item.roles || item.roles.includes(userRole)
                    );
                    if (filteredItems.length === 0) return null;

                    return (
                        <div key={gIndex} className="sb-group">
                            <p className="sb-group-label">{group.title}</p>
                            {filteredItems.map((item) => {
                                const isActive = location.pathname === item.path;
                                return (
                                    <Link
                                        key={item.path}
                                        to={item.path}
                                        className={`sb-item${isActive ? ' sb-item--active' : ''}`}
                                        style={isActive
                                            ? {
                                                background: `linear-gradient(135deg, ${item.color}20 0%, ${item.color}0d 100%)`,
                                                borderColor: `${item.color}50`,
                                              }
                                            : {}
                                        }
                                    >
                                        {/* Ícono circular coloreado */}
                                        <span
                                            className="sb-item-icon"
                                            style={{
                                                background: isActive ? item.color : item.bg,
                                                color:      isActive ? '#fff'      : item.color,
                                                boxShadow:  isActive ? `0 4px 14px ${item.color}60` : 'none',
                                            }}
                                        >
                                            {item.icon}
                                        </span>

                                        {/* Texto */}
                                        <span
                                            className="sb-item-label"
                                            style={{ color: isActive ? item.color : undefined }}
                                        >
                                            {item.label}
                                        </span>

                                        {/* Punto indicador activo */}
                                        {isActive && (
                                            <span
                                                className="sb-item-dot"
                                                style={{
                                                    background: item.color,
                                                    boxShadow: `0 0 8px ${item.color}`,
                                                }}
                                            />
                                        )}
                                    </Link>
                                );
                            })}
                        </div>
                    );
                })}
            </nav>

            {/* ── FOOTER USUARIO ── */}
            <div className="sb-footer">
                <div className="sb-user">
                    <div className="sb-user-avatar">
                        {user?.username?.charAt(0).toUpperCase()}
                    </div>
                    <div className="sb-user-info">
                        <p className="sb-user-name">{user?.username}</p>
                        <p className="sb-user-role">{userRole}</p>
                    </div>
                    <span className="sb-user-status" />
                </div>
            </div>

        </aside>
    );
};

export default Sidebar;
