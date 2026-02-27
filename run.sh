#!/bin/bash

# FixJeICT v3 - Development Runner
# Starts both main app and admin app in foreground (for development)

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "Warning: .env file not found. Copying from .env.example..."
    cp .env.example .env
    echo "Please edit .env with your configuration."
fi

echo -e "${BLUE}Starting FixJeICT v3 in development mode...${NC}"
echo -e "${GREEN}Main app:${NC}    http://localhost:5000"
echo -e "${GREEN}Admin app:${NC}   http://localhost:5001"
echo -e "${GREEN}Health check:${NC} http://localhost:5000/health"
echo ""
echo "Press Ctrl+C to stop both apps"
echo ""

# Start both apps in background
uvicorn app:app --host 0.0.0.0 --port 5000 --reload &
MAIN_PID=$!

uvicorn admin_app:admin_app --host 0.0.0.0 --port 5001 --reload &
ADMIN_PID=$!

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "Stopping services..."
    kill $MAIN_PID 2>/dev/null || true
    kill $ADMIN_PID 2>/dev/null || true
    wait $MAIN_PID 2>/dev/null || true
    wait $ADMIN_PID 2>/dev/null || true
    echo "Services stopped."
    exit 0
}

# Trap Ctrl+C
trap cleanup INT TERM

# Wait for both processes
wait $MAIN_PID $ADMIN_PID
