#!/usr/bin/env bash
set -euo pipefail

# Migrates data from the repository SQLite DB (tourist_routes/db.sqlite3)
# into PostgreSQL (running via docker-compose).
#
# Requirements: Docker + Docker Compose v2.
#
# Usage:
#   bash scripts/migrate_sqlite_to_postgres.sh

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

FIXTURE_PATH="${ROOT_DIR}/scripts/sqlite_dump.json"

echo "[1/3] Exporting data from SQLite -> ${FIXTURE_PATH}"

# We use a one-off container that points Django to SQLite.
docker compose run --rm \
  -v "${ROOT_DIR}/tourist_routes/db.sqlite3:/app/tourist_routes/db.sqlite3:ro" \
  -e DB_ENGINE=django.db.backends.sqlite3 \
  -e USE_POSTGRES=False \
  web \
  python manage.py dumpdata \
    --natural-foreign --natural-primary \
    --exclude contenttypes --exclude auth.permission \
    --indent 2 \
  > "$FIXTURE_PATH"

echo "[2/3] Applying migrations on PostgreSQL"
docker compose run --rm web python manage.py migrate --noinput

echo "[3/3] Importing data into PostgreSQL from fixture"
docker compose run --rm web python manage.py loaddata /app/scripts/sqlite_dump.json

echo "✓ Done. PostgreSQL is now filled with data from SQLite."
