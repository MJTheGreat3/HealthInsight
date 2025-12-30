# HealthInsight

A comprehensive medical test analysis web application that enables patients to upload and analyze their medical test results while providing healthcare providers with patient management capabilities.

## 🏥 Overview

HealthInsightCore is a full-stack medical report analysis platform that combines AI-powered health insights with secure patient data management. The system allows patients to upload PDF medical reports, receive intelligent analysis through AI, and track health trends over time, while enabling healthcare institutions to manage patient data with proper access controls.

The platform processes PDF reports by extracting medical test data (without storing the original files), provides personalized health recommendations, and includes an interactive chatbot for health-related conversations based on your complete medical history.

## ✨ Key Features

### Patient Portal

- **PDF Report Upload**: Secure upload and processing of medical test reports (original files are discarded after data extraction)
- **AI-Powered Analysis**: AI provides personalized health insights and lifestyle recommendations
- **Interactive Chatbot**: Context-aware chatbot with access to your complete medical history for personalized health conversations
- **Health Trends**: Interactive charts showing biomarker trends over time with fuzzy matching for test names
- **Tracked Metrics Management**: Select concerning results to actively track over time with trend analysis
- **Profile Management**: Manage personal information (height, weight, allergies) for personalized AI analysis

### Healthcare Provider Dashboard

- **Patient Management**: Searchable table of all registered patients with complete health profiles
- **Comprehensive Reports**: Access to patient test results and AI analysis (with patient consent)
- **Patient Dashboard View**: Complete patient data view including reports, tracked metrics, and profile information
- **Access Control**: Role-based access with proper authentication and audit logging

### AI Analysis Engine

- **Intelligent PDF Processing**: PyMuPDF with OCR fallback for text extraction from medical reports
- **LLM Integration**: AI for medical report interpretation with structured output
- **Interactive Chatbot**: Context-aware conversational AI with access to complete patient medical history
- **Personalized Recommendations**: Lifestyle and nutritional advice based on test results and user profile
- **Multi-Report Analysis**: Cross-report trend detection and actionable health suggestions
- **Safety Filters**: Avoids medical prescriptions and inappropriate medical advice

## 🛠 Technology Stack

### Backend Architecture

- **FastAPI**: Modern Python web framework with automatic API documentation
- **MongoDB**: NoSQL database with Motor async driver for scalability
- **Firebase Authentication**: Secure user authentication and authorization
- **AI Integration**: LLM integration for medical report interpretation
- **PyMuPDF**: High-performance PDF processing and text extraction
- **WebSocket Support**: Real-time communication for chat and synchronization

### Frontend Architecture

- **React 18**: Modern React with hooks and functional components
- **TypeScript**: Type safety and enhanced development experience
- **Vite**: Lightning-fast development server and build tool
- **Chart.js**: Interactive data visualization for health trends
- **Tailwind CSS**: Utility-first CSS framework for styling
- **React Router v6**: Client-side routing with protected routes

### Infrastructure

- **Docker**: Containerized deployment with multi-stage builds
- **Docker Compose**: Orchestrated services for development and production
- **MongoDB**: Persistent data storage
- **Firebase Auth**: Authentication service integration

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

**Backend `.env` file:**

```bash
# MongoDB Configuration
MONGO_URI=mongodb://admin:password123@mongodb:27017
MONGO_DB=healthinsight

# Google Gemini AI Configuration
GEMINI_API_KEY=your_gemini_api_key_here

# Firebase Admin Configuration (path to service account JSON)
FIREBASE_ADMIN_KEY=./firebase-admin.json

# File Processing Configuration
MAX_FILE_SIZE=10485760

# App Configuration
APP_NAME=HealthInsight Medical Reports
VERSION=1.0.0
```

**Frontend `.env` file:**

```bash
# Firebase Configuration (get from Firebase Console)
VITE_FIREBASE_API_KEY=your-api-key
VITE_FIREBASE_AUTH_DOMAIN=your-project-id.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your-project-id
VITE_FIREBASE_STORAGE_BUCKET=your-project-id.appspot.com
VITE_FIREBASE_MESSAGING_SENDER_ID=your-sender-id
VITE_FIREBASE_APP_ID=your-app-id
```

### 🐳 Docker Deployment (Recommended)

```bash
# Start all services
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

## 📁 Project Structure

```
healthinsight/
├── 📁 .kiro/                      # Kiro configuration and specs
│   └── 📁 specs/
│       └── 📁 health-insight-core/
│           ├── requirements.md     # Detailed requirements specification
│           ├── design.md          # System design and architecture
│           └── tasks.md           # Implementation plan and tasks
├── 📁 backend/                    # FastAPI Backend
│   ├── 📁 src/
│   │   ├── 📁 auth/              # Authentication & authorization
│   │   │   ├── dependencies.py    # Auth dependencies and middleware
│   │   │   └── firebase.py       # Firebase integration service
│   │   ├── 📁 core/              # Core configuration
│   │   │   └── config.py         # App settings and configuration
│   │   ├── 📁 db/                # Database layer
│   │   │   └── mongoWrapper.py   # MongoDB async wrapper and operations
│   │   ├── 📁 routers/           # API endpoints
│   │   │   ├── access.py         # Access control endpoints
│   │   │   ├── chat.py           # Chat/AI conversation endpoints
│   │   │   ├── dashboard.py      # Dashboard data and analytics endpoints
│   │   │   ├── llmReport.py      # AI analysis endpoints
│   │   │   ├── report.py         # Report management endpoints
│   │   │   └── user.py           # User management endpoints
│   │   ├── 📁 utils/             # Utility functions
│   │   │   ├── fast_ocr.py       # OCR processing utilities
│   │   │   ├── file_handler.py   # File operations and PDF processing
│   │   │   └── progress_tracker.py # Upload progress tracking
│   │   ├── llm_agent.py          # AI analysis engine and LLM integration
│   │   ├── llm_chat.py           # Chat functionality and context management
│   │   ├── main.py               # FastAPI application entry point
│   │   └── schemas.py            # Pydantic models and data validation
│   ├── requirements.txt          # Python dependencies
│   ├── Dockerfile               # Backend container configuration
│   ├── firebase-admin.json      # Firebase service account key
│   └── explore_db.py            # Database exploration and debugging tool
├── 📁 frontend/                  # React Frontend
│   ├── 📁 src/
│   │   ├── 📁 auth/             # Authentication components
│   │   │   ├── AuthContext.jsx  # Auth state management context
│   │   │   ├── ProtectedRoute.jsx # Route protection wrapper
│   │   │   └── useAuth.js       # Authentication hooks
│   │   ├── 📁 components/       # Reusable UI components
│   │   │   ├── AnalysisCard.jsx # AI analysis display component
│   │   │   ├── ChartWidget.jsx  # Data visualization component
│   │   │   ├── ChatButton.jsx   # Chat interface component
│   │   │   └── EditReportTable.jsx # Report editing interface
│   │   ├── 📁 firebase/         # Firebase configuration
│   │   │   └── firebase.js      # Firebase client setup
│   │   ├── 📁 pages/            # Page components
│   │   │   ├── Dashboard.jsx    # Patient dashboard with tracked metrics
│   │   │   ├── HospitalDashboard.jsx # Provider dashboard
│   │   │   ├── Login.jsx        # Authentication page
│   │   │   ├── Profile.jsx      # User profile management
│   │   │   ├── UploadReport.jsx # PDF report upload interface
│   │   │   ├── PreviousReports.jsx # Report history and search
│   │   │   └── AccessRequests.jsx # Access control management
│   │   ├── App.jsx              # Main application component
│   │   └── main.jsx             # React entry point
│   ├── package.json             # Node.js dependencies
│   ├── vite.config.js          # Vite build configuration
│   └── Dockerfile              # Frontend container configuration
├── docker-compose.yml          # Service orchestration
├── setup.sh                    # Environment setup script
├── verify-setup.sh            # Setup verification script
├── README.md                   # Project documentation
└── API_ENDPOINTS.md           # Comprehensive API documentation
```

## 🔧 API Documentation

The complete API documentation is available in [API_ENDPOINTS.md](API_ENDPOINTS.md).

### Key Features

- **Authentication**: Firebase JWT token-based authentication with role-based access control
- **Report Management**: Upload, analyze, and manage medical reports with PDF processing
- **AI Analysis**: Generate health insights using LLM integration with safety filters
- **Chat Interface**: Interactive health conversations based on complete medical history
- **Tracked Metrics**: Patient-selected concerning results with trend analysis over time
- **Access Control**: Hospital-patient data sharing with consent management
- **Real-time Sync**: WebSocket-based real-time updates across all active sessions

### Core Endpoints

- `POST /api/reports/upload-and-analyze` - Upload PDF and get AI analysis
- `GET /api/reports/patient/{patient_id}` - Get patient's reports with history
- `POST /api/chat` - Chat with AI about health reports using medical history context
- `GET /dashboard/actionable-suggestions` - Get personalized health recommendations
- `POST /access/request` - Request patient data access (hospitals)
- `GET /draw_graph/{patient_id}/{attribute}` - Get trend data for tracked metrics

Visit http://localhost:8000/docs for interactive API documentation when running the application.

## 🤖 AI Analysis Features

### Report Processing Pipeline

1. **PDF Upload**: Secure file validation and temporary processing
2. **Text Extraction**: PyMuPDF with OCR fallback for text extraction
3. **Data Parsing**: Intelligent extraction of test names, values, units, and ranges using LLM
4. **Data Storage**: Structured medical data stored in MongoDB (original file discarded for security)
5. **AI Analysis**: LLM processes medical data for comprehensive health insights
6. **Recommendation Generation**: Personalized lifestyle and nutritional advice

### AI Capabilities

- **Medical Report Interpretation**: Understands lab values and clinical significance
- **Structured Output**: JSON format with interpretation, lifestyle changes, nutritional changes, next steps
- **Concern Detection**: Identifies problematic test values for user tracking
- **Multi-Report Analysis**: Cross-report trend analysis for actionable health suggestions
- **Interactive Chat**: Context-aware conversations about your health reports using complete medical history
- **Safety Filters**: Avoids medical prescriptions and inappropriate medical advice
- **Personalized Recommendations**: Tailored advice based on user profile data (height, weight, allergies)

## 🔒 Security Features

### Authentication & Authorization

- **Firebase Authentication**: Industry-standard user authentication with JWT tokens
- **Token Validation**: Secure API access with Firebase Admin SDK token verification
- **Role-Based Access**: Separate permissions for patients and healthcare providers
- **Session Management**: Secure session handling with automatic token expiration

### Data Protection

- **File Security**: PDF files processed and immediately discarded, only extracted data retained
- **Access Logging**: Comprehensive audit trail for data access
- **CORS Protection**: Configured cross-origin resource sharing for localhost and production
- **Input Validation**: Comprehensive data validation and sanitization using Pydantic

### Privacy Controls

- **Patient Consent**: Explicit approval required for healthcare provider data access
- **Data Minimization**: Only necessary medical test data collected and stored
- **Access Transparency**: Clear visibility into who requested and has access to data
- **Granular Control**: Patients can approve, reject, or revoke access at any time

## 🚀 Getting Started

Ready to explore HealthInsight? The platform provides secure medical report analysis with AI-powered insights. Upload your medical reports, get personalized health recommendations, and track your health trends over time.

For healthcare providers, request access to patient data with proper consent management and view comprehensive health analytics for your approved patients.
