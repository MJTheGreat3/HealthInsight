"""
Search and filtering API endpoints
"""

from typing import List, Optional, Union
from datetime import datetime
from fastapi import APIRouter, HTTPException, status, Depends, Query, Request
from pydantic import BaseModel, Field

from app.services.search import search_service, SearchFilters, SortOrder, SearchType
from app.services.database import db_service
from app.services.audit import audit_service, AuditAction
from app.models.user import PatientModel, InstitutionModel
from app.core.middleware import get_current_user, get_current_institution, require_patient_role


router = APIRouter()


class SearchRequest(BaseModel):
    """Request model for search operations"""
    query: Optional[str] = Field(None, description="Search query string")
    date_from: Optional[datetime] = Field(None, description="Start date for filtering")
    date_to: Optional[datetime] = Field(None, description="End date for filtering")
    metric_names: Optional[List[str]] = Field(None, description="List of metric names to filter by")
    verdict_types: Optional[List[str]] = Field(None, description="List of verdict types (NORMAL, HIGH, LOW, CRITICAL)")
    has_analysis: Optional[bool] = Field(None, description="Filter by presence of AI analysis")
    sort_by: str = Field("processed_at", description="Field to sort by")
    sort_order: SortOrder = Field(SortOrder.DESC, description="Sort order (asc/desc)")
    skip: int = Field(0, ge=0, description="Number of items to skip (pagination)")
    limit: int = Field(50, ge=1, le=100, description="Maximum number of items to return")


class PatientSearchRequest(BaseModel):
    """Request model for patient search operations"""
    query: str = Field(..., description="Search query string")
    sort_by: str = Field("name", description="Field to sort by")
    sort_order: SortOrder = Field(SortOrder.ASC, description="Sort order (asc/desc)")
    skip: int = Field(0, ge=0, description="Number of items to skip (pagination)")
    limit: int = Field(50, ge=1, le=100, description="Maximum number of items to return")


class MetricSearchRequest(BaseModel):
    """Request model for metric search operations"""
    patient_id: str = Field(..., description="Patient ID to search metrics for")
    metric_names: List[str] = Field(..., description="List of metric names to search for")
    date_from: Optional[datetime] = Field(None, description="Start date for filtering")
    date_to: Optional[datetime] = Field(None, description="End date for filtering")
    sort_by: str = Field("processed_at", description="Field to sort by")
    sort_order: SortOrder = Field(SortOrder.DESC, description="Sort order (asc/desc)")
    skip: int = Field(0, ge=0, description="Number of items to skip (pagination)")
    limit: int = Field(50, ge=1, le=100, description="Maximum number of items to return")


class SearchResponse(BaseModel):
    """Response model for search operations"""
    items: List[dict] = Field(..., description="Search results")
    total: int = Field(..., description="Total number of matching items")
    search_type: SearchType = Field(..., description="Type of search performed")
    filters_applied: dict = Field(..., description="Summary of filters applied")
    execution_time_ms: float = Field(..., description="Search execution time in milliseconds")
    message: str = Field(..., description="Response message")


def _get_client_ip(request: Request) -> str:
    """Extract client IP address from request"""
    # Check for forwarded headers first (for reverse proxies)
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip
    
    # Fall back to direct client IP
    if hasattr(request, "client") and request.client:
        return request.client.host
    
    return "unknown"


@router.post("/patients", response_model=SearchResponse)
async def search_patients(
    search_request: PatientSearchRequest,
    request: Request,
    current_user: InstitutionModel = Depends(get_current_institution)
):
    """
    Search patients (hospital users only)
    
    Args:
        search_request: Patient search parameters
        request: FastAPI request object for audit logging
        current_user: Current authenticated hospital user
        
    Returns:
        SearchResponse with matching patients
        
    Raises:
        HTTPException: If search fails or access denied
    """
    try:
        # Initialize database if needed
        if not db_service.db:
            await db_service.initialize()
        
        # Create search filters
        filters = SearchFilters(
            query=search_request.query,
            sort_by=search_request.sort_by,
            sort_order=search_request.sort_order,
            skip=search_request.skip,
            limit=search_request.limit
        )
        
        # Perform search
        search_result = await search_service.search_patients(
            query=search_request.query,
            requesting_user=current_user,
            filters=filters
        )
        
        # Log search event
        ip_address = _get_client_ip(request)
        user_agent = request.headers.get("user-agent")
        
        await audit_service.log_user_action(
            current_user,
            AuditAction.SEARCH_PATIENTS,
            details={
                "query": search_request.query,
                "results_found": search_result.total,
                "execution_time_ms": search_result.execution_time_ms
            },
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return SearchResponse(
            items=search_result.items,
            total=search_result.total,
            search_type=search_result.search_type,
            filters_applied=search_result.filters_applied,
            execution_time_ms=search_result.execution_time_ms,
            message=f"Found {search_result.total} patients matching search criteria"
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Patient search failed: {str(e)}"
        )


@router.post("/reports", response_model=SearchResponse)
async def search_reports(
    search_request: SearchRequest,
    request: Request,
    patient_id: Optional[str] = Query(None, description="Patient ID to search reports for"),
    current_user: Union[PatientModel, InstitutionModel] = Depends(get_current_user)
):
    """
    Search reports with advanced filtering
    
    Args:
        search_request: Report search parameters
        request: FastAPI request object for audit logging
        patient_id: Patient ID to search reports for (optional for patients)
        current_user: Current authenticated user
        
    Returns:
        SearchResponse with matching reports
        
    Raises:
        HTTPException: If search fails or access denied
    """
    try:
        # Initialize database if needed
        if not db_service.db:
            await db_service.initialize()
        
        # Determine patient ID
        target_patient_id = patient_id
        if isinstance(current_user, PatientModel):
            # Patients can only search their own reports
            target_patient_id = current_user.uid
        elif isinstance(current_user, InstitutionModel):
            # Hospitals must specify patient ID
            if not patient_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Patient ID is required for hospital users"
                )
            target_patient_id = patient_id
        
        if not target_patient_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Patient ID is required"
            )
        
        # Create search filters
        filters = SearchFilters(
            query=search_request.query,
            date_from=search_request.date_from,
            date_to=search_request.date_to,
            metric_names=search_request.metric_names,
            verdict_types=search_request.verdict_types,
            has_analysis=search_request.has_analysis,
            sort_by=search_request.sort_by,
            sort_order=search_request.sort_order,
            skip=search_request.skip,
            limit=search_request.limit
        )
        
        # Perform search
        search_result = await search_service.search_reports(
            patient_id=target_patient_id,
            query=search_request.query,
            requesting_user=current_user,
            filters=filters
        )
        
        # Log search event
        ip_address = _get_client_ip(request)
        user_agent = request.headers.get("user-agent")
        
        await audit_service.log_user_action(
            current_user,
            AuditAction.ACCESS_PATIENT_DATA,
            details={
                "action": "search_reports",
                "patient_id": target_patient_id,
                "query": search_request.query,
                "results_found": search_result.total,
                "execution_time_ms": search_result.execution_time_ms,
                "filters_applied": search_result.filters_applied
            },
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return SearchResponse(
            items=search_result.items,
            total=search_result.total,
            search_type=search_result.search_type,
            filters_applied=search_result.filters_applied,
            execution_time_ms=search_result.execution_time_ms,
            message=f"Found {search_result.total} reports matching search criteria"
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Report search failed: {str(e)}"
        )


@router.post("/metrics", response_model=SearchResponse)
async def search_metrics(
    search_request: MetricSearchRequest,
    request: Request,
    current_user: Union[PatientModel, InstitutionModel] = Depends(get_current_user)
):
    """
    Search for specific metrics across multiple reports
    
    Args:
        search_request: Metric search parameters
        request: FastAPI request object for audit logging
        current_user: Current authenticated user
        
    Returns:
        SearchResponse with matching metric data
        
    Raises:
        HTTPException: If search fails or access denied
    """
    try:
        # Initialize database if needed
        if not db_service.db:
            await db_service.initialize()
        
        # Create search filters
        filters = SearchFilters(
            date_from=search_request.date_from,
            date_to=search_request.date_to,
            sort_by=search_request.sort_by,
            sort_order=search_request.sort_order,
            skip=search_request.skip,
            limit=search_request.limit
        )
        
        # Perform search
        search_result = await search_service.search_metrics(
            patient_id=search_request.patient_id,
            metric_names=search_request.metric_names,
            requesting_user=current_user,
            filters=filters
        )
        
        # Log search event
        ip_address = _get_client_ip(request)
        user_agent = request.headers.get("user-agent")
        
        await audit_service.log_user_action(
            current_user,
            AuditAction.ACCESS_PATIENT_DATA,
            details={
                "action": "search_metrics",
                "patient_id": search_request.patient_id,
                "metric_names": search_request.metric_names,
                "results_found": search_result.total,
                "execution_time_ms": search_result.execution_time_ms
            },
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return SearchResponse(
            items=search_result.items,
            total=search_result.total,
            search_type=search_result.search_type,
            filters_applied=search_result.filters_applied,
            execution_time_ms=search_result.execution_time_ms,
            message=f"Found {search_result.total} metric entries matching search criteria"
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Metric search failed: {str(e)}"
        )


@router.get("/reports/history")
async def get_report_history(
    request: Request,
    query: Optional[str] = Query(None, description="Search query"),
    date_from: Optional[datetime] = Query(None, description="Start date filter"),
    date_to: Optional[datetime] = Query(None, description="End date filter"),
    has_analysis: Optional[bool] = Query(None, description="Filter by analysis presence"),
    sort_by: str = Query("processed_at", description="Sort field"),
    sort_order: SortOrder = Query(SortOrder.DESC, description="Sort order"),
    skip: int = Query(0, ge=0, description="Skip items"),
    limit: int = Query(50, ge=1, le=100, description="Limit items"),
    current_user: PatientModel = Depends(require_patient_role)
):
    """
    Get patient's report history with search and filtering (patients only)
    
    Args:
        request: FastAPI request object for audit logging
        query: Optional search query
        date_from: Optional start date filter
        date_to: Optional end date filter
        has_analysis: Optional analysis presence filter
        sort_by: Field to sort by
        sort_order: Sort order
        skip: Number of items to skip
        limit: Maximum items to return
        current_user: Current authenticated patient user
        
    Returns:
        SearchResponse with patient's report history
        
    Raises:
        HTTPException: If search fails
    """
    try:
        # Initialize database if needed
        if not db_service.db:
            await db_service.initialize()
        
        # Create search filters
        filters = SearchFilters(
            query=query,
            date_from=date_from,
            date_to=date_to,
            has_analysis=has_analysis,
            sort_by=sort_by,
            sort_order=sort_order,
            skip=skip,
            limit=limit
        )
        
        # Perform search
        search_result = await search_service.search_reports(
            patient_id=current_user.uid,
            query=query,
            requesting_user=current_user,
            filters=filters
        )
        
        # Log access event
        ip_address = _get_client_ip(request)
        user_agent = request.headers.get("user-agent")
        
        await audit_service.log_user_action(
            current_user,
            AuditAction.ACCESS_PATIENT_DATA,
            details={
                "action": "get_report_history",
                "patient_id": current_user.uid,
                "query": query,
                "results_found": search_result.total,
                "execution_time_ms": search_result.execution_time_ms
            },
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return SearchResponse(
            items=search_result.items,
            total=search_result.total,
            search_type=search_result.search_type,
            filters_applied=search_result.filters_applied,
            execution_time_ms=search_result.execution_time_ms,
            message=f"Retrieved {len(search_result.items)} reports from history"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get report history: {str(e)}"
        )


@router.get("/patients/all")
async def get_all_patients(
    request: Request,
    query: Optional[str] = Query(None, description="Search query"),
    sort_by: str = Query("name", description="Sort field"),
    sort_order: SortOrder = Query(SortOrder.ASC, description="Sort order"),
    skip: int = Query(0, ge=0, description="Skip items"),
    limit: int = Query(50, ge=1, le=100, description="Limit items"),
    current_user: InstitutionModel = Depends(get_current_institution)
):
    """
    Get all patients with optional search (hospital users only)
    
    Args:
        request: FastAPI request object for audit logging
        query: Optional search query
        sort_by: Field to sort by
        sort_order: Sort order
        skip: Number of items to skip
        limit: Maximum items to return
        current_user: Current authenticated hospital user
        
    Returns:
        SearchResponse with all patients
        
    Raises:
        HTTPException: If search fails
    """
    try:
        # Initialize database if needed
        if not db_service.db:
            await db_service.initialize()
        
        # Use empty query if none provided
        search_query = query or ""
        
        # Create search filters
        filters = SearchFilters(
            query=search_query,
            sort_by=sort_by,
            sort_order=sort_order,
            skip=skip,
            limit=limit
        )
        
        # Perform search
        search_result = await search_service.search_patients(
            query=search_query,
            requesting_user=current_user,
            filters=filters
        )
        
        # Log access event
        ip_address = _get_client_ip(request)
        user_agent = request.headers.get("user-agent")
        
        await audit_service.log_user_action(
            current_user,
            AuditAction.SEARCH_PATIENTS,
            details={
                "action": "get_all_patients",
                "query": search_query,
                "results_found": search_result.total,
                "execution_time_ms": search_result.execution_time_ms
            },
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return SearchResponse(
            items=search_result.items,
            total=search_result.total,
            search_type=search_result.search_type,
            filters_applied=search_result.filters_applied,
            execution_time_ms=search_result.execution_time_ms,
            message=f"Retrieved {len(search_result.items)} patients"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get patients: {str(e)}"
        )