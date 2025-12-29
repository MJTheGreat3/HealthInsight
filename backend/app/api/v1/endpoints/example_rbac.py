"""
Example endpoints demonstrating role-based access control
"""

from typing import Union
from fastapi import APIRouter, Depends, Request
from app.models.user import UserType, UserModel, PatientModel, InstitutionModel
from app.core.middleware import (
    get_current_user, 
    get_current_patient, 
    get_current_institution,
    require_roles,
    auth_middleware
)
from app.services.audit import audit_service, AuditAction


router = APIRouter()


@router.get("/public")
async def public_endpoint():
    """
    Public endpoint that doesn't require authentication
    
    Returns:
        Public message
    """
    return {"message": "This is a public endpoint accessible to everyone"}


@router.get("/authenticated")
async def authenticated_endpoint(
    request: Request,
    current_user: Union[UserModel, PatientModel, InstitutionModel] = Depends(get_current_user)
):
    """
    Endpoint that requires any valid authentication
    
    Args:
        request: FastAPI request object for audit logging
        current_user: Current authenticated user
        
    Returns:
        Message with user information
    """
    # Log access to authenticated endpoint
    ip_address = _get_client_ip(request)
    user_agent = request.headers.get("user-agent")
    
    await audit_service.log_user_action(
        current_user,
        AuditAction.ACCESS_PATIENT_DATA,
        details={"endpoint": "authenticated", "action": "access"},
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    return {
        "message": "This endpoint requires authentication",
        "user": {
            "uid": current_user.uid,
            "type": current_user.user_type.value if current_user.user_type else "unknown",
            "name": getattr(current_user, 'name', 'Unknown')
        }
    }


@router.get("/patient-only")
async def patient_only_endpoint(
    request: Request,
    current_patient: Union[PatientModel, UserModel] = Depends(get_current_patient)
):
    """
    Endpoint that requires patient role
    
    Args:
        request: FastAPI request object for audit logging
        current_patient: Current authenticated patient
        
    Returns:
        Patient-specific message
    """
    # Log patient access
    ip_address = _get_client_ip(request)
    user_agent = request.headers.get("user-agent")
    
    await audit_service.log_user_action(
        current_patient,
        AuditAction.ACCESS_PATIENT_DATA,
        details={"endpoint": "patient-only", "action": "access_own_data"},
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    return {
        "message": "This endpoint is only accessible to patients",
        "patient": {
            "uid": current_patient.uid,
            "name": getattr(current_patient, 'name', 'Unknown Patient'),
            "favorites": getattr(current_patient, 'favorites', []),
            "reports_count": len(getattr(current_patient, 'reports', []))
        }
    }


@router.get("/hospital-only")
async def hospital_only_endpoint(
    request: Request,
    current_institution: Union[InstitutionModel, UserModel] = Depends(get_current_institution)
):
    """
    Endpoint that requires institution role
    
    Args:
        request: FastAPI request object for audit logging
        current_institution: Current authenticated institution
        
    Returns:
        Institution-specific message
    """
    # Log hospital access
    ip_address = _get_client_ip(request)
    user_agent = request.headers.get("user-agent")
    
    await audit_service.log_user_action(
        current_institution,
        AuditAction.ACCESS_PATIENT_DATA,
        details={"endpoint": "hospital-only", "action": "access_hospital_features"},
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    return {
        "message": "This endpoint is only accessible to hospitals",
        "institution": {
            "uid": current_institution.uid,
            "name": getattr(current_institution, 'name', 'Unknown Institution'),
            "patients_count": len(getattr(current_institution, 'patient_list', []))
        }
    }


@router.get("/patient-or-hospital")
async def patient_or_hospital_endpoint(
    request: Request,
    current_user: Union[UserModel, PatientModel, InstitutionModel] = Depends(
        require_roles([UserType.PATIENT, UserType.INSTITUTION])
    )
):
    """
    Endpoint that requires either patient or institution role
    
    Args:
        request: FastAPI request object for audit logging
        current_user: Current authenticated user (patient or institution)
        
    Returns:
        Message accessible to both patients and hospitals
    """
    # Log multi-role access
    ip_address = _get_client_ip(request)
    user_agent = request.headers.get("user-agent")
    
    await audit_service.log_user_action(
        current_user,
        AuditAction.ACCESS_PATIENT_DATA,
        details={
            "endpoint": "patient-or-hospital", 
            "action": "access_shared_features",
            "user_role": current_user.user_type.value if current_user.user_type else "unknown"
        },
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    return {
        "message": "This endpoint is accessible to both patients and hospitals",
        "user": {
            "uid": current_user.uid,
            "type": current_user.user_type.value if current_user.user_type else "unknown",
            "name": getattr(current_user, 'name', 'Unknown User')
        }
    }


@router.get("/hospital/patient/{patient_id}")
async def hospital_access_patient_data(
    patient_id: str,
    request: Request,
    current_institution: Union[InstitutionModel, UserModel] = Depends(get_current_institution)
):
    """
    Example endpoint for hospital accessing patient data with audit logging
    
    Args:
        patient_id: ID of patient being accessed
        request: FastAPI request object for audit logging
        current_institution: Current authenticated institution
        
    Returns:
        Patient data access confirmation with audit logging
    """
    # Log hospital access to specific patient data (compliance requirement)
    await auth_middleware.log_patient_access(
        current_institution,
        patient_id,
        AuditAction.VIEW_PATIENT_DASHBOARD,
        request=request,
        details={
            "endpoint": "hospital_access_patient_data",
            "action": "view_patient_dashboard",
            "patient_id": patient_id
        }
    )
    
    return {
        "message": f"Hospital {current_institution.uid} accessed patient {patient_id} data",
        "patient_id": patient_id,
        "hospital": {
            "uid": current_institution.uid,
            "name": getattr(current_institution, 'name', 'Unknown Institution')
        },
        "audit_logged": True
    }


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