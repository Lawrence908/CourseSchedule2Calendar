# SchedShare Deployment Guide

This guide covers deploying SchedShare using Docker and Google Cloud Platform.

## 🐳 Local Development with Docker

### Prerequisites
- Docker and Docker Compose installed
- Git repository cloned

### Quick Start
1. **Copy environment variables:**
   ```bash
   cp env.example .env
   ```

2. **Edit `.env` file** with your configuration:
   ```bash
   nano .env
   ```

3. **Start development server with file watching:**
   ```bash
   ./dev.sh
   ```

4. **Access the application:**
   - Open http://localhost:5000
   - File changes will automatically restart the server

### Development Commands
```bash
# Start with file watching
./dev.sh

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild containers
docker-compose up --build
```

## ☁️ Google Cloud Deployment

### Option 1: Google Cloud Run (Recommended)

#### Setup GitHub Actions
1. **Create a Google Cloud Project:**
   ```bash
   gcloud projects create your-project-id
   gcloud config set project your-project-id
   ```

2. **Enable required APIs:**
   ```bash
   gcloud services enable run.googleapis.com
   gcloud services enable containerregistry.googleapis.com
   ```

3. **Create Service Account:**
   ```bash
   gcloud iam service-accounts create github-actions \
     --display-name="GitHub Actions"
   
   gcloud projects add-iam-policy-binding your-project-id \
     --member="serviceAccount:github-actions@your-project-id.iam.gserviceaccount.com" \
     --role="roles/run.admin"
   
   gcloud projects add-iam-policy-binding your-project-id \
     --member="serviceAccount:github-actions@your-project-id.iam.gserviceaccount.com" \
     --role="roles/storage.admin"
   
   gcloud iam service-accounts keys create key.json \
     --iam-account=github-actions@your-project-id.iam.gserviceaccount.com
   ```

4. **Add GitHub Secrets:**
   - Go to your GitHub repository → Settings → Secrets
   - Add the following secrets:
     - `GCP_PROJECT_ID`: Your Google Cloud project ID
     - `GCP_SA_KEY`: Content of the `key.json` file
     - `FLASK_SECRET_KEY`: A secure random string
     - `REDIS_URL`: Your Redis connection string
     - `MAIL_USERNAME`: Your email address
     - `MAIL_PASSWORD`: Your email app password
     - `GOOGLE_CLIENT_ID`: Google OAuth client ID
     - `GOOGLE_CLIENT_SECRET`: Google OAuth client secret
     - `APPLE_CLIENT_ID`: Apple OAuth client ID
     - `APPLE_TEAM_ID`: Apple team ID
     - `APPLE_KEY_ID`: Apple key ID

5. **Deploy:**
   - Push to `main` branch
   - GitHub Actions will automatically build and deploy

### Option 2: Google Cloud VM

#### Manual Deployment
1. **Create a VM instance:**
   ```bash
   gcloud compute instances create schedshare-vm \
     --zone=us-central1-a \
     --machine-type=e2-medium \
     --image-family=ubuntu-2004-lts \
     --image-project=ubuntu-os-cloud \
     --tags=http-server,https-server
   ```

2. **SSH into the VM:**
   ```bash
   gcloud compute ssh schedshare-vm --zone=us-central1-a
   ```

3. **Clone and deploy:**
   ```bash
   git clone https://github.com/yourusername/CourseSchedule2Calendar.git
   cd CourseSchedule2Calendar
   ./deploy.sh
   ```

4. **Configure environment:**
   ```bash
   cp env.example .env
   nano .env  # Edit with your configuration
   ```

5. **Restart service:**
   ```bash
   sudo systemctl restart schedshare
   ```

#### Automated Updates
The deployment script creates an `update.sh` script for easy updates:
```bash
./update.sh  # Pulls latest code and restarts
```

## 🔧 Configuration

### Environment Variables
See `env.example` for all required environment variables:

- **Flask**: Secret key, environment
- **Redis**: Connection URL
- **Email**: SMTP settings for Gmail
- **OAuth**: Google and Apple calendar credentials

### SSL Certificates
For production, replace the self-signed certificates in `/opt/schedshare/ssl/` with real certificates from Let's Encrypt or your CA.

## 📊 Monitoring

### View Logs
```bash
# Development & Production
docker-compose logs -f

# System service
sudo journalctl -u schedshare -f
```

### Health Checks
- Application: http://localhost:5000/
- Docker health checks are configured in the Dockerfile

## 🔒 Security

### Firewall Rules
The deployment script configures UFW firewall:
- Port 22 (SSH)
- Port 80 (HTTP)
- Port 443 (HTTPS)

### SSL/TLS
- Nginx handles SSL termination
- Security headers are configured
- Rate limiting is enabled

## 🚀 Scaling

### Cloud Run
- Automatically scales based on traffic
- Configure concurrency and memory limits in the GitHub Actions workflow

### VM Deployment
- Use load balancer for multiple instances
- Consider using managed Redis (Cloud Memorystore)
- Monitor resource usage and scale VM size as needed

## 🛠️ Troubleshooting

### Common Issues

1. **Redis Connection Failed:**
   ```bash
   # Check Redis container
   docker-compose logs redis
   
   # Test connection
   docker-compose exec redis redis-cli ping
   ```

2. **Port Already in Use:**
   ```bash
   # Find process using port 5000
   sudo lsof -i :5000
   
   # Kill process
   sudo kill -9 <PID>
   ```

3. **Permission Denied:**
   ```bash
   # Fix Docker permissions
   sudo usermod -aG docker $USER
   newgrp docker
   ```

### Support
- Check logs: `docker-compose logs -f`
- Verify environment: `docker-compose config`
- Test connectivity: `curl http://localhost:5000` 