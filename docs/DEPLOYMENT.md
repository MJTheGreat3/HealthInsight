# Deployment Guide

## Overview

HealthInsight can be deployed in multiple ways depending on your infrastructure needs. This guide covers Docker-based deployment (recommended), manual deployment, and cloud deployment options.

## Prerequisites

### System Requirements

- **CPU**: 2+ cores (4+ recommended for production)
- **RAM**: 4GB minimum (8GB+ recommended for production)
- **Storage**: 20GB minimum (50GB+ recommended for production)
- **OS**: Linux (Ubuntu 20.04+ recommended), macOS, or Windows with WSL2

### Software Requirements

- Docker 20.10+
- Docker Compose 2.0+
- Git
- SSL certificates (for production)

## Environment Configuration

### 1. Clone Repository

```bash
git clone <repository-url>
cd healthinsight
```

### 2. Environment Files

Create environment files from templates:

```bash
cp .env.example .env
cp backend/.env.example backend/.env
```

### 3. Configure Environment Variables

#### Root `.env` File

```bash
# MongoDB Configuration
MONGODB_URL=mongodb://admin:password123@mongodb:27017/healthinsight?authSource=admin
DATABASE_NAME=healthinsight

# Firebase Configuration
FIREBASE_PROJECT_ID=your-firebase-project-id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nYOUR_PRIVATE_KEY_HERE\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=firebase-adminsdk-xxxxx@your-project-id.iam.gserviceaccount.com

# Frontend Firebase Configuration
VITE_FIREBASE_API_KEY=your-web-api-key
VITE_FIREBASE_AUTH_DOMAIN=your-project-id.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your-firebase-project-id

# AI Configuration
GEMINI_API_KEY=your-gemini-api-key

# Security
SECRET_KEY=your-super-secret-key-here-make-it-long-and-random
```

#### Backend `.env` File

```bash
# MongoDB Configuration
MONGO_URI=mongodb://admin:password123@mongodb:27017
MONGO_DB=healthinsight

# Gemini AI Configuration
GEMINI_API_KEY=your-gemini-api-key-here

# Firebase Admin Configuration
FIREBASE_ADMIN_KEY=/app/firebase-admin.json

# File Processing Configuration
MAX_FILE_SIZE=10485760

# App Configuration
APP_NAME=HealthInsight Medical Reports
VERSION=1.0.0
```

### 4. Firebase Setup

1. **Create Firebase Project**:

   - Go to [Firebase Console](https://console.firebase.google.com/)
   - Create a new project
   - Enable Authentication with Email/Password

2. **Generate Service Account Key**:

   - Go to Project Settings > Service Accounts
   - Generate new private key
   - Save as `backend/firebase-admin.json`

3. **Get Web App Config**:
   - Go to Project Settings > General
   - Add web app and copy config values to `.env`

### 5. Google AI Setup

1. **Get Gemini API Key**:
   - Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Create API key
   - Add to environment files

## Docker Deployment (Recommended)

### Quick Start Script

The project includes a convenient startup script:

```bash
# Make executable
chmod +x start.sh

# Development environment (with hot reload and debugging tools)
./start.sh dev

# Production environment (optimized builds)
./start.sh prod

# View real-time logs
./start.sh logs

# Check service health
./start.sh health

# Stop all services
./start.sh stop

# Clean up everything (removes all data!)
./start.sh clean
```

### Manual Docker Commands

#### Development Deployment

```bash
# Start with development overrides
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build

# Start with MongoDB UI (optional)
docker-compose --profile dev up --build

# Run in background
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build
```

#### Production Deployment

```bash
# Build and start all services
docker-compose up --build -d

# View logs
docker-compose logs -f

# Check status
docker-compose ps

# Stop services
docker-compose down

# Update and restart
git pull
docker-compose up --build -d
```

### Service Access Points

After deployment:

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **MongoDB**: localhost:27017
- **MongoDB UI** (dev only): http://localhost:8081

## Manual Deployment

### Backend Setup

1. **Install Python Dependencies**:

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Install System Dependencies**:

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y tesseract-ocr tesseract-ocr-eng poppler-utils ghostscript

# macOS
brew install tesseract poppler

# Windows (use WSL2 or install manually)
```

3. **Setup MongoDB**:

```bash
# Install MongoDB Community Edition
# Ubuntu
wget -qO - https://www.mongodb.org/static/pgp/server-7.0.asc | sudo apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
sudo apt-get update
sudo apt-get install -y mongodb-org

# Start MongoDB
sudo systemctl start mongod
sudo systemctl enable mongod
```

4. **Run Backend**:

```bash
cd backend
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend Setup

1. **Install Node.js Dependencies**:

```bash
cd frontend
npm install
```

2. **Build for Production**:

```bash
npm run build
```

3. **Serve with Nginx**:

```bash
# Install Nginx
sudo apt-get install nginx

# Copy built files
sudo cp -r dist/* /var/www/html/

# Configure Nginx (see nginx configuration below)
```

## Production Configuration

### Nginx Configuration

Create `/etc/nginx/sites-available/healthinsight`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL Configuration
    ssl_certificate /path/to/your/certificate.crt;
    ssl_certificate_key /path/to/your/private.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # Frontend
    location / {
        root /var/www/html;
        try_files $uri $uri/ /index.html;

        # Security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header Referrer-Policy "no-referrer-when-downgrade" always;
        add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;

        # File upload size
        client_max_body_size 10M;
    }

    # API docs
    location /docs {
        proxy_pass http://localhost:8000/docs;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/healthinsight /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### SSL Certificate Setup

#### Using Let's Encrypt (Recommended)

```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

#### Using Custom Certificate

```bash
# Copy your certificate files
sudo cp your-certificate.crt /etc/ssl/certs/
sudo cp your-private.key /etc/ssl/private/
sudo chmod 600 /etc/ssl/private/your-private.key
```

## Cloud Deployment

### AWS Deployment

#### Using ECS (Elastic Container Service)

1. **Build and Push Images**:

```bash
# Build images
docker build -t healthinsight-backend ./backend
docker build -t healthinsight-frontend ./frontend

# Tag for ECR
docker tag healthinsight-backend:latest 123456789012.dkr.ecr.us-west-2.amazonaws.com/healthinsight-backend:latest
docker tag healthinsight-frontend:latest 123456789012.dkr.ecr.us-west-2.amazonaws.com/healthinsight-frontend:latest

# Push to ECR
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-west-2.amazonaws.com
docker push 123456789012.dkr.ecr.us-west-2.amazonaws.com/healthinsight-backend:latest
docker push 123456789012.dkr.ecr.us-west-2.amazonaws.com/healthinsight-frontend:latest
```

2. **Create ECS Task Definition**:

```json
{
  "family": "healthinsight",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::123456789012:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "backend",
      "image": "123456789012.dkr.ecr.us-west-2.amazonaws.com/healthinsight-backend:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "MONGO_URI",
          "value": "mongodb://your-mongodb-connection-string"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/healthinsight",
          "awslogs-region": "us-west-2",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

#### Using EC2

1. **Launch EC2 Instance**:

   - Choose Ubuntu 20.04 LTS
   - t3.medium or larger
   - Configure security groups (ports 80, 443, 22)

2. **Setup Instance**:

```bash
# Connect to instance
ssh -i your-key.pem ubuntu@your-instance-ip

# Install Docker
sudo apt-get update
sudo apt-get install -y docker.io docker-compose
sudo usermod -aG docker ubuntu

# Clone and deploy
git clone <repository-url>
cd healthinsight
# Configure environment files
./start.sh prod
```

### Google Cloud Platform

#### Using Cloud Run

1. **Build and Deploy**:

```bash
# Enable APIs
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com

# Build and deploy backend
gcloud builds submit --tag gcr.io/PROJECT-ID/healthinsight-backend ./backend
gcloud run deploy healthinsight-backend --image gcr.io/PROJECT-ID/healthinsight-backend --platform managed

# Build and deploy frontend
gcloud builds submit --tag gcr.io/PROJECT-ID/healthinsight-frontend ./frontend
gcloud run deploy healthinsight-frontend --image gcr.io/PROJECT-ID/healthinsight-frontend --platform managed
```

### Digital Ocean

#### Using App Platform

1. **Create App Spec** (`app.yaml`):

```yaml
name: healthinsight
services:
  - name: backend
    source_dir: /backend
    github:
      repo: your-username/healthinsight
      branch: main
    run_command: uvicorn src.main:app --host 0.0.0.0 --port 8080
    environment_slug: python
    instance_count: 1
    instance_size_slug: basic-xxs
    envs:
      - key: MONGO_URI
        value: ${db.CONNECTION_STRING}
      - key: GEMINI_API_KEY
        value: ${GEMINI_API_KEY}

  - name: frontend
    source_dir: /frontend
    github:
      repo: your-username/healthinsight
      branch: main
    build_command: npm run build
    run_command: npm run preview -- --host 0.0.0.0 --port 8080
    environment_slug: node-js
    instance_count: 1
    instance_size_slug: basic-xxs

databases:
  - name: db
    engine: MONGODB
    version: "5"
```

2. **Deploy**:

```bash
doctl apps create --spec app.yaml
```

## Monitoring and Maintenance

### Health Checks

The application includes built-in health check endpoints:

```bash
# Backend health
curl http://localhost:8000/api/ping

# Database connectivity
curl http://localhost:8000/api/db-test
```

### Logging

#### Docker Logs

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f mongodb
```

#### Production Logging

```bash
# Setup log rotation
sudo nano /etc/logrotate.d/healthinsight

# Add configuration
/var/log/healthinsight/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 www-data www-data
}
```

### Database Backup

#### Automated MongoDB Backup

```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/mongodb"
DB_NAME="healthinsight"

mkdir -p $BACKUP_DIR

# Create backup
mongodump --host localhost:27017 --db $DB_NAME --out $BACKUP_DIR/$DATE

# Compress backup
tar -czf $BACKUP_DIR/$DATE.tar.gz -C $BACKUP_DIR $DATE
rm -rf $BACKUP_DIR/$DATE

# Keep only last 30 days
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

echo "Backup completed: $BACKUP_DIR/$DATE.tar.gz"
```

Add to crontab:

```bash
crontab -e
# Add: 0 2 * * * /path/to/backup.sh
```

### Performance Monitoring

#### System Monitoring

```bash
# Install monitoring tools
sudo apt-get install htop iotop nethogs

# Monitor Docker containers
docker stats

# Monitor disk usage
df -h
du -sh /var/lib/docker/
```

#### Application Monitoring

```bash
# Monitor API response times
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/api/ping

# Monitor database performance
mongo --eval "db.runCommand({serverStatus: 1})"
```

## Troubleshooting

### Common Issues

#### Port Already in Use

```bash
# Find process using port
sudo lsof -i :8000
sudo lsof -i :5173

# Kill process
sudo kill -9 <PID>
```

#### Docker Issues

```bash
# Clean up Docker
docker system prune -a
docker volume prune

# Rebuild without cache
docker-compose build --no-cache
```

#### Database Connection Issues

```bash
# Check MongoDB status
docker-compose logs mongodb

# Test connection
mongo mongodb://admin:password123@localhost:27017/healthinsight?authSource=admin
```

#### File Processing Issues

```bash
# Check backend logs for OCR errors
docker-compose logs backend

# Verify system dependencies
docker exec -it healthinsight_backend tesseract --version
```

### Performance Optimization

#### Backend Optimization

```bash
# Use production WSGI server
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker src.main:app --bind 0.0.0.0:8000
```

#### Frontend Optimization

```bash
# Optimize build
npm run build -- --mode production

# Analyze bundle size
npm install -g webpack-bundle-analyzer
npx webpack-bundle-analyzer dist/assets/*.js
```

#### Database Optimization

```javascript
// Create indexes for better performance
db.Reports.createIndex({ Patient_id: 1 });
db.Reports.createIndex({ Report_id: 1 });
db.LLMReports.createIndex({ report_id: 1 });
db.Users.createIndex({ uid: 1 });
```

## Security Checklist

- [ ] Environment variables configured securely
- [ ] Firebase authentication properly configured
- [ ] SSL certificates installed and configured
- [ ] Database access restricted to application only
- [ ] File upload validation and size limits configured
- [ ] CORS properly configured for production domains
- [ ] Security headers configured in Nginx
- [ ] Regular security updates applied
- [ ] Backup and recovery procedures verified
- [ ] Monitoring and alerting configured
- [ ] File processing security verified (temporary files only)
