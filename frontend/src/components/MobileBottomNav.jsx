import React from 'react';
import { NavLink } from 'react-router-dom';
import { IconHome, IconUser, IconBus, IconCalendar, IconAlertTriangle } from './Icons';
import './MobileBottomNav.css';

const MobileBottomNav = () => {
  return (
    <nav className="mobile-bottom-nav">
      <NavLink to="/mi-perfil" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
        <IconUser />
        <span>Mi Perfil</span>
      </NavLink>
      <NavLink to="/pizarra" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
        <IconBus />
        <span>Pizarra</span>
      </NavLink>
      <NavLink to="/reservas" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
        <IconCalendar />
        <span>Reservas</span>
      </NavLink>
    </nav>
  );
};

export default MobileBottomNav;
