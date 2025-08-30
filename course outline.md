# CSCI 491 Senior Research Project Outline

**Student:** Chris Lawrence  
**Project Title:** SchedShare – Smart Course Schedule to Calendar Automation  
**Supervisor:** Prof. Luis Meneses  
**Committee Members:** _[TBD – at least one other CS faculty member]_  
**Proposal:** CSCI 491 Senior Research Project (6 credits)  
**Duration:** September 2025 – April 2026  

---

## Topic Outline

This project proposes the design, development, and evaluation of **SchedShare**, a full-stack web application that automates the conversion of VIU students' course schedule PDFs into digital calendar events. The system integrates with multiple calendar providers (Google Calendar, Apple Calendar) and provides both automated event creation and manual ICS file export options.

### Research Problem
Students currently face significant friction in managing their academic schedules:
- **Manual Entry Burden**: Time-consuming manual calendar entry for each course
- **Format Inconsistency**: Lack of standardization across different calendar platforms
- **Integration Gaps**: No seamless connection between university course schedules and personal calendar systems
- **Privacy Concerns**: Third-party apps often require excessive permissions or data sharing

### Technical Innovation
SchedShare addresses these challenges through:
- **Advanced PDF Processing**: Intelligent text extraction and pattern recognition for course schedule parsing
- **Multi-Platform Integration**: OAuth2-based authentication with Google Calendar API and ICS file generation
- **Cloud-Native Architecture**: Containerized deployment with auto-scaling capabilities
- **Security-First Design**: Non-root containers, rate limiting, and secure session management

### Academic Significance
This project lies at the intersection of:
- **Software Engineering**: Full-stack development with modern frameworks and APIs
- **System Architecture**: Microservices design with container orchestration
- **Data Processing**: PDF parsing algorithms and pattern recognition
- **Cloud Computing**: Scalable deployment strategies and DevOps practices
- **Human-Computer Interaction**: User experience design for academic workflow automation

---

## Project Description

### Core Technical Components

#### 1. **PDF Processing Engine**
- Advanced text extraction using `pdfplumber` library
- Pattern recognition for VIU course schedule formats
- Intelligent parsing of course codes, times, locations, and instructors
- Error handling and recovery for malformed documents
- Support for various PDF layouts and formats

#### 2. **Calendar Integration System**
- **Google Calendar API**: OAuth2 integration with automatic event creation
- **Apple Calendar**: ICS file generation for manual import
- **Recurring Event Generation**: RRULE implementation for weekly schedules
- **Extensible Architecture**: Modular provider system for future platforms

#### 3. **Authentication & Security**
- Complete OAuth2 authorization code flow implementation
- Secure token storage and refresh mechanisms
- Session management with Redis backend
- Rate limiting and security headers via Nginx
- Non-root container execution for enhanced security

#### 4. **Cloud Infrastructure**
- **Docker & Docker Compose**: Containerization and service orchestration
- **Nginx**: Reverse proxy, load balancing, and SSL termination
- **Google Cloud Platform**: Cloud hosting with auto-scaling
- **CI/CD Pipeline**: GitHub Actions for automated deployment

### Research Scope & Deliverables

#### **Phase 1: Core System Development (Fall 2025)**
- PDF parsing engine with VIU schedule format support
- Google Calendar OAuth2 integration
- ICS file generation for Apple Calendar
- Responsive web interface with modern UI/UX
- Containerized deployment with Docker

#### **Phase 2: Advanced Features (Spring 2026)**
- User account system with session management
- Schedule comparison and conflict detection
- Email notification system with HTML templating
- Multi-institution parsing rule framework
- Performance optimization and scaling

#### **Phase 3: Research & Evaluation (Spring 2026)**
- User testing with VIU students and faculty
- Performance analysis and optimization
- Security audit and penetration testing
- Comparative analysis with existing solutions

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
- **Backend**: Python 3.11, Flask, Gunicorn, Redis
- **Frontend**: HTML5/CSS3, JavaScript (ES6+), Jinja2 templating
- **APIs**: Google Calendar API, Google OAuth2, Gmail SMTP
- **Infrastructure**: Docker, Docker Compose, Nginx, Google Cloud Platform
- **DevOps**: GitHub Actions, Let's Encrypt SSL, CI/CD pipeline

---

## Deliverables & Timeline

### Fall 2025

| Week | Deliverable | Technical Focus |
|------|-------------|-----------------|
| Sept 6–16 | Finalized proposal & registration form | Project scope definition |
| Sept 20 | Project kick-off meeting and refinement of scope | Technical architecture review |
| Oct | PDF parsing engine implementation, OAuth2 integration | Backend development, API integration |
| Nov | Calendar logic implementation, UI refinement | Frontend development, user experience |
| Dec | MVP complete with full deployment pipeline | DevOps, testing, documentation |

### Spring 2026

| Week | Deliverable | Research Focus |
|------|-------------|----------------|
| Jan | Formal midterm presentation + defense to committee | Technical demonstration, progress review |
| Feb | User account system, session management | Database design, security implementation |
| March | Schedule comparison features, performance optimization | Algorithm development, scalability testing |
| April | Final report, presentation, defense | Research analysis, user study results |

---

## Research Methodology

### **Technical Research**
- **Comparative Analysis**: Evaluation of existing PDF parsing libraries and calendar integration approaches
- **Performance Benchmarking**: Load testing and optimization of PDF processing algorithms
- **Security Assessment**: Penetration testing and vulnerability analysis
- **Scalability Testing**: Container orchestration and cloud deployment optimization

### **User Research**
- **User Testing**: 20+ VIU students testing the application with real course schedules
- **Usability Studies**: Task completion rates, error analysis, user satisfaction surveys
- **Comparative Evaluation**: Performance comparison with manual calendar entry methods
- **Feedback Integration**: Iterative design based on user feedback

### **Academic Research**
- **Literature Review**: PDF processing techniques, calendar integration patterns, educational technology
- **Original Contributions**: Novel approaches to academic schedule automation
- **Technical Documentation**: Comprehensive system architecture and implementation details

---

## Weekly Meetings

The student will meet weekly with Prof. Meneses (schedule TBD) to review:
- **Technical Progress**: Milestone completion and code quality
- **Research Direction**: Literature review and methodology refinement
- **Architecture Decisions**: System design choices and trade-offs
- **Documentation**: Code documentation, technical writing, and presentation preparation
- **Testing Strategy**: User testing protocols and evaluation metrics

---

## Final Deliverables

### **Technical Deliverables**
- Complete SchedShare web application (publicly accessible at schedshare.chrislawrence.ca)
- Production-ready deployment with CI/CD pipeline
- Comprehensive test suite and documentation
- Performance benchmarks and optimization results

### **Research Deliverables**
- **Final Project Report** (50+ pages) documenting:
  - Problem domain analysis and literature review
  - Technical architecture and implementation details
  - User research methodology and results
  - Performance analysis and optimization strategies
  - Security assessment and best practices implementation
  - Limitations, future work, and research contributions
- **Technical Documentation**: API documentation, deployment guides, user manuals
- **Code Repository**: Well-documented, version-controlled source code on GitHub

### **Academic Deliverables**
- **Oral Defense**: Technical demonstration and research presentation
- **Research Poster**: Visual representation of project contributions
- **Publication-Ready Paper**: Academic paper suitable for conference submission

---

## Research Contributions

### **Original Technical Contributions**
- Novel approach to academic schedule PDF parsing and calendar integration
- Implementation of secure OAuth2 flow for educational applications
- Development of scalable cloud architecture for academic tools
- Integration of multiple calendar platforms with unified interface

### **Academic Value**
- **Software Engineering**: Demonstration of full-stack development with modern practices
- **System Architecture**: Cloud-native design with container orchestration
- **Human-Computer Interaction**: User experience design for educational workflows
- **DevOps**: Production deployment and CI/CD pipeline implementation

### **Industry Relevance**
- **API Integration**: Real-world experience with Google Calendar API and OAuth2
- **Cloud Computing**: Practical experience with Google Cloud Platform
- **Security**: Implementation of production-grade security practices
- **Scalability**: Design and testing of scalable web applications

---

## Additional Notes

- **Version Control**: Complete project hosted on GitHub with comprehensive commit history
- **Deployment**: Production deployment on personal domain with SSL certification
- **Security**: Adherence to OWASP security guidelines and privacy best practices
- **Documentation**: Comprehensive technical documentation suitable for academic review
- **Testing**: Automated testing pipeline with user acceptance testing protocols
- **Research Ethics**: IRB approval for user testing with proper consent procedures

