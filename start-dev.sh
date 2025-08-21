#!/bin/bash

# Start both API server and frontend development server
# Usage: ./start-dev.sh

set -e

echo "🚀 Starting Healthcare Scenario Builder Development Environment..."

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

# Check if Node.js/npm is available
if ! command -v npm &> /dev/null; then
    echo "❌ Node.js/npm is required but not installed."
    exit 1
fi

# Install Python dependencies if needed
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt > /dev/null 2>&1

# Install frontend dependencies if needed
echo "📦 Installing frontend dependencies..."
cd apps/frontend
npm install > /dev/null 2>&1
cd ../..

# Start API server in background
echo "🔧 Starting API server on port 8080..."
python3 mock_api.py &
API_PID=$!

# Wait a moment for API to start
sleep 2

# Check if API is running
if curl -s http://localhost:8080/health > /dev/null 2>&1; then
    echo "✅ API server is running at http://localhost:8080"
else
    echo "❌ Failed to start API server"
    kill $API_PID 2>/dev/null || true
    exit 1
fi

# Start frontend development server
echo "🔧 Starting frontend development server..."
cd apps/frontend

echo ""
echo "🌟 Development environment is ready!"
echo "   📡 API: http://localhost:8080"
echo "   🌐 Frontend: http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop both servers"

# Function to cleanup background processes
cleanup() {
    echo ""
    echo "🛑 Stopping servers..."
    kill $API_PID 2>/dev/null || true
    exit 0
}

# Set trap to cleanup on exit
trap cleanup SIGINT SIGTERM

# Start frontend (this will block)
npm run dev

# Cleanup in case npm run dev exits
cleanup