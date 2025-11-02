#!/bin/bash

# SilkyNet Local Development Server
# Quick start script for testing locally

echo "🐛 Starting SilkyNet API..."
echo "================================"

# Check if model exists
if [ ! -f "Unet.hdf5" ]; then
    echo "⚠️  WARNING: Unet.hdf5 not found!"
    echo "   The API will start but segmentation will fail."
    echo "   Please place your trained model in the project root."
    echo ""
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "📥 Installing dependencies..."
pip install -q -r requirements.txt

# Check if installation succeeded
if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    echo "Try running: pip install -r requirements.txt"
    exit 1
fi

echo "✅ Dependencies installed"
echo ""
echo "================================"
echo "🚀 Starting Flask server..."
echo "================================"
echo ""
echo "📱 Web Interface: http://localhost:5000"
echo "📡 API Endpoint:  http://localhost:5000/api/segment"
echo "❤️  Health Check: http://localhost:5000/api/health"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start server
python app.py
