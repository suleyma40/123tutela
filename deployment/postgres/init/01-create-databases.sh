#!/bin/sh
set -eu

create_db() {
  db_name="$1"

  if [ -z "$db_name" ]; then
    return 0
  fi

  if psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname postgres -tAc "SELECT 1 FROM pg_database WHERE datname = '$db_name'" | grep -q 1; then
    echo "Database $db_name already exists"
    return 0
  fi

  echo "Creating database $db_name"
  psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname postgres -c "CREATE DATABASE \"$db_name\""
}

create_db "${APP_DB_NAME:-}"
create_db "${N8N_DB_NAME:-}"
