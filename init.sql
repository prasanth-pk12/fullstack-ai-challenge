-- Initialize the Task Manager database
-- This script runs automatically when the PostgreSQL container starts

-- Create database (if not exists via environment variables)
SELECT 'CREATE DATABASE taskmanager' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'taskmanager');

-- Connect to the taskmanager database
\c taskmanager;

-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Grant privileges to the user
GRANT ALL PRIVILEGES ON DATABASE taskmanager TO taskuser;
GRANT ALL PRIVILEGES ON SCHEMA public TO taskuser;

-- Set default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO taskuser;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO taskuser;

-- Log successful initialization
\echo 'Database initialization completed successfully!'