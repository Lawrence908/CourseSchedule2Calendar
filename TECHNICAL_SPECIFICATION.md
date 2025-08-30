# SchedShare - Technical Specification & Academic Project Documentation

## Project Overview

**SchedShare** is a full-stack web application that automates the conversion of university course schedules from PDF format into digital calendar events. The system integrates with multiple calendar providers (Google Calendar, Apple Calendar) and provides both automated event creation and manual ICS file export options.

### Core Problem Solved
- Eliminates manual calendar entry for university course schedules
- Provides seamless integration with existing calendar workflows
- Supports multiple calendar platforms and export formats
- Offers both automated and manual scheduling options

## Technical Architecture

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
- **Bootstrap** - Responsive UI framework (implied from modern UI description)

#### **External APIs & Services**
- **Google Calendar API** - OAuth2 integration for automated event creation
- **Google OAuth2** - Secure authentication flow
- **Apple Sign In** - OAuth integration for Apple Calendar (configured)
- **Gmail SMTP** - Email service for confirmation notifications
- **Let's Encrypt** - Automated SSL certificate management

#### **DevOps & Infrastructure**
- **Docker & Docker Compose** - Containerization and service orchestration
- **Nginx** - Reverse proxy, load balancing, and SSL termination
- **GitHub Actions** - CI/CD pipeline automation
- **Google Cloud Platform** - Cloud hosting infrastructure
- **Google Cloud Run** - Serverless container deployment
- **Google Cloud VM** - Traditional VM deployment option

#### **Core Libraries & Dependencies**
- **pdfplumber** - Advanced PDF text extraction and parsing
- **icalendar** - iCalendar format generation and manipulation
- **PyJWT** - JSON Web Token handling for secure authentication
- **python-dotenv** - Environment variable management
- **requests** - HTTP client for API interactions
- **redis** - Redis client for session management

## Key Technical Features

### 1. PDF Processing Engine
```python
# Core PDF parsing functionality
- Automated text extraction from VIU course schedule PDFs
- Intelligent parsing of course codes, times, locations, and instructors
- Error handling for malformed or corrupted PDF files
- Support for various PDF formats and layouts
```

### 2. Calendar Integration System
```python
# Multi-provider architecture
- Google Calendar: Direct OAuth2 integration with automatic event creation
- Apple Calendar: ICS file generation for manual import
- Extensible provider system for future calendar platforms
- Recurring event generation using RRULE standards
```

### 3. Authentication & Security
```python
# OAuth2 implementation
- Secure Google OAuth2 flow with state validation
- Session management with Redis backend
- JWT token handling for API security
- Rate limiting via Nginx configuration
- Non-root container execution for security
```

### 4. Email Notification System
```python
# Automated communication
- HTML email templating with Jinja2
- Gmail SMTP integration
- Confirmation emails for successful calendar creation
- Error notification system
```

## Advanced Technical Concepts Implemented

### 1. **OAuth2 Flow Implementation**
- Complete OAuth2 authorization code flow
- Secure token storage and refresh mechanisms
- State parameter validation for CSRF protection
- Scope management for calendar permissions

### 2. **PDF Parsing & Text Extraction**
- Advanced text extraction using pdfplumber
- Pattern recognition for course schedule formats
- Intelligent parsing of recurring schedules
- Error recovery for malformed documents

### 3. **Recurring Event Generation**
- RRULE (Recurrence Rule) implementation
- Weekly schedule pattern recognition
- Academic calendar integration
- Exception handling for holidays and breaks

### 4. **Container Orchestration**
- Multi-service Docker Compose architecture
- Development vs. production configurations
- Health check implementation
- Volume mounting for persistent data

### 5. **Production Deployment Architecture**
```yaml
# Nginx reverse proxy configuration
- SSL/TLS termination
- Load balancing across multiple application instances
- Rate limiting and security headers
- Static file serving optimization
```

## Development Workflow & DevOps

### **Local Development Environment**
```bash
# Development setup with hot reload
./dev.sh  # Starts development server with file watching
```

### **CI/CD Pipeline**
```yaml
# GitHub Actions workflow
- Automated testing on pull requests
- Docker image building and testing
- Deployment to Google Cloud Run
- Environment-specific configurations
```

### **Production Deployment**
```bash
# Automated deployment script
./deploy.sh  # Handles VM setup, Docker deployment, SSL configuration
```

## Academic Project Value

### **Computer Science Learning Outcomes**

#### **Software Engineering**
- Full-stack web application development
- API design and integration patterns
- Database design and session management
- Error handling and logging strategies

#### **System Architecture**
- Microservices architecture with Docker
- Load balancing and reverse proxy configuration
- Scalable cloud deployment strategies
- Security best practices implementation

#### **Data Processing**
- PDF text extraction and parsing algorithms
- Pattern recognition for structured data
- Data transformation and format conversion
- Error recovery and validation

#### **Web Technologies**
- Modern web framework development (Flask)
- OAuth2 authentication implementation
- RESTful API design principles
- Frontend-backend integration

#### **DevOps & Infrastructure**
- Containerization with Docker
- Cloud platform deployment (Google Cloud)
- CI/CD pipeline implementation
- Production environment management

### **Technical Skills Demonstrated**

#### **Programming Languages**
- **Python**: Advanced usage with Flask, API integration, PDF processing
- **JavaScript**: Frontend interactivity and API consumption
- **HTML/CSS**: Responsive web design and user interface development
- **YAML**: Configuration management for Docker and CI/CD

#### **Frameworks & Libraries**
- **Flask**: Web application framework with extensions
- **Gunicorn**: Production WSGI server configuration
- **Redis**: Session storage and caching implementation
- **Nginx**: Reverse proxy and load balancer configuration

#### **Cloud & DevOps**
- **Docker**: Containerization and orchestration
- **Google Cloud Platform**: Cloud infrastructure management
- **GitHub Actions**: Automated deployment pipeline
- **SSL/TLS**: Security certificate management

#### **APIs & Integration**
- **Google Calendar API**: OAuth2 integration and event management
- **SMTP**: Email service integration
- **RESTful APIs**: Design and implementation
- **OAuth2**: Authentication flow implementation

## Project Scalability & Future Enhancements

### **Current Architecture Strengths**
- Modular calendar provider system
- Containerized deployment for easy scaling
- Cloud-native design with auto-scaling capabilities
- Extensible PDF parsing engine

### **Potential Academic Extensions**
1. **Machine Learning Integration**
   - OCR improvement for better PDF parsing
   - Natural language processing for course description extraction
   - Predictive scheduling based on historical data

2. **Advanced Analytics**
   - Course scheduling optimization algorithms
   - Conflict detection and resolution
   - Academic calendar analytics

3. **Mobile Application**
   - React Native or Flutter mobile app
   - Push notifications for schedule changes
   - Offline calendar synchronization

4. **Multi-Institution Support**
   - Support for multiple universities
   - Institution-specific parsing rules
   - Centralized calendar management

## Research Opportunities

### **Computer Science Research Areas**
- **Natural Language Processing**: Advanced PDF text extraction
- **Scheduling Algorithms**: Optimal course scheduling
- **Cloud Computing**: Scalable web application architecture
- **Security**: OAuth2 implementation and API security
- **Human-Computer Interaction**: Calendar interface design

### **Academic Applications**
- **Capstone Project**: Full-stack development demonstration
- **Research Paper**: PDF processing and calendar integration
- **Portfolio Project**: Showcase of modern web development skills
- **Thesis Topic**: Automated academic scheduling systems

## Conclusion

This project demonstrates comprehensive full-stack development skills, modern DevOps practices, and integration with multiple external services. It serves as an excellent foundation for academic applications, showcasing practical implementation of theoretical concepts in software engineering, system architecture, and cloud computing.

The modular design and cloud-native architecture make it suitable for further academic research and development, with clear pathways for expansion into machine learning, mobile development, and multi-institution support.

