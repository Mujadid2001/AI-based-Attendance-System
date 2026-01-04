#!/bin/bash
# ============================================================================
# AI-BASED ATTENDANCE SYSTEM - PRODUCTION SETUP SCRIPT
# ============================================================================
# This script sets up the project for production deployment
# ============================================================================

echo "========================================"
echo "AI Attendance System - Production Setup"
echo "========================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Check prerequisites
echo -e "${YELLOW}[1/9] Checking prerequisites...${NC}"

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[ERROR] Python 3 is not installed${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo -e "${GREEN}[OK] Python found: $PYTHON_VERSION${NC}"

if ! command -v node &> /dev/null; then
    echo -e "${RED}[ERROR] Node.js is not installed${NC}"
    exit 1
fi

NODE_VERSION=$(node --version)
echo -e "${GREEN}[OK] Node.js found: $NODE_VERSION${NC}"

echo ""

# Install system dependencies for dlib and face_recognition
echo -e "${YELLOW}[2/9] Installing system dependencies...${NC}"
sudo apt update
sudo apt install -y \
    build-essential \
    cmake \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    libgtk-3-dev \
    python3-dev \
    libgl1 \
    libglib2.0-0 \
    redis-server \
    postgresql \
    postgresql-contrib \
    libpq-dev \
    nginx

echo -e "${GREEN}[OK] System dependencies installed${NC}"
echo ""

# Setup Python virtual environment
echo -e "${YELLOW}[3/9] Setting up Python virtual environment...${NC}"
python3 -m venv venv
source venv/bin/activate
echo -e "${GREEN}[OK] Virtual environment activated${NC}"

echo -e "${YELLOW}[4/9] Upgrading pip...${NC}"
pip install --upgrade pip setuptools wheel
echo -e "${GREEN}[OK] pip upgraded${NC}"

echo -e "${YELLOW}[5/9] Installing Python dependencies...${NC}"
pip install -r requirements.txt
echo -e "${GREEN}[OK] Python dependencies installed${NC}"

echo -e "${YELLOW}[6/9] Checking production environment file...${NC}"
if [ ! -f ".env.production" ]; then
    echo -e "${RED}[ERROR] .env.production file not found${NC}"
    echo "Please create .env.production with your production settings"
    exit 1
fi
echo -e "${GREEN}[OK] .env.production file found${NC}"

# Verify critical production settings
echo -e "${YELLOW}[7/9] Verifying production configuration...${NC}"
source .env.production

if [ -z "$SECRET_KEY" ]; then
    echo -e "${RED}[ERROR] SECRET_KEY not set in .env.production${NC}"
    exit 1
fi

if [ -z "$DB_NAME" ]; then
    echo -e "${RED}[ERROR] DB_NAME not set in .env.production${NC}"
    exit 1
fi

if [ "$DEBUG" = "True" ]; then
    echo -e "${YELLOW}[WARNING] DEBUG is set to True in production environment${NC}"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo -e "${GREEN}[OK] Production configuration verified${NC}"

# Database migrations
cd attendance_system
echo -e "${YELLOW}[8/9] Running database migrations...${NC}"
export DJANGO_SETTINGS_MODULE=config.settings.production
python manage.py makemigrations
python manage.py migrate
echo -e "${GREEN}[OK] Database migrations completed${NC}"

echo -e "${YELLOW}[9/9] Collecting static files...${NC}"
python manage.py collectstatic --noinput
echo -e "${GREEN}[OK] Static files collected${NC}"
cd ..

# Start Redis
echo ""
echo -e "${YELLOW}Starting Redis server...${NC}"
sudo systemctl start redis-server
sudo systemctl enable redis-server
echo -e "${GREEN}[OK] Redis server started${NC}"

echo ""
echo "========================================"
echo -e "${GREEN}[OK] Production Setup Complete!${NC}"
echo "========================================"
echo ""
echo -e "${CYAN}Next steps:${NC}"
echo "1. Create a superuser: cd attendance_system && source ../venv/bin/activate && python manage.py createsuperuser"
echo "2. Configure Nginx (optional): Copy nginx.conf to /etc/nginx/sites-available/"
echo "3. Start production server: ./start_production.sh"
echo "4. For systemd service: sudo cp attendance-api.service /etc/systemd/system/"
echo ""
echo -e "${YELLOW}Important:${NC}"
echo "- Ensure PostgreSQL database exists and is accessible"
echo "- Ensure Redis is running: redis-cli ping"
echo "- Configure firewall rules for ports 80, 443, 8000"
echo "- Set up SSL certificates for HTTPS"
echo ""
