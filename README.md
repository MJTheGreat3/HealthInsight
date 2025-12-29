# HealthInsight Core

A comprehensive medical test analysis web application that enables patients to upload and analyze their medical test results while providing healthcare providers with patient management capabilities.

## Features

- **Patient Portal**: Upload PDF medical reports, receive AI-powered analysis and lifestyle advice
- **Hospital Dashboard**: Patient management and comprehensive data access
- **AI Analysis**: LLM-powered insights and recommendations
- **Real-time Sync**: Live data synchronization across sessions
- **Data Visualization**: Interactive charts and trend analysis

## Technology Stack

### Backend

- FastAPI with Python 3.11+
- MongoDB with Motor (async driver)
- Firebase Authentication
- OpenAI API integration
- PyMuPDF for PDF processing

### Frontend

- React 18 with TypeScript
- Vite for fast development
- Tailwind CSS for styling
- Chart.js for data visualization
- Socket.io for real-time communication

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)

### Environment Setup

1. Copy the environment template:

```bash
cp .env.example .env
```

2. Update the `.env` file with your configuration:
   - Firebase credentials
   - OpenAI API key
   - MongoDB connection string (if not using Docker)

### Using Docker (Recommended)

1. Start all services:

```bash
docker-compose up -d
```

2. Access the application:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Local Development

#### Backend Setup

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

#### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

## Testing

### Backend Tests

```bash
cd backend
pytest
```

### Frontend Tests

```bash
cd frontend
npm run test
```

## Project Structure

```
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── core/           # Configuration and database
│   │   ├── models/         # Pydantic models
│   │   └── services/       # Business logic
│   └── tests/              # Backend tests
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/          # Page components
│   │   ├── services/       # API services
│   │   └── types/          # TypeScript types
│   └── tests/              # Frontend tests
└── docker-compose.yml      # Docker configuration
```

## API Documentation

Once the backend is running, visit http://localhost:8000/docs for interactive API documentation.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License.
