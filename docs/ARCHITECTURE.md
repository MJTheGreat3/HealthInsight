# System Architecture

## Overview

HealthInsight is a modern, microservices-based medical report analysis platform built with a React frontend, FastAPI backend, and MongoDB database. The system leverages AI for intelligent report analysis and provides secure, role-based access to medical data. It serves as the foundation for a comprehensive health information management system.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                          Client Layer                           │
├─────────────────────────────────────────────────────────────────┤
│  React Frontend (Port 5173)                                    │
│  ├── Authentication (Firebase Auth)                            │
│  ├── Patient Dashboard                                         │
│  ├── Hospital Dashboard                                        │
│  ├── Report Upload & Visualization                             │
│  └── Real-time Charts (Chart.js)                              │
└─────────────────────────────────────────────────────────────────┘
                                │
                                │ HTTPS/REST API
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                        API Gateway Layer                        │
├─────────────────────────────────────────────────────────────────┤
│  FastAPI Backend (Port 8000)                                   │
│  ├── Authentication Middleware (Firebase JWT)                  │
│  ├── CORS Middleware                                          │
│  ├── File Upload Middleware                                   │
│  └── Error Handling Middleware                                │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Business Logic Layer                      │
├─────────────────────────────────────────────────────────────────┤
│  API Routers                                                   │
│  ├── User Management (/user)                                  │
│  ├── Report Management (/api/reports)                         │
│  ├── AI Analysis (/api/llm-reports)                          │
│  ├── Dashboard (/dashboard)                                   │
│  ├── Access Control (/access)                                │
│  └── Hospital Management (/hospital)                          │
└─────────────────────────────────────────────────────────────────┘
                                │
                    ┌───────────┼───────────┐
                    ▼           ▼           ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│   Data Storage  │ │   AI Services   │ │   Database      │
│                 │ │                 │ │                 │
│ Temporary PDF   │ │ Google Gemini   │ │ MongoDB         │
│ Processing      │ │ ├── Text        │ │ ├── Users       │
│ (Files          │ │ │   Analysis    │ │ ├── Reports     │
│  Discarded)     │ │ ├── Medical     │ │ ├── LLMReports  │
│                 │ │ │   Insights    │ │ └── Access      │
│                 │ │ └── Trends      │ │     Requests    │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

## Component Architecture

### Frontend Architecture (React)

```
src/
├── components/           # Reusable UI components
│   ├── AnalysisCard.jsx     # AI analysis display
│   ├── ChartWidget.jsx      # Data visualization
│   ├── ChatButton.jsx       # Support interface
│   └── EditReportTable.jsx  # Report editing
├── pages/               # Route-based page components
│   ├── Dashboard.jsx        # Patient main dashboard
│   ├── HospitalDashboard.jsx # Provider dashboard
│   ├── Login.jsx           # Authentication
│   ├── Profile.jsx         # User profile management
│   ├── UploadReport.jsx    # File upload interface
│   └── ReportVisualization.jsx # Charts and trends
├── auth/                # Authentication logic
│   ├── AuthContext.jsx     # Global auth state
│   ├── ProtectedRoute.jsx  # Route protection
│   └── useAuth.js         # Auth hooks
├── hooks/               # Custom React hooks
├── utils/               # Utility functions
└── firebase/            # Firebase configuration
```

**Key Frontend Patterns:**

- **Context API**: Global state management for authentication
- **Custom Hooks**: Reusable logic for API calls and auth
- **Protected Routes**: Role-based route access control
- **Component Composition**: Modular, reusable UI components
- **Error Boundaries**: Graceful error handling

### Backend Architecture (FastAPI)

```
src/
├── routers/             # API endpoint definitions
│   ├── user.py             # User management endpoints
│   ├── report.py           # Report CRUD operations
│   ├── llmReport.py        # AI analysis endpoints
│   ├── dashboard.py        # Dashboard data endpoints
│   ├── access.py           # Access control endpoints
│   └── __init__.py
├── auth/                # Authentication & authorization
│   ├── dependencies.py     # Auth dependency injection
│   └── firebase.py        # Firebase JWT verification
├── core/                # Core configuration
│   └── config.py          # Application settings
├── db/                  # Database layer
│   └── mongoWrapper.py    # MongoDB async operations
├── utils/               # Utility functions
│   ├── file_handler.py    # File processing
│   ├── fast_ocr.py       # OCR processing
│   └── progress_tracker.py # Upload progress
├── schemas.py           # Pydantic data models
├── llm_agent.py        # AI analysis engine
└── main.py             # FastAPI application
```

**Key Backend Patterns:**

- **Dependency Injection**: Clean separation of concerns
- **Repository Pattern**: Database abstraction layer
- **Service Layer**: Business logic separation
- **Middleware Pattern**: Cross-cutting concerns (auth, CORS, etc.)
- **Factory Pattern**: Configuration and service creation

## Data Flow Architecture

### 1. User Authentication Flow

```
User Login Request
       │
       ▼
Firebase Authentication
       │
       ▼
JWT Token Generation
       │
       ▼
Frontend Token Storage
       │
       ▼
API Request with Bearer Token
       │
       ▼
Backend JWT Verification
       │
       ▼
User Context Injection
       │
       ▼
Protected Resource Access
```

### 2. Report Upload and Analysis Flow

```
PDF File Upload
       │
       ▼
File Validation & Temporary Storage
       │
       ▼
OCR Text Extraction (PyMuPDF + Tesseract)
       │
       ▼
CSV Data Parsing
       │
       ▼
Database Storage (Reports Collection)
       │
       ▼
File Deletion (Original PDF Discarded)
       │
       ▼
AI Analysis Request (Google Gemini)
       │
       ▼
Analysis Storage (LLMReports Collection)
       │
       ▼
Response with Analysis Results
       │
       ▼
Frontend Display & Visualization
```

### 3. Data Visualization Flow

```
Chart Request (Patient ID + Attribute)
       │
       ▼
Database Query (Multiple Reports)
       │
       ▼
Data Aggregation & Filtering
       │
       ▼
Trend Analysis
       │
       ▼
JSON Response (Time Series Data)
       │
       ▼
Chart.js Rendering
       │
       ▼
Interactive Chart Display
```

## Database Schema

### Collections Overview

```
MongoDB Database: healthinsight
├── Users                 # User profiles and preferences
├── Reports              # Medical test reports (extracted data only)
├── LLMReports          # AI analysis results
└── AccessRequests      # Hospital access requests
```

### Detailed Schema

#### Users Collection

```javascript
{
  _id: ObjectId,
  uid: String,              // Firebase UID
  email: String,            // User email
  user_type: String,        // "patient" | "institution"
  name: String,             // Display name
  hospital_name: String,    // For institutions only
  BioData: {               // Patient metadata
    age: Number,
    gender: String,
    medical_history: Array
  },
  Favorites: Array,        // Preferred health markers
  Reports: Array,          // Report IDs (deprecated)
  created_at: Date,
  updated_at: Date
}
```

#### Reports Collection

```javascript
{
  _id: ObjectId,
  Report_id: String,       // Unique report identifier
  Patient_id: String,      // Patient UID
  Processed_at: String,    // ISO timestamp
  Attributes: {            // Test results (extracted from PDF)
    test_1: {
      name: String,        // Test name
      value: String,       // Test value
      unit: String,        // Measurement unit
      range: String,       // Reference range
      remark: String       // Additional notes
    }
  },
  llm_report_id: String,   // Reference to AI analysis
  created_at: Date
}
```

#### LLMReports Collection

```javascript
{
  _id: ObjectId,
  patient_id: String,      // Patient UID
  report_id: String,       // Original report ID
  time: String,            // Analysis timestamp
  output: {                // AI analysis results
    interpretation: String,     // Summary interpretation
    lifestyle_changes: Array,   // Lifestyle recommendations
    nutritional_changes: Array, // Nutrition recommendations
    symptom_probable_cause: String, // Symptom analysis
    next_steps: Array,         // Recommended actions
    concern_options: Array     // Areas of concern
  },
  input: Object,           // Original test data
  created_at: Date
}
```

#### AccessRequests Collection

```javascript
{
  _id: ObjectId,
  patient_email: String,   // Patient email
  hospital_uid: String,    // Hospital UID
  hospital_name: String,   // Hospital display name
  message: String,         // Request message
  status: String,          // "pending" | "approved" | "denied"
  created_at: Date,
  updated_at: Date
}
```

## Security Architecture

### Authentication & Authorization

```
┌─────────────────────────────────────────────────────────────────┐
│                    Security Layers                              │
├─────────────────────────────────────────────────────────────────┤
│  1. Firebase Authentication                                     │
│     ├── Email/Password Authentication                           │
│     ├── JWT Token Generation                                   │
│     └── Token Refresh Management                               │
│                                                                │
│  2. Backend Authorization                                       │
│     ├── JWT Token Verification                                 │
│     ├── User Context Injection                                │
│     └── Role-Based Access Control                             │
│                                                                │
│  3. Database Security                                          │
│     ├── Connection String Encryption                           │
│     ├── User-Based Data Isolation                             │
│     └── Query Parameter Validation                            │
│                                                                │
│  4. API Security                                               │
│     ├── CORS Configuration                                     │
│     ├── Request Rate Limiting                                 │
│     ├── Input Validation (Pydantic)                          │
│     └── File Upload Restrictions                              │
│                                                                │
│  5. Data Privacy                                               │
│     ├── Temporary File Processing                             │
│     ├── Immediate File Deletion                               │
│     └── Data Minimization                                     │
└─────────────────────────────────────────────────────────────────┘
```

### Data Privacy Controls

1. **Patient Data Isolation**: Each patient can only access their own data
2. **Hospital Access Control**: Hospitals require explicit patient approval
3. **Audit Logging**: All data access is logged for compliance
4. **Data Encryption**: Sensitive data encrypted at rest and in transit
5. **File Security**: Uploaded files are processed and immediately discarded
6. **Data Minimization**: Only extracted medical data is retained

## AI/ML Architecture

### LLM Integration Pipeline

```
Medical Report Data
       │
       ▼
Data Preprocessing
├── Text Cleaning
├── Format Standardization
└── Validation
       │
       ▼
Google Gemini API
├── Prompt Engineering
├── Context Injection
└── Response Processing
       │
       ▼
Analysis Post-Processing
├── JSON Validation
├── Safety Filtering
└── Confidence Scoring
       │
       ▼
Structured Analysis Output
├── Health Interpretation
├── Lifestyle Recommendations
├── Nutritional Advice
└── Next Steps
```

### OCR Processing Pipeline

```
PDF Upload
       │
       ▼
PyMuPDF Text Extraction
       │
       ├── Success ──────────┐
       │                     │
       ▼                     │
Tesseract OCR Fallback       │
       │                     │
       └─────────────────────┘
                             │
                             ▼
                    Text Preprocessing
                             │
                             ▼
                    CSV Structure Detection
                             │
                             ▼
                    Medical Data Extraction
                             │
                             ▼
                    Structured Data Output
                             │
                             ▼
                    File Deletion (PDF Discarded)
```

## Performance Architecture

### Caching Strategy

```
┌─────────────────────────────────────────────────────────────────┐
│                      Caching Layers                             │
├─────────────────────────────────────────────────────────────────┤
│  Browser Cache                                                 │
│  ├── Static Assets (CSS, JS, Images)                          │
│  ├── API Response Cache (Short TTL)                           │
│  └── Authentication Tokens                                    │
│                                                                │
│  CDN Cache (Production)                                        │
│  ├── Static Frontend Assets                                   │
│  ├── Public API Responses                                     │
│  └── Image Assets                                             │
│                                                                │
│  Application Cache                                             │
│  ├── Database Query Results                                   │
│  ├── AI Analysis Results                                      │
│  └── User Session Data                                        │
│                                                                │
│  Database Indexes                                              │
│  ├── User UID Index                                           │
│  ├── Report ID Index                                          │
│  └── Patient ID Index                                         │
└─────────────────────────────────────────────────────────────────┘
```

### Scalability Considerations

1. **Horizontal Scaling**: Stateless backend design allows multiple instances
2. **Database Sharding**: MongoDB supports horizontal partitioning
3. **CDN Integration**: Static assets served from edge locations
4. **Async Processing**: Non-blocking I/O for file processing and AI calls
5. **Load Balancing**: Multiple backend instances behind load balancer
6. **File Processing Optimization**: Temporary processing reduces storage overhead

## Deployment Architecture

### Container Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Docker Containers                            │
├─────────────────────────────────────────────────────────────────┤
│  Frontend Container (nginx:alpine)                             │
│  ├── React Build Output                                        │
│  ├── Nginx Configuration                                       │
│  └── SSL Certificates                                          │
│                                                                │
│  Backend Container (python:3.11-slim)                         │
│  ├── FastAPI Application                                       │
│  ├── Python Dependencies                                       │
│  ├── OCR Libraries                                            │
│  └── File Processing Tools                                     │
│                                                                │
│  Database Container (mongo:7.0)                               │
│  ├── MongoDB Server                                           │
│  ├── Data Persistence Volume                                  │
│  └── Backup Scripts                                           │
│                                                                │
│  Monitoring Container (Optional)                               │
│  ├── MongoDB Express UI                                       │
│  ├── Log Aggregation                                          │
│  └── Health Check Dashboard                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Network Architecture

```
Internet
    │
    ▼
Load Balancer / Reverse Proxy (nginx)
    │
    ├── /api/* ──────────► Backend Container(s)
    │                           │
    ├── /docs ───────────► API Documentation
    │                           │
    └── /* ──────────────► Frontend Container
                                │
                                ▼
                        Internal Network
                                │
                                ├── MongoDB Container
                                ├── Temporary Processing Space
                                └── Monitoring Services
```

## Integration Architecture

### External Service Integrations

```
┌─────────────────────────────────────────────────────────────────┐
│                  External Integrations                          │
├─────────────────────────────────────────────────────────────────┤
│  Firebase Services                                              │
│  ├── Authentication (JWT Tokens)                               │
│  ├── User Management                                           │
│  └── Security Rules                                            │
│                                                                │
│  Google AI Services                                            │
│  ├── Gemini API (Text Analysis)                               │
│  ├── Rate Limiting                                            │
│  └── Error Handling                                           │
│                                                                │
│  File Processing Services                                       │
│  ├── PyMuPDF (PDF Processing)                                 │
│  ├── Tesseract OCR                                           │
│  └── Image Processing Libraries                               │
└─────────────────────────────────────────────────────────────────┘
```

## Monitoring and Observability

### Logging Architecture

```
Application Logs
       │
       ▼
Structured Logging (JSON)
       │
       ├── Error Logs ──────────► Error Tracking Service
       ├── Access Logs ─────────► Analytics Dashboard
       ├── Performance Logs ────► Performance Monitoring
       └── Audit Logs ─────────► Compliance Reporting
```

### Health Check Architecture

```
Health Check Endpoints
├── /api/ping ──────────► Basic API Health
├── /api/db-test ───────► Database Connectivity
├── /health ────────────► Overall System Health
└── /metrics ───────────► Performance Metrics
```

## Future Architecture Considerations

### Planned Enhancements for Health Information Management System

1. **Microservices Migration**: Split monolithic backend into focused services

   - **Prescription Service**: Medication management and tracking
   - **Medical History Service**: Comprehensive patient history
   - **Appointment Service**: Scheduling and calendar management
   - **Notification Service**: Alerts and reminders

2. **Event-Driven Architecture**: Implement message queues for async processing

   - **Health Event Streaming**: Real-time health data processing
   - **Care Coordination Events**: Multi-provider communication
   - **Medication Adherence Events**: Smart reminder system

3. **Advanced Data Management**: Enhanced storage and processing

   - **FHIR Compliance**: Healthcare data interoperability
   - **Data Lake Integration**: Population health analytics
   - **Real-time Sync**: Multi-device data synchronization

4. **Enhanced Security**: Advanced privacy and compliance features

   - **HIPAA Compliance**: Healthcare data protection
   - **Audit Trail Enhancement**: Comprehensive access logging
   - **Zero-Trust Architecture**: Enhanced security model

5. **AI/ML Expansion**: Advanced analytics and predictions
   - **Predictive Health Analytics**: Early warning systems
   - **Clinical Decision Support**: AI-powered recommendations
   - **Population Health Insights**: Aggregate health trends

### Scalability Roadmap

1. **Phase 1**: Current architecture with optimized file processing
2. **Phase 2**: Database optimization and advanced caching
3. **Phase 3**: Microservices decomposition for health management
4. **Phase 4**: Event-driven architecture with real-time processing
5. **Phase 5**: Multi-region deployment with global health data sync
