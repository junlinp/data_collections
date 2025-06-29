#!/bin/bash

# Ollama Setup Script for Web Crawler with AI Summarization
# This script helps set up Ollama for local LLM processing

set -e

echo "🚀 Setting up Ollama for local LLM processing..."

# Check if Ollama is already installed
if command -v ollama &> /dev/null; then
    echo "✅ Ollama is already installed"
    OLLAMA_VERSION=$(ollama --version)
    echo "   Version: $OLLAMA_VERSION"
else
    echo "📥 Installing Ollama..."
    
    # Detect OS and install Ollama
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "   Detected Linux"
        curl -fsSL https://ollama.ai/install.sh | sh
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "   Detected macOS"
        curl -fsSL https://ollama.ai/install.sh | sh
    else
        echo "❌ Unsupported OS: $OSTYPE"
        echo "   Please install Ollama manually from https://ollama.ai/download"
        exit 1
    fi
    
    echo "✅ Ollama installed successfully"
fi

# Start Ollama service if not running
echo "🔧 Starting Ollama service..."
if ! pgrep -x "ollama" > /dev/null; then
    echo "   Starting Ollama daemon..."
    ollama serve &
    sleep 5  # Wait for service to start
else
    echo "   Ollama service is already running"
fi

# Check if service is responding
echo "🔍 Checking Ollama service..."
if curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "✅ Ollama service is responding"
else
    echo "❌ Ollama service is not responding"
    echo "   Please ensure Ollama is running: ollama serve"
    exit 1
fi

# List available models
echo "📋 Available models:"
ollama list

# Ask user which model to use
echo ""
echo "🤖 Which model would you like to use for summarization?"
echo "   Recommended models:"
echo "   - llama2 (good balance of speed and quality)"
echo "   - mistral (fast and efficient)"
echo "   - llama2:7b (smaller, faster)"
echo "   - llama2:13b (larger, better quality)"
echo ""

read -p "Enter model name (default: llama2): " MODEL_NAME
MODEL_NAME=${MODEL_NAME:-llama2}

echo "📥 Downloading model: $MODEL_NAME"
ollama pull $MODEL_NAME

echo ""
echo "✅ Setup complete!"
echo ""
echo "📝 Next steps:"
echo "1. Start the web crawler services:"
echo "   docker-compose up -d"
echo ""
echo "2. Access the services:"
echo "   - Web UI: http://localhost:5002"
echo "   - Summary Display: http://localhost:5004"
echo ""
echo "3. The LLM processor will use model: $MODEL_NAME"
echo ""
echo "🔧 To change the model later, update LOCAL_LLM_MODEL in docker-compose.yml"
echo "   or set the environment variable: export LOCAL_LLM_MODEL=your_model_name"
echo ""
echo "📚 For more models, visit: https://ollama.ai/library" 