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
from app.services.performance_monitor import performance_monitor, PerformanceMiddleware
from app.services.optimized_database import optimized_db_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    await connect_to_mongo()
    
    # Initialize database services
    await db_service.initialize()
    await optimized_db_service.initialize()
    
    # Start performance monitoring
    await performance_monitor.start_monitoring()
    
    # Initialize services
    auth_service = AuthService()
    
    # Initialize chatbot service
    chatbot_service = initialize_chatbot_service(llm_analysis_service, optimized_db_service)
    
    # Initialize WebSocket service
    websocket_service = initialize_websocket_service(chatbot_service, auth_service)
    
    yield
    
    # Shutdown
    await performance_monitor.stop_monitoring()
    await optimized_db_service.close_connections()
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

# Add performance monitoring middleware
performance_middleware = PerformanceMiddleware(performance_monitor)
app.middleware("http")(performance_middleware)

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
    """Enhanced health check endpoint with performance metrics"""
    from app.services.performance_monitor import performance_monitor
    from app.core.cache import cache_manager
    
    # Get basic health status
    health_status = await performance_monitor.get_health_status()
    
    # Get cache statistics
    cache_stats = cache_manager.get_all_stats()
    
    # Get optimized database health
    db_health = await optimized_db_service.health_check_optimized()
    
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": health_status.get("timestamp"),
        "performance": health_status.get("performance_summary", {}),
        "system": health_status.get("system_summary", {}),
        "cache": cache_stats,
        "database": db_health
    }


@app.get("/metrics")
async def get_performance_metrics():
    """Get detailed performance metrics"""
    from app.services.performance_monitor import performance_monitor
    
    return await performance_monitor.get_performance_summary(hours_back=24)


@app.get("/metrics/system")
async def get_system_metrics():
    """Get system resource metrics"""
    from app.services.performance_monitor import performance_monitor
    
    return await performance_monitor.get_system_metrics_summary(hours_back=24)


@app.get("/metrics/slow-queries")
async def get_slow_queries():
    """Get recent slow queries"""
    from app.services.performance_monitor import performance_monitor
    
    return await performance_monitor.get_slow_queries(limit=50)


@app.get("/security/audit")
async def run_security_audit():
    """Run comprehensive security audit"""
    from app.services.security_audit import security_auditor
    
    result = await security_auditor.run_comprehensive_audit()
    
    return {
        "timestamp": result.timestamp.isoformat(),
        "overall_score": result.overall_score,
        "total_issues": len(result.issues),
        "issues_by_severity": {
            "critical": len([i for i in result.issues if i.severity == "critical"]),
            "high": len([i for i in result.issues if i.severity == "high"]),
            "medium": len([i for i in result.issues if i.severity == "medium"]),
            "low": len([i for i in result.issues if i.severity == "low"])
        },
        "passed_checks": len(result.passed_checks),
        "failed_checks": len(result.failed_checks),
        "issues": [
            {
                "severity": issue.severity,
                "category": issue.category,
                "title": issue.title,
                "description": issue.description,
                "recommendation": issue.recommendation,
                "affected_component": issue.affected_component
            }
            for issue in result.issues
        ],
        "recommendations": result.recommendations
    }


@app.post("/security/validate-input")
async def validate_input_security(data: dict):
    """Validate input for security issues"""
    from app.core.security import security_validator
    
    errors = security_validator.validate_user_input(data)
    
    return {
        "is_safe": len(errors) == 0,
        "errors": errors,
        "fields_checked": len(data),
        "issues_found": len(errors)
    }


# Mount Socket.IO after app initialization
@app.on_event("startup")
async def mount_socketio():
    """Mount Socket.IO after services are initialized."""
    pass  # Services are initialized in lifespan


# Export the app with Socket.IO integration
def get_app():
    """Get the application with Socket.IO integration."""
    return create_socketio_app()