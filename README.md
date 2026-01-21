# 🎓 AI-Based Attendance System

Modern attendance management with AI-powered facial recognition. Complete separation of Django REST API backend and React TypeScript frontend.

## ✨ Features

- 👤 **AI Facial Recognition** - Automatic attendance via face detection
- 📷 **External Camera Support** - Use mobile phones/tablets as cameras
- 🔐 **JWT Authentication** - Secure token-based auth with email verification
- 👥 **Role-Based Access** - Admin, Teacher, Student permissions
- 📊 **Attendance Tracking** - Sessions, reports, manual/AI marking
- 🎤 **Voice Feedback** - Audio notifications for attendance
- 🌐 **Real-time Updates** - WebSocket support for live camera streaming
- 📱 **Modern UI** - Responsive React frontend
- 📷 **QR Code Pairing** - Easy mobile camera connection

## 🏗️ Tech Stack

**Backend:** Django 4.2.7 | DRF | JWT | dlib | face_recognition | OpenCV | Channels | Redis  
**Frontend:** React 18 | TypeScript | Vite | TailwindCSS | Axios | Zustand

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL (production only)
- Redis (for WebSocket support)
- Build tools for dlib (cmake, gcc, etc.)

### Development Setup

```bash
# 1. Make scripts executable
chmod +x setup.sh start.sh

# 2. Run setup (installs dependencies, creates database, etc.)
./setup.sh

# 3. Start both backend and frontend
./start.sh
```

**Access:**
- Frontend: https://localhost:3000
- Backend API: https://localhost:8000/api
- Admin Panel: https://localhost:8000/admin

**Note:** Development uses SQLite and console email. Configure `.env.development` if needed.

---

## 📋 WebSocket Setup for Real-Time Camera Streaming

### Overview
The system supports WebSocket-based real-time video streaming from mobile cameras to the laptop interface for better performance and lower latency.

### Architecture
- **Mobile Phone**: Uploads frames via HTTP POST to `/api/camera/sources/upload-frame`
- **Django Backend**: 
  - Caches frames (30s TTL)
  - Broadcasts frames to WebSocket channel group using Django Channels + Redis
- **Laptop Browser**: 
  - Connects via WebSocket to `wss://server:8000/ws/camera/{camera_id}/`
  - Receives frames in real-time
  - Automatically falls back to HTTP polling if WebSocket fails

### Redis Installation

#### On Ubuntu/WSL:
```bash
sudo apt-get update
sudo apt-get install redis-server
redis-server --version  # Verify installation
```

#### On Windows (native):
Download from: https://github.com/microsoftarchive/redis/releases  
Or use WSL (recommended)

#### On macOS:
```bash
brew install redis
```

### Running WebSocket Services

#### 1. Start Redis Server
```bash
# In a separate terminal
redis-server

# Or run in background
redis-server --daemonize yes

# Verify it's running
redis-cli ping  # Should return "PONG"
```

#### 2. Start Django with ASGI Server

**Development (Daphne):**
```bash
cd attendance_system
source venv/bin/activate
daphne -b 0.0.0.0 -p 8000 config.asgi:application
```

**Production (Gunicorn + Uvicorn workers):**
```bash
gunicorn config.asgi:application -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --workers 4 \
  --access-logfile - \
  --error-logfile -
```

**Important:** Do NOT use `python manage.py runserver` - it doesn't support WebSockets!

#### 3. Using the start.sh Script
The `./start.sh` script uses Django's development server by default. For WebSocket support during development:
- Either start Redis and use Daphne manually (as shown above)
- Or the system will automatically fall back to HTTP polling

### WebSocket Configuration

Django settings already include:

```python
# ASGI Application
ASGI_APPLICATION = 'config.asgi.application'

# Channel Layers (Redis backend)
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [('127.0.0.1', 6379)],
        },
    },
}
```

Environment variables (optional in `.env.development` or `.env.production`):
```bash
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
```

### Troubleshooting WebSocket

#### WebSocket Connection Failed
**Solutions:**
1. Check if Redis is running: `redis-cli ping`
2. Verify Django is using Daphne/Uvicorn (not runserver)
3. Check firewall allows port 8000
4. System automatically falls back to HTTP polling if WebSocket fails

#### Redis Connection Error
**Solutions:**
1. Start Redis: `redis-server`
2. Check Redis port: `netstat -an | grep 6379`
3. Update REDIS_HOST/REDIS_PORT in .env if needed

#### Frames Not Updating
**Solutions:**
1. Check mobile is uploading frames (should be ~2 requests/second)
2. Check Django logs for WebSocket broadcasts
3. Check browser console for WebSocket messages
4. Verify camera ID matches

### Performance Comparison

**HTTP Polling:**
- Latency: 500ms average
- Server Load: 2-5 requests/second per client

**WebSocket:**
- Latency: <50ms (real-time)
- Server Load: Constant (independent of clients)
- Scalability: High (1 upload = broadcast to all)

---

## 🌐 Network Configuration

The system automatically detects your local network IP for QR code generation, ensuring mobile devices can connect to external cameras.

### Development (Auto-Detection)
```bash
# Leave SERVER_BASE_URL empty in .env.development
SERVER_BASE_URL=
FORCE_DYNAMIC_IP_DETECTION=True

# System will auto-detect your LAN IP (e.g., 192.168.1.100)
# QR codes will contain: https://192.168.1.100:8000/camera.html
```

### Production (Fixed Domain)
```bash
# Set your public domain in .env.production
SERVER_BASE_URL=https://attendance.yourdomain.com
FORCE_DYNAMIC_IP_DETECTION=False
```

### Docker Deployment
```bash
# Use host machine's LAN IP
SERVER_BASE_URL=https://192.168.1.100:8000
# OR use host network mode in docker-compose.yml
```

### WSL (Windows Subsystem for Linux) Setup

The system automatically detects WSL and uses Windows host's LAN IP. However, WSL2 requires additional Windows configuration for external device access.

#### Manual WSL Network Configuration

**ONE-TIME SETUP (Required after each Windows restart):**

1. **Get your WSL IP address:**
   ```bash
   # In WSL terminal
   hostname -I
   # Example output: 172.20.10.5
   ```

2. **Configure Windows Firewall (PowerShell as Administrator):**
   ```powershell
   # Allow port 8000 through Windows Firewall
   New-NetFirewallRule -DisplayName "WSL Django Server" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow
   ```

3. **Set up Port Forwarding (PowerShell as Administrator):**
   ```powershell
   # Replace WSL_IP with your actual WSL IP from step 1
   netsh interface portproxy add v4tov4 listenport=8000 listenaddress=0.0.0.0 connectport=8000 connectaddress=WSL_IP
   
   # Example:
   netsh interface portproxy add v4tov4 listenport=8000 listenaddress=0.0.0.0 connectport=8000 connectaddress=172.20.10.5
   ```

4. **Get your Windows IP address:**
   ```powershell
   # In PowerShell
   ipconfig
   # Look for "Wireless LAN adapter Wi-Fi" or "Ethernet adapter"
   # Example: 192.168.1.100
   ```

5. **Start Django server in WSL:**
   ```bash
   # In WSL terminal
   ./start.sh
   ```

6. **Access from mobile device:**
   - Use the Windows IP address (e.g., https://192.168.1.100:8000)
   - Scan QR code which will contain the Windows IP

#### Verifying WSL Configuration

```bash
# Check detected IP (DEBUG mode only)
curl -k https://localhost:8000/api/camera/sources/network-info/
```

#### Managing WSL Port Forwarding

**View existing port forwarding rules:**
```powershell
netsh interface portproxy show all
```

**Remove port forwarding (cleanup):**
```powershell
netsh interface portproxy delete v4tov4 listenport=8000 listenaddress=0.0.0.0
```

**Remove firewall rule:**
```powershell
Remove-NetFirewallRule -DisplayName "WSL Django Server"
```

#### Troubleshooting WSL

- **Port forwarding is lost after Windows restart**: Re-run the port forwarding command
- **Mobile can't connect**: Verify Windows Firewall rule is active
- **Auto-detection fails**: Manually set `SERVER_BASE_URL=https://YOUR_WINDOWS_IP:8000` in `.env.development`
- **Wrong IP detected**: Set `SERVER_BASE_URL` manually in `.env.development`

### General Network Troubleshooting

- **Check detected IP**: Visit `https://localhost:8000/api/camera/sources/network-info/` (DEBUG mode only)
- **WSL users**: Server binds to `0.0.0.0:8000` but mobile must use Windows host IP
- **VPN interference**: If VPN is active, manually set `SERVER_BASE_URL`
- **Multiple network adapters**: System prioritizes private IP ranges (192.168.x.x, 10.x.x.x)
- **Firewall**: Ensure port 8000 accepts LAN connections
- **Mobile can't connect**: Verify mobile and server are on same network

---

## 🏭 Production Deployment

### Production Setup (Manual)

```bash
# 1. Make scripts executable
chmod +x setup_deploy.sh start_production.sh

# 2. Configure environment
# Edit .env.production with your production values

# 3. Run production setup
./setup_deploy.sh

# 4. Start production server
./start_production.sh
```

### Production Setup (Docker)

```bash
# 1. Configure environment
# Edit .env.production with your values

# 2. Start services
docker-compose up -d

# 3. Create superuser
docker-compose exec api python manage.py createsuperuser
```

### Environment Files

The project uses separate environment files for development and production:

**Root Level (Django Backend):**
- `.env.development` - SQLite, console email, DEBUG=True
- `.env.production` - PostgreSQL, SMTP, DEBUG=False

**Frontend (Vite):**
- `frontend/.env.development` - Development API URL
- `frontend/.env.production` - Production API URL

---

## 🗂️ Project Structure

```
AI-based-Attendance-System/
├── attendance_system/          # Django Backend
│   ├── apps/
│   │   ├── authentication/    # User auth & JWT
│   │   ├── student/          # Students & courses
│   │   ├── attendance/       # Attendance tracking
│   │   ├── ai_core/         # Face recognition AI
│   │   └── camera_integration/ # External camera support
│   ├── config/              # Settings & ASGI
│   │   ├── settings/        # Environment-based settings
│   │   ├── asgi.py         # ASGI application
│   │   └── routing.py      # WebSocket routing
│   ├── media/              # Uploaded images
│   ├── staticfiles/        # Collected static files
│   └── manage.py
│
├── frontend/                  # React Frontend
│   ├── src/
│   │   ├── pages/           # Page components
│   │   ├── components/      # Reusable components
│   │   ├── services/        # API integration
│   │   ├── store/          # State management (Zustand)
│   │   └── types/          # TypeScript types
│   ├── public/             # Static assets
│   └── package.json
│
├── models/                   # AI model files
├── .env.development         # Development config
├── .env.production          # Production config
├── setup.sh                # Development setup script
├── setup_deploy.sh         # Production setup script
├── start.sh                # Development start script
├── start_production.sh     # Production start script
├── docker-compose.yml      # Docker configuration
├── Dockerfile             # Docker image
├── nginx.conf             # Nginx configuration
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

---

## 📱 Usage Guide

### For Students
1. **Register** → Verify email → Login
2. Complete your profile
3. **Register face** (Profile → Face Registration)
   - Upload 3-5 clear photos of your face
4. **Enroll in courses**
5. Attend classes - your attendance will be marked automatically

### For Teachers
1. **Login** with teacher account
2. **Create course** (Course Management)
3. **Add students** to course
4. **Create attendance session** before class
5. **Mark attendance** using:
   - Manual entry
   - AI camera (laptop webcam)
   - External camera (mobile device via QR code)
6. **View reports** and analytics

### External Camera Setup (Teachers)
1. Navigate to **AI → External Cameras**
2. Click **Add Camera** and fill in details (name, location)
3. Click **QR Code** icon on the camera card
4. **Scan QR code** with mobile device
5. Grant camera permissions on mobile
6. Mobile camera is now ready for face recognition
7. Go to **Face Recognition** page and select mobile camera as source

### For Admins
1. Access **admin panel**: https://localhost:8000/admin
2. Manage users, courses, attendance records
3. Configure system settings
4. Load training data for face recognition

---

## 🔌 API Endpoints

### Authentication
- `POST /api/auth/register/` - Register new user
- `POST /api/auth/login/` - Login and get JWT tokens
- `POST /api/auth/verify-email/` - Verify email with token
- `POST /api/auth/token/refresh/` - Refresh access token
- `GET /api/auth/me/` - Get current user info

### Students & Courses
- `GET /api/students/profiles/` - List student profiles
- `POST /api/students/profiles/` - Create student profile
- `GET /api/students/courses/` - List courses
- `POST /api/students/courses/` - Create course
- `POST /api/students/enrollments/` - Enroll student in course

### Attendance
- `POST /api/attendance/sessions/` - Create attendance session
- `GET /api/attendance/sessions/` - List sessions
- `POST /api/attendance/records/` - Mark attendance manually
- `GET /api/attendance/records/today/` - Today's attendance

### AI Operations
- `POST /api/ai/face-registration/register-face/` - Register student face
- `POST /api/ai/face-recognition/recognize-and-mark-attendance/` - Recognize and mark
- `POST /api/ai/face-recognition/recognize-only/` - Recognize without marking
- `POST /api/ai/face-recognition/bulk-recognize-attendance/` - Bulk recognition

### Camera Integration
- `GET /api/camera/sources/` - List external cameras
- `POST /api/camera/sources/` - Create camera source
- `GET /api/camera/sources/{id}/qr-code/` - Get QR code for camera
- `POST /api/camera/sources/upload-frame/` - Upload frame from mobile
- `WS /ws/camera/{camera_id}/` - WebSocket for real-time streaming

**Full API documentation:** https://localhost:8000/api/

---

## 🐛 Troubleshooting

### Port Already in Use
The `start.sh` script automatically kills processes on ports 3000, 3001, 3002. If you still have issues:

```bash
# Manual port killing
npx kill-port 8000,3000,3001,3002

# Or on Linux/Mac
lsof -ti:8000 | xargs kill -9
lsof -ti:3000 | xargs kill -9
```

### Module Not Found / Import Errors
```bash
# Reinstall Python dependencies
cd attendance_system
source venv/bin/activate
pip install -r ../requirements.txt

# Reinstall frontend dependencies
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Database Issues
```bash
cd attendance_system
source venv/bin/activate
python manage.py migrate --run-syncdb
```

### Face Recognition Not Working
```bash
# Check if training data is loaded
curl https://localhost:8000/api/ai/configuration/load-training-data/ -X POST -k

# Check if students have registered faces
# Admin panel → Student Face Images
```

### Mobile Camera Connection Issues
1. Verify mobile and server are on same WiFi network
2. Check firewall allows port 8000
3. For WSL users: Follow WSL network configuration steps above
4. Check `SERVER_BASE_URL` in environment variables
5. Verify QR code URL is accessible from mobile browser

### WebSocket Not Working
1. Ensure Redis is running: `redis-cli ping`
2. Check if using ASGI server (Daphne/Uvicorn), not runserver
3. System falls back to HTTP polling automatically if WebSocket fails

---

## 🎯 Common Commands

### Start/Stop Services
```bash
# Start both backend and frontend
./start.sh

# Backend only (development)
cd attendance_system
source venv/bin/activate
python manage.py runserver 0.0.0.0:8000

# Backend with WebSocket support
cd attendance_system
source venv/bin/activate
daphne -b 0.0.0.0 -p 8000 config.asgi:application

# Frontend only
cd frontend
npm run dev -- --host 0.0.0.0

# Production
./start_production.sh
```

### Database Management
```bash
cd attendance_system
source venv/bin/activate

# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Django shell
python manage.py shell
```

### Static Files (Production)
```bash
cd attendance_system
source venv/bin/activate
python manage.py collectstatic --noinput
```

### Testing
```bash
# Backend tests
cd attendance_system
source venv/bin/activate
python manage.py test

# Frontend tests
cd frontend
npm run test
```

---

## 🔐 Security Features

- **JWT Authentication** with auto-refresh (15 min access, 7 day refresh)
- **Email verification** required for new accounts
- **Password hashing** with PBKDF2
- **CORS protection** for cross-origin requests
- **CSRF protection** for form submissions
- **Role-based permissions** (Admin, Teacher, Student)
- **Secure file uploads** with validation
- **Rate limiting** on API endpoints (production)

---

## 🚀 Technology Stack Details

### Backend
- **Django 4.2.7** - Web framework
- **Django REST Framework** - API development
- **Simple JWT** - JWT authentication
- **dlib** - Face detection and recognition
- **face_recognition** - Face recognition library
- **OpenCV** - Image processing
- **Django Channels** - WebSocket support
- **Redis** - Channel layer backend
- **Daphne** - ASGI server for WebSockets
- **Gunicorn** - Production WSGI server

### Frontend
- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **TailwindCSS** - Utility-first CSS
- **Axios** - HTTP client
- **Zustand** - State management
- **React Router** - Routing
- **React Query** - Data fetching

### DevOps
- **Docker** - Containerization
- **Docker Compose** - Multi-container orchestration
- **Nginx** - Reverse proxy
- **PostgreSQL** - Production database
- **SQLite** - Development database

---

## 📊 System Requirements

### Development
- **OS**: Windows 10/11, macOS 10.15+, Ubuntu 20.04+
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 2GB free space
- **Python**: 3.11 or higher
- **Node.js**: 18 or higher
- **Redis**: Latest stable version

### Production
- **OS**: Ubuntu 20.04+ or similar Linux distribution
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 10GB free space
- **Database**: PostgreSQL 12+
- **Python**: 3.11+
- **Node.js**: 18+
- **Redis**: Latest stable version
- **Nginx**: Latest stable version

---

## 📄 License

Educational project for Final Year Project (FYP).

---

## 🤝 Contributing

This is an educational project. For issues or suggestions:
1. Document the issue
2. Provide steps to reproduce
3. Include system information (OS, Python version, etc.)

---

## 📞 Support

For setup help or issues:
1. Check this README thoroughly
2. Review troubleshooting section
3. Check API documentation at `/api/`
4. Verify environment configuration

---

**Made with ❤️ for efficient attendance management**
