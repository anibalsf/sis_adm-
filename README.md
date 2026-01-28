# Sistema Administrativo - Sindicato Mixto Integración Taipiplaya

Sistema integral de gestión administrativa para sindicatos de transporte, desarrollado con Django REST Framework y React.

## 🚀 Características Principales

- **Dashboard Premium**: Métricas en tiempo real con diseño glassmorphism
- **Gestión de Afiliados**: Control completo de socios y vehículos
- **Hojas de Ruta**: Asignación y seguimiento de viajes
- **Tesorería**: Gestión de pagos, egresos y balance financiero
- **Reportes Automáticos**: Envío programado de reportes por WhatsApp
- **Chatbot Asistente**: Consultas rápidas y navegación asistida
- **Exportaciones**: PDF y Excel de todos los módulos
- **Sistema de Sanciones**: Control de asistencia y multas

## 📋 Requisitos

### Backend
- Python 3.10+
- PostgreSQL 13+
- Redis (opcional, para caché)

### Frontend
- Node.js 18+
- npm o yarn

## 🔧 Instalación (Desarrollo)

### 1. Clonar Repositorio
```bash
git clone <repositorio>
cd sistema_administracion
```

### 2. Backend
```bash
# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales

# Migrar base de datos
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# Iniciar servidor
python manage.py runserver
```

### 3. Frontend
```bash
cd frontend

# Instalar dependencias
npm install

# Configurar variables de entorno
cp .env.example .env
# Editar .env con la URL del backend

# Iniciar servidor de desarrollo
npm run dev
```

## 🌐 Variables de Entorno

### Backend (.env)
```env
SECRET_KEY=tu_secret_key_aqui
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=taipiplaya_db
DB_USER=postgres
DB_PASSWORD=tu_password
DB_HOST=localhost
DB_PORT=5432

WHATSAPP_WEBHOOK_URL=https://api.whatsapp.com/send
ADMIN_PHONE_NUMBER=+59112345678
```

### Frontend (.env)
```env
VITE_API_URL=http://localhost:8000/api
```

## 📚 Estructura del Proyecto

```
sistema_administracion/
├── afiliados/          # Gestión de socios
├── vehiculos/          # Gestión de vehículos
├── hojasruta/          # Hojas de ruta y viajes
├── tesoreria/          # Pagos y egresos
├── reportes/           # Reportes y estadísticas
├── sanciones/          # Sistema de sanciones
├── whatsapp_notif/     # Notificaciones WhatsApp
├── frontend/           # Aplicación React
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   └── context/
│   └── public/
└── manage.py
```

## 🎨 Tecnologías Utilizadas

### Backend
- Django 4.2+
- Django REST Framework
- PostgreSQL
- APScheduler (reportes automáticos)
- ReportLab (generación PDF)
- openpyxl (exportación Excel)

### Frontend
- React 18
- React Router
- Chart.js (gráficos)
- Axios (HTTP client)
- Vite (build tool)

## 📖 Documentación Adicional

- [Guía de Deployment](deployment_guide.md)
- [Checklist de Producción](production_checklist.md)
- [Manual de Usuario](user_manual.md) *(próximamente)*

## 🔒 Seguridad

- Autenticación JWT
- Permisos basados en roles
- CORS configurado
- Rate limiting en APIs
- Validación de datos en backend y frontend

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📝 Licencia

Este proyecto es privado y de uso exclusivo para el Sindicato Mixto Integración Taipiplaya.

## 📞 Soporte

Para soporte técnico, contactar al administrador del sistema.

---

**Desarrollado con ❤️ para el Sindicato Mixto Integración Taipiplaya**
