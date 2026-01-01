#!/bin/bash

# Start script for Django with WebSocket support (Daphne ASGI server)

echo "======================================"
echo "Starting Django with WebSocket Support"
echo "======================================"
echo ""

# Check if Redis is running
echo "[1/3] Checking Redis..."
if ! redis-cli ping > /dev/null 2>&1; then
    echo "⚠️  Redis is not running!"
    echo "Starting Redis in background..."
    redis-server --daemonize yes
    sleep 2
    if redis-cli ping > /dev/null 2>&1; then
        echo "✓ Redis started successfully"
    else
        echo "✗ Failed to start Redis"
        echo "Please start Redis manually: redis-server"
        exit 1
    fi
else
    echo "✓ Redis is running"
fi

# Navigate to Django project
cd "$(dirname "$0")/attendance_system"

# Set Django settings module
export DJANGO_SETTINGS_MODULE=config.settings.development

# Check if virtual environment is activated
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo ""
    echo "⚠️  Warning: No virtual environment detected"
    echo "It's recommended to activate your venv first"
    echo ""
fi

# Start Daphne ASGI server
echo ""
echo "[2/3] Starting Daphne ASGI server..."
echo "Server will be available at: http://0.0.0.0:8000"
echo "WebSocket endpoint: ws://0.0.0.0:8000/ws/camera/{camera_id}/"
echo ""
echo "Press Ctrl+C to stop the server"
echo "======================================"
echo ""

daphne -b 0.0.0.0 -p 8000 config.asgi:application
