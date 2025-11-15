@echo off
REM Quick Start Script for AI-Based Attendance System (Windows)

echo ==================================================
echo AI-Based Attendance System - Quick Start (Windows)
echo ==================================================
echo.

REM Check Python
echo Checking Python installation...
python --version

REM Create virtual environment
echo Creating virtual environment...
python -m venv venv

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Navigate to project
cd attendance_system

REM Run migrations
echo Running database migrations...
python manage.py makemigrations
python manage.py migrate

REM Create superuser
echo.
echo Creating superuser account...
echo Please enter admin credentials:
python manage.py createsuperuser

REM Populate sample data
echo.
echo Populating sample data...
python manage.py populate_data

REM Collect static files
echo Collecting static files...
python manage.py collectstatic --noinput

REM Run development server
echo.
echo ==================================================
echo Setup Complete!
echo ==================================================
echo.
echo Starting development server...
echo.
echo Access the application at: http://localhost:8000
echo Admin panel at: http://localhost:8000/admin
echo.
echo Sample Credentials:
echo   Email: admin@attendance.com
echo   Password: Admin@123
echo.
echo Press Ctrl+C to stop the server
echo.

python manage.py runserver
