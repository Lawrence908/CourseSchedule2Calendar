#!/bin/bash

echo "🚀 Starting SchedShare in development mode..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found!"
    echo "📝 Please copy env.example to .env and update the values"
    echo "cp env.example .env"
    exit 1
fi

# Start the application with file watching
echo "🐳 Starting Docker Compose with file watching..."
docker-compose up --build

echo "✅ Development server started!"
echo "🌐 Visit: http://localhost:5000"
echo "📊 Logs: docker-compose logs -f"
echo "🛑 Stop: docker-compose down" 