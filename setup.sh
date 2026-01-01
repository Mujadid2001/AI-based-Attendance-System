#!/bin/bash
# ============================================================================
# AI-BASED ATTENDANCE SYSTEM - SETUP SCRIPT (Ubuntu/WSL)
# ============================================================================
# This script sets up the complete project - both backend and frontend
# ============================================================================

echo "========================================"
echo "AI Attendance System - Setup Script"
echo "========================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Check if running in WSL or Linux
if grep -qi microsoft /proc/version; then
    echo -e "${CYAN}Running in WSL (Windows Subsystem for Linux)${NC}"
else
    echo -e "${CYAN}Running in native Linux${NC}"
fi
echo ""

# Check prerequisites
echo -e "${YELLOW}[1/12] Checking prerequisites...${NC}"

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[ERROR] Python 3 is not installed${NC}"
    echo "Install it with: sudo apt update && sudo apt install python3 python3-pip python3-venv"
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo -e "${GREEN}[OK] Python found: $PYTHON_VERSION${NC}"

if ! command -v node &> /dev/null; then
    echo -e "${RED}[ERROR] Node.js is not installed${NC}"
    echo "Install it with: curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash - && sudo apt install -y nodejs"
    exit 1
fi

NODE_VERSION=$(node --version)
echo -e "${GREEN}[OK] Node.js found: $NODE_VERSION${NC}"

if ! command -v npm &> /dev/null; then
    echo -e "${RED}[ERROR] npm is not installed${NC}"
    exit 1
fi

NPM_VERSION=$(npm --version)
echo -e "${GREEN}[OK] npm found: v$NPM_VERSION${NC}"
echo ""

# Install system dependencies for dlib and face_recognition
echo -e "${YELLOW}[2/12] Installing system dependencies...${NC}"
echo "This requires sudo privileges and may take a few minutes..."

sudo apt update
sudo apt install -y \
    build-essential \
    cmake \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    libgtk-3-dev \
    python3-dev \
    python3-pip \
    python3-full \
    python3-venv \
    libgl1 \
    libglib2.0-0

echo -e "${GREEN}[OK] System dependencies installed${NC}"
echo ""

# Backend Setup - ROOT LEVEL VENV
echo -e "${YELLOW}[3/12] Setting up Python virtual environment at root level...${NC}"

# Remove old nested venv if exists
if [ -d "attendance_system/venv" ]; then
    echo "Removing old nested virtual environment..."
    rm -rf attendance_system/venv
    echo -e "${GREEN}[OK] Old venv removed${NC}"
fi

# Create root level venv
if [ -d "venv" ]; then
    echo "Removing existing root virtual environment..."
    rm -rf venv
fi

python3 -m venv venv
echo -e "${GREEN}[OK] Virtual environment created at root level${NC}"

echo ""
echo -e "${YELLOW}[4/12] Activating virtual environment...${NC}"
if [ ! -f "venv/bin/activate" ]; then
    echo -e "${RED}[ERROR] Virtual environment activation script not found${NC}"
    exit 1
fi
source venv/bin/activate
echo -e "${GREEN}[OK] Virtual environment activated${NC}"
echo ""

echo -e "${YELLOW}[5/12] Upgrading pip...${NC}"
pip install --upgrade pip setuptools wheel
echo -e "${GREEN}[OK] pip upgraded${NC}"
echo ""

echo -e "${YELLOW}[6/12] Installing Python dependencies...${NC}"
echo "This may take several minutes (especially dlib compilation)..."
echo "Please be patient..."

# Install dlib first (it takes longest)
echo ""
echo -e "${CYAN}Installing dlib (this will compile from source, may take 5-10 minutes)...${NC}"
pip install dlib

# Install other dependencies from root requirements.txt
pip install -r requirements.txt

echo -e "${GREEN}[OK] Python dependencies installed${NC}"
echo ""

echo -e "${YELLOW}[7/12] Checking environment configuration...${NC}"
if [ ! -f ".env" ]; then
    echo -e "${RED}[ERROR] .env file not found in root directory${NC}"
    echo "Please copy .env.example to .env and configure it"
    exit 1
fi
echo -e "${GREEN}[OK] .env file found${NC}"
echo ""

# Change to attendance_system for migrations
cd attendance_system

echo -e "${YELLOW}[8/12] Running database migrations...${NC}"
python manage.py makemigrations
python manage.py migrate
echo -e "${GREEN}[OK] Database migrations completed${NC}"
cd ..
echo ""

echo -e "${YELLOW}[9/12] Collecting static files...${NC}"
cd attendance_system
python manage.py collectstatic --noinput
echo -e "${GREEN}[OK] Static files collected${NC}"
cd ..
echo ""

# Frontend Setup
cd ../frontend
echo -e "${YELLOW}[10/12] Setting up frontend...${NC}"

if [ ! -f ".env" ]; then
    echo "Creating frontend .env file..."
    cp ".env.example" ".env"
    echo -e "${GREEN}[OK] Frontend .env file created${NC}"
fi

echo ""
echo -e "${YELLOW}[11/12] Installing frontend dependencies...${NC}"
echo "This may take several minutes..."
npm install
echo -e "${GREEN}[OK] Frontend dependencies installed${NC}"
echo ""

cd ..

echo -e "${YELLOW}[12/12] Creating superuser...${NC}"
echo -e "${CYAN}Please create an admin account:${NC}"
cd attendance_system
python manage.py createsuperuser
echo ""

echo "========================================"
echo -e "${GREEN}[OK] Setup Complete!${NC}"
echo "========================================"
echo ""
echo -e "${CYAN}Next steps:${NC}"
echo "1. Run './start.sh' to start both backend and frontend"
echo "2. Backend will be at: http://localhost:8000"
echo "3. Frontend will be at: http://localhost:3000"
echo "4. Admin panel at: http://localhost:8000/admin"
echo ""
echo -e "${YELLOW}Note: If using WSL, access from Windows browser using localhost${NC}"
echo ""

cd ..
