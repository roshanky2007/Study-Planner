#!/bin/bash

# Smart Study Planner - Quick Start Script
# This script helps you get the application running quickly

echo "🎓 Smart Study Planner - Quick Start"
echo "======================================"
echo ""

# Check Python installation
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

echo "✓ Python 3 found: $(python3 --version)"

# Check if MongoDB is running
if ! pgrep -x "mongod" > /dev/null; then
    echo "⚠️  MongoDB is not running. Starting MongoDB..."
    echo "   If this fails, please start MongoDB manually:"
    echo "   - Linux/macOS: sudo systemctl start mongod"
    echo "   - Windows: net start MongoDB"
    echo ""
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -q -r requirements.txt
echo "✓ Dependencies installed"

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo "✓ .env file created. Please edit it if needed."
fi

echo ""
echo "======================================"
echo "✅ Setup complete!"
echo ""
echo "🚀 Starting Smart Study Planner..."
echo "   Open your browser to: http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop the server"
echo "======================================"
echo ""

# Run the application
python app.py
