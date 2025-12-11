# AI-Based Attendance System - Backend API

A Django REST API for an intelligent attendance tracking system using facial recognition and voice notifications. **Backend only** - frontend to be implemented separately in React.

## 🎯 Features

- 🔐 **Token Authentication** - Secure REST API with token-based auth
- 👤 **Facial Recognition** - Advanced face detection and recognition using deep learning
- 🌐 **WebSocket Support** - Real-time face recognition via WebSockets
- 🎤 **Voice Notifications** - Audio feedback during attendance marking
- 📊 **Attendance Management** - Session-based tracking with comprehensive API
- 🛡️ **Role-Based Access Control** - Admin, Teacher, Student permissions
- 📈 **REST API** - Full CRUD operations for all resources
- 📦 **Media Handling** - Face image uploads and storage

## 🏗️ Architecture

**Backend Stack:**
- Django 4.2.7
- Django REST Framework 3.14.0
- Django Channels 4.0.0 (WebSocket)
- Face Recognition (dlib-based)
- OpenCV for image processing
- Redis (for production WebSocket)

**Frontend:** Implement separately in React/Next.js/Vue

## 📚 Documentation

See **[API_DOCUMENTATION.md](API_DOCUMENTATION.md)** for complete API reference including:
- All REST endpoints
- WebSocket API
- Authentication methods
- Request/response formats
- Example integrations

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip and virtualenv
- Redis (for production WebSocket support)

### Installation

```bash
# Navigate to project directory
cd attendance_system

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # On Windows
source venv/bin/activate  # On Mac/Linux

# Install dependencies
pip install -r ../requirements.txt

# Set up environment variables
cp ../.env.development.example .env
# Edit .env with your settings

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# (Optional) Load sample data
python manage.py populate_data

# Start development server
python manage.py runserver
```

### With WebSocket Support (Channels)

```bash
# Install and start Redis (for production)
# Windows: Download from https://github.com/microsoftarchive/redis/releases
# Linux: sudo apt-get install redis-server
# Mac: brew install redis

# Run with Daphne (ASGI server)
daphne -b 0.0.0.0 -p 8000 config.asgi:application
```

API will be available at `http://localhost:8000/api/`

## 🔑 API Access

### Get Authentication Token

```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "your-password"}'
```

Response:
```json
{
  "token": "your-auth-token-here",
  "user": {...}
}
```

### Use Token in Requests

```bash
curl http://localhost:8000/api/students/ \
  -H "Authorization: Token your-auth-token-here"
```

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@attendance.com | Admin@123 |
| Teacher | teacher@attendance.com | Teacher@123 |
| Student | (Check admin panel) | (Check admin panel) |

## API Endpoints

### Authentication
- `POST /api/auth/register/` - Register new user
- `POST /api/auth/login/` - User login
- `POST /api/auth/logout/` - User logout
- `GET /api/auth/profile/` - Get user profile

### Student Management
- `GET /api/students/` - List students
- `POST /api/students/` - Create student
- `GET /api/courses/` - List courses
- `POST /api/face-register/` - Register face

### Attendance
- `POST /api/attendance/sessions/` - Create session
- `POST /api/attendance/mark/` - Mark attendance
- `GET /api/attendance/reports/` - Get reports

### AI Operations
- `POST /api/ai/face-recognize/` - Recognize face and mark attendance
- `GET /api/ai/training-data/` - Get training data

## Project Structure

```
attendance_system/
├── apps/
│   ├── authentication/  # User authentication & RBAC
│   ├── student/         # Student & course management
│   ├── attendance/      # Attendance tracking
│   └── ai_core/         # Facial recognition & voice
├── config/              # Django configuration
├── templates/           # HTML templates
├── static/              # CSS, JS, images
└── manage.py            # Django management
```

## Technology Stack

- **Backend**: Django 4.2.7, Django REST Framework 3.14
- **AI/ML**: OpenCV, face_recognition, dlib
- **Voice**: pyttsx3
- **Database**: SQLite/MySQL
- **Frontend**: Bootstrap 5, HTML5, JavaScript

## Documentation

- **Settings Configuration**: Edit `.env` file for database and AI settings
- **Admin Interface**: Access at `/admin/` for user and data management
- **API Documentation**: Available at `/api/` endpoints

## Security Features

- Custom User model with email authentication
- Password hashing and validation
- RBAC permission classes
- Login audit logs
- CORS protection
- SQL injection prevention

## License

MIT License - 2025

## Support

For issues or questions, contact the development team.
