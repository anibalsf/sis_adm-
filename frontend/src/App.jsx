import React, { useState, lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ToastProvider } from './context/ToastContext';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import ErrorBoundary from './components/ErrorBoundary';
import SkeletonLoader from './components/SkeletonLoader';
import ChatbotWidget from './components/ChatbotWidget';
import MobileBottomNav from './components/MobileBottomNav';
import './index.css';
import './App.css';

// Lazy load page components
const DashboardMejorado = lazy(() => import('./pages/DashboardMejorado'));
const Login = lazy(() => import('./pages/Login'));
const Register = lazy(() => import('./pages/Register'));
const ForgotPassword = lazy(() => import('./pages/ForgotPassword'));
const Afiliados = lazy(() => import('./pages/Afiliados'));
const Vehiculos = lazy(() => import('./pages/Vehiculos'));
const Directorio = lazy(() => import('./pages/Directorio'));
const HojasRuta = lazy(() => import('./pages/HojasRuta'));
const PrintHojaRuta = lazy(() => import('./pages/PrintHojaRuta'));
const VerificarHoja = lazy(() => import('./pages/VerificarHoja'));
const PagosYEgresos = lazy(() => import('./pages/PagosY_Egresos'));
const ArqueoCaja = lazy(() => import('./pages/ArqueoCaja'));
const Balance = lazy(() => import('./pages/Balance'));
const Reportes = lazy(() => import('./pages/Reportes'));
const ReciboPago = lazy(() => import('./pages/ReciboPago'));
const Reservas = lazy(() => import('./pages/Reservas'));
const SancionesAsistencia = lazy(() => import('./pages/SancionesAsistencia'));
const Usuarios = lazy(() => import('./pages/Usuarios'));
const Rutas = lazy(() => import('./pages/Rutas'));
const AsignacionLaPaz = lazy(() => import('./pages/AsignacionLaPaz'));
const Bitacora = lazy(() => import('./pages/Bitacora'));
const ChangePassword = lazy(() => import('./pages/ChangePassword'));
const MiPerfil = lazy(() => import('./pages/MiPerfil'));
const ReportesAutomaticos = lazy(() => import('./pages/ReportesAutomaticos'));
const PizarraPublica = lazy(() => import('./pages/PizarraPublica'));
const VoucherReserva = lazy(() => import('./pages/VoucherReserva'));
const LibroActas = lazy(() => import('./pages/LibroActas'));
const Kiosco = lazy(() => import('./pages/Kiosco'));
const Encomiendas = lazy(() => import('./pages/Encomiendas'));
const WhatsAppAdmin = lazy(() => import('./pages/WhatsAppAdmin'));

const PageLoader = () => (
    <div style={{ padding: '2rem' }}>
        <SkeletonLoader type="card" count={3} height="200px" />
    </div>
);

function MainLayout() {
    const { user, isAuthenticated, loading } = useAuth();

    const [isSidebarOpen, setIsSidebarOpen] = useState(false);

    const toggleSidebar = () => setIsSidebarOpen(!isSidebarOpen);

    if (loading) {
        return <div className="loading-screen">Cargando sistema...</div>;
    }

    if (!isAuthenticated) {
        return <Navigate to="/login" replace />;
    }

    return (
        <div className="app-layout">
            <Sidebar isOpen={isSidebarOpen} toggleSidebar={toggleSidebar} />
            {isSidebarOpen && (
                <div
                    className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40 lg:hidden"
                    onClick={toggleSidebar}
                ></div>
            )}
            <div className="main-content">
                <Header toggleSidebar={toggleSidebar} />
                <div className="content">
                    <ErrorBoundary>
                        <Suspense fallback={<PageLoader />}>
                            <Routes>
                                <Route path="/" element={<Navigate to="/dashboard" replace />} />
                                <Route path="/dashboard" element={<DashboardMejorado />} />
                                <Route path="/afiliados" element={<Afiliados />} />
                                <Route path="/vehiculos" element={<Vehiculos />} />
                                <Route path="/directorio" element={<Directorio />} />
                                <Route path="/hojas-ruta" element={<HojasRuta />} />
                                <Route path="/asignacion-la-paz" element={<AsignacionLaPaz />} />
                                <Route path="/pagos-y-egresos" element={<PagosYEgresos />} />
                                <Route path="/arqueo-caja" element={<ArqueoCaja />} />
                                <Route path="/balance" element={<Balance />} />
                                <Route path="/reportes" element={<Reportes />} />
                                <Route path="/recibo/:type/:id" element={<ReciboPago />} />
                                <Route path="/reservas" element={<Reservas />} />
                                <Route path="/sanciones-asistencia" element={<SancionesAsistencia />} />
                                <Route path="/usuarios" element={<Usuarios />} />
                                <Route path="/rutas" element={<Rutas />} />
                                <Route path="/bitacora" element={<Bitacora />} />
                                <Route path="/change-password" element={<ChangePassword />} />
                                <Route path="/mi-perfil" element={<MiPerfil />} />
                                <Route path="/reportes-automaticos" element={<ReportesAutomaticos />} />
                                <Route path="/libro-actas" element={<LibroActas />} />
                                <Route path="/encomiendas" element={<Encomiendas />} />
                                <Route path="/whatsapp" element={<WhatsAppAdmin />} />
                            </Routes>
                        </Suspense>
                    </ErrorBoundary>
                </div>
            </div>
            <ChatbotWidget />
            {user?.role === 'Afiliado' && <MobileBottomNav />}
        </div>
    );
}

function App() {
    return (
        <BrowserRouter>
            <ToastProvider>
                <AuthProvider>
                    <Suspense fallback={<PageLoader />}>
                        <Routes>
                            <Route path="/login" element={<Login />} />
                            <Route path="/register" element={<Register />} />
                            <Route path="/forgot-password" element={<ForgotPassword />} />
                            <Route path="/hojas-ruta/print" element={<PrintHojaRuta />} />
                            <Route path="/verificar-hoja/:id" element={<VerificarHoja />} />
                            <Route path="/pizarra" element={<PizarraPublica />} />
                            <Route path="/kiosco" element={<Kiosco />} />
                            <Route path="/voucher/:id" element={<VoucherReserva />} />
                            <Route path="/*" element={<MainLayout />} />
                        </Routes>
                    </Suspense>
                </AuthProvider>
            </ToastProvider>
        </BrowserRouter>
    );
}

export default App;
