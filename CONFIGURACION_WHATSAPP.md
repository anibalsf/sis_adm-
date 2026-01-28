# 📱 Guía de Configuración de WhatsApp

## 📋 **Resumen**

Este módulo permite enviar notificaciones automáticas de WhatsApp para:
- ✅ Confirmaciones de pago
- 📅 Recordatorios de turno
- ⚠️ Notificaciones de sanciones
- 🎫 Confirmaciones de reserva
- 📣 Recordatorios de reunión
- 💳 Recordatorios de deuda

---

## 🚀 **Instalación**

### 1. Instalar dependencias

```bash
pip install -r requirements.txt
```

Esto instalará `twilio` y otras dependencias necesarias.

### 2. Crear migraciones y migrar

```bash
python manage.py makemigrations whatsapp_notif
python manage.py migrate
```

### 3. Inicializar plantillas

```bash
python crear_plantillas_whatsapp.py
```

---

## ⚙️ **Configuración**

### Opción 1: Twilio WhatsApp (Recomendada) ⭐

#### Paso 1: Crear cuenta Twilio

1. Regístrate en [https://www.twilio.com/](https://www.twilio.com/)
2. Verifica tu cuenta
3. Obtén tu **Account SID** y **Auth Token**

#### Paso 2: Configurar WhatsApp Sandbox (Desarrollo)

1. En Twilio Console, ve a: **Messaging** > **Try it out** > **Send a WhatsApp message**
2. Sigue las instrucciones para conectar tu WhatsApp personal
3. Envía el código de activación que te indican (ej: `join <código>`)
4. Obtén el número: `whatsapp:+14155238886` (sandbox)

#### Paso 3: Configurar variables de entorno

Edita tu archivo `.env` y agrega:

```bash
# WhatsApp via Twilio
TWILIO_ACCOUNT_SID=ACXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
```

**¿Dónde encontrar estos datos?**
- Account SID y Auth Token: [Twilio Console](https://console.twilio.com/)
- WhatsApp From: El que obtuviste en el sandbox

#### Paso 4: Activar en Django Admin

1. Iniciar sesión en `/admin/`
2. Ir a **WhatsApp Notif** > **Configuración WhatsApp**
3. Configurar:
   - **Proveedor:** Twilio
   - **Habilitado:** ✅ Marcar
   - **Límite diario:** 1000 (o el que necesites)
4. Guardar

#### Paso 5: Probar conexión

**Opción A: Desde Django Admin**
1. Ve a `/admin/whatsapp_notif/whatsappconfig/`
2. Verás un botón: **"Test Connection"**

**Opción B: Desde API**
```bash
POST /api/whatsapp/config/test_connection/
Body: {
  "test_phone": "+59176543210"
}
```

**Opción C: Desde Python Shell**
```python
python manage.py shell

from whatsapp_notif.services import whatsapp_service

whatsapp_service.send_message(
    phone="+59176543210",
    message="Mensaje de prueba ✅",
    message_type="general",
    recipient_name="Test"
)
```

---

### Opción 2: WhatsApp Business API (Producción)

Para producción necesitas:
1. **WhatsApp Business Account** aprobada por Meta
2. **Phone Number verificado** para WhatsApp Business
3. Configurar plantillas aprobadas por WhatsApp

**Proceso:**
1. Solicitar acceso: [Meta Business Suite](https://business.facebook.com/)
2. Verificar tu negocio
3. Obtener credenciales API
4. Configurar en `.env`:

```bash
WHATSAPP_BUSINESS_API_KEY=your_key_here
WHATSAPP_BUSINESS_PHONE_ID=your_phone_id
```

---

## 📝 **Uso**

### Envío Automático (Recomendado)

El sistema envía mensajes automáticamente cuando:
- Se registra un pago → `payment_confirmation`
- Se aplica una sanción → `sanction_notice`
- Se crea una reserva → `reservation_confirmation`

**Configurado en:** `whatsapp_notif/signals.py`

### Envío Manual (vía API)

#### Enviar mensaje simple

```bash
POST /api/whatsapp/messages/send_manual/
Content-Type: application/json

{
  "phone": "+59176543210",
  "message": "Hola, este es un mensaje de prueba",
  "recipient_name": "Juan Pérez",
  "message_type": "general"
}
```

#### Enviar usando plantilla

```bash
POST /api/whatsapp/messages/send_from_template/
Content-Type: application/json

{
  "template_name": "payment_confirmation",
  "phone": "+59176543210",
  "context": {
    "nombre": "Juan Pérez",
    "monto": "150.00",
    "tipo": "Cuota Mensual",
    "fecha": "19/12/2024",
    "recibo": "00123"
  },
  "recipient_name": "Juan Pérez"
}
```

### Envío Manual (vía Python)

```python
from whatsapp_notif.services import whatsapp_service

# Opción 1: Mensaje directo
whatsapp_service.send_message(
    phone="+59176543210",
    message="Tu mensaje aquí",
    message_type="general",
    recipient_name="Juan Pérez"
)

# Opción 2: Usando plantilla
whatsapp_service.send_payment_confirmation(
    phone="+59176543210",
    recipient_name="Juan Pérez",
    amount=150.00,
    payment_type="Cuota Mensual",
    payment_id=123
)
```

---

## 🎨 **Plantillas Disponibles**

### 1. `payment_confirmation`
Variables: `{nombre}`, `{monto}`, `{tipo}`, `{fecha}`, `{recibo}`

### 2. `shift_reminder`
Variables: `{nombre}`, `{fecha}`, `{ruta}`, `{hora}`

### 3. `sanction_notice`
Variables: `{nombre}`, `{tipo}`, `{monto}`, `{fecha}`

### 4. `reservation_confirmation`
Variables: `{nombre}`, `{codigo}`, `{ruta}`, `{fecha}`, `{hora}`, `{asiento}`

### 5. `meeting_reminder`
Variables: `{nombre}`, `{tipo}`, `{fecha}`, `{hora}`, `{lugar}`, `{monto_sancion}`, `{agenda}`

### 6. `debt_reminder`
Variables: `{nombre}`, `{monto}`, `{concepto}`, `{dias_mora}`

---

## 📊 **Monitoreo**

### Ver mensajes enviados

**Django Admin:**
`/admin/whatsapp_notif/whatsappmessage/`

**API:**
```bash
GET /api/whatsapp/messages/
GET /api/whatsapp/messages/?status=sent
GET /api/whatsapp/messages/?message_type=payment_confirmation
```

### Estadísticas

```bash
GET /api/whatsapp/messages/stats/
```

Respuesta:
```json
{
  "total": 150,
  "by_status": {
    "sent": 120,
    "delivered": 100,
    "failed": 5
  },
  "by_type": {
    "payment_confirmation": 80,
    "shift_reminder": 40,
    "sanction_notice": 30
  }
}
```

---

## 🔒 **Seguridad y Límites**

### Límites de Twilio (Sandbox)
- **Mensajes por día:** ~100 (gratis durante prueba)
- **Solo números verificados:** Deben unirse al sandbox primero

### Límites de producción
- Configurar en Django Admin: **Límite diario de mensajes**
- Sistema respetará este límite automáticamente

### Privacidad
- Todos los mensajes se loguean en BD
- Solo usuarios autenticados pueden ver logs
- Números de teléfono no se exponen en frontend

---

## 💰 **Costos**

### Twilio Pricing (aprox.)
- **WhatsApp salientes:** ~$0.005 USD por mensaje
- **Estimado mensual (1000 msg):** ~$5 USD

### Alternativa Gratuita
Usar **Baileys** (requiere WhatsApp Web conectado)
- Gratuito pero menos estable
- No recomendado para producción

---

## ❓ **Troubleshooting**

### Error: "Twilio credentials not configured"
✅ Verifica que `.env` tenga las 3 variables configuradas

### Error: "Unable to create record: Permission denied"
✅ Tu número no está en el sandbox. Envía `join <código>` primero

### Mensaje no llega
1. Verificar que el número esté en formato internacional: `+591XXXXXXXX`
2. Revisar logs en `/admin/whatsapp_notif/whatsappmessage/`
3. Ver el campo `error_message` del mensaje fallido

### "Daily limit exceeded"
✅ Aumentar límite en Django Admin o esperar al día siguiente

---

## 🚀 **Siguientes Pasos**

1. ✅ Configurar Twilio
2. ✅ Probar con mensaje de prueba
3. ✅ Personalizar plantillas según tus necesidades
4. ✅ Activar envíos automáticos
5. ✅ Monitorear en Django Admin

---

## 📞 **Soporte**

Para más ayuda:
- Documentación Twilio: [https://www.twilio.com/docs/whatsapp](https://www.twilio.com/docs/whatsapp)
- Código fuente: `/whatsapp_notif/`
