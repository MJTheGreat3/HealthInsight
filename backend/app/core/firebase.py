"""
Firebase Admin SDK configuration
"""

import json
import firebase_admin
from firebase_admin import credentials, auth
from app.core.config import settings


def initialize_firebase():
    """Initialize Firebase Admin SDK"""
    if not firebase_admin._apps:
        # Skip Firebase initialization if credentials are not provided (for testing)
        if not all([settings.FIREBASE_PROJECT_ID, settings.FIREBASE_PRIVATE_KEY, settings.FIREBASE_CLIENT_EMAIL]):
            print("Warning: Firebase credentials not provided, skipping initialization")
            return
            
        # Create credentials from environment variables
        cred_dict = {
            "type": "service_account",
            "project_id": settings.FIREBASE_PROJECT_ID,
            "private_key": settings.FIREBASE_PRIVATE_KEY.replace('\\n', '\n'),
            "client_email": settings.FIREBASE_CLIENT_EMAIL,
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/{settings.FIREBASE_CLIENT_EMAIL}"
        }
        
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)


async def verify_firebase_token(token: str) -> dict:
    """Verify Firebase ID token and return user info"""
    try:
        initialize_firebase()
        
        # If Firebase is not initialized (no credentials), return a mock response for testing
        if not firebase_admin._apps:
            return {
                "uid": "test-user-id",
                "email": "test@example.com",
                "name": "Test User"
            }
            
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        raise ValueError(f"Invalid token: {str(e)}")