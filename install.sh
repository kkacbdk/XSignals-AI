#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║     XSignals AI - Automated Installation Script        ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Check Python installation
echo "[1/5] Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ ERROR: Python 3 is not installed${NC}"
    echo ""
    echo "Please install Python 3.8 or higher:"
    echo "  • macOS: brew install python3"
    echo "  • Ubuntu/Debian: sudo apt install python3 python3-pip"
    echo "  • Other: https://www.python.org/downloads/"
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo -e "${GREEN}✅ $PYTHON_VERSION found${NC}"
echo ""

# Create virtual environment
echo "[2/5] Creating virtual environment..."
if [ -d "venv" ]; then
    echo "Virtual environment already exists, skipping..."
else
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
fi
echo ""

# Activate virtual environment
echo "[3/5] Activating virtual environment..."
source venv/bin/activate
echo -e "${GREEN}✅ Activated${NC}"
echo ""

# Install dependencies
echo "[4/5] Installing dependencies (this may take a minute)..."
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
echo -e "${GREEN}✅ Dependencies installed${NC}"
echo ""

# Setup environment file
echo "[5/5] Setting up configuration..."
if [ -f ".env" ]; then
    echo ".env file already exists"
else
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${GREEN}✅ Created .env file from template${NC}"
        echo ""
        echo -e "${YELLOW}⚠️  IMPORTANT: Edit .env file and add your API keys:${NC}"
        echo "   - BINANCE_API_KEY"
        echo "   - BINANCE_API_SECRET"
        echo "   - OPENROUTER_API_KEY"
    else
        echo -e "${YELLOW}⚠️  Warning: .env.example not found${NC}"
    fi
fi
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✅ INSTALLATION COMPLETE!${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Next steps:"
echo "  1. Edit .env file with your API keys"
echo "  2. Run './run.sh' to start using XSignals AI"
echo "  3. Check README.md for detailed documentation"
echo ""
echo "Get API keys from:"
echo "  • Binance: https://www.binance.com/en/my/settings/api-management"
echo "  • OpenRouter: https://openrouter.ai/keys"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Make run.sh executable
if [ -f "run.sh" ]; then
    chmod +x run.sh
    echo -e "${GREEN}Made run.sh executable${NC}"
fi