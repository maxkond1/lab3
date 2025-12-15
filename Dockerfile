FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# System deps: psycopg (libpq), healthcheck tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    postgresql-client \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Project lives in /app, Django manage.py in /app/tourist_routes
WORKDIR /app/tourist_routes

COPY requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

# Copy sources
COPY . /app

# Runtime directories for collected static & uploaded media
RUN mkdir -p /app/tourist_routes/staticfiles /app/tourist_routes/media \
    && chmod -R 755 /app/tourist_routes/staticfiles /app/tourist_routes/media

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]

# NOTE: module path resolves because WORKDIR=/app/tourist_routes
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "tourist_routes.wsgi:application"]
