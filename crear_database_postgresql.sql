-- Script SQL para crear la base de datos del Sistema Sindicato Taipiplaya
-- PostgreSQL 16

-- Crear la base de datos
CREATE DATABASE sindicato_taipiplaya 
    WITH 
    ENCODING 'UTF8' 
    LC_COLLATE='Spanish_Bolivia.1252' 
    LC_CTYPE='Spanish_Bolivia.1252'
    TEMPLATE=template0;

-- Crear el usuario de la aplicación
CREATE USER admin_sindicato WITH PASSWORD 'Taipiplaya2025!';

-- Dar privilegios al usuario
ALTER DATABASE sindicato_taipiplaya OWNER TO admin_sindicato;
GRANT ALL PRIVILEGES ON DATABASE sindicato_taipiplaya TO admin_sindicato;

-- Conectar a la base de datos creada
\c sindicato_taipiplaya

-- Dar permisos sobre el esquema público
GRANT ALL ON SCHEMA public TO admin_sindicato;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO admin_sindicato;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO admin_sindicato;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO admin_sindicato;

-- Configurar permisos por defecto para objetos futuros
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO admin_sindicato;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO admin_sindicato;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO admin_sindicato;

-- Mostrar mensaje de éxito
\echo '=========================================='
\echo 'Base de datos creada exitosamente!'
\echo '=========================================='
\echo 'Base de datos: sindicato_taipiplaya'
\echo 'Usuario: admin_sindicato'
\echo 'Password: Taipiplaya2025!'
\echo '=========================================='
