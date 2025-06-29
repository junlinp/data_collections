#!/bin/bash

# Web Crawler Services Startup Script

echo "🚀 Starting Web Crawler Services..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Build and start services
echo "📦 Building and starting services..."
docker-compose up --build -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check service health
echo "🔍 Checking service health..."

# Check crawler service
if curl -f http://localhost:5001/api/health > /dev/null 2>&1; then
    echo "✅ Crawler service is healthy"
else
    echo "❌ Crawler service is not responding"
fi

# Check UI service
if curl -f http://localhost:5000/api/health > /dev/null 2>&1; then
    echo "✅ UI service is healthy"
else
    echo "❌ UI service is not responding"
fi

echo ""
echo "🎉 Services are starting up!"
echo "📊 UI Server: http://localhost:5000"
echo "🔧 Crawler Server: http://localhost:5001"
echo ""
echo "To view logs: docker-compose logs -f"
echo "To stop services: docker-compose down" 