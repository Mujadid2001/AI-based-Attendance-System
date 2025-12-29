#!/usr/bin/env bash
set -e

echo "Starting Production Deployment..."

export DJANGO_SETTINGS_MODULE=config.settings.production

# Check .env.production exists
if [ ! -f ".env.production" ]; then
    echo "ERROR: .env.production not found!"
    exit 1
fi

source .env.production

# Validate SECRET_KEY
if [ -z "$SECRET_KEY" ] || [ "$SECRET_KEY" = "GENERATE_A_SECURE_KEY_HERE_50_CHARS_MINIMUM" ]; then
    echo "ERROR: Configure SECRET_KEY in .env.production"
    exit 1
fi

cd attendance_system

if [ ! -f "venv/bin/activate" ]; then
    echo "ERROR: Run setup.sh first"
    exit 1
fi

source venv/bin/activate

python manage.py migrate --noinput
python manage.py collectstatic --noinput --clear

echo "Starting Gunicorn..."
exec gunicorn -c ../gunicorn_config.py config.wsgi:application
