#!/usr/bin/env sh
set -e

# We expect Django project to be in /app/tourist_routes (see Dockerfile).
cd /app/tourist_routes

if [ "${DB_ENGINE}" = "django.db.backends.postgresql" ] || [ -n "${DB_HOST}" ]; then
  echo "Waiting for PostgreSQL (${DB_HOST:-db}:${DB_PORT:-5432})..."
  until pg_isready -h "${DB_HOST:-db}" -p "${DB_PORT:-5432}" -U "${DB_USER:-postgres}" >/dev/null 2>&1; do
    sleep 1
  done
  echo "PostgreSQL is ready"
fi

python manage.py migrate --noinput

# Collect static files into STATIC_ROOT (mapped to a volume in docker-compose)
python manage.py collectstatic --noinput

exec "$@"
