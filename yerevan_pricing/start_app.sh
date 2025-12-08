#!/bin/bash
# Script to start the Yerevan Pricing application

echo "🚀 Starting Yerevan Pricing Application..."
echo ""

# Navigate to project directory
cd "$(dirname "$0")"

# Check if Docker is running
if ! docker ps > /dev/null 2>&1; then
    echo "❌ Docker daemon is not running!"
    echo "Please start Docker Desktop and try again."
    exit 1
fi

echo "✅ Docker is running"
echo ""

# Stop any existing containers
echo "🛑 Stopping existing containers..."
docker-compose down

# Build and start all services
echo ""
echo "🔨 Building and starting all services..."
docker-compose up --build -d

# Wait for services to be ready
echo ""
echo "⏳ Waiting for services to start..."
sleep 10

# Check service status
echo ""
echo "📊 Service Status:"
docker-compose ps

echo ""
echo "✅ Application is starting!"
echo ""
echo "📍 Access URLs:"
echo "   🌐 Frontend (Streamlit):    http://localhost:8501"
echo "   🔧 Backend API:            http://localhost:8008"
echo "   📚 API Documentation:      http://localhost:8008/docs"
echo "   🗄️  pgAdmin:                http://localhost:5050"
echo ""
echo "📝 Logs:"
echo "   View all logs:    docker-compose logs -f"
echo "   View API logs:    docker-compose logs -f group1_api"
echo "   View Frontend:    docker-compose logs -f group1_app"
echo ""
echo "🛑 To stop: docker-compose down"

