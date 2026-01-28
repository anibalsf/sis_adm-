# Frontend - Sistema Sindicato Taipiplaya

Aplicación React moderna para el sistema de gestión del Sindicato Mixto de Transporte Integración Taipiplaya.

## 🚀 Características

- ✅ **Autenticación** - Sistema de login con tokens
- ✅ **Dashboard** - Estadísticas y visualización de datos
- ✅ **Navegación intuitiva** - Sidebar con todos los módulos
- ✅ **Diseño responsive** - Funciona en desktop y móvil
- ✅ **Conexión API** - Integrado con Django REST Framework
- ✅ **Diseño moderno** - UI/UX profesional

## 📋 Requisitos Previos

- Node.js 18.0 o superior
- npm o yarn
- Backend Django corriendo en http://localhost:8000

## 🛠️ Instalación

```bash
# Ya instalado automáticamente con npm install
# Si necesitas reinstalar:
npm install
```

## 🚀 Ejecutar en Desarrollo

```bash
npm run dev
```

La aplicación estará disponible en: **http://localhost:5173/**

## 🏗️ Estructura del Proyecto

```
frontend/
├── src/
│   ├── components/        # Componentes reutilizables
│   │   ├── Sidebar.jsx    # Navegación lateral
│   │   ├── Sidebar.css
│   │   ├── Header.jsx     # Encabezado
│   │   └── Header.css
│   ├── pages/             # Páginas de la aplicación
│   │   ├── Dashboard.jsx  # Dashboard principal
│   │   ├── Dashboard.css
│   │   ├── Login.jsx      # Página de login
│   │   └── Login.css
│   ├── services/          # Servicios y APIs
│   │   └── api.js         # Cliente API REST
│   ├── context/           # Contexts de React
│   │   └── AuthContext.jsx  # Contexto de autenticación
│   ├── App.jsx            # Componente principal
│   ├── App.css
│   ├── main.jsx           # Entry point
│   └── index.css          # Estilos globales
├── public/
├── package.json
└── vite.config.js
```

## 🔐 Uso

### 1. Iniciar Sesión

1. Abre http://localhost:5173/
2. Ingresa tus credenciales (crear usuario con `python manage.py createsuperuser` en el backend)
3. Click en "Iniciar Sesión"

### 2. Navegar en el Sistema

- **Dashboard**: Vista general con estadísticas
- **Afiliados**: Gestión de miembros
- **Vehículos**: Control de flota
- **Rutas**: Administración de rutas
- **Hojas de Ruta**: Registro de viajes
- **Y más...**

## 🎨 Personalización

### Colores

Los colores principales se definen en `src/index.css`:

```css
:root {
  --primary: #4a9d9c;
  --primary-dark: #3a7d7c;
  --secondary: #e1f5f4;
  /* ... */
}
```

### Configuración de API

En `src/services/api.js` puedes cambiar la URL del backend:

```javascript
const API_URL = 'http://localhost:8000/api';
```

## 📦 Build para Producción

```bash
npm run build
```

Los archivos optimizados estarán en `dist/`

## 🧪 Scripts Disponibles

```bash
npm run dev      # Servidor de desarrollo
npm run build    # Build para producción
npm run preview  # Preview del build
npm run lint     # Linter (si configurado)
```

## 🔗 Conexión con Backend

Asegúrate de que:

1. ✅ El backend Django esté corriendo en `http://localhost:8000`
2. ✅ CORS esté habilitado en Django (ya configurado)
3. ✅ Las rutas API coincidan con las esperadas

## 📱 Responsive

La aplicación está optimizada para:
- 💻 Desktop (> 768px) - Sidebar completo
- 📱 Tablet/Mobile (< 768px) - Sidebar compacto con solo íconos

## 🐛 Troubleshooting

### Error: "Network Error"
- Verifica que el backend esté corriendo
- Check la configuración de CORS en Django

### Error 401 Unauthorized
- Verifica tus credenciales
- El token puede haber expirado - intenta login nuevamente

### Cambios no se reflejan
- Limpia la caché del navegador (Ctrl+Shift+R)
- Verifica que el servidor de desarrollo esté corriendo

## 📄 Licencia

Desarrollado para el Sindicato Mixto de Transporte Integración Taipiplaya
