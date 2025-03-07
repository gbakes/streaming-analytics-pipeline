#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE USER $DEBEZIUM_USER WITH PASSWORD '$DEBEZIUM_PASSWORD' REPLICATION;
    GRANT ALL PRIVILEGES ON DATABASE $POSTGRES_DB TO $DEBEZIUM_USER;
    GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO $DEBEZIUM_USER;
    GRANT USAGE ON SCHEMA public TO $DEBEZIUM_USER;
EOSQL
