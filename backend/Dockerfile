# ============================================================
# EcoTrack Backend — Dockerfile (Cloud Run optimised)
# ============================================================
FROM python:3.12-slim AS base

# Prevent Python from writing .pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Cloud Run injects PORT — default to 8080
ENV PORT=8080

WORKDIR /app

# Install OS-level build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ---- dependency layer (cached separately for faster rebuilds) ----
FROM base AS deps
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ---- app layer ----
FROM deps AS app
COPY . .

# Collect static files (requires minimal env vars)
ENV DJANGO_SETTINGS_MODULE=config.settings.cloudrun
ENV DJANGO_SECRET_KEY=collect-static-placeholder-not-used-in-runtime
ENV DJANGO_ALLOWED_HOSTS=*
ENV DATABASE_URL=sqlite:///tmp/placeholder.db

RUN python manage.py collectstatic --noinput

# ---- runtime ----
# Cloud Run: listen on $PORT, use Gunicorn with threads for concurrency
CMD gunicorn config.wsgi:application \
    --bind 0.0.0.0:$PORT \
    --workers 2 \
    --threads 4 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
