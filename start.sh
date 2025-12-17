#!/bin/bash
# ============================================================================
# AI-BASED ATTENDANCE SYSTEM - START SCRIPT (Ubuntu/WSL)
# ============================================================================
# This script starts both backend and frontend servers
# ============================================================================

echo "========================================"
echo "AI Attendance System - Starting..."
echo "========================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Check if ports are available
echo -e "${YELLOW}Checking ports...${NC}"

# Kill any processes on ports 8000 and 3000
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}[WARNING] Port 8000 is in use. Attempting to kill...${NC}"
    npx kill-port 8000
    sleep 1
fi

if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}[WARNING] Port 3000 is in use. Attempting to kill...${NC}"
    npx kill-port 3000
    sleep 1
fi

echo -e "${GREEN}[OK] Ports 8000 and 3000 are available${NC}"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}Stopping services...${NC}"
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    wait $BACKEND_PID $FRONTEND_PID 2>/dev/null
    echo -e "${GREEN}[OK] Services stopped${NC}"
    exit 0
}

trap cleanup INT TERM

# Start Backend
echo -e "${YELLOW}Starting Django Backend...${NC}"
cd attendance_system

if [ ! -f "venv/bin/activate" ]; then
    echo -e "${RED}[ERROR] Virtual environment not found${NC}"
    echo "Please run ./setup.sh first"
    exit 1
fi

source venv/bin/activate
export DJANGO_SETTINGS_MODULE=config.settings.development
python manage.py runserver 0.0.0.0:8000 &
BACKEND_PID=$!
cd ..

echo -e "${GREEN}[OK] Backend starting on http://localhost:8000${NC}"
sleep 3

# Start Frontend
echo -e "${YELLOW}Starting React Frontend...${NC}"
cd frontend
npm run dev -- --host 0.0.0.0 &
FRONTEND_PID=$!
cd ..

echo -e "${GREEN}[OK] Frontend starting on http://localhost:3000${NC}"
echo ""

echo "========================================"
echo -e "${GREEN}[OK] Both services are running!${NC}"
echo "========================================"
echo ""
echo -e "${CYAN}Access the application:${NC}"
echo "  Frontend:     http://localhost:3000"
echo "  Backend API:  http://localhost:8000/api"
echo "  Admin Panel:  http://localhost:8000/admin"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop both services${NC}"
echo ""

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID
