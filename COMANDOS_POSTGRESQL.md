# 🔧 COMANDOS ÚTILES DE POSTGRESQL

## 🎯 Acceso Rápido a PostgreSQL

### Abrir psql (Consola PostgreSQL)
```powershell
# Opción 1: Desde el menú de Windows
# Buscar "SQL Shell (psql)" y ejecutar

# Opción 2: Desde PowerShell
psql -U admin_sindicato -d sindicato_taipiplaya

# Opción 3: Como superusuario
psql -U postgres
```

---

## 📊 COMANDOS BÁSICOS EN psql

### Comandos de Información
```sql
-- Ver todas las bases de datos
\l

-- Conectar a una base de datos
\c sindicato_taipiplaya

-- Ver todas las tablas
\dt

-- Describir una tabla
\d afiliados_afiliado

-- Ver todos los índices
\di

-- Ver usuarios/roles
\du

-- Ver tamaño de las tablas
\dt+

-- Salir de psql
\q
```

---

## 🔍 CONSULTAS ÚTILES

### Estadísticas de Datos
```sql
-- Conectar a la base de datos
\c sindicato_taipiplaya

-- Contar afiliados
SELECT COUNT(*) as total_afiliados FROM afiliados_afiliado;

-- Contar afiliados por estado
SELECT estado, COUNT(*) as total 
FROM afiliados_afiliado 
GROUP BY estado;

-- Contar vehículos
SELECT COUNT(*) as total_vehiculos FROM vehiculos_vehiculo;

-- Contar hojas de ruta del mes actual
SELECT COUNT(*) as hojas_este_mes 
FROM hojasruta_hojaruta 
WHERE fecha >= date_trunc('month', CURRENT_DATE);

-- Ingresos del mes actual
SELECT SUM(monto) as ingresos_mes 
FROM cuotas_pago 
WHERE fecha >= date_trunc('month', CURRENT_DATE);
```

### Verificar Integridad
```sql
-- Ver tablas y cantidad de registros
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
    n_live_tup AS rows
FROM pg_stat_user_tables
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Ver índices y su uso
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan as index_scans,
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;
```

---

## 💾 BACKUP Y RESTORE

### Backup Manual
```powershell
# Backup completo (formato custom - comprimido)
pg_dump -U admin_sindicato -F c -b -v -f backup_manual.sql sindicato_taipiplaya

# Backup en formato SQL plano
pg_dump -U admin_sindicato -f backup_manual.sql sindicato_taipiplaya

# Backup solo de datos (sin estructura)
pg_dump -U admin_sindicato --data-only -f backup_data.sql sindicato_taipiplaya

# Backup solo de estructura (sin datos)
pg_dump -U admin_sindicato --schema-only -f backup_schema.sql sindicato_taipiplaya

# Backup de una tabla específica
pg_dump -U admin_sindicato -t afiliados_afiliado -f backup_afiliados.sql sindicato_taipiplaya
```

### Restore Manual
```powershell
# Restore desde formato custom
pg_restore -U admin_sindicato -d sindicato_taipiplaya -v backup_manual.sql

# Restore desde SQL plano
psql -U admin_sindicato -d sindicato_taipiplaya -f backup_manual.sql

# Restore creando nueva base de datos
createdb -U postgres nueva_db
pg_restore -U admin_sindicato -d nueva_db -v backup_manual.sql
```

### Backup Automático (Ya configurado)
```powershell
# Ejecutar script de backup manual
.\backup_postgresql.ps1

# El backup automático ya está en: backup_postgresql.ps1
# Para programarlo, revisar MIGRACION_POSTGRESQL.md
```

---

## 🔒 SEGURIDAD Y USUARIOS

### Gestión de Usuarios
```sql
-- Crear nuevo usuario
CREATE USER nuevo_usuario WITH PASSWORD 'password123';

-- Dar permisos de lectura
GRANT CONNECT ON DATABASE sindicato_taipiplaya TO nuevo_usuario;
GRANT USAGE ON SCHEMA public TO nuevo_usuario;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO nuevo_usuario;

-- Dar permisos completos
GRANT ALL PRIVILEGES ON DATABASE sindicato_taipiplaya TO nuevo_usuario;

-- Cambiar contraseña
ALTER USER admin_sindicato WITH PASSWORD 'nueva_contraseña';

-- Eliminar usuario
DROP USER nombre_usuario;

-- Ver permisos de un usuario
\du nombre_usuario
```

### Conexiones Activas
```sql
-- Ver conexiones activas
SELECT 
    pid,
    usename,
    application_name,
    client_addr,
    state,
    query_start
FROM pg_stat_activity
WHERE datname = 'sindicato_taipiplaya';

-- Terminar una conexión
SELECT pg_terminate_backend(pid) 
FROM pg_stat_activity 
WHERE datname = 'sindicato_taipiplaya' 
  AND pid <> pg_backend_pid();
```

---

## 🛠️ MANTENIMIENTO

### Optimización
```sql
-- Analizar y actualizar estadísticas
ANALYZE;

-- Analizar tabla específica
ANALYZE afiliados_afiliado;

-- Vacuum (limpiar espacio)
VACUUM;

-- Vacuum completo (más agresivo)
VACUUM FULL;

-- Reindexar base de datos
REINDEX DATABASE sindicato_taipiplaya;

-- Reindexar tabla específica
REINDEX TABLE afiliados_afiliado;
```

### Información del Sistema
```sql
-- Versión de PostgreSQL
SELECT version();

-- Tamaño de la base de datos
SELECT pg_size_pretty(pg_database_size('sindicato_taipiplaya'));

-- Tablas más grandes
SELECT 
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
LIMIT 10;

-- Configuración actual
SHOW ALL;

-- Ver configuración específica
SHOW max_connections;
SHOW shared_buffers;
SHOW work_mem;
```

---

## 🔍 BÚSQUEDA FULL-TEXT

### Configurar búsqueda en español
```sql
-- Crear índice de búsqueda full-text
CREATE INDEX idx_afiliados_fulltext ON afiliados_afiliado 
USING gin(to_tsvector('spanish', nombres || ' ' || apellidos));

-- Buscar afiliados (insensible a tildes y mayúsculas)
SELECT * FROM afiliados_afiliado
WHERE to_tsvector('spanish', nombres || ' ' || apellidos) @@ 
      to_tsquery('spanish', 'jose & perez');

-- Buscar con ranking
SELECT 
    nombres,
    apellidos,
    ts_rank(to_tsvector('spanish', nombres || ' ' || apellidos),
            to_tsquery('spanish', 'juan')) as rank
FROM afiliados_afiliado
WHERE to_tsvector('spanish', nombres || ' ' || apellidos) @@ 
      to_tsquery('spanish', 'juan')
ORDER BY rank DESC;
```

---

## 📈 PERFORMANCE MONITORING

### Queries Lentas
```sql
-- Habilitar logging de queries lentas
-- Editar postgresql.conf:
-- log_min_duration_statement = 1000  # Log queries > 1 segundo

-- Ver queries más costosas
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    max_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
```

### Cache Hit Ratio
```sql
-- Ratio de cache (debe ser > 99%)
SELECT 
    sum(heap_blks_read) as heap_read,
    sum(heap_blks_hit) as heap_hit,
    sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)) as ratio
FROM pg_statio_user_tables;
```

---

## 🚨 SOLUCIÓN DE PROBLEMAS

### Reiniciar PostgreSQL
```powershell
# Detener servicio
Stop-Service postgresql-x64-16

# Iniciar servicio
Start-Service postgresql-x64-16

# Reiniciar servicio
Restart-Service postgresql-x64-16

# Ver estado
Get-Service postgresql-x64-16
```

### Resetear Base de Datos
```sql
-- CUIDADO: Esto borra TODOS los datos

-- Conectar como postgres
\c postgres

-- Terminar conexiones
SELECT pg_terminate_backend(pid) 
FROM pg_stat_activity 
WHERE datname = 'sindicato_taipiplaya';

-- Borrar base de datos
DROP DATABASE sindicato_taipiplaya;

-- Recrear
CREATE DATABASE sindicato_taipiplaya 
    WITH 
    ENCODING 'UTF8' 
    OWNER admin_sindicato;
```

Luego ejecutar migraciones de Django:
```powershell
python manage.py migrate
python manage.py loaddata backup_data.json
```

---

## 📁 EXPORTAR/IMPORTAR DATOS

### Exportar a CSV
```sql
-- Exportar afiliados a CSV
\copy (SELECT * FROM afiliados_afiliado) TO 'C:/temp/afiliados.csv' CSV HEADER;

-- Exportar con query personalizada
\copy (SELECT nombres, apellidos, ci FROM afiliados_afiliado WHERE estado='activo') 
TO 'C:/temp/afiliados_activos.csv' CSV HEADER;
```

### Importar desde CSV
```sql
-- Importar datos
\copy afiliados_afiliado FROM 'C:/temp/afiliados.csv' CSV HEADER;
```

---

## 🔐 ARCHIVO .pgpass (No pedir contraseña)

Crear archivo: `C:\Users\Once\AppData\Roaming\postgresql\pgpass.conf`

Contenido:
```
localhost:5432:sindicato_taipiplaya:admin_sindicato:Taipiplaya2025!
```

Ahora los comandos `pg_dump` y `psql` no pedirán contraseña.

---

## 📚 RECURSOS

- Documentación oficial: https://www.postgresql.org/docs/
- pgAdmin 4 Guide: https://www.pgadmin.org/docs/
- PostgreSQL Tutorial: https://www.postgresqltutorial.com/

---

**Última actualización:** 12 de diciembre de 2025
