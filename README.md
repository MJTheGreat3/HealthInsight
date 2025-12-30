# HealthInsight

A comprehensive medical test analysis web application that enables patients to upload and analyze their medical test results while providing healthcare providers with patient management capabilities.

## 🏥 Overview

HealthInsight is a full-stack medical report analysis platform that combines AI-powered health insights with secure patient data management. The system allows patients to upload PDF medical reports, receive intelligent analysis, and track health trends over time, while enabling healthcare institutions to manage patient data with proper access controls.

HealthInsight is designed as the foundation for a complete health information management system, designed to expand beyond test results to encompass prescriptions, medical history, treatment plans, and comprehensive patient care coordination.

## ✨ Key Features

### Patient Portal

- **PDF Report Upload**: Secure upload and OCR processing of medical test reports
- **AI-Powered Analysis**: Gemini AI provides personalized health insights and recommendations
- **Health Trends**: Interactive charts showing biomarker trends over time
- **Favorites System**: Track important health metrics and receive targeted advice
- **Access Management**: Control which healthcare providers can view your data

### Healthcare Provider Dashboard

- **Patient Management**: View approved patients and their complete health profiles
- **Comprehensive Reports**: Access to patient test results and AI analysis
- **Trend Analysis**: Monitor patient health progression over time
- **Secure Access**: Role-based access with patient consent requirements

### AI Analysis Engine

- **Intelligent OCR**: Advanced PDF text extraction with PyMuPDF and OCR fallback
- **LLM Integration**: Google Gemini AI for medical report interpretation
- **Personalized Recommendations**: Lifestyle and nutritional advice based on test results
- **Trend Detection**: Multi-report analysis for health pattern identification

## 🛠 Technology Stack

### Backend Architecture

- **FastAPI**: Modern Python web framework with automatic API documentation
- **MongoDB**: NoSQL database with Motor async driver for scalability
- **Firebase Authentication**: Secure user authentication and authorization
- **Google Gemini AI**: Advanced language model for medical analysis
- **PyMuPDF**: High-performance PDF processing and text extraction
- **OCR Integration**: Fallback OCR for complex PDF layouts

### Frontend Architecture

- **React 18**: Modern React with hooks and functional components
- **Vite**: Lightning-fast development server and build tool
- **Chart.js**: Interactive data visualization for health trends
- **Lucide React**: Beautiful, consistent icon system
- **CSS Modules**: Scoped styling with modern CSS features

### Infrastructure

- **Docker**: Containerized deployment with multi-stage builds
- **Docker Compose**: Orchestrated services for development and production
- **MongoDB**: Persistent data storage with automatic backups
- **Nginx**: Production-ready reverse proxy and static file serving

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)

### Environment Configuration

1. **Copy environment templates:**

```bash
cp .env.example .env
cp backend/.env.example backend/.env
```

2. **Configure environment variables:**

**Root `.env` file:**

```bash
# MongoDB Configuration
MONGODB_URL=mongodb://admin:password@localhost:27017/healthinsight?authSource=admin
DATABASE_NAME=healthinsight

# Firebase Configuration (get from Firebase Console)
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nYOUR_PRIVATE_KEY_HERE\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=firebase-adminsdk-xxxxx@your-project-id.iam.gserviceaccount.com

# Frontend Firebase Configuration
VITE_FIREBASE_API_KEY=your-api-key
VITE_FIREBASE_AUTH_DOMAIN=your-project-id.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your-project-id

# AI Configuration
GEMINI_API_KEY=your-gemini-api-key-here
```

**Backend `.env` file:**

```bash
# MongoDB Configuration
MONGO_URI=mongodb://admin:password123@mongodb:27017
MONGO_DB=healthinsight

# Gemini AI Configuration
GEMINI_API_KEY=your_gemini_api_key_here

# File Processing Configuration
MAX_FILE_SIZE=10485760

# App Configuration
APP_NAME=HealthInsight Medical Reports
VERSION=1.0.0
```

### 🐳 Docker Deployment (Recommended)

The project includes a convenient startup script for easy deployment:

```bash
# Make the script executable
chmod +x start.sh

# Start development environment (with hot reload)
./start.sh dev

# Start production environment
./start.sh prod

# View logs
./start.sh logs

# Stop all services
./start.sh stop

# Clean up (removes all data)
./start.sh clean
```

**Manual Docker commands:**

```bash
# Development with hot reload
docker-compose --profile dev up --build

# Production deployment
docker-compose up --build -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### 💻 Local Development

**Backend Setup:**

```bash
cd backend
pip install -r requirements.txt
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend Setup:**

```bash
cd frontend
npm install
npm run dev
```

### 🌐 Access Points

After deployment, access the application at:

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **MongoDB UI** (dev mode): http://localhost:8081

## 📁 Project Structure

```
healthinsight/
├── 📁 backend/                    # FastAPI Backend
│   ├── 📁 src/
│   │   ├── 📁 auth/              # Authentication & authorization
│   │   │   ├── dependencies.py    # Auth dependencies
│   │   │   └── firebase.py       # Firebase integration
│   │   ├── 📁 core/              # Core configuration
│   │   │   └── config.py         # App settings
│   │   ├── 📁 db/                # Database layer
│   │   │   └── mongoWrapper.py   # MongoDB async wrapper
│   │   ├── 📁 routers/           # API endpoints
│   │   │   ├── access.py         # Access control endpoints
│   │   │   ├── dashboard.py      # Dashboard data endpoints
│   │   │   ├── llmReport.py      # AI analysis endpoints
│   │   │   ├── report.py         # Report management endpoints
│   │   │   └── user.py           # User management endpoints
│   │   ├── 📁 utils/             # Utility functions
│   │   │   ├── fast_ocr.py       # OCR processing
│   │   │   ├── file_handler.py   # File operations
│   │   │   └── progress_tracker.py # Upload progress
│   │   ├── llm_agent.py          # AI analysis engine
│   │   ├── main.py               # FastAPI application
│   │   └── schemas.py            # Pydantic models
│   ├── requirements.txt          # Python dependencies
│   ├── Dockerfile               # Backend container
│   └── explore_db.py            # Database exploration tool
├── 📁 frontend/                  # React Frontend
│   ├── 📁 src/
│   │   ├── 📁 auth/             # Authentication components
│   │   │   ├── AuthContext.jsx  # Auth state management
│   │   │   ├── ProtectedRoute.jsx # Route protection
│   │   │   └── useAuth.js       # Auth hooks
│   │   ├── 📁 components/       # Reusable UI components
│   │   │   ├── AnalysisCard.jsx # AI analysis display
│   │   │   ├── ChartWidget.jsx  # Data visualization
│   │   │   ├── ChatButton.jsx   # Support chat
│   │   │   └── EditReportTable.jsx # Report editing
│   │   ├── 📁 firebase/         # Firebase configuration
│   │   │   └── firebase.js      # Firebase setup
│   │   ├── 📁 hooks/            # Custom React hooks
│   │   │   └── useAuthRedirect.js # Auth redirect logic
│   │   ├── 📁 pages/            # Page components
│   │   │   ├── Dashboard.jsx    # Patient dashboard
│   │   │   ├── HospitalDashboard.jsx # Provider dashboard
│   │   │   ├── Login.jsx        # Authentication
│   │   │   ├── Profile.jsx      # User profile
│   │   │   ├── UploadReport.jsx # Report upload
│   │   │   └── ReportVisualization.jsx # Data charts
│   │   ├── 📁 utils/            # Utility functions
│   │   │   └── api.js           # API configuration
│   │   ├── App.jsx              # Main application
│   │   └── main.jsx             # React entry point
│   ├── package.json             # Node.js dependencies
│   ├── vite.config.js          # Vite configuration
│   └── Dockerfile              # Frontend container
├── 📁 Reports/                  # Sample report files
├── docker-compose.yml          # Production orchestration
├── docker-compose.dev.yml      # Development overrides
├── start.sh                    # Deployment script
└── README.md                   # This documentation
```

## 🔧 API Documentation

### Authentication Endpoints

- `POST /user` - User registration/onboarding
- `GET /auth/me` - Get current user info
- `GET /user/me` - Get detailed user profile
- `PATCH /user/me` - Update user profile

### Report Management

- `POST /api/reports/upload` - Upload PDF report (data extracted and stored, file discarded)
- `POST /api/reports/upload-and-analyze` - Upload and auto-analyze
- `GET /api/reports/{report_id}` - Get specific report
- `GET /api/reports/patient/{patient_id}` - Get patient reports
- `DELETE /api/reports/{report_id}` - Delete report
- `PATCH /api/reports/{report_id}/attribute-by-name` - Update test values

### AI Analysis

- `GET /api/llm-reports/{report_id}` - Get AI analysis
- `POST /api/llm-reports/analyze` - Generate new analysis
- `GET /dashboard/actionable-suggestions` - Get health recommendations

### Data Visualization

- `GET /api/draw_graph/{patient_id}/{attribute}` - Get trend data for charts

### Access Control

- `POST /access/request` - Request patient data access
- `GET /access/requests` - List access requests
- `PATCH /access/requests/{request_id}` - Approve/deny access

### Hospital Management

- `GET /hospital/patients` - List approved patients
- `GET /hospital/patient/{patient_uid}` - Get patient details

## 🤖 AI Analysis Features

### Report Processing Pipeline

1. **PDF Upload**: Secure file validation and temporary processing
2. **OCR Extraction**: PyMuPDF with OCR fallback for text extraction
3. **Data Parsing**: Intelligent extraction of test names, values, units, and ranges
4. **Data Storage**: Structured medical data stored in MongoDB (original file discarded)
5. **AI Analysis**: Gemini AI processes medical data for insights
6. **Recommendation Generation**: Personalized lifestyle and nutritional advice

### AI Capabilities

- **Medical Report Interpretation**: Understands lab values and clinical significance
- **Trend Analysis**: Identifies patterns across multiple reports
- **Personalized Recommendations**: Tailored advice based on user preferences
- **Risk Assessment**: Flags concerning values and suggests next steps
- **Nutritional Guidance**: Specific dietary recommendations for health optimization

## 🔒 Security Features

### Authentication & Authorization

- **Firebase Authentication**: Industry-standard user authentication
- **JWT Token Validation**: Secure API access with token verification
- **Role-Based Access**: Separate permissions for patients and healthcare providers
- **Session Management**: Secure session handling with automatic expiration

### Data Protection

- **Encrypted Storage**: All sensitive data encrypted at rest
- **Secure File Processing**: Files processed and discarded, only extracted data retained
- **Access Logging**: Comprehensive audit trail for data access
- **CORS Protection**: Configured cross-origin resource sharing
- **Input Validation**: Comprehensive data validation and sanitization

### Privacy Controls

- **Patient Consent**: Explicit approval required for data sharing
- **Data Minimization**: Only necessary data collected and stored
- **Right to Deletion**: Complete data removal capabilities
- **Access Transparency**: Clear visibility into who accessed what data

## 🔮 Future Roadmap

HealthInsight is designed as the foundation for a comprehensive health information management system. Planned expansions include:

### Phase 1: Enhanced Medical Records

- **Prescription Management**: Digital prescription tracking and medication adherence
- **Medical History**: Comprehensive patient medical history management
- **Treatment Plans**: Care plan creation and monitoring
- **Appointment Scheduling**: Integrated healthcare provider scheduling

### Phase 2: Advanced Health Management

- **Vital Signs Tracking**: Integration with wearable devices and manual entry
- **Symptom Logging**: Patient-reported outcome measures (PROMs)
- **Medication Reminders**: Smart notification system for medication adherence
- **Health Goals**: Personalized health goal setting and tracking

### Phase 3: Provider Collaboration

- **Multi-Provider Access**: Seamless data sharing between healthcare providers
- **Referral Management**: Digital referral system with progress tracking
- **Care Team Coordination**: Multi-disciplinary team communication platform
- **Clinical Decision Support**: AI-powered clinical recommendations

### Phase 4: Population Health

- **Health Analytics**: Population-level health insights and reporting
- **Preventive Care**: Proactive health screening and prevention programs
- **Research Integration**: Anonymized data contribution to medical research
- **Public Health Reporting**: Integration with public health surveillance systems

## 🚀 Deployment Guide

### Production Deployment

1. **Server Requirements:**

   - 2+ CPU cores
   - 4GB+ RAM
   - 20GB+ storage
   - Docker and Docker Compose installed

2. **Environment Setup:**

   ```bash
   # Clone repository
   git clone <repository-url>
   cd healthinsight

   # Configure environment
   cp .env.example .env
   cp backend/.env.example backend/.env
   # Edit .env files with production values

   # Deploy
   ./start.sh prod
   ```

3. **SSL Configuration:**
   - Configure reverse proxy (nginx/Apache)
   - Install SSL certificates
   - Update CORS origins in backend configuration

### Monitoring & Maintenance

- **Health Checks**: Built-in health check endpoints
- **Log Management**: Centralized logging with Docker
- **Database Backups**: Automated MongoDB backup scripts
- **Performance Monitoring**: API response time tracking
- **Error Tracking**: Comprehensive error logging and alerting

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes** following the coding standards
4. **Commit your changes**: `git commit -m 'Add amazing feature'`
5. **Push to the branch**: `git push origin feature/amazing-feature`
6. **Open a Pull Request**

### Development Guidelines

- Follow PEP 8 for Python code
- Use ESLint configuration for JavaScript/React
- Update documentation for API changes
- Ensure Docker builds pass before submitting

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:

- Create an issue in the GitHub repository
- Check the API documentation at `/docs`
- Review the troubleshooting section below

## 🔧 Troubleshooting

### Common Issues

**Database Connection Failed:**

```bash
# Check MongoDB container status
docker-compose ps mongodb

# View MongoDB logs
docker-compose logs mongodb
```

**AI Analysis Not Working:**

```bash
# Verify Gemini API key
echo $GEMINI_API_KEY

# Check backend logs
docker-compose logs backend
```

**File Processing Issues:**

```bash
# Check backend logs for OCR errors
docker-compose logs backend

# Verify file size limits in configuration
```

**Frontend Build Errors:**

```bash
# Clear node modules and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
```
