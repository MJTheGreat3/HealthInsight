from pydantic import BaseModel
from typing import Optional
from .user import UserType


class OnboardRequest(BaseModel):
    role: UserType  # "patient" or "institution"
    name: Optional[str] = None