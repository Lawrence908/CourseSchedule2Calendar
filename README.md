# SchedShare - Course Schedule to Calendar Converter

A Python Flask application that extracts course schedules from VIU course schedule PDFs and creates calendar events in your Google or Apple calendar. You can choose to allow permissions for automatic entry or select the calendar files (.ics) to schedule if you prefer to enter it yourself.

## ✨ Features

- **PDF Parsing**: Automatically extracts course information from VIU course schedule PDFs
- **Multi-Platform Support**: Integrates with Google Calendar and Apple Calendar
- **Flexible Export**: Download ICS files for manual import or direct calendar integration
- **Email Summaries**: Receive email confirmations of created events
- **Modern UI**: Clean, responsive web interface
- **Docker Support**: Easy deployment with Docker and Docker Compose
- **File Watching**: Automatic server restart on code changes during development

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Git

### Local Development
1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/CourseSchedule2Calendar.git
   cd CourseSchedule2Calendar
   ```

2. **Set up environment:**
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

3. **Start development server:**
   ```bash
   ./dev.sh
   ```

4. **Access the application:**
   - Open http://localhost:5000
   - Upload a course schedule PDF
   - Choose your calendar provider
   - Create calendar events

## 🐳 Docker Deployment

### Development Mode (with file watching)
```bash
./dev.sh
```

### Production Mode
```bash
docker-compose up -d --build
```

## ☁️ Cloud Deployment

### Google Cloud Run (Recommended)
- **Automatic CI/CD**: Push to `main` branch triggers deployment
- **Auto-scaling**: Handles traffic spikes automatically
- **Managed**: No server maintenance required

### Google Cloud VM
- **Full control**: Complete server access
- **Cost-effective**: Pay only for compute resources
- **Custom configuration**: Full customization options

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions.

## 🔧 Configuration

### Environment Variables
Required environment variables (see `env.example`):

- **Flask**: `FLASK_SECRET_KEY`, `FLASK_ENV`
- **Redis**: `REDIS_URL`
- **Email**: `MAIL_USERNAME`, `MAIL_PASSWORD`
- **Google OAuth**: `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`
- **Apple OAuth**: `APPLE_CLIENT_ID`, `APPLE_TEAM_ID`, `APPLE_KEY_ID`

### Calendar Providers
- **Google Calendar**: OAuth2 integration with automatic event creation
- **Apple Calendar**: ICS file download for manual import

## 📁 Project Structure

```
CourseSchedule2Calendar/
├── app.py                 # Main Flask application
├── pdf_parser.py          # PDF text extraction and parsing
├── calendar_providers/    # Calendar integration modules
├── templates/            # HTML templates
├── static/              # CSS, JS, images
├── uploads/             # Temporary PDF storage
├── Dockerfile           # Docker configuration
├── docker-compose.yml   # Development environment
├── docker-compose.prod.yml  # Production environment
├── deploy.sh           # VM deployment script
├── dev.sh              # Development startup script
└── DEPLOYMENT.md       # Detailed deployment guide
```

## 🛠️ Development

### Running Tests
```bash
python -m pytest
```

### Code Style
```bash
# Install pre-commit hooks
pre-commit install
```

### Database
The application uses Redis for session storage and caching. Redis is included in the Docker setup.

## 📊 Monitoring

### Logs
```bash
# Development
docker-compose logs -f

# Production
docker-compose logs -f
```

### Health Checks
- Application: http://localhost:5000/
- Docker health checks configured in Dockerfile

## 🔒 Security

- **HTTPS**: SSL/TLS encryption in production
- **Rate Limiting**: API rate limiting via Nginx
- **Security Headers**: XSS protection, content type validation
- **Non-root User**: Docker containers run as non-root user

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Issues**: Create an issue on GitHub
- **Documentation**: See [DEPLOYMENT.md](DEPLOYMENT.md) for deployment help
- **Logs**: Check application logs for debugging

## 🚀 Roadmap

- [ ] Support for more calendar providers (Outlook, etc.)
- [ ] Batch processing for multiple PDFs
- [ ] Advanced scheduling options
- [ ] Mobile app
- [ ] API endpoints for third-party integration