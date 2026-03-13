#!/bin/bash

set -e

echo "Starting Nepal Voting App..."

# Install packages
echo "Installing requirements..."
pip install --upgrade pip
pip install -r requirements.txt

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput || true

# Run migrations
echo "Running migrations..."
python manage.py migrate --noinput || true

# Start gunicorn with proper logging
echo "Starting gunicorn server..."
gunicorn \
  --workers 3 \
  --worker-class sync \
  --bind 0.0.0.0:8000 \
  --timeout 60 \
  --access-logfile - \
  --error-logfile - \
  nepal_voting.wsgi:application
