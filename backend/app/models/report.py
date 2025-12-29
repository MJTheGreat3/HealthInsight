from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime


class MetricData(BaseModel):
    name: Optional[str] = None
    value: Optional[str] = None
    remark: Optional[str] = None
    range: Optional[str] = None
    unit: Optional[str] = None
    verdict: Optional[str] = None  # NORMAL | HIGH | LOW | CRITICAL


class Report(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    report_id: str = Field(..., description="Unique report identifier")
    patient_id: str = Field(..., description="Patient identifier")
    processed_at: datetime = Field(default_factory=datetime.utcnow)
    attributes: Dict[str, MetricData] = Field(..., description="Medical test results")
    llm_output: Optional[str] = Field(None, description="LLM-generated health assessment")
    llm_report_id: Optional[str] = Field(None, description="Reference to LLM analysis report")
    selected_concerns: Optional[List[str]] = None  # Metrics added to favorites

    model_config = ConfigDict(populate_by_name=True)


class LLMReportModel(BaseModel):
    patient_id: str = Field(..., min_length=1)
    report_id: str = Field(..., min_length=1)
    time: Optional[str] = None
    output: Dict[str, Any]  # AI analysis results
    input: Dict[str, Any]   # Original test data
    model_config = ConfigDict(extra="allow")


# Request/Response Models
class ReportCreate(BaseModel):
    report_id: str
    patient_id: str
    attributes: Dict[str, MetricData]
    llm_output: Optional[str] = None


class ReportUpdate(BaseModel):
    patient_id: Optional[str] = None
    attributes: Optional[Dict[str, MetricData]] = None
    llm_output: Optional[str] = None


class AttributeUpdateByName(BaseModel):
    name: str  # e.g. "BILIRUBIN, TOTAL"
    value: Optional[str] = None
    remark: Optional[str] = None
    range: Optional[str] = None
    unit: Optional[str] = None