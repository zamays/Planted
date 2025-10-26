#!/usr/bin/env bash
# Planted - Garden Management System
# Unix/Linux/macOS startup script

set -e  # Exit on error

echo ""
echo "===================================="
echo "   Planted - Garden Management"
echo "===================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.9 or higher"
    echo ""
    echo "On Ubuntu/Debian: sudo apt install python3 python3-pip"
    echo "On macOS: brew install python3"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "Found Python $PYTHON_VERSION"

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "ERROR: pip3 is not installed"
    echo "Please install pip3"
    echo ""
    echo "On Ubuntu/Debian: sudo apt install python3-pip"
    exit 1
fi

# Check if requirements are installed
echo "Checking dependencies..."
if ! python3 -c "import flask" &> /dev/null; then
    echo "Installing dependencies..."
    echo ""
    
    # Check if in virtual environment
    if [ -z "$VIRTUAL_ENV" ]; then
        echo "⚠️  WARNING: Not running in a virtual environment"
        echo "It's recommended to use a virtual environment to avoid conflicts."
        echo ""
        echo "To create a virtual environment:"
        echo "  python3 -m venv venv"
        echo "  source venv/bin/activate  # On Windows: venv\\Scripts\\activate"
        echo "  pip install -r requirements.txt"
        echo ""
        read -p "Install system-wide anyway? (y/N): " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Cancelled. Please set up a virtual environment first."
            exit 1
        fi
    fi
    
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to install dependencies"
        echo "Try manually: pip3 install -r requirements.txt"
        exit 1
    fi
fi

# Check for .env file
if [ ! -f .env ]; then
    echo ""
    echo "WARNING: No .env file found"
    echo "The application will use mock weather data"
    echo "To use real weather data:"
    echo "  1. Copy .env.example to .env: cp .env.example .env"
    echo "  2. Add your OpenWeatherMap API key"
    echo ""
fi

echo "Starting Planted..."
echo ""
echo "The application will open in your browser at http://localhost:5000"
echo "Press Ctrl+C to stop the server"
echo ""

# Start the application
python3 main.py
