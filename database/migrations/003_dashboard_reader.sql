-- Read-only login for the analytics dashboard: it can SELECT, never change data.
-- Local development password; also run on first start of the Docker database.
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'dashboard_reader') THEN
        CREATE ROLE dashboard_reader LOGIN PASSWORD 'dashboard_reader';
    END IF;
END
$$;

GRANT CONNECT ON DATABASE smart_cart_recovery TO dashboard_reader;
GRANT USAGE ON SCHEMA public TO dashboard_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO dashboard_reader;

-- Tables created later are readable too.
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO dashboard_reader;
