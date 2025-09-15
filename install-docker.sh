#!/bin/bash

# Comprehensive VM setup script for Docker development environment
set -e

echo "🚀 Starting fresh VM setup for Docker development..."

# Update system packages
echo "📦 Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

# Install essential development tools
echo "🛠️  Installing essential development tools..."
sudo apt-get install git python3.11-venv curl wget unzip build-essential -y

# Set up Python virtual environment
echo "🐍 Setting up Python virtual environment..."
python3 -m venv .venv
source .venv/bin/activate

# Install Python packages
echo "📚 Installing Python packages..."
pip install ipykernel
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    echo "⚠️  requirements.txt not found, skipping pip install -r requirements.txt"
fi

# Install Jupyter kernel
echo "📓 Installing Jupyter kernel..."
python3 -m ipykernel install --user --name=.venv

# Configure Git
echo "🔧 Configuring Git..."
git config user.name "Chris Lawrence"
git config user.email "c.lawrence908@gmail.com"

# Install Docker
echo "🐳 Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
else
    echo "✅ Docker is already installed"
fi

# Install Docker Compose v2 plugin if available; fallback to v1
echo "📋 Ensuring Docker Compose is available..."
if ! docker compose version &> /dev/null; then
    if ! command -v docker-compose &> /dev/null; then
        echo "⚠️  Docker Compose not found. Installing v2 plugin via apt..."
        sudo apt-get update
        sudo apt-get install -y docker-compose-plugin
    fi
fi

# Add user to docker group and activate virtual environment
echo "👤 Adding user to docker group..."
sudo usermod -aG docker $USER

echo "✅ VM setup complete!"
echo ""
echo "📝 Next steps:"
echo "1. Log out and log back in (or run 'newgrp docker') to apply docker group changes"
echo "2. Activate the virtual environment with: source .venv/bin/activate"
echo "3. Verify Docker installation with: docker --version"
echo "4. Test Docker with: docker run hello-world"
echo ""
echo "🎉 Your VM is now ready for Docker development!"