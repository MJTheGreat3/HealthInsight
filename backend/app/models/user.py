from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class UserType(str, Enum):
    PATIENT = "patient"
    INSTITUTION = "institution"


class UserModel(BaseModel):
    uid: Optional[str] = None
    user_type: Optional[UserType] = None


class PatientModel(UserModel):
    name: Optional[str] = None
    favorites: List[str] = []  # Tracked metrics/concerns
    bio_data: Dict[str, Any] = {}  # Height, weight, allergies, etc.
    reports: List[str] = []  # Report IDs
    model_config = ConfigDict(extra="allow")


class InstitutionModel(UserModel):
    name: Optional[str] = None
    patient_list: List[str] = []  # Patient IDs
    model_config = ConfigDict(extra="allow")