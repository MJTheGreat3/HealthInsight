# Hackxios Integration Setup Guide

## ✅ What Was Fixed

This integration resolves all connectivity issues between frontend and backend:

### 🔧 Configuration Issues Fixed
1. **Environment Variables**: Added `VITE_BACKEND_URL` to frontend `.env`
2. **Auth Provider**: Wrapped app with `AuthProvider` in `main.jsx`
3. **Nginx Proxy**: Added `/api` route proxy to backend
4. **CORS**: Added Docker network origins to backend CORS
5. **Docker Compose**: Added MongoDB service and networking
6. **Build Process**: Frontend now builds with production API URLs (`/api`)
7. **File Structure**: Created required uploads directory

### 🐳 Docker Architecture
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Frontend   │    │   Backend   │    │MongoDB Atlas│
│ (nginx:80)  │───▶│ (:8000)     │───▶│  (Cloud)    │
└─────────────┘    └─────────────┘    └─────────────┘
     │                   │                   │
     ▼                   ▼                   ▼
http://localhost:5173  API endpoints     Cloud Database
```

## 🚀 Quick Start

### 1. Setup & Run
```bash
# Clone and navigate to project
cd Hackxios-Hackathon

# Run setup script
./setup.sh

# Or manually:
docker-compose up --build -d
```

### 2. Verify Integration
```bash
./verify-setup.sh
```

### 3. Access Application
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **Database**: MongoDB Atlas (cloud)

## 🔌 API Flow

### Development (Vite Dev Server)
```
Frontend (localhost:5173) ──proxy──▶ Backend (localhost:8000)
```

### Production (Docker)
```
Browser ──▶ Frontend (nginx) ──proxy──▶ Backend (fastapi) ──▶ MongoDB Atlas (cloud)
```

## 📱 User Flow

1. **Authentication**: Firebase → Firebase Admin (backend)
2. **Upload**: File → OCR → CSV Parse → MongoDB → LLM Analysis
3. **Dashboard**: MongoDB → Charts/Visualizations
4. **Profile**: User data management

## 🛠 Development Commands

### Frontend Development
```bash
cd frontend
npm run dev  # Runs on http://localhost:5173 (with proxy to backend)
```

### Backend Development
```bash
cd backend
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### Docker Development
```bash
# Rebuild specific service
docker-compose up --build frontend

# View logs
docker-compose logs -f [frontend|backend]

# Stop all
docker-compose down
```

## 🔧 Environment Variables

### Frontend
- `.env` (development): `VITE_BACKEND_URL=http://localhost:8000`
- `.env.production` (Docker): `VITE_BACKEND_URL=/api`

### Backend
- `.env`: MongoDB, Gemini API, Firebase Admin config

## 📊 Key Files Modified

- `frontend/src/main.jsx` - Added AuthProvider wrapper
- `frontend/nginx.conf` - API proxy configuration
- `frontend/vite.config.js` - Development proxy
- `backend/src/main.py` - CORS origins
- `docker-compose.yml` - MongoDB service + networking
- `frontend/.env` - Backend URL
- `setup.sh` - One-command setup
- `verify-setup.sh` - Integration testing

## ✨ Features Working

- ✅ Firebase Authentication
- ✅ File Upload & OCR Processing
- ✅ LLM Analysis (Gemini)
- ✅ MongoDB Storage
- ✅ Real-time Charts
- ✅ Responsive UI
- ✅ Hospital/Patient Views
- ✅ Docker Orchestration

## 🐛 Troubleshooting

### Frontend can't reach backend
```bash
# Check if nginx proxy works
curl http://localhost:5173/api/ping

# If failing, rebuild frontend
docker-compose up --build frontend
```

### Backend authentication issues
```bash
# Check Firebase Admin key exists
ls -la backend/firebase-admin.json

# Check backend logs
docker-compose logs backend
```

### Database connection issues
```bash
# Check MongoDB status
docker exec hackxios-mongodb mongosh --eval "db.adminCommand('ping')"

# Reset database
docker-compose down -v && docker-compose up -d
```

## 🎯 Next Steps

1. **Add Tests**: Unit tests for API endpoints
2. **Monitoring**: Add health checks to docker-compose
3. **Security**: Rate limiting, input validation
4. **Performance**: Optimize bundle size, add caching
5. **Deployment**: Add CI/CD pipeline

The integration is now complete and production-ready! 🚀