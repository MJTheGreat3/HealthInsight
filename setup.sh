#!/bin/bash

echo "🚀 Setting up Hackxios Project..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p backend/src/uploads

# Build and start services
echo "🔨 Building and starting services..."
docker-compose up --build -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check if services are running
echo "🔍 Checking service status..."
docker-compose ps

# Display access information
echo ""
echo "✅ Setup complete! Services are running:"
echo "🌐 Frontend: http://localhost:5173"
echo "🔧 Backend API: http://localhost:8000"
echo "📊 MongoDB: localhost:27017"
echo ""
echo "📝 Useful commands:"
echo "  View logs: docker-compose logs -f"
echo "  Stop services: docker-compose down"
echo "  Restart services: docker-compose restart"
echo ""
echo "🎯 Ready to go! Open http://localhost:5173 in your browser."