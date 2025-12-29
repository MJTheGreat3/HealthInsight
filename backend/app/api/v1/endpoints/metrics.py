"""
Tracked Metrics API endpoints
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query, Request
from pydantic import BaseModel, Field
from datetime import datetime

from app.core.middleware import get_current_user, require_patient_role
from app.services.tracked_metrics import tracked_metrics_service

router = APIRouter()


# Request/Response Models
class AddMetricRequest(BaseModel):
    metric_name: str = Field(..., description="Name of the metric to track")


class RemoveMetricRequest(BaseModel):
    metric_name: str = Field(..., description="Name of the metric to remove from tracking")


class TrackedMetricsResponse(BaseModel):
    tracked_metrics: List[str] = Field(..., description="List of tracked metric names")


class TimeSeriesDataPoint(BaseModel):
    date: datetime
    report_id: str
    value: Optional[str]
    numeric_value: Optional[float]
    unit: Optional[str]
    range: Optional[str]
    verdict: Optional[str]
    remark: Optional[str]


class TrendAnalysisResponse(BaseModel):
    metric_name: str
    trend: str
    recent_trend: str
    data_points: int
    numeric_data_points: int
    latest_value: Optional[float]
    earliest_value: Optional[float]
    mean_value: Optional[float]
    change_percentage: Optional[float]
    variability: str
    latest_date: Optional[datetime]
    earliest_date: Optional[datetime]
    unit: Optional[str]
    latest_verdict: Optional[str]


class DashboardSummary(BaseModel):
    total_tracked: int
    improving: int
    worsening: int
    stable: int


class DashboardDataResponse(BaseModel):
    patient_id: str
    tracked_metrics: List[str]
    trends: Dict[str, TrendAnalysisResponse]
    time_series: Dict[str, List[TimeSeriesDataPoint]]
    summary: DashboardSummary
    generated_at: datetime


class ActionableAdviceResponse(BaseModel):
    advice: List[str] = Field(..., description="List of actionable advice based on trends")


@router.post("/track", response_model=Dict[str, str])
async def add_metric_to_tracking(
    request: AddMetricRequest,
    current_user: Dict[str, Any] = Depends(require_patient_role)
):
    """Add a metric to patient's tracked metrics"""
    try:
        patient_id = current_user.uid
        success = await tracked_metrics_service.add_metric_to_tracking(
            patient_id, request.metric_name
        )
        
        if success:
            # Send real-time notification
            from app.services.websocket import websocket_service
            if websocket_service:
                await websocket_service.broadcast_data_update(
                    patient_id,
                    "metric_added_to_tracking",
                    {
                        "metric_name": request.metric_name,
                        "action": "added"
                    }
                )
            
            return {"message": f"Metric '{request.metric_name}' added to tracking"}
        else:
            raise HTTPException(status_code=400, detail="Failed to add metric to tracking")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete("/track", response_model=Dict[str, str])
async def remove_metric_from_tracking(
    request: RemoveMetricRequest,
    current_user: Dict[str, Any] = Depends(require_patient_role)
):
    """Remove a metric from patient's tracked metrics"""
    try:
        patient_id = current_user.uid
        success = await tracked_metrics_service.remove_metric_from_tracking(
            patient_id, request.metric_name
        )
        
        if success:
            # Send real-time notification
            from app.services.websocket import websocket_service
            if websocket_service:
                await websocket_service.broadcast_data_update(
                    patient_id,
                    "metric_removed_from_tracking",
                    {
                        "metric_name": request.metric_name,
                        "action": "removed"
                    }
                )
            
            return {"message": f"Metric '{request.metric_name}' removed from tracking"}
        else:
            raise HTTPException(status_code=400, detail="Failed to remove metric from tracking")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/tracked", response_model=TrackedMetricsResponse)
async def get_tracked_metrics(
    current_user: Dict[str, Any] = Depends(require_patient_role)
):
    """Get list of tracked metrics for the current patient"""
    try:
        patient_id = current_user.uid
        tracked_metrics = await tracked_metrics_service.get_tracked_metrics(patient_id)
        
        return TrackedMetricsResponse(tracked_metrics=tracked_metrics)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/time-series/{metric_name}", response_model=List[TimeSeriesDataPoint])
async def get_metric_time_series(
    metric_name: str,
    days_back: int = Query(365, description="Number of days to look back for data"),
    current_user: Dict[str, Any] = Depends(require_patient_role)
):
    """Get time-series data for a specific metric"""
    try:
        patient_id = current_user.uid
        time_series_data = await tracked_metrics_service.get_metric_time_series_data(
            patient_id, metric_name, days_back
        )
        
        return [TimeSeriesDataPoint(**point) for point in time_series_data]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/trend/{metric_name}", response_model=TrendAnalysisResponse)
async def get_metric_trend_analysis(
    metric_name: str,
    days_back: int = Query(365, description="Number of days to look back for analysis"),
    current_user: Dict[str, Any] = Depends(require_patient_role)
):
    """Get trend analysis for a specific metric"""
    try:
        patient_id = current_user.uid
        trend_analysis = await tracked_metrics_service.analyze_metric_trend(
            patient_id, metric_name, days_back
        )
        
        return TrendAnalysisResponse(**trend_analysis)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/dashboard", response_model=DashboardDataResponse)
async def get_dashboard_data(
    days_back: int = Query(365, description="Number of days to look back for data"),
    current_user: Dict[str, Any] = Depends(require_patient_role)
):
    """Get comprehensive dashboard data for tracked metrics"""
    try:
        patient_id = current_user.uid
        dashboard_data = await tracked_metrics_service.get_dashboard_data(
            patient_id, days_back
        )
        
        # Convert nested dictionaries to proper response models
        trends = {}
        for metric_name, trend_data in dashboard_data["trends"].items():
            trends[metric_name] = TrendAnalysisResponse(**trend_data)
        
        time_series = {}
        for metric_name, series_data in dashboard_data["time_series"].items():
            time_series[metric_name] = [TimeSeriesDataPoint(**point) for point in series_data]
        
        return DashboardDataResponse(
            patient_id=dashboard_data["patient_id"],
            tracked_metrics=dashboard_data["tracked_metrics"],
            trends=trends,
            time_series=time_series,
            summary=DashboardSummary(**dashboard_data["summary"]),
            generated_at=dashboard_data["generated_at"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/advice", response_model=ActionableAdviceResponse)
async def get_actionable_advice(
    limit_reports: int = Query(5, description="Number of recent reports to consider"),
    current_user: Dict[str, Any] = Depends(require_patient_role)
):
    """Get actionable advice based on tracked metrics trends"""
    try:
        patient_id = current_user.uid
        advice = await tracked_metrics_service.generate_actionable_advice(
            patient_id, limit_reports
        )
        
        return ActionableAdviceResponse(advice=advice)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# Hospital endpoints for viewing patient metrics
@router.get("/patient/{patient_id}/tracked", response_model=TrackedMetricsResponse)
async def get_patient_tracked_metrics(
    patient_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get tracked metrics for a specific patient (hospital access)"""
    try:
        # Verify hospital role
        if current_user.user_type != "institution":
            raise HTTPException(status_code=403, detail="Access denied: Hospital role required")
        
        tracked_metrics = await tracked_metrics_service.get_tracked_metrics(patient_id)
        return TrackedMetricsResponse(tracked_metrics=tracked_metrics)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/patient/{patient_id}/dashboard", response_model=DashboardDataResponse)
async def get_patient_dashboard_data(
    patient_id: str,
    days_back: int = Query(365, description="Number of days to look back for data"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get dashboard data for a specific patient (hospital access)"""
    try:
        # Verify hospital role
        if current_user.user_type != "institution":
            raise HTTPException(status_code=403, detail="Access denied: Hospital role required")
        
        dashboard_data = await tracked_metrics_service.get_dashboard_data(
            patient_id, days_back
        )
        
        # Convert nested dictionaries to proper response models
        trends = {}
        for metric_name, trend_data in dashboard_data["trends"].items():
            trends[metric_name] = TrendAnalysisResponse(**trend_data)
        
        time_series = {}
        for metric_name, series_data in dashboard_data["time_series"].items():
            time_series[metric_name] = [TimeSeriesDataPoint(**point) for point in series_data]
        
        return DashboardDataResponse(
            patient_id=dashboard_data["patient_id"],
            tracked_metrics=dashboard_data["tracked_metrics"],
            trends=trends,
            time_series=time_series,
            summary=DashboardSummary(**dashboard_data["summary"]),
            generated_at=dashboard_data["generated_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/patient/{patient_id}/advice", response_model=ActionableAdviceResponse)
async def get_patient_actionable_advice(
    patient_id: str,
    limit_reports: int = Query(5, description="Number of recent reports to consider"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get actionable advice for a specific patient (hospital access)"""
    try:
        # Verify hospital role
        if current_user.user_type != "institution":
            raise HTTPException(status_code=403, detail="Access denied: Hospital role required")
        
        advice = await tracked_metrics_service.generate_actionable_advice(
            patient_id, limit_reports
        )
        
        return ActionableAdviceResponse(advice=advice)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")