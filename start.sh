#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Force unbuffered Python output to ensure logs appear immediately
export PYTHONUNBUFFERED=1

# Apply database migrations
echo "Running migrations..."
python manage.py migrate --noinput

# Create superuser if configured (non-blocking)
echo "Checking for superuser creation..."
python create_superuser.py 2>/dev/null || true

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

# Sync role permissions for all users (non-blocking)
echo "Syncing role permissions..."
python manage.py sync_roles 2>/dev/null || true

# Start Gunicorn with proper configuration
echo "Starting Gunicorn..."
gunicorn ai_club.wsgi:application --bind 0.0.0.0:$PORT --workers 4 --worker-class sync --timeout 60
