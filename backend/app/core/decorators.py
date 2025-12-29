"""
Authorization decorators for role-based access control
"""

from functools import wraps
from typing import List, Union, Callable, Any
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.models.user import UserType, UserModel, PatientModel, InstitutionModel
from app.core.middleware import auth_middleware


# Alias decorators for backward compatibility will be defined after the functions


def require_roles(allowed_roles: List[UserType]):
    """
    Decorator factory to require specific roles for endpoint access
    
    Args:
        allowed_roles: List of allowed user types
        
    Returns:
        Decorator function that validates user roles
        
    Usage:
        @require_roles([UserType.PATIENT])
        async def patient_only_endpoint():
            pass
            
        @require_roles([UserType.PATIENT, UserType.INSTITUTION])
        async def patient_or_institution_endpoint():
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract credentials from kwargs or dependencies
            credentials = None
            for key, value in kwargs.items():
                if isinstance(value, HTTPAuthorizationCredentials):
                    credentials = value
                    break
            
            if not credentials:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Authenticate and validate role
            user = await auth_middleware.require_any_role(credentials, allowed_roles)
            
            # Add user to kwargs for endpoint access
            kwargs['current_user'] = user
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_patient_role(func: Callable) -> Callable:
    """
    Decorator to require patient role for endpoint access
    
    Usage:
        @require_patient_role
        async def patient_endpoint(current_user: PatientModel):
            pass
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Extract credentials from kwargs or dependencies
        credentials = None
        for key, value in kwargs.items():
            if isinstance(value, HTTPAuthorizationCredentials):
                credentials = value
                break
        
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Authenticate and validate patient role
        user = await auth_middleware.require_patient_role(credentials)
        
        # Add user to kwargs for endpoint access
        kwargs['current_user'] = user
        
        return await func(*args, **kwargs)
    
    return wrapper


def require_institution_role(func: Callable) -> Callable:
    """
    Decorator to require institution role for endpoint access
    
    Usage:
        @require_institution_role
        async def hospital_endpoint(current_user: InstitutionModel):
            pass
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Extract credentials from kwargs or dependencies
        credentials = None
        for key, value in kwargs.items():
            if isinstance(value, HTTPAuthorizationCredentials):
                credentials = value
                break
        
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Authenticate and validate institution role
        user = await auth_middleware.require_institution_role(credentials)
        
        # Add user to kwargs for endpoint access
        kwargs['current_user'] = user
        
        return await func(*args, **kwargs)
    
    return wrapper


def require_authentication(func: Callable) -> Callable:
    """
    Decorator to require any valid authentication for endpoint access
    
    Usage:
        @require_authentication
        async def authenticated_endpoint(current_user: UserModel):
            pass
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Extract credentials from kwargs or dependencies
        credentials = None
        for key, value in kwargs.items():
            if isinstance(value, HTTPAuthorizationCredentials):
                credentials = value
                break
        
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Authenticate user
        user = await auth_middleware.require_authentication(credentials)
        
        # Add user to kwargs for endpoint access
        kwargs['current_user'] = user
        
        return await func(*args, **kwargs)
    
    return wrapper

# Alias decorators for backward compatibility
require_auth = require_authentication
require_patient = require_patient_role