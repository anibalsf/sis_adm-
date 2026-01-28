import React from 'react';
import ReactDOM from 'react-dom/client';
import * as Sentry from "@sentry/react";
import App from './App.jsx';
import './index.css';
import { registerSW } from 'virtual:pwa-register';
import { ThemeProvider } from './context/ThemeContext.jsx';

// Solo inicializar Sentry si hay un DSN configurado
const SENTRY_DSN = ""; // El usuario puede configurar esto en su entorno

if (SENTRY_DSN) {
  Sentry.init({
    dsn: SENTRY_DSN,
    integrations: [
      Sentry.browserTracingIntegration(),
      Sentry.replayIntegration(),
    ],
    tracesSampleRate: 1.0,
    replaysSessionSampleRate: 0.1,
    replaysOnErrorSampleRate: 1.0,
  });
}

const updateSW = registerSW({
  onNeedRefresh() {
    // Podríamos usar un toast aquí en el futuro para una mejor UX
    // Por ahora, mantenemos el confirm pero con un mensaje más claro
    if (confirm('Hay una nueva versión del sistema disponible. ¿Deseas actualizar ahora para ver los cambios?')) {
      updateSW(true);
    }
  },
  onOfflineReady() {
    console.log('El sistema está listo para funcionar offline.');
  },
});

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <ThemeProvider>
      <App />
    </ThemeProvider>
  </React.StrictMode>,
);
