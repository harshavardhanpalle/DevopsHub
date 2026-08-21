#!/usr/bin/env bash
# Runs automatically on first Postgres container start (official postgres
# image executes every *.sh in /docker-entrypoint-initdb.d/). Creates one
# database per microservice so table ownership stays cleanly separated,
# per PROJECT_AUDIT.md / the assignment's database ownership rules.
set -e

for DB in userdb blogdb categorydb notificationdb; do
    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
        SELECT 'CREATE DATABASE $DB' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$DB')\gexec
EOSQL
done
