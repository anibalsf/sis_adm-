"""
URL configuration for sistema project.
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import TemplateView
from rest_framework import routers
from afiliados.views import AfiliadoViewSet
from vehiculos.views import VehiculoViewSet
from hojasruta.views import HojaRutaViewSet
from cuotas.views import CuotaViewSet
from rutas.views import RutaViewSet
from tesoreria.views import EgresoViewSet, PagoViewSet, TipoPagoViewSet, ReciboView
from usuarios.views import RegisterView, LoginView, MeView, LogoutView, UserViewSet, CaptchaView
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from reuniones.views import ReunionViewSet
from asistencias.views import AsistenciaViewSet
from sanciones.views import SancionViewSet
from reservas.views import ReservaViewSet
# Reportes antiguos - comentados temporalmente
from reportes.views import (
    AfiliadosMorososView, 
    RutasRentablesView, 
    OcupacionHistoricaView, 
    BalanceView,
    FinanzasView,
    ReportesGraficosView,
    TransaccionesView,
    ReportesOperativosView,
    AfiliadosMorososPDFView,
    TransaccionesCSVView,
    TransaccionesPDFView,
    ReportesOperativosCSVView,
    ReportesOperativosPDFView
)
from reportes.views_advanced import (
    RentabilidadRutasView,
    KPIsEjecutivosView,
    TendenciasMensualesView
)
from historial.views import HistorialView, BitacoraView
from usuarios.views import ChangePasswordView
from sistema.scheduler_views import SchedulerViewSet
from directorio.views import MiembroDirectorioViewSet
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from sistema.health import health_check

router = routers.DefaultRouter()
router.register(r'afiliados', AfiliadoViewSet)
router.register(r'vehiculos', VehiculoViewSet)
router.register(r'hojas-ruta', HojaRutaViewSet)
router.register(r'cuotas', CuotaViewSet)
router.register(r'reuniones', ReunionViewSet)
router.register(r'asistencias', AsistenciaViewSet)
router.register(r'sanciones', SancionViewSet)
router.register(r'rutas', RutaViewSet)
router.register(r'reservas', ReservaViewSet)
router.register(r'directorio', MiembroDirectorioViewSet)
router.register(r'egresos', EgresoViewSet)
router.register(r'pagos', PagoViewSet)
router.register(r'tipos-pago', TipoPagoViewSet)
router.register(r'users', UserViewSet)

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # API Endpoints
    path('api/', include(router.urls)),
    path('api/web/', include('web_publica.urls')),  # Web Publica (Multimedia, etc)
    path('api/whatsapp/', include('whatsapp_notif.urls')),  # WhatsApp notifications
    path('api/mantenimiento/', include('mantenimiento.urls')),  # Vehicle Maintenance
    path('api/reportes-auto/', include('reportes_auto.urls')),  # Reportes Automáticos
    path('api/dashboard', ReportesOperativosView.as_view()), # Usamos Operativos como dashboard base
    # path('dashboard', DashboardHTMLView.as_view()),  # Comentado
    path('api/historial', HistorialView.as_view()),
    path('api/bitacora', BitacoraView.as_view()),
    
    # Recibos
    path('api/pagos/<int:pk>/recibo/', ReciboView.as_view(), name='pago-recibo'),

    # Reportes Antiguos - Comentados temporalmente
    # path('api/reportes/hojas-ruta.csv', HojaRutaCSVView.as_view()),
    # path('api/reportes/hojas-ruta.pdf', HojaRutaPDFView.as_view()),
    # path('api/reportes/finanzas', FinanzasView.as_view()),
    # path('api/reportes/cuotas.csv', CuotaCSVView.as_view()),
    # path('api/reportes/sanciones.csv', SancionCSVView.as_view()),
    path('api/reportes/operativos/pdf', ReportesOperativosPDFView.as_view()),
    path('api/reportes/operativos/csv', ReportesOperativosCSVView.as_view()),
    path('api/reportes/transacciones/pdf', TransaccionesPDFView.as_view()),
    path('api/reportes/transacciones/csv', TransaccionesCSVView.as_view()),
    
    # Nuevos Reportes Avanzados
    path('api/reportes/rentabilidad-rutas', RentabilidadRutasView.as_view()),
    path('api/reportes/kpis-ejecutivos', KPIsEjecutivosView.as_view()),
    path('api/reportes/tendencias-mensuales', TendenciasMensualesView.as_view()),
    
    # Balance Financiero
    path('api/reportes/balance', BalanceView.as_view()),
    path('api/reportes/finanzas', FinanzasView.as_view()),
    
    # Reportes Gráficos y Transacciones
    path('api/reportes/graficos', ReportesGraficosView.as_view()),
    path('api/reportes/transacciones', TransaccionesView.as_view()),
    path('api/reportes/operativos', ReportesOperativosView.as_view()),
    
    # Nuevos Reportes Analíticos
    path('api/reportes/afiliados-morosos/', AfiliadosMorososView.as_view()),
    path('api/reportes/rutas-rentables/', RutasRentablesView.as_view()),
    path('api/reportes/ocupacion-historica/', OcupacionHistoricaView.as_view()),
    path('api/reportes/afiliados-morosos/pdf/', AfiliadosMorososPDFView.as_view()),
    
    # Autenticación
    path('api/auth/register', RegisterView.as_view()),
    path('api/auth/login', LoginView.as_view()),
    path('api/auth/captcha', CaptchaView.as_view()),
    path('api/auth/me', MeView.as_view()),
    path('api/auth/logout', LogoutView.as_view()),
    path('api/auth/change-password', ChangePasswordView.as_view()),
    
    # JWT endpoints
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    # Scheduler management (admin only)
    path('api/scheduler/jobs/', SchedulerViewSet.as_view({'get': 'jobs'}), name='scheduler-jobs'),
    path('api/scheduler/test-pagos/', SchedulerViewSet.as_view({'post': 'test_pagos'}), name='scheduler-test-pagos'),
    path('api/scheduler/test-sanciones/', SchedulerViewSet.as_view({'post': 'test_sanciones'}), name='scheduler-test-sanciones'),
    path('api/scheduler/test-reporte-diario/', SchedulerViewSet.as_view({'post': 'test_reporte_diario'}), name='scheduler-test-reporte-diario'),
    path('api/scheduler/test-alerta-morosos/', SchedulerViewSet.as_view({'post': 'test_alerta_morosos'}), name='scheduler-test-alerta-morosos'),
    
    # Salud del sistema
    path('api/health/', health_check, name='health-check'),
    
    # Catch-all route para React SPA
    re_path(r'^.*$', TemplateView.as_view(template_name='index.html')),
]

from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
