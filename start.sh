#!/bin/bash

echo "======================================"
echo "Customer Service Copilot - Quick Start"
echo "======================================"
echo ""

# Check if OPENAI_API_KEY is set
if [ ! -f api/.env ]; then
    echo "⚠️  No .env file found in api/"
    echo ""
    echo "Creating .env file from template..."
    cp api/.env.example api/.env
    echo ""
    echo "📝 Please edit api/.env and add your GOOGLE_API_KEY"
    echo "   Get your key at: https://makersuite.google.com/app/apikey"
    echo "   Then run this script again."
    echo ""
    exit 1
fi

# Check if venv exists
if [ ! -d "api/venv" ]; then
    echo "📦 Creating Python virtual environment..."
    cd api
    python3 -m venv venv
    cd ..
    echo "✅ Virtual environment created"
    echo ""
fi

# Check if dependencies are installed
if [ ! -f "api/venv/bin/uvicorn" ]; then
    echo "📦 Installing backend dependencies..."
    cd api
    ./venv/bin/pip install -r requirements.txt > /dev/null 2>&1
    cd ..
    echo "✅ Backend dependencies installed"
    echo ""
fi

# Check if frontend dependencies are installed
if [ ! -d "frontend/node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    cd frontend
    npm install > /dev/null 2>&1
    cd ..
    echo "✅ Frontend dependencies installed"
    echo ""
fi

echo "🚀 Starting services..."
echo ""
echo "Backend will run on: http://localhost:8000"
echo "Frontend will run on: http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Function to cleanup background processes
cleanup() {
    echo ""
    echo "🛑 Stopping services..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start backend
cd api
./venv/bin/python index.py &
BACKEND_PID=$!
cd ..

# Wait a bit for backend to start
sleep 3

# Start frontend
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

# Wait for both processes
wait
