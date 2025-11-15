# AI-Based Attendance System

## 🚀 Quick Start

### Install & Run (Windows)
```bash
cd attendance_system
python -m venv venv
venv\Scripts\activate
pip install -r ../requirements.txt
python manage.py migrate
python manage.py populate_data
python manage.py runserver
```

Visit: **http://localhost:8000**

### Install & Run (Mac/Linux)
```bash
bash ../quickstart.sh
```

## 📋 Demo Credentials

| Role | Email | Password |
|------|-------|----------|
| **Admin** | admin@attendance.com | Admin@123 |
| **Teacher** | teacher@attendance.com | Teacher@123 |

## ✨ Features

✅ Facial recognition with anti-spoofing  
✅ Voice notifications  
✅ Role-based access control (Admin, Teacher, Student)  
✅ Attendance tracking & reporting  
✅ Student management  
✅ Comprehensive analytics  
✅ Secure authentication  

## 🏗️ Architecture

- **Backend**: Django 4.2 + DRF
- **AI/ML**: OpenCV, face_recognition, dlib
- **Voice**: pyttsx3
- **Database**: SQLite (default) / MySQL
- **Frontend**: Bootstrap 5 + Modern CSS

## 📁 Project Structure

```
attendance_system/
├── apps/
│   ├── authentication/  → User auth & RBAC
│   ├── student/        → Student & courses
│   ├── attendance/      → Attendance tracking
│   └── ai_core/        → Facial recognition
├── config/              → Django settings
├── templates/           → HTML pages
├── static/              → CSS, JS
└── manage.py
```

## 🔧 Configuration

Edit `.env` file:
```bash
DEBUG=True
DB_ENGINE=django.db.backends.sqlite3
AI_CONFIDENCE_THRESHOLD=0.6
ATTENDANCE_LATE_MINUTES=5
```

## 📚 API Endpoints

**Authentication**
- `POST /api/auth/register/` - Register
- `POST /api/auth/login/` - Login
- `POST /api/auth/logout/` - Logout

**Attendance**
- `POST /api/attendance/sessions/` - Create session
- `POST /api/attendance/mark/` - Mark attendance
- `GET /api/attendance/reports/` - Get reports

**AI Operations**
- `POST /api/ai/face-recognize/` - Recognize face
- `POST /api/ai/face-register/` - Register face

## 🎯 Next Steps

1. Run the quickstart script
2. Login with demo credentials
3. Explore Admin Panel at `/admin/`
4. Create attendance sessions
5. Test face recognition

## 🛡️ Security

- Custom user model with email auth
- Password hashing & validation
- RBAC permission classes
- Login audit logs
- SQL injection prevention

---

**Made with ❤️ | 2025**
