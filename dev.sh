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
echo "🐳 Starting Docker Compose (single file, production defaults)..."

# Prefer Docker Compose v2 (docker compose); fallback to v1 (docker-compose)
if docker compose version >/dev/null 2>&1; then
  COMPOSE_CMD="docker compose"
elif command -v docker-compose >/dev/null 2>&1; then
  COMPOSE_CMD="docker-compose"
else
  echo "❌ Neither 'docker compose' nor 'docker-compose' found. Please install Docker Compose."
  exit 1
fi

$COMPOSE_CMD up --build

echo "✅ Development server started!"
echo "🌐 Visit: http://localhost:5000"
echo "📊 Logs: $COMPOSE_CMD logs -f"
echo "🛑 Stop: $COMPOSE_CMD down"