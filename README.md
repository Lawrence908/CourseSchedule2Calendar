# SchedShare - Course Schedule to Calendar Converter

**Live Application**: [schedshare.chrislawrence.ca](https://schedshare.chrislawrence.ca)

A full-stack web application that automates the conversion of university course schedules from PDF format into digital calendar events. SchedShare integrates with multiple calendar providers and provides both automated event creation and manual ICS file export options.

## 🎯 Problem Solved

University students and faculty often spend hours manually entering course schedules into their digital calendars. SchedShare eliminates this tedious process by:

- **Automatically extracting** course information from VIU course schedule PDFs
- **Seamlessly integrating** with existing calendar workflows (Google Calendar, Apple Calendar)
- **Providing flexibility** through both automated and manual scheduling options
- **Supporting multiple platforms** and export formats

## ✨ Core Features

### 📄 Intelligent PDF Processing
- **Advanced Text Extraction**: Uses pdfplumber for robust PDF parsing
- **Pattern Recognition**: Automatically identifies course codes, times, locations, and instructors
- **Error Recovery**: Handles malformed or corrupted PDF files gracefully
- **Format Flexibility**: Supports various PDF layouts and structures

### 📅 Multi-Platform Calendar Integration
- **Google Calendar**: Direct OAuth2 integration with automatic event creation
- **Apple Calendar**: ICS file generation for manual import
- **Recurring Events**: Generates proper RRULE standards for weekly schedules
- **Extensible Architecture**: Easy to add support for additional calendar providers

### 🔐 Secure Authentication
- **OAuth2 Implementation**: Secure Google OAuth2 flow with state validation
- **Session Management**: Redis-backed session storage
- **JWT Tokens**: Secure API authentication
- **Rate Limiting**: Protection against abuse

### 📧 Automated Notifications
- **Email Confirmations**: Receive detailed summaries of created events
- **HTML Templates**: Professional email formatting
- **Error Notifications**: Alerts for failed operations

### 🎨 Modern User Experience
- **Responsive Design**: Works seamlessly on desktop and mobile devices
- **Intuitive Interface**: Clean, user-friendly web interface
- **Real-time Feedback**: Immediate processing status updates
- **Progressive Enhancement**: Graceful degradation for older browsers

## 🏗️ Technical Architecture

### System Design
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Frontend  │    │  Flask Backend  │    │ Calendar APIs   │
│   (HTML/CSS/JS) │◄──►│   (Python)      │◄──►│ Google/Apple    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   Redis Cache   │
                       │  (Sessions)     │
                       └─────────────────┘
```

### Technology Stack

#### **Backend Technologies**
- **Python 3.11** - Primary programming language
- **Flask** - Lightweight web framework for rapid development
- **Gunicorn** - Production WSGI HTTP server
- **Redis** - Session storage and caching layer
- **Jinja2** - Template engine for dynamic content generation

#### **Frontend Technologies**
- **HTML5/CSS3** - Semantic markup and responsive design
- **JavaScript (ES6+)** - Client-side interactivity
- **Bootstrap** - Responsive UI framework

#### **External APIs & Services**
- **Google Calendar API** - OAuth2 integration for automated event creation
- **Google OAuth2** - Secure authentication flow
- **Apple Sign In** - OAuth integration for Apple Calendar
- **Gmail SMTP** - Email service for confirmation notifications

#### **DevOps & Infrastructure**
- **Docker & Docker Compose** - Containerization and service orchestration
- **Nginx** - Reverse proxy, load balancing, and SSL termination
- **GitHub Actions** - CI/CD pipeline automation
- **Google Cloud Platform** - Cloud hosting infrastructure

## 🚀 Key Technical Features

### 1. **Advanced PDF Parsing Engine**
- Intelligent text extraction using pdfplumber
- Pattern recognition for course schedule formats
- Support for various academic calendar structures
- Robust error handling and recovery

### 2. **OAuth2 Authentication System**
- Complete OAuth2 authorization code flow
- Secure token storage and refresh mechanisms
- State parameter validation for CSRF protection
- Scope management for calendar permissions

### 3. **Recurring Event Generation**
- RRULE (Recurrence Rule) implementation
- Weekly schedule pattern recognition
- Academic calendar integration
- Exception handling for holidays and breaks

### 4. **Production-Ready Architecture**
- Containerized deployment with Docker
- Auto-scaling cloud infrastructure
- SSL/TLS encryption
- Comprehensive monitoring and logging

## 🎓 Academic Project Value

This project demonstrates comprehensive full-stack development skills and modern software engineering practices:

### **Computer Science Learning Outcomes**
- **Software Engineering**: Full-stack web application development
- **System Architecture**: Microservices with Docker and cloud deployment
- **Data Processing**: PDF text extraction and pattern recognition
- **Web Technologies**: Modern web framework development with OAuth2
- **DevOps**: CI/CD pipelines and production environment management

### **Technical Skills Demonstrated**
- **Programming**: Python, JavaScript, HTML/CSS, YAML
- **Frameworks**: Flask, Gunicorn, Redis, Nginx
- **Cloud & DevOps**: Docker, Google Cloud Platform, GitHub Actions
- **APIs & Integration**: Google Calendar API, OAuth2, SMTP

## 🔮 Future Enhancements

### **Planned Features**
- Support for additional calendar providers (Outlook, etc.)
- Batch processing for multiple PDFs
- Advanced scheduling options and conflict detection
- Mobile application development
- API endpoints for third-party integration

### **Research Opportunities**
- **Machine Learning**: OCR improvement and natural language processing
- **Scheduling Algorithms**: Course scheduling optimization
- **Cloud Computing**: Scalable web application architecture
- **Security**: Advanced OAuth2 implementation and API security

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📞 Support

- **Live Application**: [schedshare.chrislawrence.ca](https://schedshare.chrislawrence.ca)
- **Issues**: Create an issue on GitHub for bug reports or feature requests
- **Documentation**: See [TECHNICAL_SPECIFICATION.md](TECHNICAL_SPECIFICATION.md) for detailed technical information