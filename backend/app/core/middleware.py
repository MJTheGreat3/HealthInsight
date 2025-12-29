"""
Authentication middleware for FastAPI
"""

from typing import Optional, Union
from fastapi import HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.services.auth import AuthService
from app.models.user import UserType, UserModel, PatientModel, InstitutionModel
from app.services.audit import audit_service, AuditAction, AuditLevel


class AuthMiddleware:
    """Authentication middleware for FastAPI"""
    
    def __init__(self):
        self.auth_service = AuthService()
        self.security = HTTPBearer()
    
    async def authenticate_request(
        self, 
        credentials: HTTPAuthorizationCredentials,
        request: Optional[Request] = None
    ) -> Union[UserModel, PatientModel, InstitutionModel]:
        """
        Authenticate request using Bearer token
        
        Args:
            credentials: HTTP authorization credentials
            request: FastAPI request object for audit logging
            
        Returns:
            Authenticated user model
            
        Raises:
            HTTPException: If authentication fails
        """
        if not credentials or not credentials.credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing authentication token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        try:
            user = await self.auth_service.authenticate_user(credentials.credentials)
            
            # Log successful authentication for audit
            if request:
                ip_address = self._get_client_ip(request)
                user_agent = request.headers.get("user-agent")
                
                await audit_service.log_authentication_event(
                    user,
                    AuditAction.LOGIN,
                    success=True,
                    ip_address=ip_address,
                    user_agent=user_agent
                )
            
            return user
            
        except HTTPException as e:
            # Log failed authentication attempt
            if request:
                ip_address = self._get_client_ip(request)
                user_agent = request.headers.get("user-agent")
                
                # Create a minimal user object for logging failed attempts
                failed_user = UserModel(uid="unknown", user_type=None)
                await audit_service.log_authentication_event(
                    failed_user,
                    AuditAction.LOGIN,
                    success=False,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    error_details=str(e.detail)
                )
            
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Authentication error: {str(e)}"
            )
    
    async def require_authentication(
        self, 
        credentials: HTTPAuthorizationCredentials,
        request: Optional[Request] = None
    ) -> Union[UserModel, PatientModel, InstitutionModel]:
        """
        Require valid authentication for endpoint access
        
        Args:
            credentials: HTTP authorization credentials
            request: FastAPI request object for audit logging
            
        Returns:
            Authenticated user model
        """
        return await self.authenticate_request(credentials, request)
    
    async def require_patient_role(
        self, 
        credentials: HTTPAuthorizationCredentials,
        request: Optional[Request] = None
    ) -> Union[PatientModel, UserModel]:
        """
        Require patient role for endpoint access
        
        Args:
            credentials: HTTP authorization credentials
            request: FastAPI request object for audit logging
            
        Returns:
            Authenticated patient user model
            
        Raises:
            HTTPException: If user is not a patient
        """
        user = await self.authenticate_request(credentials, request)
        
        if not self.auth_service.validate_user_role(user, UserType.PATIENT):
            # Log unauthorized access attempt
            if request:
                ip_address = self._get_client_ip(request)
                user_agent = request.headers.get("user-agent")
                
                await audit_service.log_user_action(
                    user,
                    AuditAction.ACCESS_PATIENT_DATA,
                    AuditLevel.WARNING,
                    {"error": "Non-patient user attempted patient-only access"},
                    ip_address=ip_address,
                    user_agent=user_agent
                )
            
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Patient access required"
            )
        
        return user
    
    async def require_institution_role(
        self, 
        credentials: HTTPAuthorizationCredentials,
        request: Optional[Request] = None
    ) -> Union[InstitutionModel, UserModel]:
        """
        Require institution role for endpoint access
        
        Args:
            credentials: HTTP authorization credentials
            request: FastAPI request object for audit logging
            
        Returns:
            Authenticated institution user model
            
        Raises:
            HTTPException: If user is not an institution
        """
        user = await self.authenticate_request(credentials, request)
        
        if not self.auth_service.validate_user_role(user, UserType.INSTITUTION):
            # Log unauthorized access attempt
            if request:
                ip_address = self._get_client_ip(request)
                user_agent = request.headers.get("user-agent")
                
                await audit_service.log_user_action(
                    user,
                    AuditAction.ACCESS_PATIENT_DATA,
                    AuditLevel.WARNING,
                    {"error": "Non-institution user attempted institution-only access"},
                    ip_address=ip_address,
                    user_agent=user_agent
                )
            
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Institution access required"
            )
        
        return user
    
    async def require_any_role(
        self, 
        credentials: HTTPAuthorizationCredentials, 
        allowed_roles: list[UserType],
        request: Optional[Request] = None
    ) -> Union[UserModel, PatientModel, InstitutionModel]:
        """
        Require any of the specified roles for endpoint access
        
        Args:
            credentials: HTTP authorization credentials
            allowed_roles: List of allowed user types
            request: FastAPI request object for audit logging
            
        Returns:
            Authenticated user model
            
        Raises:
            HTTPException: If user doesn't have any of the required roles
        """
        user = await self.authenticate_request(credentials, request)
        
        if not self.auth_service.validate_user_roles(user, allowed_roles):
            # Log unauthorized access attempt
            if request:
                ip_address = self._get_client_ip(request)
                user_agent = request.headers.get("user-agent")
                
                role_names = [role.value for role in allowed_roles]
                await audit_service.log_user_action(
                    user,
                    AuditAction.ACCESS_PATIENT_DATA,
                    AuditLevel.WARNING,
                    {
                        "error": f"User with role {user.user_type} attempted access requiring roles: {role_names}",
                        "required_roles": role_names,
                        "user_role": user.user_type.value if user.user_type else "unknown"
                    },
                    ip_address=ip_address,
                    user_agent=user_agent
                )
            
            role_names = [role.value for role in allowed_roles]
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access requires one of the following roles: {', '.join(role_names)}"
            )
        
        return user
    
    async def log_patient_access(
        self,
        hospital_user: Union[InstitutionModel, UserModel],
        patient_id: str,
        action: AuditAction,
        request: Optional[Request] = None,
        details: Optional[dict] = None
    ) -> None:
        """
        Log hospital user access to patient data for compliance
        
        Args:
            hospital_user: Hospital user accessing patient data
            patient_id: ID of patient being accessed
            action: Type of access being performed
            request: FastAPI request object for audit logging
            details: Additional details about the access
        """
        ip_address = None
        user_agent = None
        
        if request:
            ip_address = self._get_client_ip(request)
            user_agent = request.headers.get("user-agent")
        
        await audit_service.log_hospital_patient_access(
            hospital_user,
            patient_id,
            action,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    def _get_client_ip(self, request: Request) -> str:
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


# Global middleware instance
auth_middleware = AuthMiddleware()


# Dependency functions for FastAPI endpoints
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = HTTPBearer(),
    request: Request = None
) -> Union[UserModel, PatientModel, InstitutionModel]:
    """Dependency to get current authenticated user"""
    return await auth_middleware.require_authentication(credentials, request)


async def get_current_patient(
    credentials: HTTPAuthorizationCredentials = HTTPBearer(),
    request: Request = None
) -> Union[PatientModel, UserModel]:
    """Dependency to get current authenticated patient"""
    return await auth_middleware.require_patient_role(credentials, request)


async def require_patient_role(
    credentials: HTTPAuthorizationCredentials = HTTPBearer(),
    request: Request = None
) -> Union[PatientModel, UserModel]:
    """Dependency to require patient role (alias for get_current_patient)"""
    return await auth_middleware.require_patient_role(credentials, request)


async def get_current_institution(
    credentials: HTTPAuthorizationCredentials = HTTPBearer(),
    request: Request = None
) -> Union[InstitutionModel, UserModel]:
    """Dependency to get current authenticated institution"""
    return await auth_middleware.require_institution_role(credentials, request)


def require_roles(allowed_roles: list[UserType]):
    """
    Dependency factory to require specific roles
    
    Args:
        allowed_roles: List of allowed user types
        
    Returns:
        Dependency function
    """
    async def role_dependency(
        credentials: HTTPAuthorizationCredentials = HTTPBearer(),
        request: Request = None
    ) -> Union[UserModel, PatientModel, InstitutionModel]:
        return await auth_middleware.require_any_role(credentials, allowed_roles, request)
    
    return role_dependency