"""
HealthInsightCore FastAPI Application
Main entry point for the backend API
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import socketio

from app.core.config import settings
from app.core.database import connect_to_mongo, close_mongo_connection
from app.core.error_handlers import setup_exception_handlers, create_error_middleware
from app.api.v1.api import api_router
from app.services import db_service, llm_analysis_service
from app.services.auth import AuthService
from app.services.chatbot import initialize_chatbot_service
from app.services.websocket import initialize_websocket_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    await connect_to_mongo()
    
    # Initialize database service
    await db_service.initialize()
    
    # Initialize services
    auth_service = AuthService()
    
    # Initialize chatbot service
    chatbot_service = initialize_chatbot_service(llm_analysis_service, db_service)
    
    # Initialize WebSocket service
    websocket_service = initialize_websocket_service(chatbot_service, auth_service)
    
    yield
    
    # Shutdown
    await close_mongo_connection()


app = FastAPI(
    title="HealthInsightCore API",
    description="Medical test analysis and patient management system",
    version="1.0.0",
    lifespan=lifespan
)

# Setup global exception handlers
setup_exception_handlers(app)

# Add error handling middleware
app.middleware("http")(create_error_middleware())

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create Socket.IO ASGI app after WebSocket service is initialized
def create_socketio_app():
    """Create Socket.IO ASGI app with the initialized WebSocket service."""
    from app.services.websocket import websocket_service
    if websocket_service is not None:
        return socketio.ASGIApp(websocket_service.sio, app)
    return app

# Include API router
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "HealthInsightCore API is running"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "1.0.0"}


# Mount Socket.IO after app initialization
@app.on_event("startup")
async def mount_socketio():
    """Mount Socket.IO after services are initialized."""
    pass  # Services are initialized in lifespan


# Export the app with Socket.IO integration
def get_app():
    """Get the application with Socket.IO integration."""
    return create_socketio_app()