# 🎓 AI-Based Attendance System

Modern attendance management with AI-powered facial recognition. Complete separation of Django REST API backend and React TypeScript frontend.

## ✨ Features

- 👤 **AI Facial Recognition** - Automatic attendance via face detection
- 🔐 **JWT Authentication** - Secure token-based auth with email verification
- 👥 **Role-Based Access** - Admin, Teacher, Student permissions
- 📊 **Attendance Tracking** - Sessions, reports, manual/AI marking
- 🎤 **Voice Feedback** - Audio notifications for attendance
- 🌐 **Real-time Updates** - WebSocket support
- 📱 **Modern UI** - Responsive React frontend

## 🏗️ Tech Stack

**Backend:** Django 4.2.7 | DRF | JWT | dlib | face_recognition | OpenCV | Channels  
**Frontend:** React 18 | TypeScript | Vite | TailwindCSS | Axios | Zustand

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL (production only)
- Redis (production only)

### Development

```bash
# 1. Setup
chmod +x setup.sh start.sh
./setup.sh

# 2. Start servers
./start.sh
```

**Access:**
- Frontend: http://localhost:3000
- Backend: http://localhost:8000/api
- Admin: http://localhost:8000/admin

**Note:** Development uses SQLite and console email. Configure `.env.development` if needed.

### Production (Docker)

```bash
# 1. Configure environment
# Edit .env.production with your values

# 2. Start services
docker-compose up -d

# 3. Create superuser
docker-compose exec api python manage.py createsuperuser
```

### Production (Manual)

```bash
# 1. Configure environment
# Edit .env.production

# 2. Deploy
export DJANGO_SETTINGS_MODULE=config.settings.production
chmod +x start_production.sh
./start_production.sh
```

---

## � Project Structure

```
├── attendance_system/          # Django Backend
│   ├── apps/                   # Django apps
│   │   ├── ai_core/           # Face recognition
│   │   ├── attendance/        # Attendance management
│   │   ├── authentication/    # User auth & JWT
│   │   └── student/           # Student/Course management
│   ├── config/                # Settings & configuration
│   │   └── settings/          # Environment-based settings
│   └── manage.py
├── frontend/                  # React Frontend
│   ├── src/
│   │   ├── components/       # Reusable components
│   │   ├── pages/            # Page components
│   │   ├── services/         # API services
│   │   └── store/            # State management
│   └── package.json
├── .env.development          # Development config
├── .env.production           # Production config
├── docker-compose.yml        # Docker setup
└── requirements.txt          # Python dependencies
```

## 🔑 Environment Files

- **`.env.development`** - SQLite, console email, relaxed security
- **`.env.production`** - PostgreSQL, SMTP, strict security

Copy and customize as needed. The system auto-loads based on `DJANGO_SETTINGS_MODULE`.

# Install dependencies
npm install
```

### Step 4: Start Services

**Backend:**
```bash
cd attendance_system
source venv/bin/activate
python manage.py runserver 0.0.0.0:8000
```

**Frontend:**
```bash
cd frontend
npm run dev -- --host 0.0.0.0
```

---

## 🗂️ Project Structure

```
AI-based-Attendance-System/
├── attendance_system/          # Django Backend
│   ├── apps/
│   │   ├── authentication/    # User auth & JWT
│   │   ├── student/          # Students & courses
│   │   ├── attendance/       # Attendance tracking
│   │   └── ai_core/         # Face recognition AI
│   ├── config/              # Settings
│   ├── media/              # Uploaded images
│   └── manage.py
│
├── frontend/                  # React Frontend
│   ├── src/
│   │   ├── pages/           # UI pages
│   │   ├── services/        # API integration
│   │   └── components/      # Reusable components
│   └── package.json
│
├── setup.sh                  # Setup script
├── start.sh                  # Start script
└── requirements.txt          # Python dependencies
```

---

## 🔧 Configuration

### Backend (.env in root)
```env
DEBUG=True
SECRET_KEY=your-secret-key
DB_ENGINE=django.db.backends.sqlite3
DB_NAME=db.sqlite3
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
CORS_ALLOWED_ORIGINS=http://localhost:3000
```

### Frontend (frontend/.env)
```env
VITE_API_URL=http://localhost:8000/api
NODE_ENV=development
```

---

## 📱 Usage

### For Students
1. Register → Verify email → Login
2. Complete profile
3. Register face (Profile → Face Registration)
4. Enroll in courses
5. Attend classes

### For Teachers
1. Login
2. Create course
3. Add students
4. Create attendance session
5. Mark attendance (manual or AI camera)
6. View reports

### For Admins
1. Access admin panel: http://localhost:8000/admin
2. Manage users, courses, attendance
3. Configure system settings

---

## 🔌 API Endpoints

### Authentication
- `POST /api/auth/authentication/register/` - Register
- `POST /api/auth/authentication/login/` - Login
- `POST /api/auth/authentication/verify-email/` - Verify email
- `GET /api/auth/authentication/me/` - Current user

### Students & Courses
- `GET /api/students/profiles/` - List students
- `POST /api/students/profiles/` - Create student
- `GET /api/students/courses/` - List courses
- `POST /api/students/enrollments/` - Enroll

### Attendance
- `POST /api/attendance/sessions/` - Create session
- `POST /api/attendance/records/` - Mark attendance
- `GET /api/attendance/today/` - Today's records

### AI Operations
- `POST /api/ai/face-registration/register-face/` - Register face
- `POST /api/ai/face-recognition/recognize/` - Recognize face
- `POST /api/ai/face-recognition/mark-attendance/` - Auto mark

**Full API docs:** http://localhost:8000/api/

---

## 🐛 Troubleshooting

### Port in use
```bash
# Kill process on port
kill $(lsof -t -i:8000)
kill $(lsof -t -i:3000)
```

### Module not found
```bash
cd attendance_system
source venv/bin/activate
pip install -r ../requirements.txt
```

### Database issues
```bash
cd attendance_system
source venv/bin/activate
python manage.py migrate --run-syncdb
```

### Frontend errors
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

---

## 🎯 Common Commands

```bash
# Start both services
./start.sh

# Backend only
cd attendance_system && source venv/bin/activate
python manage.py runserver 0.0.0.0:8000

# Frontend only
cd frontend && npm run dev -- --host 0.0.0.0

# Database migrations
cd attendance_system && source venv/bin/activate
python manage.py makemigrations
python manage.py migrate

# Create superuser
cd attendance_system && source venv/bin/activate
python manage.py createsuperuser

# Django shell
cd attendance_system && source venv/bin/activate
python manage.py shell
```

---

## 🔐 Security

- JWT tokens with auto-refresh (15 min access, 7 day refresh)
- Email verification required for new accounts
- Password hashing with PBKDF2
- CORS protection
- CSRF protection
- Role-based permissions

---

## 📄 License

Educational project for FYP.

---

**Made with ❤️ for efficient attendance management**
