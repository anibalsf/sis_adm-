# Plan: Reporte "Estado de Cuentas" — quiénes cancelaron vs. deudores con monto por cobrar

## Decisiones tomadas con el usuario
- **Ubicación**: pestaña **Estado de Cuentas** (`ReporteDeudas.jsx`) del módulo Reportes.
- **Criterio "canceló"**: estado global → afiliado activo **sin deuda** (cero cuotas y cero sanciones pendientes).
- **Monto por cobrar**: cuotas + sanciones (`deuda_total` de `reportes_auto/morosidad.py`).

## Estado actual (lo que ya existe)
- `reportes_auto/morosidad.py:40` `_deuda_queryset()` → anota deuda por afiliado; `Q_deuda()` filtra solo deudores. **No existe el queryset complementario (sin deuda).**
- `reportes/views.py:219` `AfiliadosMorososView` → solo devuelve `morosos` (+ `deuda_total_sistema`), paginado.
- `reportes/views.py:282` `AfiliadosMorososPDFView` → solo deudores, con loop N+1 y una sola tabla que se desborda de la página con >25 filas.
- `frontend/src/pages/ReporteDeudas.jsx` → solo tabla de deudores; ya tiene 2 KPIs y gráfico torta "Al Día / Con Deuda" (usa `totalAfiliados - morosos`).
- `frontend/src/services/api.js:86` `getAfiliadosMorosos(params)` → ya pasa parámetros arbitrarios (**no requiere cambios**).
- Consumidores adicionales del endpoint: `DashboardMejorado.jsx:181` y `ChatbotWidget.jsx:208` (ambos `{page_size: 5}`) → los cambios deben ser **aditivos**.

---

## 1. Backend — `reportes_auto/morosidad.py`

1. Nueva función `al_dia_queryset(periodo_limite=None)`:
   - `activos = Afiliado.objects.filter(estado='activo', is_active=True)`
   - `.exclude(id__in=_deuda_queryset(periodo_limite=periodo_limite).values('id'))`
   - Anotar `ultimo_pago` con la misma subquery que usa `_deuda_queryset` (L80-84 / L97).
   - Ordenar por `apellidos`, `nombres`.
2. Nueva función `contar_al_dia(periodo_limite=None)` → `.count()` (para el resumen, sin materializar filas).
3. Ampliar `resumen_morosidad()` (L160) con claves nuevas (aditivas): `total_activos`, `sin_deuda` (`total_activos - con_deuda`), `porcentaje_al_dia`.
4. Nuevo `CAMPOS_AL_DIA` + `serializar_filas_al_dia(filas, hoy)` → `{afiliado_id, nombre_completo, ci, telefono, ultimo_pago, dias_desde_ultimo_pago}` (reutiliza el patrón de `serializar_filas`, L121).

## 2. Backend — `reportes/views.py::AfiliadosMorososView` (L219-279)

1. Nuevo query param **`lista`** = `deudores` (default) | `cancelaron`.
2. Soporte **`meses=0`** (o `todos`) → `periodo_limite=None` = **toda la deuda pendiente**.
   - Ojo: el clamp actual `max(1, min(int(...), 36))` (L234) obliga a reestructurar para permitir `0`.
   - `meses` no enviado o con valor N → mantiene la ventana actual (retrocompatible con Dashboard/Chatbot).
3. Agregar al response (aditivo):
   ```json
   "resumen": {
     "total_activos": n,
     "total_deudores": n,
     "total_cancelaron": n,
     "porcentaje_al_dia": n,
     "monto_por_cobrar": float
   }
   ```
4. `lista=deudores` → respuesta actual + `resumen`.
   `lista=cancelaron` → pagina `al_dia_queryset()` y responde `cancelaron: [...]` con su propia paginación (`count`, `total_pages`, `current_page`) + `resumen`.

## 3. Backend — `AfiliadosMorososPDFView` (L282-366)

1. Reemplazar el loop N+1 por `_deuda_queryset()` / `al_dia_queryset()` (misma lógica que la vista, ya no diverge).
2. Dos secciones: **"DEUDORES — MONTO POR COBRAR"** (con fila TOTAL) y **"AFILIADOS QUE CANCELARON (AL DÍA)"**.
3. Cortes de página (`showPage`) cuando la tabla supere las ~22 filas (corrige el desbordamiento actual).
4. Encabezado con resumen: total deudores, total al día, monto por cobrar.

## 4. Frontend — `frontend/src/pages/ReporteDeudas.jsx`

1. Estado nuevo `lista` (`'deudores' | 'cancelaron'`) + sub-pestañas reusando las clases globales existentes `tabs-container` / `tab-button` (definidas en `ReportesFinancieros.css:183-210`, ya importado por el archivo):
   - `❌ Deudores (N)` · `✅ Que Cancelaron (N)`.
2. KPIs (fila de 4 tarjetas + torta existente):
   - **Monto por Cobrar** (Bs., rojo) · **Deudores** (N) · **Que Cancelaron** (N) · **% Al Día**.
   - El gráfico torta pasa a usar `resumen.total_deudores` / `resumen.total_cancelaron` (más preciso que `totalAfiliados - morosos`).
3. Tabla **Deudores** (la actual, conserva columnas, badge de nivel, botón QR 📱) + fila de pie **"TOTAL POR COBRAR: Bs. X"**.
4. Tabla **Que Cancelaron** (nueva): Afiliado (nombre + teléfono), Carnet (CI), Último Pago, Estado (badge verde "Al día"); buscador por nombre/CI y paginación propia (mismo componente de paginación existente).
5. Llamadas: `api.getAfiliadosMorosos({ page, page_size: 20, lista, meses: 0 })`; al cambiar de sub-pestaña, resetear `page` a 1.
6. Sin cambios en `api.js`.

## 5. Estilos — `ReportesFinancieros.css`
- Agregar solo lo mínimo: `.deudas-subtabs` (si se necesita espaciado distinto al de las tabs principales) y `.badge-al-dia` (verde). Reusar `metrics-grid`, `metric-card`, `table-container`, `vehiculos-table`, `pagination` tal cual.

## 6. Tests — `reportes/tests.py` (pytest + pytest-django, fixtures en `conftest.py`)

- `test_al_dia_queryset_excluye_afiliados_con_deuda` (cuota pendiente y sanción pendiente).
- `test_resumen_morosidad_incluye_sin_deuda`.
- `test_vista_lista_cancelaron` (autenticado: `?lista=cancelaron&meses=0` → `resumen.total_cancelaron` + `cancelaron`).
- `test_meses_cero_sin_limite_de_periodo` (cuota del mes en curso sí cuenta como deuda).
- `test_vista_sigue_devolviendo_morosos_por_defecto` (retrocompatibilidad con Dashboard/Chatbot).

## 7. Verificación

- `python -m pytest reportes/tests.py -q` (config en `pyproject.toml` + `conftest.py`).
- `python manage.py check` para validar imports/urls.
- Frontend: `npm run lint` (o `npx eslint src/pages/ReporteDeudas.jsx`) y `npm run build` en `frontend/`.
- Manual: pestaña Reportes → Estado de Cuentas → verificar ambas sub-pestañas, paginación, KPIs, PDF y botón QR.

## Fuera de alcance (se puede hacer después)
- Unificar el Dashboard/Chatbot para que usen `meses=0` (hoy seguirán con la ventana de 3 meses).
- Exportar Excel del estado de cuentas (hoy solo PDF).
- Pestaña "Por Categoría" ya cubre el análisis por período/tipo de pago; no se toca.
