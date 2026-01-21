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

# Kill any processes on ports 3000, 3001, 3002 to ensure system runs on 3000
echo -e "${YELLOW}Killing processes on ports 3000, 3001, 3002...${NC}"
npx kill-port 3000,3001,3002
sleep 1

echo -e "${GREEN}[OK] Ports cleared${NC}"
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

if [ ! -f "venv/bin/activate" ]; then
    echo -e "${RED}[ERROR] Virtual environment not found at root level${NC}"
    echo "Please run ./setup.sh first"
    exit 1
fi

source venv/bin/activate
cd attendance_system
export DJANGO_SETTINGS_MODULE=config.settings.development
python manage.py runserver 0.0.0.0:8000 &
BACKEND_PID=$!
cd ..

echo -e "${GREEN}[OK] Backend starting on https://localhost:8000${NC}"
sleep 3

# Start Frontend
echo -e "${YELLOW}Starting React Frontend...${NC}"
cd frontend
npm run dev -- --host 0.0.0.0 &
FRONTEND_PID=$!
cd ..

echo -e "${GREEN}[OK] Frontend starting on https://localhost:3000${NC}"
echo ""

echo "========================================"
echo -e "${GREEN}[OK] Both services are running!${NC}"
echo "========================================"
echo ""
echo -e "${CYAN}Access the application:${NC}"
echo "  Frontend:     https://localhost:3000"
echo "  Backend API:  https://localhost:8000/api"
echo "  Admin Panel:  https://localhost:8000/admin"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop both services${NC}"
echo ""

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID
