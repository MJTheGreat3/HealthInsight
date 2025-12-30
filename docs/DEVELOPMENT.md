# Development Guide

## Getting Started

This guide covers setting up the development environment, coding standards, and contribution guidelines for HealthInsight.

## Prerequisites

### Required Software

- **Node.js**: 18.0+ (LTS recommended)
- **Python**: 3.11+
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **Git**: 2.30+

### Recommended Tools

- **VS Code** with extensions:
  - Python
  - ES7+ React/Redux/React-Native snippets
  - Prettier - Code formatter
  - ESLint
  - Docker
  - MongoDB for VS Code
- **Postman** or **Insomnia** for API testing
- **MongoDB Compass** for database management

## Development Environment Setup

### 1. Clone Repository

```bash
git clone <repository-url>
cd healthinsight
```

### 2. Environment Configuration

Create environment files:

```bash
cp .env.example .env
cp backend/.env.example backend/.env
```

Configure development environment variables:

**Root `.env`:**

```bash
# Development MongoDB
MONGODB_URL=mongodb://admin:password123@localhost:27017/healthinsight_dev?authSource=admin
DATABASE_NAME=healthinsight_dev

# Firebase (use development project)
FIREBASE_PROJECT_ID=your-dev-project-id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nYOUR_DEV_KEY\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=firebase-adminsdk-xxxxx@your-dev-project.iam.gserviceaccount.com

# Frontend Firebase
VITE_FIREBASE_API_KEY=your-dev-api-key
VITE_FIREBASE_AUTH_DOMAIN=your-dev-project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your-dev-project-id

# Development AI key (use with caution)
GEMINI_API_KEY=your-dev-gemini-key
```

**Backend `.env`:**

```bash
# Development database
MONGO_URI=mongodb://admin:password123@mongodb:27017
MONGO_DB=healthinsight_dev

# AI configuration
GEMINI_API_KEY=your-dev-gemini-key

# Development settings
DEBUG=true
RELOAD=true
```

### 3. Development Setup Options

#### Option A: Docker Development (Recommended)

```bash
# Start development environment with hot reload
./start.sh dev

# Or manually:
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

#### Option B: Local Development

**Backend Setup:**

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install black isort flake8

# Run development server
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend Setup:**

```bash
cd frontend

# Install dependencies
npm install

# Install development dependencies
npm install --save-dev @types/node @vitejs/plugin-react eslint prettier

# Start development server
npm run dev
```

**Database Setup (if not using Docker):**

```bash
# Install MongoDB locally
# Ubuntu/Debian:
sudo apt-get install -y mongodb

# macOS:
brew install mongodb-community

# Start MongoDB
sudo systemctl start mongod  # Linux
brew services start mongodb-community  # macOS
```

## Project Structure

### Backend Structure

```
backend/
├── src/
│   ├── auth/                 # Authentication logic
│   │   ├── dependencies.py   # Auth dependencies
│   │   └── firebase.py       # Firebase integration
│   ├── core/                 # Core configuration
│   │   └── config.py         # Settings management
│   ├── db/                   # Database layer
│   │   └── mongoWrapper.py   # MongoDB operations
│   ├── routers/              # API endpoints
│   │   ├── __init__.py
│   │   ├── access.py         # Access control
│   │   ├── dashboard.py      # Dashboard data
│   │   ├── llmReport.py      # AI analysis
│   │   ├── report.py         # Report management
│   │   └── user.py           # User management
│   ├── utils/                # Utility functions
│   │   ├── fast_ocr.py       # OCR processing
│   │   ├── file_handler.py   # File operations
│   │   └── progress_tracker.py
│   ├── llm_agent.py          # AI analysis engine
│   ├── main.py               # FastAPI app
│   └── schemas.py            # Pydantic models
├── requirements.txt          # Dependencies
├── Dockerfile               # Container definition
└── .env.example             # Environment template
```

### Frontend Structure

```
frontend/
├── src/
│   ├── auth/                 # Authentication
│   │   ├── AuthContext.jsx   # Auth state
│   │   ├── ProtectedRoute.jsx
│   │   └── useAuth.js
│   ├── components/           # Reusable components
│   │   ├── AnalysisCard.jsx
│   │   ├── ChartWidget.jsx
│   │   ├── ChatButton.jsx
│   │   └── EditReportTable.jsx
│   ├── firebase/             # Firebase config
│   │   └── firebase.js
│   ├── hooks/                # Custom hooks
│   │   └── useAuthRedirect.js
│   ├── pages/                # Page components
│   │   ├── Dashboard.jsx
│   │   ├── HospitalDashboard.jsx
│   │   ├── Login.jsx
│   │   ├── Profile.jsx
│   │   ├── UploadReport.jsx
│   │   └── ReportVisualization.jsx
│   ├── utils/                # Utilities
│   │   └── api.js
│   ├── App.jsx               # Main app
│   ├── main.jsx              # Entry point
│   └── index.css             # Global styles
├── public/                   # Static assets
├── package.json              # Dependencies
├── vite.config.js           # Vite configuration
└── Dockerfile               # Container definition
```

## Coding Standards

### Python (Backend)

#### Code Style

- Follow **PEP 8** style guide
- Use **Black** for code formatting
- Use **isort** for import sorting
- Maximum line length: 88 characters

#### Setup Pre-commit Hooks

```bash
cd backend
pip install pre-commit black isort flake8
pre-commit install

# Create .pre-commit-config.yaml
cat > .pre-commit-config.yaml << EOF
repos:
  - repo: https://github.com/psf/black
    rev: 22.3.0
    hooks:
      - id: black
        language_version: python3.11
  - repo: https://github.com/pycqa/isort
    rev: 5.10.1
    hooks:
      - id: isort
  - repo: https://github.com/pycqa/flake8
    rev: 4.0.1
    hooks:
      - id: flake8
EOF
```

#### Naming Conventions

```python
# Variables and functions: snake_case
user_id = "123"
def get_user_profile():
    pass

# Classes: PascalCase
class UserModel:
    pass

# Constants: UPPER_SNAKE_CASE
MAX_FILE_SIZE = 10 * 1024 * 1024

# Private methods: _leading_underscore
def _internal_helper():
    pass
```

#### Type Hints

```python
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

def process_report(
    report_id: str,
    patient_data: Dict[str, Any],
    options: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Process medical report with type hints."""
    pass

class ReportModel(BaseModel):
    report_id: str
    patient_id: str
    attributes: Dict[str, Any]
```

#### Error Handling

```python
from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)

async def get_report(report_id: str):
    try:
        report = await mongo.find_one("Reports", {"Report_id": report_id})
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found"
            )
        return report
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        logger.error(f"Error retrieving report {report_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
```

### JavaScript/React (Frontend)

#### Code Style

- Use **ESLint** with React configuration
- Use **Prettier** for code formatting
- Prefer **functional components** with hooks
- Use **camelCase** for variables and functions

#### Setup ESLint and Prettier

```bash
cd frontend
npm install --save-dev eslint prettier eslint-config-prettier eslint-plugin-react

# Create .eslintrc.js
cat > .eslintrc.js << EOF
module.exports = {
  env: {
    browser: true,
    es2021: true,
  },
  extends: [
    'eslint:recommended',
    '@vitejs/eslint-config-react',
    'prettier'
  ],
  parserOptions: {
    ecmaVersion: 'latest',
    sourceType: 'module',
  },
  rules: {
    'react/prop-types': 'off',
    'no-unused-vars': 'warn',
  },
}
EOF

# Create .prettierrc
cat > .prettierrc << EOF
{
  "semi": false,
  "singleQuote": true,
  "tabWidth": 2,
  "trailingComma": "es5"
}
EOF
```

#### Component Structure

```jsx
import React, { useState, useEffect } from "react";
import { useAuth } from "../auth/useAuth";
import "./ComponentName.css";

/**
 * ComponentName - Brief description
 * @param {Object} props - Component props
 * @param {string} props.title - Component title
 * @param {Function} props.onAction - Action callback
 */
const ComponentName = ({ title, onAction }) => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Effect logic
  }, []);

  const handleAction = async () => {
    setLoading(true);
    try {
      await onAction();
    } catch (error) {
      console.error("Action failed:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="component-name">
      <h2>{title}</h2>
      <button onClick={handleAction} disabled={loading}>
        {loading ? "Loading..." : "Action"}
      </button>
    </div>
  );
};

export default ComponentName;
```

#### API Integration

```javascript
// utils/api.js
const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export const apiCall = async (endpoint, options = {}) => {
  const token = localStorage.getItem("authToken");

  const config = {
    headers: {
      "Content-Type": "application/json",
      ...(token && { Authorization: `Bearer ${token}` }),
      ...options.headers,
    },
    ...options,
  };

  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, config);

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error("API call failed:", error);
    throw error;
  }
};

// Usage in components
const fetchUserData = async () => {
  try {
    const userData = await apiCall("/user/me");
    setUser(userData);
  } catch (error) {
    setError("Failed to fetch user data");
  }
};
```

## Database Development

### MongoDB Development Setup

#### Using Docker (Recommended)

```bash
# Start MongoDB with Docker
docker-compose up mongodb

# Access MongoDB shell
docker exec -it healthinsight_mongodb mongo -u admin -p password123 --authenticationDatabase admin
```

#### Local MongoDB Setup

```bash
# Install MongoDB locally
# Ubuntu/Debian:
sudo apt-get install -y mongodb-org

# Start MongoDB
sudo systemctl start mongod

# Access MongoDB shell
mongo mongodb://localhost:27017/healthinsight_dev
```

#### Database Exploration

```bash
# Use the exploration script
cd backend
python explore_db.py
```

### Database Operations

#### Creating Indexes

```javascript
// Connect to MongoDB
use healthinsight_dev

// Create performance indexes
db.Users.createIndex({"uid": 1}, {"unique": true})
db.Reports.createIndex({"Patient_id": 1})
db.Reports.createIndex({"Report_id": 1}, {"unique": true})
db.LLMReports.createIndex({"report_id": 1})
db.AccessRequests.createIndex({"patient_email": 1, "hospital_uid": 1})

// Check indexes
db.Users.getIndexes()
```

#### Sample Data Creation

```javascript
// Create test user
db.Users.insertOne({
  uid: "test-user-123",
  email: "test@example.com",
  user_type: "patient",
  name: "Test User",
  BioData: {
    age: 30,
    gender: "male",
  },
  Favorites: ["hemoglobin", "cholesterol"],
  created_at: new Date(),
});

// Create test report
db.Reports.insertOne({
  Report_id: "test-report-123",
  Patient_id: "test-user-123",
  Processed_at: new Date().toISOString(),
  Attributes: {
    test_1: {
      name: "Hemoglobin",
      value: "12.5",
      unit: "g/dL",
      range: "12.0-15.5",
      remark: "Normal",
    },
  },
});
```

## API Development

### Adding New Endpoints

#### 1. Define Pydantic Models

```python
# schemas.py
class NewFeatureRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    options: List[str] = []

class NewFeatureResponse(BaseModel):
    id: str
    name: str
    created_at: datetime
```

#### 2. Create Router

```python
# routers/new_feature.py
from fastapi import APIRouter, Depends, HTTPException
from src.auth.dependencies import get_current_user
from src.schemas import NewFeatureRequest, NewFeatureResponse

router = APIRouter(prefix="/api/new-feature", tags=["New Feature"])

@router.post("/", response_model=NewFeatureResponse)
async def create_feature(
    request: NewFeatureRequest,
    current_user: dict = Depends(get_current_user)
):
    # Implementation
    pass

@router.get("/{feature_id}", response_model=NewFeatureResponse)
async def get_feature(
    feature_id: str,
    current_user: dict = Depends(get_current_user)
):
    # Implementation
    pass
```

#### 3. Register Router

```python
# main.py
from src.routers import new_feature

app.include_router(new_feature.router)
```

### API Documentation

FastAPI automatically generates OpenAPI documentation. Access it at:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

#### Enhancing Documentation

```python
@router.post(
    "/upload",
    summary="Upload medical report",
    description="Upload a PDF medical report for processing and analysis",
    response_description="Upload confirmation with report ID",
    responses={
        200: {"description": "Report uploaded successfully"},
        400: {"description": "Invalid file format or size"},
        401: {"description": "Authentication required"},
        413: {"description": "File too large"},
    }
)
async def upload_report(
    file: UploadFile = File(..., description="PDF medical report"),
    patient_id: Optional[str] = Form(None, description="Optional patient ID"),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload and process a medical report PDF.

    - **file**: PDF file containing medical test results
    - **patient_id**: Optional patient identifier (defaults to current user)

    Returns report ID and processing status.
    Note: The uploaded file is processed and then discarded. Only extracted data is stored.
    """
    pass
```

## Debugging

### Backend Debugging

#### VS Code Debug Configuration

```json
// .vscode/launch.json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "FastAPI Debug",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/backend/src/main.py",
      "args": [],
      "console": "integratedTerminal",
      "env": {
        "PYTHONPATH": "${workspaceFolder}/backend/src"
      },
      "cwd": "${workspaceFolder}/backend"
    }
  ]
}
```

#### Logging Configuration

```python
# core/config.py
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
```

#### Debug Utilities

```python
# utils/debug.py
import json
from typing import Any

def debug_print(obj: Any, label: str = "DEBUG"):
    """Pretty print objects for debugging."""
    print(f"\n{label}:")
    print(json.dumps(obj, indent=2, default=str))

def log_request(request, response):
    """Log request/response for debugging."""
    logger.info(f"Request: {request.method} {request.url}")
    logger.info(f"Response: {response.status_code}")
```

### Frontend Debugging

#### Browser DevTools

- Use React Developer Tools extension
- Monitor network requests in Network tab
- Check console for errors and warnings
- Use Application tab for localStorage/sessionStorage

#### Debug Logging

```javascript
// utils/debug.js
export const debugLog = (message, data = null) => {
  if (import.meta.env.DEV) {
    console.log(`[DEBUG] ${message}`, data);
  }
};

export const debugError = (message, error) => {
  if (import.meta.env.DEV) {
    console.error(`[ERROR] ${message}`, error);
  }
};

// Usage in components
import { debugLog, debugError } from "../utils/debug";

const fetchData = async () => {
  try {
    debugLog("Fetching user data");
    const data = await apiCall("/user/me");
    debugLog("User data received", data);
    setUser(data);
  } catch (error) {
    debugError("Failed to fetch user data", error);
  }
};
```

## Performance Optimization

### Backend Performance

#### Database Optimization

```python
# Use indexes for frequent queries
await mongo.collection("Reports").create_index([("Patient_id", 1)])
await mongo.collection("Reports").create_index([("Report_id", 1)])

# Use projection to limit returned fields
report = await mongo.find_one(
    "Reports",
    {"Report_id": report_id},
    {"Attributes": 1, "Processed_at": 1}  # Only return these fields
)

# Use aggregation for complex queries
pipeline = [
    {"$match": {"Patient_id": patient_id}},
    {"$sort": {"Processed_at": -1}},
    {"$limit": 10}
]
recent_reports = await mongo.collection("Reports").aggregate(pipeline).to_list(10)
```

#### Async Optimization

```python
import asyncio

# Process multiple operations concurrently
async def process_multiple_reports(report_ids: List[str]):
    tasks = [process_single_report(report_id) for report_id in report_ids]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results

# Use async context managers
async def process_with_cleanup():
    async with get_database_connection() as db:
        # Database operations
        pass
    # Connection automatically closed
```

### Frontend Performance

#### Code Splitting

```javascript
// Lazy load components
import { lazy, Suspense } from "react";

const Dashboard = lazy(() => import("./pages/Dashboard"));
const ReportVisualization = lazy(() => import("./pages/ReportVisualization"));

function App() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <Routes>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/report/:id" element={<ReportVisualization />} />
      </Routes>
    </Suspense>
  );
}
```

#### Memoization

```javascript
import { memo, useMemo, useCallback } from "react";

const ExpensiveComponent = memo(({ data, onAction }) => {
  const processedData = useMemo(() => {
    return data.map((item) => ({
      ...item,
      processed: expensiveCalculation(item),
    }));
  }, [data]);

  const handleAction = useCallback(
    (id) => {
      onAction(id);
    },
    [onAction]
  );

  return (
    <div>
      {processedData.map((item) => (
        <div key={item.id} onClick={() => handleAction(item.id)}>
          {item.processed}
        </div>
      ))}
    </div>
  );
});
```

## Git Workflow

### Branch Strategy

```
main                    # Production-ready code
├── develop            # Integration branch
├── feature/user-auth  # Feature branches
├── feature/ai-analysis
├── hotfix/security-fix # Hotfix branches
└── release/v1.2.0     # Release branches
```

### Commit Message Format

```
type(scope): description

[optional body]

[optional footer]
```

**Types:**

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `chore`: Maintenance tasks

**Examples:**

```
feat(auth): add Firebase authentication integration

fix(api): resolve report upload timeout issue

docs(readme): update installation instructions

refactor(user): improve profile update logic
```

### Pre-commit Hooks

```bash
# Install pre-commit
pip install pre-commit
pre-commit install

# Run on all files
pre-commit run --all-files
```

## Contribution Guidelines

### Pull Request Process

1. **Create Feature Branch**

   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes**

   - Follow coding standards
   - Update documentation
   - Ensure functionality works as expected

3. **Manual Verification**

   ```bash
   # Backend verification
   cd backend && python -m uvicorn src.main:app --reload

   # Frontend verification
   cd frontend && npm run dev

   # Integration verification
   ./start.sh dev
   # Manual testing of new functionality
   ```

4. **Create Pull Request**
   - Use descriptive title and description
   - Reference related issues
   - Include screenshots for UI changes
   - Ensure Docker builds pass

### Code Review Checklist

#### For Reviewers

- [ ] Code follows project standards
- [ ] Documentation is updated
- [ ] No security vulnerabilities
- [ ] Performance considerations addressed
- [ ] Error handling is appropriate
- [ ] API changes are backward compatible

#### For Contributors

- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No console errors or warnings
- [ ] Responsive design verified (frontend)
- [ ] Cross-browser compatibility checked (frontend)
- [ ] Database migrations included (if needed)

### Issue Reporting

When reporting bugs or requesting features:

1. **Use Issue Templates**
2. **Provide Reproduction Steps**
3. **Include Environment Details**
4. **Add Screenshots/Logs**
5. **Label Appropriately**

### Release Process

1. **Create Release Branch**

   ```bash
   git checkout -b release/v1.2.0
   ```

2. **Update Version Numbers**

   - `package.json` (frontend)
   - `src/core/config.py` (backend)
   - `README.md`

3. **Manual Verification**

   - Full integration verification
   - Performance verification
   - Security verification

4. **Create Release**
   - Merge to main
   - Tag release
   - Deploy to production
   - Update documentation
