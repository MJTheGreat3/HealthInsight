# Docker Setup for HealthInsight

This Docker setup provides a complete development and production environment for HealthInsight application.

## 🏗️ Architecture

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Frontend  │────▶│   Nginx     │────▶│   Backend   │
│  (React/Vite)│    │ (Proxy/SPA) │    │ (FastAPI)   │
└─────────────┘    └─────────────┘    └─────────────┘
                                             │
                                             ▼
                                      ┌─────────────┐
                                      │  MongoDB    │
                                      │  Database   │
                                      └─────────────┘
```

## 🚀 Quick Start

### Production Mode
```bash
# Build and start all services
docker-compose up --build -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Development Mode
```bash
# Start with development overrides
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build

# Or for individual development
docker-compose up mongodb backend  # Start DB and API
# Then run frontend locally: cd Frontend && npm run dev
```

### With MongoDB UI (Development)
```bash
docker-compose --profile dev up
# Access MongoDB UI at: http://localhost:8081
```

## 📋 Services

| Service | Port | Description | Health Check |
|---------|-------|-------------|--------------|
| Frontend | 5173 | React application | `/health` |
| Backend | 8000 | FastAPI server | `/api/ping` |
| MongoDB | 27017 | Data storage | MongoDB ping |
| Mongo Express | 8081 | Database UI | - |

## 🔧 Environment Variables

### Backend (`.env`)
```bash
# Firebase Configuration
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_PRIVATE_KEY_ID=your-key-id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n..."

# MongoDB
MONGODB_URL=mongodb://admin:password123@mongodb:27017/healthinsight?authSource=admin

# API Keys
GOOGLE_API_KEY=your-gemini-api-key
```

### Frontend
- Built from `vite.config.js` settings
- Production: Uses Nginx proxy to `/api/*`
- Development: Direct calls to `http://localhost:8000`

## 🗂️ Volume Mounts

### Production
- `mongodb_data`: Persistent database storage
- `firebase_creds`: Firebase credentials (read-only)

### Development
- `./backend/src`: Live code mounting for hot reload
- `./Frontend/src`: Live frontend code
- `firebase-admin.json`: Mounted as read-only

## 🏥 Health Checks

All services include health checks:

```bash
# Check service health
docker-compose ps
# or individual
curl http://localhost:5173/health  # Frontend
curl http://localhost:8000/api/ping  # Backend
```

## 🔄 Development Workflow

### 1. Start Development Environment
```bash
# Start database and API with live code mounting
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build

# Frontend will hot-reload on file changes
# Backend will auto-restart on Python file changes
```

### 2. Production Build
```bash
# Build production images
docker-compose build --no-cache

# Deploy to production
docker-compose -f docker-compose.yml up -d
```

### 3. Database Management
```bash
# Access MongoDB directly
docker exec -it healthinsight_mongodb mongosh

# View logs
docker-compose logs mongodb

# Reset database
docker-compose down -v  # Removes volumes
docker-compose up --build
```

## 🐛 Troubleshooting

### Common Issues

1. **Port Conflicts**
   ```bash
   # Check what's using ports
   lsof -i :8000
   lsof -i :5173
   lsof -i :27017
   ```

2. **Permission Issues**
   ```bash
   # Fix Docker permissions
   sudo chown -R $USER:$USER ./backend ./Frontend
   ```

3. **Build Failures**
   ```bash
   # Clean rebuild
   docker-compose down --volumes
   docker-compose build --no-cache
   docker-compose up
   ```

4. **Health Check Failures**
   ```bash
   # Check individual service health
   docker health healthinsight_backend
   docker health healthinsight_frontend
   ```

### Logs Debugging
```bash
# Real-time logs for all services
docker-compose logs -f

# Specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f mongodb
```

## 🔐 Security Considerations

- **Production**: Change default MongoDB credentials
- **Firebase**: Keep private keys secure, never commit to git
- **Network**: All services communicate on private Docker network
- **CORS**: Configured for development, restrict in production

## 📦 Production Deployment

### Environment Setup
```bash
# Production environment file
cp backend/.env.example backend/.env
# Edit with production values
```

### SSL/HTTPS
1. Update `nginx.conf` with SSL certificates
2. Update `docker-compose.yml` ports (443, 80)
3. Add Let's Encrypt certificates

### Scaling
```bash
# Scale backend services
docker-compose up --scale backend=3
```

## 🔄 Updates and Maintenance

### Updating Dependencies
```bash
# Rebuild with latest dependencies
docker-compose build --no-cache
docker-compose up -d
```

### Backup Database
```bash
# Export MongoDB data
docker exec healthinsight_mongodb mongodump --out /backup
docker cp healthinsight_mongodb:/backup ./backup
```

### Restore Database
```bash
# Import backup
docker cp ./backup healthinsight_mongodb:/backup
docker exec healthinsight_mongodb mongorestore /backup
```