from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ChatSession(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    patient_id: str
    messages: List[ChatMessage] = []
    context: Dict[str, Any] = {}  # Recent reports, tracked metrics
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)