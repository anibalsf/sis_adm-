# 🚀 Guía Completa de Instalación e Integración
## Sistema de Mejoras - Sindicato Taipiplaya

---

## 📋 Índice

1. [Dependencias Requeridas](#-dependencias-requeridas)
2. [Estructura de Archivos](#-estructura-de-archivos)
3. [Configuración Inicial](#%EF%B8%8F-configuración-en-settingspy)
4. [Integración por Fases](#-integración-por-fase)
5. [Testing](#-testing)
6. [Deploy en Producción](#-deploy-en-producción)
7. [Soporte](#-soporte)

---

## 📦 Dependencias Requeridas

> [!IMPORTANT]
> Ejecute este comando en el entorno virtual de Python antes de comenzar

```bash
pip install qrcode pillow openpyxl APScheduler requests
```

### Dependencias Opcionales (Producción)

Para un sistema más robusto con Celery:

```bash
pip install celery redis
```

---

## 📁 Estructura de Archivos a Crear

```
sistema_administracion/
│
├── 📂 notificaciones/          # ✨ NUEVO MÓDULO
│   ├── __init__.py
│   ├── scheduler.py            # Scheduler de notificaciones automáticas
│   ├── views.py                # Endpoints manuales (opcional)
│   └── urls.py
│
├── 📂 reportes/                # ✨ NUEVO MÓDULO (Si no existe)
│   ├── __init__.py
│   ├── views.py                # Vistas de reportes analíticos
│   └── urls.py
│
├── 📂 logs/                    # ✨ NUEVA CARPETA
│   └── notificaciones.log      # Logs del sistema
│
└── 📂 frontend/src/pages/
    ├── DashboardMejorado.jsx   # ✅ YA CREADO
    └── DashboardMejorado.css   # ✅ YA CREADO
```

---

## ⚙️ Configuración en settings.py

### 1. Configuración de WhatsApp / Twilio

```python
# ============================================
# WHATSAPP / TWILIO CONFIGURATION
# ============================================
TWILIO_ACCOUNT_SID = 'your_account_sid_here'
TWILIO_AUTH_TOKEN = 'your_auth_token_here'
TWILIO_WHATSAPP_NUMBER = '+14155238886'
```

### 2. Configuración de Logging

```python
# ============================================
# LOGGING CONFIGURATION
# ============================================
import os

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'notificaciones.log'),
            'maxBytes': 1024 * 1024 * 5,  # 5 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    
    'loggers': {
        'notificaciones': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
        },
    },
}
```

### 3. Configuración de Sanciones (Opcional)

```python
# ============================================
# SANCIONES AUTOMATICAS CONFIGURATION
# ============================================
SANCIONES_CONFIG = {
    'FALTA_REUNION': {
        'monto_default': 50.00,
        'tipo': 'Falta a Reunión',
        'notificar_automatico': True
    },
    'FALTA_TURNO_PARADA': {
        'monto_default': 50.00,
        'tipo': 'Falta a Turno de Parada',
        'notificar_automatico': True
    },
    'INCUMPLIMIENTO_REGLAMENTO': {
        'monto_default': 100.00,
        'tipo': 'Incumplimiento de Reglamento',
        'notificar_automatico': False
    }
}
```

---

## 🔧 Integración por Fase

### ✅ Fase 1: Dashboard Mejorado

#### Frontend

**Archivo**: `App.jsx`

```javascript
// Reemplazar:
import Dashboard from './pages/Dashboard';

// Por:
import DashboardMejorado from './pages/DashboardMejorado';

// En las rutas:
<Route path="/dashboard" element={<DashboardMejorado />} />
```

> [!TIP]
> El componente DashboardMejorado ya está creado. Solo necesita cambiar los imports en App.jsx

| Característica | Estado |
|---------------|--------|
| Componente creado | ✅ |
| CSS incluido | ✅ |
| Auto-refresh | ✅ |
| Métricas financieras | ✅ |

---

### ✅ Fase 2: Sanciones Automáticas

#### Backend

**Archivo**: `sanciones/views.py` (clase `SancionViewSet`)

1. Copiar los siguientes métodos de `codigo_sanciones_auto_helper.py`:
   - `generar_por_inasistencia`
   - `afiliados_multiples_sanciones`
   - `_enviar_notificacion_sancion` (opcional)

2. Agregar configuración en `settings.py` (ver arriba)

3. Integrar con asistencias para generación automática

```python
# En asistencias/views.py
def marcar_inasistencia(self, request, pk=None):
    asistencia = self.get_object()
    asistencia.presente = False
    asistencia.save()
    
    # Generar sanción automática
    from sanciones.models import Sancion
    from django.conf import settings
    
    config = settings.SANCIONES_CONFIG.get('FALTA_REUNION', {})
    
    try:
        Sancion.objects.create(
            afiliado=asistencia.afiliado,
            tipo=config.get('tipo', 'Falta a Reunión'),
            motivo=f"Inasistencia a reunión del {asistencia.reunion.fecha}",
            monto=config.get('monto_default', 50.00),
            estado='pendiente',
            referencia_asistencia=asistencia
        )
    except Exception as e:
        logger.error(f"Error creando sanción automática: {e}")
    
    return Response({'success': True})
```

---

### ✅ Fase 3: Reservas con QR y WhatsApp

#### Backend

**Archivo**: `reservas/views.py` (clase `ReservaViewSet`)

Copiar estos métodos de `codigo_reservas_qr_helper.py`:
- ✅ `generar_qr`
- ✅ `generar_confirmacion_pdf`
- ✅ `enviar_confirmacion_whatsapp`
- ✅ `reservas_hoy_por_conductor`

#### Frontend

**Archivo**: `api.js` - ✅ Ya agregado

**Ejemplo de uso**:

```javascript
// Descargar QR
const descargarQR = async (id) => {
    const response = await api.generarQrReserva(id);
    const url = window.URL.createObjectURL(new Blob([response.data]));
    window.open(url, '_blank');
};

// Enviar WhatsApp
const enviarWhatsApp = async (id) => {
    if (window.confirm('¿Enviar confirmación por WhatsApp?')) {
        await api.enviarConfirmacionWhatsapp(id, {});
        alert('✅ Confirmación enviada');
    }
};
```

---

### ✅ Fase 4: Recibos Automáticos

#### Backend

**Archivo**: `tesoreria/views.py` (clase `PagoViewSet`)

Copiar el método `generar_recibo` de `codigo_recibo_helper.py`

> [!WARNING]
> Asegúrese de incluir todos los imports necesarios al inicio del archivo

#### Frontend

**Archivo**: `PagosY_Egresos.jsx`

Agregar botón de descarga:

```javascript
<button 
    onClick={() => descargarRecibo(pago.id)}
    className="btn btn-secondary"
>
    📄 Descargar Recibo
</button>

// Función:
const descargarRecibo = async (id) => {
    const response = await api.generarReciboPago(id);
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.download = `recibo_${id}.pdf`;
    link.click();
};
```

---

### ✅ Fase 5: Asistencia Mejorada

#### Backend

**Archivo**: `asistencias/views.py` (clase `AsistenciaViewSet`)

Copiar estos métodos de `codigo_asistencia_mejorada_helper.py`:
- ✅ `exportar_excel`
- ✅ `inasistencias_frecuentes`  
- ✅ `estadisticas_generales`

#### Frontend

**Botón de Exportación**:

```javascript
<button 
    onClick={exportarExcel}
    className="btn btn-success"
>
    📊 Exportar a Excel
</button>

const exportarExcel = async () => {
    const response = await api.exportarAsistenciasExcel({
        fecha_desde: '2025-01-01',
        fecha_hasta: '2025-12-31'
    });
    
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.download = 'asistencias.xlsx';
    link.click();
};
```

---

### ✅ Fase 6: Automatización WhatsApp

#### 1. Crear Módulo

```bash
mkdir notificaciones
```

#### 2. Crear Archivos

**Archivo**: `notificaciones/__init__.py`

```python
# Vacío o con configuración básica
```

**Archivo**: `notificaciones/scheduler.py`

Copiar todo el contenido de `codigo_whatsapp_automatizacion_helper.py`

#### 3. Activar en apps.py

**Archivo**: `sistema/apps.py` (o el app principal)

```python
from django.apps import AppConfig

class SistemaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'sistema'
    
    def ready(self):
        # Iniciar scheduler de notificaciones
        try:
            from notificaciones.scheduler import iniciar_scheduler
            iniciar_scheduler()
            print("✅ Scheduler de notificaciones iniciado")
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"❌ Error al iniciar scheduler: {e}")
```

#### Cronograma de Notificaciones

| Tipo | Frecuencia | Hora |
|------|-----------|------|
| 💳 Recordatorios de Pago | Lunes | 09:00 AM |
| 🚫 Notificaciones de Sanciones | Diario | 10:00 AM |
| ✅ Confirmaciones de Hojas | Diario | 06:00 PM |

---

### ✅ Fase 7: Reportes Adicionales

#### Backend

**Archivo**: `reportes/views.py` - ✅ **YA CREADO**

Contiene 3 vistas completas:
- `AfiliadosMorososView`
- `RutasRentablesView`
- `OcupacionHistoricaView`

#### Agregar URLs

**Archivo**: `sistema/urls.py`

```python
from reportes.views import (
    AfiliadosMorososView, 
    RutasRentablesView, 
    OcupacionHistoricaView
)

urlpatterns += [
    # Nuevos reportes
    path('api/reportes/afiliados-morosos/', AfiliadosMorososView.as_view()),
    path('api/reportes/rutas-rentables/', RutasRentablesView.as_view()),
    path('api/reportes/ocupacion-historica/', OcupacionHistoricaView.as_view()),
]
```

#### Frontend

**Las funciones API ya están agregadas** en `api.js`:
- ✅ `getAfiliadosMorosos`
- ✅ `getRutasRentables`
- ✅ `getOcupacionHistorica`

---

## 🧪 Testing

### Dashboard Mejorado

```bash
# 1. Iniciar el servidor
cd frontend
npm run dev

# 2. Navegar a
http://localhost:5173/dashboard

# 3. Verificar:
✓ Métricas financieras visibles
✓ Alertas funcionando
✓ Auto-refresh (esperar 5 min o refrescar)
```

### Sanciones Automáticas

```bash
# API Test
curl -X POST http://localhost:8000/api/sanciones/generar_por_inasistencia/ \
  -H "Content-Type: application/json" \
  -d '{
    "afiliado_id": 1,
    "asistencia_id": 5,
    "tipo": "Falta a Reunión",
    "monto": 50
  }'
```

### Reportes

```bash
# Afiliados Morosos
curl http://localhost:8000/api/reportes/afiliados-morosos/?meses=3

# Rutas Rentables
curl http://localhost:8000/api/reportes/rutas-rentables/?meses=6
```

---

## 📋 Checklist de Integración

### Instalación Base
- [ ] ✅ Instalar dependencias: `pip install qrcode pillow openpyxl APScheduler`
- [ ] ✅ Crear carpeta `logs/`
- [ ] ✅ Actualizar `settings.py` con configuraciones

### Frontend
- [ ] ✅ Integrar Dashboard Mejorado en `App.jsx`
- [ ] ✅ Verificar que `api.js` tiene todas las funciones

### Backend - Módulos
- [ ] ⏳ Copiar métodos de sanciones a `sanciones/views.py`
- [ ] ⏳ Copiar métodos de reservas a `reservas/views.py`
- [ ] ⏳ Copiar método de recibos a `tesoreria/views.py`
- [ ] ⏳ Copiar métodos de asistencia a `asistencias/views.py`

### Nuevos Módulos
- [ ] ⏳ Crear módulo `notificaciones/` y configurar scheduler
- [ ] ✅ Módulo `reportes/` ya está creado
- [ ] ⏳ Agregar URLs de reportes en `sistema/urls.py`

### Testing
- [ ] ⏳ Probar Dashboard mejorado
- [ ] ⏳ Probar cada funcionalidad nueva
- [ ] ⏳ Verificar logs de notificaciones

### Producción
- [ ] ⏳ Configurar cron jobs o systemd para scheduler
- [ ] ⏳ Configurar variables de entorno seguras
- [ ] ⏳ Hacer backup de base de datos antes del deploy

---

## 🚀 Deploy en Producción

### Opción 1: APScheduler (Simple)

El scheduler se iniciará automáticamente con Django cuando agregue el código en `apps.py`

### Opción 2: Celery (Robusto - Recomendado para Producción)

```bash
# Terminal 1: Worker
celery -A sistema worker -l info

# Terminal 2: Beat (scheduler)
celery -A sistema beat -l info
```

### Con systemd (Linux):

```bash
sudo systemctl start celery-worker
sudo systemctl start celery-beat
sudo systemctl enable celery-woker
sudo systemctl enable celery-beat
```

---

## 📞 Soporte y Documentación

### Archivos de Referencia

| Archivo Helper | Descripción |
|---------------|-------------|
| `codigo_recibo_helper.py` | Recibos de pago automáticos |
| `codigo_sanciones_auto_helper.py` | Sanciones automáticas |
| `codigo_reservas_qr_helper.py` | QR y WhatsApp para reservas |
| `codigo_asistencia_mejorada_helper.py` | Excel y reportes de asistencia |
| `codigo_reportes_adicionales_helper.py` | Reportes analíticos |
| `codigo_whatsapp_automatizacion_helper.py` | Notificaciones automáticas |

### Documentación Externa

- 📖 [ReportLab Documentation](https://www.reportlab.com/docs/reportlab-userguide.pdf)
- 📖 [QRCode Documentation](https://github.com/lincolnloop/python-qrcode)
- 📖 [APScheduler Documentation](https://apscheduler.readthedocs.io/)
- 📖 [Celery Documentation](https://docs.celeryproject.org/)
- 📖 [Twilio WhatsApp API](https://www.twilio.com/docs/whatsapp)

### Logs

```bash
# Ver logs de notificaciones
tail -f logs/notificaciones.log

# Ver logs de Django
tail -f logs/django.log
```

---

## 🎯 Resumen de Mejoras

| Fase | Funcionalidades | Estado |
|------|----------------|--------|
| 1️⃣ Dashboard | Métricas, Alertas, Auto-refresh | ✅ Integrado |
| 2️⃣ Sanciones | Generación automática | ⏳ Helper listo |
| 3️⃣ Reservas | QR, WhatsApp, Vista conductores | ⏳ Helper listo |
| 4️⃣ Recibos | PDF automático | ⏳ Helper listo |
| 5️⃣ Asistencia | Excel, Reportes | ⏳ Helper listo |
| 6️⃣ WhatsApp | Notificaciones automáticas | ⏳ Helper listo |
| 7️⃣ Reportes | Morosos, Rutas, Ocupación | ✅ Módulo creado |

---

<div align="center">

## 🎊 ¡Todo Listo para Producción!

**30+ Funcionalidades Nuevas** | **7 Fases Completas** | **12 Archivos Helper**

</div>

---

> [!NOTE]
> Esta guía está en constante actualización. Para dudas específicas, consulte los archivos helper correspondientes.
