#!/bin/bash
# start.sh - Launch both backend and frontend

set -e

echo "========================================"
echo "  Company Policy Chatbot - Startup"
echo "========================================"

# Check for .env file
if [ ! -f backend/.env ]; then
    echo ""
    echo "⚠️  Missing backend/.env file!"
    echo "   Run: cp backend/.env.example backend/.env"
    echo "   Then add your GROQ_API_KEY to the .env file."
    echo "   Get a free key at: https://console.groq.com"
    echo ""
    exit 1
fi

# Backend
echo ""
echo "📦 Starting backend..."
cd backend

if [ ! -d "venv" ]; then
    echo "   Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install -r requirements.txt -q

# Start backend in background
uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
echo "   ✅ Backend started (PID $BACKEND_PID) → http://localhost:8000"

cd ..

# Frontend
echo ""
echo "🎨 Starting frontend..."
cd frontend

if [ ! -d "node_modules" ]; then
    echo "   Installing npm packages..."
    npm install
fi

npm start &
FRONTEND_PID=$!
echo "   ✅ Frontend started (PID $FRONTEND_PID) → http://localhost:3000"

echo ""
echo "========================================"
echo "  ✅ All services running!"
echo "  Frontend: http://localhost:3000"
echo "  Backend:  http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo "  Press Ctrl+C to stop all services"
echo "========================================"

# Wait and handle shutdown
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo 'Stopped.'" EXIT
wait
