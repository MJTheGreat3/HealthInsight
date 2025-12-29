"""
API v1 router configuration
"""

from fastapi import APIRouter
from app.api.v1.endpoints import auth, example_rbac, reports, metrics

api_router = APIRouter()

# Include authentication endpoints
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])

# Include report endpoints
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])

# Include tracked metrics endpoints
api_router.include_router(metrics.router, prefix="/metrics", tags=["tracked-metrics"])

# Include example RBAC endpoints for demonstration
api_router.include_router(example_rbac.router, prefix="/rbac", tags=["role-based-access-control"])

@api_router.get("/status")
async def api_status():
    """API status endpoint"""
    return {"status": "API v1 is running"}