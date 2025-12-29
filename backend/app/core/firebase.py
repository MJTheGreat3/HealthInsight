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
        # Create credentials from environment variables
        cred_dict = {
            "type": "service_account",
            "project_id": settings.FIREBASE_PROJECT_ID,
            "private_key": settings.FIREBASE_PRIVATE_KEY.replace('\\n', '\n'),
            "client_email": settings.FIREBASE_CLIENT_EMAIL,
        }
        
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)


async def verify_firebase_token(token: str) -> dict:
    """Verify Firebase ID token and return user info"""
    try:
        initialize_firebase()
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        raise ValueError(f"Invalid token: {str(e)}")