from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # MongoDB settings
    MONGO_URI: str = "mongodb://localhost:27017"
    MONGO_DB: str = "hackxios_db"
    
    # File upload settings
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    UPLOAD_DIR: str = "src/uploads"
    
    # App settings
    APP_NAME: str = "Hackxios Medical Reports"
    VERSION: str = "1.0.0"
    
    # LLM Settings
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.5-flash"
    GEMINI_TEMPERATURE: float = 0.0

    # Firebase settings
    FIREBASE_ADMIN_KEY: Optional[str] = None
    
    class Config:
        env_file = ".env"


settings = Settings()
