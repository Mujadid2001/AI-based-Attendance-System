# 🐧 WSL/Ubuntu Setup Guide

**Why WSL?** The `dlib` library needs compilation. On Windows it requires Visual Studio C++. On Ubuntu/WSL, it's much simpler!

## ⚡ Quick Start

```bash
# 1. Open Ubuntu/WSL terminal
cd "/mnt/d/FYP project/AI-based-Attendance-System"

# 2. Make scripts executable
chmod +x setup.sh start.sh

# 3. Run setup (one time only - takes 15-20 min)
./setup.sh

# 4. Start application (every time you want to use it)
./start.sh
```

**Access from Windows browser:** http://localhost:3000

---

## 📋 First Time Prerequisites

If you don't have Python/Node.js in WSL:

```bash
# Update system
sudo apt update

# Install Python
sudo apt install -y python3 python3-pip python3-venv

# Install Node.js 20
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Verify
python3 --version
node --version
```

---

## 🚀 What setup.sh Does

1. Checks Python, Node.js, npm
2. Installs system dependencies (cmake, build tools, etc.)
3. Creates Python virtual environment
4. Installs Python packages (including dlib - takes longest)
5. Sets up database
6. Installs frontend dependencies
7. Prompts for superuser creation

**Time:** ~15-20 minutes (mostly dlib compilation)

---

## 🎯 Daily Usage

```bash
# Navigate to project
cd "/mnt/d/FYP project/AI-based-Attendance-System"

# Start both servers
./start.sh

# Press Ctrl+C to stop
```

**Access:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/api
- Admin Panel: http://localhost:8000/admin

---

## 🛠️ Manual Control

### Backend Only
```bash
cd attendance_system
source venv/bin/activate
python manage.py runserver 0.0.0.0:8000
```

### Frontend Only
```bash
cd frontend
npm run dev -- --host 0.0.0.0
```

### Database Operations
```bash
cd attendance_system
source venv/bin/activate
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

---

## 🐛 Common Issues

### "Permission denied"
```bash
chmod +x setup.sh start.sh
```

### Port already in use
```bash
kill $(lsof -t -i:8000)  # Backend
kill $(lsof -t -i:3000)  # Frontend
```

### Module not found
```bash
cd attendance_system
source venv/bin/activate
pip install -r ../requirements.txt
```

### Can't access from Windows
Make sure servers bind to `0.0.0.0` (not `127.0.0.1`)

---

## 💡 Tips

1. **Keep terminal open** while using the app
2. **VS Code + Remote WSL** extension for editing
3. **Windows Terminal** with multiple tabs for convenience
4. **Access WSL files** from Windows: `\\wsl$\Ubuntu\`

---

**That's it! Much easier than Windows setup! 🎉**

For more details, see [README.md](README.md)
