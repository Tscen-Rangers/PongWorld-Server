CREATE DATABASE pong_world;
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'root') THEN
        CREATE USER root WITH PASSWORD 'password';
    END IF;
END $$;
GRANT ALL PRIVILEGES ON DATABASE pong_world TO root;