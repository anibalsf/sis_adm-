# Plan: Mejora del módulo RESERVAS

## Decisiones tomadas con el usuario
- **Frentes**: (1) Críticos de dinero y seguridad, (2) Gestión y estados de reservas.
- **Orden**: críticos primero, en fases verificables.
- **Listado de reservas**: pasa a exigir login (hoy es anónimo). Pizarra pública y voucher siguen públicos.
- **Fuera de alcance** (no seleccionados): pago QR funcional de punta a punta (Pago en tesorería, expiración de QR), notificaciones/limpieza general (3 WhatsApp duplicados, `.backup`, logger).

> Nota: la Fase 1 sí deja **alcanzable** la verificación del QR (hoy es código muerto), porque sin eso el "botón de verificar pago" no puede funcionar. El monto total del grupo y el registro del `Pago` en tesorería quedan pendientes (ver §Fuera de alcance).

---

# FASE 1 — Críticos (dinero y seguridad)

## 1.1 Modelo `reservas/models.py`
- Agregar `ESTADOS` choices: `('pendiente','confirmada','cancelada')` y `estado = CharField(choices=ESTADOS, default='pendiente', db_index=True)`.
  - `'pagada'` se consulta en `hojasruta/views.py:661` pero **nunca se asigna** → se elimina de ese filtro.
- Exportar `ESTADOS_ACTIVOS = ('pendiente','confirmada')` (única fuente de verdad para todos los filtros de cupos).
- Validación de dominio en el modelo (contrasta con `hojasruta/models.py:33` que ya llama `full_clean()`):
  - `clean()`: `cantidad >= 1`, `asiento >= 1` si está presente.
  - `Meta.constraints`: `CheckConstraint(Q(cantidad__gte=1))` (cierra el bypass de valores negativos incluso vía SQL directo).
  - `Meta.constraints`: `UniqueConstraint(fields=['ruta','fecha_viaje','asiento'], condition=Q(estado__in=ESTADOS_ACTIVOS), name='reserva_asiento_unico')` → no se puede tomar dos veces el mismo asiento activo; al cancelar se libera.
  - `Meta.indexes`: `(ruta, fecha_viaje, estado)` y `(fecha_viaje)` (hoy `fecha_viaje` no tiene `db_index`, modelos.py:11 → full-scan en cada agregado).
- **Migración con paso de datos previo**: antes de aplicar el unique, verificar duplicados activos en la BD (`reservas` con mismo ruta+fecha+asiento en estado activo) y resolverlos (anular los más antiguos dejando el más reciente). Comando de comprobación incluido en los tests/paso manual.

## 1.2 Serializer `reservas/serializers.py`
- `cantidad = serializers.IntegerField(min_value=1)` (hoy `fields` lo deja pasar con `-5`/`0` → resta cupos, `serializers.py:24-31`).
- `asiento = serializers.IntegerField(min_value=1, required=False, allow_null=True)`.
- `estado` → **read-only** (cierra el salto de pago `{"estado":"confirmada"}` en endpoint anónimo, `serializers.py:25`). Los clientes envían `estado:'pendiente'` (`Reservas.jsx:225`) → DRF lo ignora sin romper nada.
- Nuevo `ReservaPublicaSerializer` (sin `telefono` del cliente ni `afiliado_direccion`) para `public_retrieve`; conserva `afiliado_telefono` porque el voucher lo muestra (`VoucherReserva.jsx:112`).
- N+1 (`serializers.py:38-63`): los 3 `get_*` reutilizan **una sola** búsqueda de hoja (`_get_hoja(obj)`) con `.order_by('id')` y, en Fase 2, con `select_related` vía la nueva FK `hoja_ruta`.

## 1.3 Creación atómica `ReservaViewSet.create` (`reservas/views.py:57-102`)
Reescritura del flujo:
1. `serializer.is_valid(raise_exception=True)` **antes** de tocar la BD (valida cantidad/asiento).
2. `with transaction.atomic():`
   - `HojaRuta.objects.select_for_update().filter(ruta_id=..., fecha_salida=..., estado__in=['emitida','notificada','pagada']).order_by('id').first()`
     - `select_for_update` serializa las reservas del mismo viaje en Postgres (en SQLite es no-op; ahí protege el unique constraint).
     - **Corrige dos bugs**: `MultipleObjectsReturned` → 500 (`views.py:68-72`) y el desajuste `estado='emitida'` vs los 3 estados que muestra el listado (`views.py:71` vs `hojasruta/views.py:358`).
   - Recuento de cupos + validación de capacidad y de asientos dentro de la transacción.
   - `IntegrityError` del unique constraint → respuesta **409** con detalle "asiento ya reservado".
3. Soporte de **lote**: aceptar `asientos: [1,2,3]` en el POST (además del `asiento` simple, por compatibilidad). Se crea todo en la misma transacción → el frontend deja de hacer N POSTs concurrentes.
   - `views.py:64` `int()` sin capturar → hoy 500 con valores no numéricos; con `IntegerField` del serializer ya no llega.

## 1.4 Permisos (`reservas/views.py:30-55`)
- Reemplazar la clase interna por una única `ReservaPermission`:
  - **Público**: `create`, `generar_pago_qr`, `public_retrieve`, `generar_qr` (el voucher se abre desde el QR impreso, `VoucherReserva.jsx`).
  - **Lectura autenticada** (`IsAuthenticated`) para `list`/`retrieve` → cierra la fuga de teléfonos/direcciones de `GET /api/reservas/` (`views.py:49-50`, comentario "¿requiere login (o no?)").
  - **Escritura**: superuser o grupos `Secretaria`, `Directiva`, **`Sistemas`** (hoy falta, `views.py:53`; alineado con `sistema/permissions.py:16`).
  - `notificar` conserva restricción Secretaria.
- `public_retrieve` pasa a usar `ReservaPublicaSerializer` (mitiga el IDOR de IDs secuenciales al eliminar PII; el token UUID del QR queda como pendiente).

## 1.5 Verificación de QR alcanzable
- `sistema/urls.py`: registrar `QRTransactionViewSet` (prefijo `pagos-qr`) — hoy no está (registros en `urls.py:54-70`) → `webhook` (`pagos_qr/views.py:34-50`) y `check_status` son código muerto.
  - Restringir `http_method_names = ['get','post','head','options']` para no exponer PUT/DELETE sobre transacciones.
- `frontend/src/services/api.js`: nuevo `verificarPagoQr: (transactionId) => axios.post('/pagos-qr/webhook/', { transaction_id })`.
- `Reservas.jsx:73-95` `verificarPago`: hoy llama `api.getReserva(qrData.id)` donde `qrData.id` es el **ID de la QRTransaccion** (`reservas/views.py:384`) → consulta incorrecta. Pasa a usar `qrData.transaction_id` contra el nuevo endpoint.
- En producción esa llamada la haría el banco; aquí queda como disparador de la simulación (`pagos_qr/services.py:79-83`).

## 1.6 Frontend — un solo POST (`Reservas.jsx:214-228`, `PizarraPublica.jsx:102-115`)
- Reemplazar `Promise.all` de N POSTs por **un** `createReserva({ ..., asientos: selectedSeats })`.
- Manejo de errores: mostrar el `detail` y `cupos_disponibles` que devuelve el backend (hoy solo un `alert` genérico).

## 1.7 Tests — nuevo `reservas/tests.py` (pytest + `conftest.py`)
- `cantidad` 0 / -5 → 400.
- `asiento` fuera de capacidad o repetido → 400 / 409.
- `estado: 'confirmada'` en POST anónimo → se ignora, queda `pendiente`.
- `GET /api/reservas/` sin login → 401; con login → 200.
- `public_retrieve` no expone `telefono` ni `afiliado_direccion`.
- Capacidad agotada → 400 con `cupos_disponibles`.
- Lote de asientos en un POST → N filas creadas o ninguna (atomicidad).
- Ejecución: `python -m pytest reservas/tests.py -q` (el `testpaths = ["tests"]` de `pyproject.toml:35` no se toca en esta fase).

---

# FASE 2 — Gestión y estados

## 2.1 Máquina de estados y acciones
- Nuevas acciones en `ReservaViewSet` (permiso escrita: superuser/Secretaria/Directiva/Sistemas):
  - `POST /api/reservas/{pk}/confirmar/` → `pendiente → confirmada` (400 si no está en `pendiente`).
  - `POST /api/reservas/{pk}/cancelar/` → `* → cancelada`; registra `fecha_anulacion` y `motivo` (campos nuevos nullable, sin romper datos existentes).
  - `cancelada` queda fuera de `ESTADOS_ACTIVOS` → **libera cupo y asiento automáticamente**.
- `destroy` pasa a **soft-delete**: en vez de borrar, marca `cancelada` (conserva histórico y auditoría de `historial/signals.py`).

## 2.2 Unicidad de estados en todo el sistema
- Reemplazar los literales dispersos por `ESTADOS_ACTIVOS`:
  - `reservas/views.py:83` (create), `hojasruta/views.py:378`, `:387`, `:448`, `:661` (planilla, hoy incluye `'pagada'`), `:964`.
  - Deja de divergir la planilla vs el contador de cupos (#12).

## 2.3 `update` re-validado (`reservas/views.py` — hoy `ModelViewSet` sin control)
- `update`/`partial_update` envueltos en `transaction.atomic()`:
  - si cambia `cantidad` o `asiento` → re-cálculo de cupos con la misma lógica que `create`;
  - `ruta`/`fecha_viaje` no se pueden cambiar en reservas activas (la hoja asociada quedaría inválida).

## 2.4 FK a `HojaRuta` + fin del N+1
- `hoja_ruta = FK(HojaRuta, on_delete=PROTECT, null=True, blank=True, related_name='reservas')` (nullable → migración segura).
- Se setea en `create` con la hoja ya resuelta; migración de datos que rellena las filas existentes por `(ruta, fecha_viaje)`.
- `ReservaViewSet.queryset` → `.select_related('afiliado','ruta','hoja_ruta__vehiculo')`; los 3 `get_*` del serializer leen de `hoja_ruta` con fallback al join actual (3 queries → 0).

## 2.5 Monto único
- Campos nuevos: `monto_unitario` y `monto_total` (Decimal, nullable para filas antiguas).
- Helper único `reservas/services.py::precio_de(hoja, ruta)` → `hoja.precio` si existe, si no `ruta.tarifa_base`. Hoy hay **4 fuentes distintas**: `Reservas.jsx:191/653/874/885` (`tarifa_base || precio`), `PizarraPublica.jsx:487/341` (`precio`), `reservas/views.py:371` (`hoja.precio`), `reportes/views_advanced.py:115` (`tarifa_base`).
- El serializer expone `monto_total` → el frontend deja de calcular total.
- `generar_pago_qr` usa `reserva.monto_total` (no el precio unitario de `views.py:371`) y acepta `{"reservas": [ids]}` para cubrir el grupo → `monto = sum(monto_total)`.
- Campo `grupo_id = UUIDField(null=True, db_index=True)` en las reservas creadas en el mismo POST; `verify_payment` (`pagos_qr/services.py:93-97`) confirma **todas** las reservas del grupo, no solo la primera.

## 2.6 Frontend: pantalla de listado/gestión
- `Reservas.jsx` pasa a sub-pestañas (mismo patrón que `Reportes.jsx:14-45`, clases `tabs-container`/`tab-button`):
  - **🗓 Nueva Reserva** → el flujo actual de asientos.
  - **📋 Listado** → tabla con: cliente, teléfono, ruta, fecha, asiento, cantidad, estado (badge), conductor, monto, acciones.
- Acciones por fila: **Confirmar**, **Cancelar** (con motivo), **Ver voucher** (`/voucher/{id}`), **QR**.
- Filtros server-side nuevos en `ReservaViewSet`: `filterset_fields = ['estado','ruta','fecha_viaje']` (`DjangoFilterBackend`) + `?search=` y `?ordering=` que ya están declarados (`views.py:26-28`) pero nunca usados; paginación la estándar (`PAGE_SIZE=20`, `settings.py:234`).
- `frontend/src/services/api.js`: empiezan a usarse `getReservas`, `updateReserva`, `deleteReserva` (hoy muertos) + nuevos `confirmarReserva`, `cancelarReserva`.
- Nueva UI usa `useToast()` (`context/ToastContext.jsx:6`) en vez de `alert()`, siguiendo la convención de `Afiliados.jsx:11` / `Vehiculos.jsx:9`.

## 2.7 Tests adicionales
- Transiciones: confirmar/cancelar válidas e inválidas (400).
- `cancelada` libera cupo y asiento (vuelve a estar disponible).
- `destroy` no borra la fila (soft-delete).
- `update` que amplía `cantidad` más allá de la capacidad → 400.
- FK `hoja_ruta` seteada al crear y backfill de filas antiguas.
- `monto_total = precio * cantidad` y el QR del grupo suma el total.

---

## Verificación
1. `python manage.py makemigrations reservas` (con comprobación previa de duplicados de asiento).
2. `python manage.py migrate` y `python manage.py check`.
3. `python -m pytest reservas/tests.py -q`.
4. Frontend: `npm run lint` / `npx eslint src/pages/Reservas.jsx src/pages/PizarraPublica.jsx` y `npm run build`.
5. Manual: crear reserva con 3 asientos (1 POST), comprobar cupos, repetir asiento (409), listar sin login (401), voucher público, confirmar/cancelar desde el listado.

## Fuera de alcance / pendientes recomendados
- **Pago QR completo**: expiración real del QR (`pagos_qr/services.py:18` ignora `valid_hours`), creación del `Pago` en tesorería, reembolsos.
- **Notificaciones**: 3 WhatsApp contradictorios por reserva (`reservas/views.py:111` + `whatsapp_notif/signals.py:124/145`), `print()` en vez de logger (`views.py:115`), `enviar_confirmacion_whatsapp` que reporta éxito sin enviar (`settings.py:120`).
- **Limpieza**: código muerto (`notificar`, `generar_confirmacion_pdf`), `Reservas.jsx.backup`, `Reservas.css.backup`, `testpaths` de `pyproject.toml:35`, layouts de asientos hardcodeados (`Reservas.jsx:646/737-780`), `alert()` generales.
