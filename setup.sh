#!/bin/bash

# Gemini CLI Docker Integration - Quick Setup Script
# This script helps new users quickly set up the development environment

set -e  # Exit on any error

echo "🚀 Gemini CLI Docker Integration - Quick Setup"
echo "=============================================="

# Check prerequisites
echo "📋 Checking prerequisites..."

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    echo "   Please install Python 3.8+ and try again."
    exit 1
fi
echo "✅ Python 3 found: $(python3 --version)"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is required but not installed."
    echo "   Please install Docker and try again."
    exit 1
fi
echo "✅ Docker found: $(docker --version)"

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo "❌ Docker is not running."
    echo "   Please start Docker and try again."
    exit 1
fi
echo "✅ Docker is running"

# Setup Python virtual environment
echo ""
echo "🐍 Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment and install dependencies
echo "📦 Installing Python dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo "✅ Dependencies installed"

# Setup environment configuration
echo ""
echo "⚙️ Setting up environment configuration..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "✅ Environment file created (.env)"
    echo "⚠️  IMPORTANT: Please edit .env and add your Gemini API key!"
    echo "   Get your API key from: https://makersuite.google.com/app/apikey"
else
    echo "✅ Environment file already exists"
fi

# Build Docker image
echo ""
echo "🐳 Building Docker image..."
cd core/agent
docker build -t agent-service:latest .
cd ../..
echo "✅ Docker image built successfully"

# Make scripts executable
echo ""
echo "🔧 Setting up scripts..."
chmod +x cleanup.sh
chmod +x setup.sh
echo "✅ Scripts are now executable"

# Final instructions
echo ""
echo "🎉 Setup completed successfully!"
echo "================================"
echo ""
echo "📝 Next steps:"
echo "1. Edit .env file and add your Gemini API key:"
echo "   GEMINI_API_KEY=your_actual_api_key_here"
echo ""
echo "2. Start the main service:"
echo "   source venv/bin/activate"
echo "   python main.py"
echo ""
echo "3. Run the demo (in another terminal):"
echo "   source venv/bin/activate"
echo "   python demos/demo_final_showcase.py"
echo ""
echo "4. When done, cleanup with:"
echo "   ./cleanup.sh"
echo ""
echo "📚 For more information, see README.md"
echo "🆘 For help, check CONTRIBUTING.md"
echo ""
echo "Happy coding with AI! 🤖✨"
