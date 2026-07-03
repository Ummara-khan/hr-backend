#!/bin/bash

set -e

echo "========================================"
echo "  Company Policy Chatbot - Backend"
echo "========================================"

# Load .env if it exists (for local development)
if [ -f backend/.env ]; then
    echo "📄 Loading backend/.env..."
    export $(grep -v '^#' backend/.env | xargs)
else
    echo "ℹ️ No backend/.env found. Using environment variables from the hosting platform."
fi

# Check that GROQ_API_KEY exists
if [ -z "$GROQ_API_KEY" ]; then
    echo ""
    echo "❌ GROQ_API_KEY is not set!"
    echo "Add it as an environment variable in your hosting platform."
    exit 1
fi

echo "✅ GROQ_API_KEY found."

cd backend

# Create virtual environment if needed
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate

pip install -r requirements.txt

echo ""
echo "🚀 Starting FastAPI..."

exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
