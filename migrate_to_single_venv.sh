#!/bin/bash
# ============================================================================
# MIGRATE TO SINGLE VIRTUAL ENVIRONMENT
# ============================================================================
# This script migrates from nested venv to single root-level venv
# ============================================================================

echo "========================================"
echo "Migrate to Single Virtual Environment"
echo "========================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# Check if Django server is running
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${RED}[ERROR] Django server is running on port 8000${NC}"
    echo "Please stop the server first (Ctrl+C in the terminal running it)"
    exit 1
fi

echo -e "${CYAN}This script will:${NC}"
echo "1. Remove old nested venv (attendance_system/venv)"
echo "2. Use/create root-level venv (./venv)"
echo "3. Install all dependencies from requirements.txt"
echo ""
echo -e "${YELLOW}Press Enter to continue or Ctrl+C to cancel${NC}"
read

# Step 1: Remove old nested venv
echo ""
echo -e "${YELLOW}[1/4] Removing old nested venv...${NC}"
if [ -d "attendance_system/venv" ]; then
    rm -rf attendance_system/venv
    echo -e "${GREEN}[OK] attendance_system/venv removed${NC}"
else
    echo -e "${CYAN}[INFO] No nested venv found to remove${NC}"
fi

# Step 2: Create/verify root venv
echo ""
echo -e "${YELLOW}[2/4] Setting up root-level venv...${NC}"
if [ -d "venv" ]; then
    echo -e "${CYAN}[INFO] Root venv already exists${NC}"
    echo "Do you want to recreate it? (y/N)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        rm -rf venv
        python3 -m venv venv
        echo -e "${GREEN}[OK] Root venv recreated${NC}"
    else
        echo -e "${CYAN}[INFO] Using existing root venv${NC}"
    fi
else
    python3 -m venv venv
    echo -e "${GREEN}[OK] Root venv created${NC}"
fi

# Step 3: Activate and upgrade pip
echo ""
echo -e "${YELLOW}[3/4] Activating venv and upgrading pip...${NC}"
source venv/bin/activate
pip install --upgrade pip setuptools wheel >/dev/null 2>&1
echo -e "${GREEN}[OK] pip upgraded${NC}"

# Step 4: Install dependencies
echo ""
echo -e "${YELLOW}[4/4] Installing dependencies...${NC}"
echo "This may take a few minutes..."
pip install -r requirements.txt
echo -e "${GREEN}[OK] All dependencies installed${NC}"

# Verify installation
echo ""
echo -e "${YELLOW}Verifying installation...${NC}"
python -c "import django; import rest_framework; import qrcode; print('Django:', django.VERSION); print('DRF: OK'); print('qrcode: OK')"

echo ""
echo "========================================"
echo -e "${GREEN}[SUCCESS] Migration Complete!${NC}"
echo "========================================"
echo ""
echo -e "${CYAN}Summary:${NC}"
echo "✅ Single venv at root level (./venv)"
echo "✅ Old nested venv removed"
echo "✅ All dependencies installed"
echo ""
echo -e "${CYAN}To use:${NC}"
echo "  Activate: source venv/bin/activate"
echo "  Start:    ./start.sh"
echo ""
echo -e "${YELLOW}Note: Scripts (setup.sh, start.sh, start_production.sh) are already updated${NC}"
echo ""
