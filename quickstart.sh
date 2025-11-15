#!/bin/bash
# Quick Start Script for AI-Based Attendance System

echo "=================================================="
echo "AI-Based Attendance System - Quick Start"
echo "=================================================="
echo ""

# Check Python
echo "✓ Checking Python installation..."
python --version

# Create virtual environment
echo "✓ Creating virtual environment..."
python -m venv venv

# Activate virtual environment
echo "✓ Activating virtual environment..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Install dependencies
echo "✓ Installing dependencies..."
pip install -r requirements.txt

# Navigate to project
cd attendance_system

# Run migrations
echo "✓ Running database migrations..."
python manage.py makemigrations
python manage.py migrate

# Create superuser
echo ""
echo "✓ Creating superuser account..."
echo "Please enter admin credentials:"
python manage.py createsuperuser

# Populate sample data
echo ""
echo "✓ Populating sample data..."
python manage.py populate_data

# Collect static files
echo "✓ Collecting static files..."
python manage.py collectstatic --noinput

# Run development server
echo ""
echo "=================================================="
echo "✅ Setup Complete!"
echo "=================================================="
echo ""
echo "Starting development server..."
echo ""
echo "Access the application at: http://localhost:8000"
echo "Admin panel at: http://localhost:8000/admin"
echo ""
echo "Sample Credentials:"
echo "  Email: admin@attendance.com"
echo "  Password: Admin@123"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python manage.py runserver
