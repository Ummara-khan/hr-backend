#!/bin/bash

set -e

echo "========================================"
echo "  Company Policy Chatbot - Backend"
echo "========================================"

# Load .env for local development only
if [ -f backend/.env ]; then
    echo "📄 Loading backend/.env..."
    set -a
    source backend/.env
    set +a
else
    echo "ℹ️ No backend/.env found."
    echo "ℹ️ Assuming environment variables are provided by Railway."
fi

echo ""
echo "===== Environment Check ====="

if [ -n "$GROQ_API_KEY" ]; then
    echo "✅ GROQ_API_KEY is available"
else
    echo "⚠️ GROQ_API_KEY is NOT available"
fi

echo "PORT=${PORT:-8000}"
echo "============================="
echo ""

cd backend

# Create virtual environment if needed
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

source venv/bin/activate

echo "Installing requirements..."
pip install -r requirements.txt

echo ""
echo "🚀 Starting FastAPI..."

exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
