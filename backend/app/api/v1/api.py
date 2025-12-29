"""
API v1 router configuration
"""

from fastapi import APIRouter

api_router = APIRouter()

# Placeholder for future endpoint imports
# from app.api.v1.endpoints import auth, patients, reports, analysis, chat, hospitals

@api_router.get("/status")
async def api_status():
    """API status endpoint"""
    return {"status": "API v1 is running"}