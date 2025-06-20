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

# Install Docker Compose
echo "📋 Installing Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
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
    -keyout /opt/schedshare/ssl/key.pem \
    -out /opt/schedshare/ssl/cert.pem \
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
ExecStart=/usr/local/bin/docker-compose -f docker-compose.prod.yml up -d
ExecStop=/usr/local/bin/docker-compose -f docker-compose.prod.yml down
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
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d
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
echo "📊 To check logs, run: docker-compose -f docker-compose.prod.yml logs -f" 