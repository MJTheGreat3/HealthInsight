"""
Report upload and processing endpoints
"""

import asyncio
from typing import List, Optional, Union
from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File, BackgroundTasks, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uuid
from datetime import datetime

from app.services.pdf_parser import pdf_parser_service, PDFParsingError
from app.services.database import db_service
from app.services.llm_analysis import llm_analysis_service
from app.models.user import UserModel, PatientModel, InstitutionModel
from app.models.report import Report, ReportCreate, MetricData, LLMReportModel
from app.core.middleware import get_current_user, require_patient_role
from app.services.audit import audit_service, AuditAction


router = APIRouter()


class UploadResponse(BaseModel):
    """Response model for file upload"""
    message: str
    report_id: str
    processing_status: str


class ReportResponse(BaseModel):
    """Response model for report data"""
    report: dict
    message: str


class ReportListResponse(BaseModel):
    """Response model for report list"""
    reports: List[dict]
    total: int
    message: str


# File upload constraints
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_CONTENT_TYPES = ["application/pdf"]


@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_report(
    background_tasks: BackgroundTasks,
    request: Request,
    file: UploadFile = File(...),
    current_user: PatientModel = Depends(require_patient_role)
):
    """
    Upload a PDF medical test report for processing
    
    Args:
        background_tasks: FastAPI background tasks for async processing
        request: FastAPI request object for audit logging
        file: Uploaded PDF file
        current_user: Current authenticated patient user
        
    Returns:
        UploadResponse with report ID and processing status
        
    Raises:
        HTTPException: If file validation fails or upload processing fails
    """
    try:
        # Validate file type
        if file.content_type not in ALLOWED_CONTENT_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type. Only PDF files are allowed. Got: {file.content_type}"
            )
        
        # Read file content
        file_content = await file.read()
        
        # Validate file size
        if len(file_content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB"
            )
        
        # Validate PDF content
        if not pdf_parser_service.validate_pdf_content(file_content):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid PDF file. Please upload a valid PDF document."
            )
        
        # Generate unique report ID
        report_id = str(uuid.uuid4())
        
        # Log upload event
        ip_address = _get_client_ip(request)
        user_agent = request.headers.get("user-agent")
        
        await audit_service.log_user_action(
            current_user,
            AuditAction.UPLOAD_REPORT,
            details={
                "report_id": report_id,
                "filename": file.filename,
                "file_size": len(file_content),
                "content_type": file.content_type
            },
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Schedule background processing
        background_tasks.add_task(
            process_pdf_report,
            report_id=report_id,
            patient_id=current_user.uid,
            pdf_content=file_content,
            filename=file.filename
        )
        
        return UploadResponse(
            message="File uploaded successfully. Processing started.",
            report_id=report_id,
            processing_status="processing"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )


@router.get("/status/{report_id}")
async def get_processing_status(
    report_id: str,
    request: Request,
    current_user: PatientModel = Depends(require_patient_role)
):
    """
    Get processing status of an uploaded report
    
    Args:
        report_id: Unique report identifier
        request: FastAPI request object for audit logging
        current_user: Current authenticated patient user
        
    Returns:
        Processing status and report data if available
        
    Raises:
        HTTPException: If report not found or access denied
    """
    try:
        # Initialize database if needed
        if not db_service.db:
            await db_service.initialize()
        
        # Get report from database
        report_data = await db_service.get_report_by_id(report_id)
        
        if not report_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found"
            )
        
        # Verify ownership
        if report_data.get("patient_id") != current_user.uid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You can only view your own reports."
            )
        
        # Log access event
        ip_address = _get_client_ip(request)
        user_agent = request.headers.get("user-agent")
        
        await audit_service.log_user_action(
            current_user,
            AuditAction.ACCESS_PATIENT_DATA,
            details={
                "action": "get_report_status",
                "report_id": report_id
            },
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Determine processing status
        processing_status = "completed" if report_data.get("attributes") else "processing"
        
        return {
            "report_id": report_id,
            "processing_status": processing_status,
            "processed_at": report_data.get("processed_at"),
            "has_data": bool(report_data.get("attributes")),
            "has_analysis": bool(report_data.get("llm_output")),
            "message": "Report status retrieved successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get report status: {str(e)}"
        )


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: str,
    request: Request,
    current_user: Union[PatientModel, InstitutionModel] = Depends(get_current_user)
):
    """
    Get a specific report by ID
    
    Args:
        report_id: Unique report identifier
        request: FastAPI request object for audit logging
        current_user: Current authenticated user (patient or institution)
        
    Returns:
        ReportResponse with complete report data
        
    Raises:
        HTTPException: If report not found or access denied
    """
    try:
        # Initialize database if needed
        if not db_service.db:
            await db_service.initialize()
        
        # Get report from database
        report_data = await db_service.get_report_by_id(report_id)
        
        if not report_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found"
            )
        
        # Verify access permissions
        patient_id = report_data.get("patient_id")
        
        if isinstance(current_user, PatientModel):
            # Patients can only access their own reports
            if patient_id != current_user.uid:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied. You can only view your own reports."
                )
        elif isinstance(current_user, InstitutionModel):
            # Institutions can access reports of their patients
            if patient_id not in current_user.patient_list:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied. Patient is not in your institution's patient list."
                )
        
        # Log access event
        ip_address = _get_client_ip(request)
        user_agent = request.headers.get("user-agent")
        
        await audit_service.log_user_action(
            current_user,
            AuditAction.ACCESS_PATIENT_DATA,
            details={
                "action": "get_report",
                "report_id": report_id,
                "patient_id": patient_id
            },
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return ReportResponse(
            report=report_data,
            message="Report retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get report: {str(e)}"
        )


@router.get("/", response_model=ReportListResponse)
async def get_reports(
    request: Request,
    skip: int = 0,
    limit: int = 50,
    current_user: Union[PatientModel, InstitutionModel] = Depends(get_current_user)
):
    """
    Get list of reports for current user
    
    Args:
        request: FastAPI request object for audit logging
        skip: Number of reports to skip (pagination)
        limit: Maximum number of reports to return
        current_user: Current authenticated user (patient or institution)
        
    Returns:
        ReportListResponse with list of reports
        
    Raises:
        HTTPException: If database query fails
    """
    try:
        # Initialize database if needed
        if not db_service.db:
            await db_service.initialize()
        
        reports = []
        total = 0
        
        if isinstance(current_user, PatientModel):
            # Get patient's own reports
            reports = await db_service.get_reports_by_patient_id(
                current_user.uid, skip=skip, limit=limit
            )
            total = await db_service.count_reports_by_patient_id(current_user.uid)
            
        elif isinstance(current_user, InstitutionModel):
            # Get reports for all patients in institution
            reports = await db_service.get_reports_by_patient_ids(
                current_user.patient_list, skip=skip, limit=limit
            )
            total = await db_service.count_reports_by_patient_ids(current_user.patient_list)
        
        # Log access event
        ip_address = _get_client_ip(request)
        user_agent = request.headers.get("user-agent")
        
        await audit_service.log_user_action(
            current_user,
            AuditAction.ACCESS_PATIENT_DATA,
            details={
                "action": "list_reports",
                "skip": skip,
                "limit": limit,
                "total_found": total
            },
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return ReportListResponse(
            reports=reports,
            total=total,
            message=f"Retrieved {len(reports)} reports successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get reports: {str(e)}"
        )


@router.delete("/{report_id}")
async def delete_report(
    report_id: str,
    request: Request,
    current_user: PatientModel = Depends(require_patient_role)
):
    """
    Delete a report (patients only)
    
    Args:
        report_id: Unique report identifier
        request: FastAPI request object for audit logging
        current_user: Current authenticated patient user
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If report not found or access denied
    """
    try:
        # Initialize database if needed
        if not db_service.db:
            await db_service.initialize()
        
        # Get report to verify ownership
        report_data = await db_service.get_report_by_id(report_id)
        
        if not report_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found"
            )
        
        # Verify ownership
        if report_data.get("patient_id") != current_user.uid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You can only delete your own reports."
            )
        
        # Delete report
        await db_service.delete_report(report_id)
        
        # Log deletion event
        ip_address = _get_client_ip(request)
        user_agent = request.headers.get("user-agent")
        
        await audit_service.log_user_action(
            current_user,
            AuditAction.DELETE_REPORT,
            details={
                "report_id": report_id,
                "patient_id": current_user.uid
            },
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return {"message": "Report deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete report: {str(e)}"
        )


async def process_pdf_report(report_id: str, patient_id: str, pdf_content: bytes, filename: str):
    """
    Background task to process uploaded PDF report
    
    Args:
        report_id: Unique report identifier
        patient_id: Patient's user ID
        pdf_content: PDF file content as bytes
        filename: Original filename
    """
    try:
        # Initialize database if needed
        if not db_service.db:
            await db_service.initialize()
        
        # Parse PDF to extract medical test data
        extracted_data = await pdf_parser_service.parse_medical_report(pdf_content)
        
        # Create report object
        report = Report(
            report_id=report_id,
            patient_id=patient_id,
            processed_at=datetime.utcnow(),
            attributes=extracted_data,
            llm_output=None,  # Will be populated by AI analysis later
            llm_report_id=None,
            selected_concerns=None
        )
        
        # Save report to database
        await db_service.create_report(report)
        
        # Update patient's report list
        await db_service.add_report_to_patient(patient_id, report_id)
        
        print(f"Successfully processed report {report_id} for patient {patient_id}")
        
    except PDFParsingError as e:
        # Handle PDF parsing errors
        print(f"PDF parsing failed for report {report_id}: {str(e)}")
        
        # Save error report to database
        error_report = Report(
            report_id=report_id,
            patient_id=patient_id,
            processed_at=datetime.utcnow(),
            attributes={},
            llm_output=f"PDF parsing failed: {str(e)}",
            llm_report_id=None,
            selected_concerns=None
        )
        
        await db_service.create_report(error_report)
        
    except Exception as e:
        # Handle other processing errors
        print(f"Report processing failed for report {report_id}: {str(e)}")
        
        # Save error report to database
        error_report = Report(
            report_id=report_id,
            patient_id=patient_id,
            processed_at=datetime.utcnow(),
            attributes={},
            llm_output=f"Processing failed: {str(e)}",
            llm_report_id=None,
            selected_concerns=None
        )
        
        try:
            await db_service.create_report(error_report)
        except Exception as db_error:
            print(f"Failed to save error report {report_id}: {str(db_error)}")


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


# AI Analysis Endpoints

class AnalysisRequest(BaseModel):
    """Request model for AI analysis generation"""
    report_id: str
    include_profile: bool = True


class AnalysisResponse(BaseModel):
    """Response model for AI analysis"""
    analysis: dict
    report_id: str
    llm_report_id: Optional[str] = None
    message: str


class TrendAnalysisRequest(BaseModel):
    """Request model for trend analysis"""
    tracked_metrics: List[str]
    max_reports: int = 5


class TrendAnalysisResponse(BaseModel):
    """Response model for trend analysis"""
    trend_analysis: dict
    patient_id: str
    metrics_analyzed: List[str]
    reports_used: int
    message: str


@router.post("/{report_id}/analyze", response_model=AnalysisResponse)
async def generate_analysis(
    report_id: str,
    analysis_request: AnalysisRequest,
    request: Request,
    current_user: Union[PatientModel, InstitutionModel] = Depends(get_current_user)
):
    """
    Generate AI analysis for a specific report
    
    Args:
        report_id: Unique report identifier
        analysis_request: Analysis generation parameters
        request: FastAPI request object for audit logging
        current_user: Current authenticated user (patient or institution)
        
    Returns:
        AnalysisResponse with AI-generated health analysis
        
    Raises:
        HTTPException: If report not found, access denied, or analysis fails
    """
    try:
        # Initialize database if needed
        if not db_service.db:
            await db_service.initialize()
        
        # Get report from database
        report_data = await db_service.get_report_by_id(report_id)
        
        if not report_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found"
            )
        
        # Verify access permissions
        patient_id = report_data.get("patient_id")
        
        if isinstance(current_user, PatientModel):
            # Patients can only analyze their own reports
            if patient_id != current_user.uid:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied. You can only analyze your own reports."
                )
        elif isinstance(current_user, InstitutionModel):
            # Institutions can analyze reports of their patients
            if patient_id not in current_user.patient_list:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied. Patient is not in your institution's patient list."
                )
        
        # Check if report has test data
        attributes = report_data.get("attributes", {})
        if not attributes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Report has no test data to analyze. Please ensure the PDF was processed successfully."
            )
        
        # Convert attributes to MetricData objects
        test_data = {}
        for key, attr_data in attributes.items():
            if isinstance(attr_data, dict):
                test_data[key] = MetricData(**attr_data)
            else:
                # Handle legacy data format
                test_data[key] = attr_data
        
        # Get patient profile if requested
        patient_profile = None
        if analysis_request.include_profile:
            patient_profile = await db_service.get_user_by_uid(patient_id)
        
        # Generate AI analysis
        llm_report = await llm_analysis_service.analyze_test_results(
            patient_id=patient_id,
            report_id=report_id,
            test_data=test_data,
            patient_profile=patient_profile
        )
        
        # Save LLM report to database
        llm_report_id = await db_service.create_llm_report(llm_report)
        
        # Update original report with LLM output reference
        await db_service.update_report(
            report_id, 
            {"llm_output": str(llm_report.output), "llm_report_id": llm_report_id}
        )
        
        # Log analysis event
        ip_address = _get_client_ip(request)
        user_agent = request.headers.get("user-agent")
        
        await audit_service.log_user_action(
            current_user,
            AuditAction.ACCESS_PATIENT_DATA,
            details={
                "action": "generate_analysis",
                "report_id": report_id,
                "patient_id": patient_id,
                "llm_report_id": llm_report_id,
                "include_profile": analysis_request.include_profile
            },
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return AnalysisResponse(
            analysis=llm_report.output,
            report_id=report_id,
            llm_report_id=llm_report_id,
            message="AI analysis generated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate analysis: {str(e)}"
        )


@router.get("/{report_id}/analysis", response_model=AnalysisResponse)
async def get_analysis(
    report_id: str,
    request: Request,
    current_user: Union[PatientModel, InstitutionModel] = Depends(get_current_user)
):
    """
    Get existing AI analysis for a specific report
    
    Args:
        report_id: Unique report identifier
        request: FastAPI request object for audit logging
        current_user: Current authenticated user (patient or institution)
        
    Returns:
        AnalysisResponse with existing AI analysis
        
    Raises:
        HTTPException: If report not found, access denied, or no analysis exists
    """
    try:
        # Initialize database if needed
        if not db_service.db:
            await db_service.initialize()
        
        # Get report from database
        report_data = await db_service.get_report_by_id(report_id)
        
        if not report_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found"
            )
        
        # Verify access permissions
        patient_id = report_data.get("patient_id")
        
        if isinstance(current_user, PatientModel):
            if patient_id != current_user.uid:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied. You can only view your own analyses."
                )
        elif isinstance(current_user, InstitutionModel):
            if patient_id not in current_user.patient_list:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied. Patient is not in your institution's patient list."
                )
        
        # Check if analysis exists
        llm_output = report_data.get("llm_output")
        llm_report_id = report_data.get("llm_report_id")
        
        if not llm_output:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No AI analysis found for this report. Generate analysis first."
            )
        
        # Parse LLM output
        try:
            if isinstance(llm_output, str):
                import json
                analysis_data = json.loads(llm_output)
            else:
                analysis_data = llm_output
        except (json.JSONDecodeError, TypeError):
            analysis_data = {"error": "Failed to parse analysis data", "raw_output": str(llm_output)}
        
        # Log access event
        ip_address = _get_client_ip(request)
        user_agent = request.headers.get("user-agent")
        
        await audit_service.log_user_action(
            current_user,
            AuditAction.ACCESS_PATIENT_DATA,
            details={
                "action": "get_analysis",
                "report_id": report_id,
                "patient_id": patient_id,
                "llm_report_id": llm_report_id
            },
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return AnalysisResponse(
            analysis=analysis_data,
            report_id=report_id,
            llm_report_id=llm_report_id,
            message="AI analysis retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get analysis: {str(e)}"
        )


@router.post("/trends/analyze", response_model=TrendAnalysisResponse)
async def generate_trend_analysis(
    trend_request: TrendAnalysisRequest,
    request: Request,
    current_user: PatientModel = Depends(require_patient_role)
):
    """
    Generate trend analysis for tracked metrics across multiple reports
    
    Args:
        trend_request: Trend analysis parameters
        request: FastAPI request object for audit logging
        current_user: Current authenticated patient user
        
    Returns:
        TrendAnalysisResponse with trend analysis and insights
        
    Raises:
        HTTPException: If insufficient data or analysis fails
    """
    try:
        # Initialize database if needed
        if not db_service.db:
            await db_service.initialize()
        
        # Get recent reports for the patient
        recent_reports = await db_service.get_reports_by_patient_id(
            current_user.uid, 
            skip=0, 
            limit=trend_request.max_reports
        )
        
        if len(recent_reports) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient data for trend analysis. At least 2 reports are required."
            )
        
        # Get patient profile
        patient_profile = await db_service.get_user_by_uid(current_user.uid)
        
        # Generate trend analysis
        trend_analysis = await llm_analysis_service.generate_trend_analysis(
            patient_id=current_user.uid,
            tracked_metrics=trend_request.tracked_metrics,
            recent_reports=recent_reports,
            patient_profile=patient_profile
        )
        
        # Log trend analysis event
        ip_address = _get_client_ip(request)
        user_agent = request.headers.get("user-agent")
        
        await audit_service.log_user_action(
            current_user,
            AuditAction.ACCESS_PATIENT_DATA,
            details={
                "action": "generate_trend_analysis",
                "patient_id": current_user.uid,
                "tracked_metrics": trend_request.tracked_metrics,
                "reports_analyzed": len(recent_reports)
            },
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return TrendAnalysisResponse(
            trend_analysis=trend_analysis,
            patient_id=current_user.uid,
            metrics_analyzed=trend_request.tracked_metrics,
            reports_used=len(recent_reports),
            message="Trend analysis generated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate trend analysis: {str(e)}"
        )


@router.put("/{report_id}/concerns")
async def update_selected_concerns(
    report_id: str,
    concerns: List[str],
    request: Request,
    current_user: PatientModel = Depends(require_patient_role)
):
    """
    Update selected concerns (tracked metrics) for a report
    
    Args:
        report_id: Unique report identifier
        concerns: List of metric names to track
        request: FastAPI request object for audit logging
        current_user: Current authenticated patient user
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If report not found or access denied
    """
    try:
        # Initialize database if needed
        if not db_service.db:
            await db_service.initialize()
        
        # Get report to verify ownership
        report_data = await db_service.get_report_by_id(report_id)
        
        if not report_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found"
            )
        
        # Verify ownership
        if report_data.get("patient_id") != current_user.uid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You can only update your own reports."
            )
        
        # Update selected concerns
        await db_service.update_report(report_id, {"selected_concerns": concerns})
        
        # Update patient's favorites (tracked metrics)
        await db_service.update_user_favorites(current_user.uid, concerns)
        
        # Log update event
        ip_address = _get_client_ip(request)
        user_agent = request.headers.get("user-agent")
        
        await audit_service.log_user_action(
            current_user,
            AuditAction.ACCESS_PATIENT_DATA,
            details={
                "action": "update_concerns",
                "report_id": report_id,
                "concerns": concerns
            },
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return {
            "message": "Selected concerns updated successfully",
            "report_id": report_id,
            "concerns": concerns
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update concerns: {str(e)}"
        )