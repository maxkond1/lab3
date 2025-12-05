-- Initialize PostgreSQL database
-- This script runs automatically when the PostgreSQL container starts

-- Create database user if not exists (handled by docker-compose environment variables)
-- Create necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Set default encoding and locale
SET TIMEZONE = 'UTC';

-- Create any additional schemas if needed
-- CREATE SCHEMA IF NOT EXISTS public;

-- Grant privileges
-- ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO postgres;
-- ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO postgres;

-- Log initialization
SELECT now() as initialization_timestamp;
