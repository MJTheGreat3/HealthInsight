"""
Authentication endpoints for user registration and login
"""

from typing import Union
from fastapi import APIRouter, HTTPException, status, Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from app.services.auth import AuthService
from app.models.user import UserType, UserModel, PatientModel, InstitutionModel
from app.models.requests import OnboardRequest
from app.core.middleware import get_current_user
from app.services.audit import audit_service, AuditAction


router = APIRouter()
auth_service = AuthService()
security = HTTPBearer()


class AuthResponse(BaseModel):
    """Response model for authentication endpoints"""
    message: str
    user: dict
    user_type: str


class LoginResponse(BaseModel):
    """Response model for login endpoint"""
    message: str
    user: dict
    user_type: str
    is_new_user: bool


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    onboard_request: OnboardRequest,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Register a new user with specified role
    
    Args:
        onboard_request: User registration data including role and name
        request: FastAPI request object for audit logging
        credentials: Firebase authentication credentials
        
    Returns:
        AuthResponse with user data and success message
        
    Raises:
        HTTPException: If registration fails or user already exists
    """
    try:
        user = await auth_service.register_user(
            token=credentials.credentials,
            user_type=onboard_request.role,
            name=onboard_request.name
        )
        
        # Log successful registration
        ip_address = _get_client_ip(request)
        user_agent = request.headers.get("user-agent")
        
        await audit_service.log_user_action(
            user,
            AuditAction.LOGIN,  # Registration is essentially a login event
            details={"registration": True, "role": onboard_request.role.value},
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return AuthResponse(
            message="User registered successfully",
            user=user.model_dump(exclude_none=True),
            user_type=user.user_type.value if user.user_type else "unknown"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


@router.post("/login", response_model=LoginResponse)
async def login_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Authenticate user with Firebase token
    
    Args:
        request: FastAPI request object for audit logging
        credentials: Firebase authentication credentials
        
    Returns:
        LoginResponse with user data and authentication status
        
    Raises:
        HTTPException: If authentication fails
    """
    try:
        # Verify token and get user info
        decoded_token = await auth_service.verify_token(credentials.credentials)
        uid = decoded_token.get("uid")
        
        if not uid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user ID"
            )
        
        # Initialize database service if needed
        if not auth_service.db_service.db:
            await auth_service.db_service.initialize()
        
        # Check if user exists in database
        existing_user_data = await auth_service.db_service.get_user_by_uid(uid)
        is_new_user = existing_user_data is None
        
        # Get or create user
        user = await auth_service.get_or_create_user(uid)
        
        # Log successful login
        ip_address = _get_client_ip(request)
        user_agent = request.headers.get("user-agent")
        
        await audit_service.log_authentication_event(
            user,
            AuditAction.LOGIN,
            success=True,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return LoginResponse(
            message="Login successful",
            user=user.model_dump(exclude_none=True),
            user_type=user.user_type.value if user.user_type else "unknown",
            is_new_user=is_new_user
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )


@router.get("/me", response_model=AuthResponse)
async def get_current_user_info(
    request: Request,
    current_user: Union[UserModel, PatientModel, InstitutionModel] = Depends(get_current_user)
):
    """
    Get current authenticated user information
    
    Args:
        request: FastAPI request object for audit logging
        current_user: Current authenticated user from dependency
        
    Returns:
        AuthResponse with current user data
    """
    # Log user info access
    ip_address = _get_client_ip(request)
    user_agent = request.headers.get("user-agent")
    
    await audit_service.log_user_action(
        current_user,
        AuditAction.ACCESS_PATIENT_DATA,  # Accessing own profile data
        details={"action": "get_user_info"},
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    return AuthResponse(
        message="User information retrieved successfully",
        user=current_user.model_dump(exclude_none=True),
        user_type=current_user.user_type.value if current_user.user_type else "unknown"
    )


@router.post("/logout")
async def logout_user(
    request: Request,
    current_user: Union[UserModel, PatientModel, InstitutionModel] = Depends(get_current_user)
):
    """
    Logout endpoint (client-side token invalidation)
    
    Args:
        request: FastAPI request object for audit logging
        current_user: Current authenticated user from dependency
        
    Returns:
        Success message for logout
        
    Note:
        Firebase tokens are stateless, so logout is handled client-side
        by removing the token from client storage
    """
    # Log logout event
    ip_address = _get_client_ip(request)
    user_agent = request.headers.get("user-agent")
    
    await audit_service.log_authentication_event(
        current_user,
        AuditAction.LOGOUT,
        success=True,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    return {"message": "Logout successful. Please remove token from client storage."}


@router.get("/verify")
async def verify_token(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Verify Firebase token validity
    
    Args:
        request: FastAPI request object for audit logging
        credentials: Firebase authentication credentials
        
    Returns:
        Token verification status and user info
        
    Raises:
        HTTPException: If token is invalid
    """
    try:
        decoded_token = await auth_service.verify_token(credentials.credentials)
        
        return {
            "message": "Token is valid",
            "valid": True,
            "uid": decoded_token.get("uid"),
            "email": decoded_token.get("email"),
            "expires_at": decoded_token.get("exp")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token verification failed: {str(e)}"
        )


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