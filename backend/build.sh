#!/usr/bin/env bash
# Render.com build script for EcoTrack Django backend
set -o errexit   # Exit on any error

echo "==> Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "==> Collecting static files..."
python manage.py collectstatic --noinput

echo "==> Running database migrations..."
python manage.py migrate --noinput

echo "==> Build complete!"
