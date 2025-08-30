#!/bin/bash

# Deploy script for Google Cloud VM
set -e

echo "🚀 Starting deployment..."

# Update system
echo "📦 Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

# Install Docker
echo "🐳 Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
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

# Create app directory
echo "📁 Setting up application directory..."
sudo mkdir -p /opt/schedshare
sudo chown $USER:$USER /opt/schedshare

# Copy application files
echo "📄 Copying application files..."
cp -r . /opt/schedshare/
cd /opt/schedshare

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "⚠️  Please create a .env file with your configuration"
    echo "📝 Copy env.example to .env and update the values"
    cp env.example .env
fi

# Create SSL directory
sudo mkdir -p /opt/schedshare/ssl

# Generate self-signed certificate for development
echo "🔐 Generating SSL certificate..."
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/letsencrypt/live/schedshare.chrislawrence.ca/fullchain.pem \
    -out /etc/letsencrypt/live/schedshare.chrislawrence.ca/fullchain.pem \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"

sudo chown -R $USER:$USER /opt/schedshare/ssl

# Create systemd service
echo "⚙️  Creating systemd service..."
sudo tee /etc/systemd/system/schedshare.service > /dev/null <<EOF
[Unit]
Description=SchedShare Application
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/schedshare
ExecStart=/usr/bin/env bash -lc '\n  if docker compose version >/dev/null 2>&1; then\n    docker compose up -d\n  elif command -v docker-compose >/dev/null 2>&1; then\n    docker-compose up -d\n  else\n    echo "Docker Compose not found"\n    exit 1\n  fi\n'
ExecStop=/usr/bin/env bash -lc '\n  if docker compose version >/dev/null 2>&1; then\n    docker compose down\n  elif command -v docker-compose >/dev/null 2>&1; then\n    docker-compose down\n  else\n    echo "Docker Compose not found"\n    exit 1\n  fi\n'
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
echo "🔄 Enabling and starting service..."
sudo systemctl enable schedshare.service
sudo systemctl start schedshare.service

# Create update script
echo "📝 Creating update script..."
tee update.sh > /dev/null <<EOF
#!/bin/bash
cd /opt/schedshare
git pull origin main
if docker compose version >/dev/null 2>&1; then
  docker compose down
  docker compose build --no-cache
  docker compose up -d
elif command -v docker-compose >/dev/null 2>&1; then
  docker-compose down
  docker-compose build --no-cache
  docker-compose up -d
else
  echo "Docker Compose not found"
  exit 1
fi
echo "✅ Application updated successfully!"
EOF

chmod +x update.sh

# Setup firewall
echo "🔥 Configuring firewall..."
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable

echo "✅ Deployment completed!"
echo "🌐 Your application should be available at: https://$(curl -s ifconfig.me)"
echo "📋 To update the application, run: ./update.sh"
echo "📊 To check logs, run: docker compose logs -f (or docker-compose logs -f)"