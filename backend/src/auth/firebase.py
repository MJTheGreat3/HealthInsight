import os
import firebase_admin
from firebase_admin import credentials, auth
from fastapi import HTTPException, status
from dotenv import load_dotenv
load_dotenv()

FIREBASE_KEY_PATH = os.environ.get("FIREBASE_ADMIN_KEY")

if not FIREBASE_KEY_PATH:
    raise RuntimeError("FIREBASE_ADMIN_KEY environment variable not set")

if not firebase_admin._apps:
    cred = credentials.Certificate(FIREBASE_KEY_PATH)
    firebase_admin.initialize_app(cred)

def verify_firebase_token(token: str):
    try:
        decoded_token = auth.verify_id_token(token)
        return {
            "uid": decoded_token.get("uid"),
            "email": decoded_token.get("email")
        }
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired Firebase token"
        )
