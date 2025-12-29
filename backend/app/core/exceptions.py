"""
Custom exceptions and error handling for HealthInsightCore
"""

from typing import Any, Dict, Optional, Union
from fastapi import HTTPException, status
from pydantic import BaseModel


class ErrorDetail(BaseModel):
    """Structured error detail model"""
    code: str
    message: str
    field: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """Standardized error response model"""
    error: str
    message: str
    status_code: int
    details: Optional[Union[str, Dict[str, Any], list]] = None
    request_id: Optional[str] = None


# Custom Exception Classes

class HealthInsightException(Exception):
    """Base exception for HealthInsightCore application"""
    
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class AuthenticationError(HealthInsightException):
    """Authentication related errors"""
    
    def __init__(self, message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details
        )


class AuthorizationError(HealthInsightException):
    """Authorization related errors"""
    
    def __init__(self, message: str = "Access forbidden", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            details=details
        )


class ValidationError(HealthInsightException):
    """Data validation errors"""
    
    def __init__(self, message: str = "Validation failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details
        )


class NotFoundError(HealthInsightException):
    """Resource not found errors"""
    
    def __init__(self, message: str = "Resource not found", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            details=details
        )


class ConflictError(HealthInsightException):
    """Resource conflict errors"""
    
    def __init__(self, message: str = "Resource conflict", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            details=details
        )


class PDFProcessingError(HealthInsightException):
    """PDF processing related errors"""
    
    def __init__(self, message: str = "PDF processing failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details
        )


class LLMAnalysisError(HealthInsightException):
    """LLM analysis related errors"""
    
    def __init__(self, message: str = "AI analysis failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details=details
        )


class DatabaseError(HealthInsightException):
    """Database operation errors"""
    
    def __init__(self, message: str = "Database operation failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details
        )


class RateLimitError(HealthInsightException):
    """Rate limiting errors"""
    
    def __init__(self, message: str = "Rate limit exceeded", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details=details
        )


class FileSizeError(HealthInsightException):
    """File size limit errors"""
    
    def __init__(self, message: str = "File size limit exceeded", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            details=details
        )


class TimeoutError(HealthInsightException):
    """Request timeout errors"""
    
    def __init__(self, message: str = "Request timeout", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            details=details
        )


class WebSocketError(HealthInsightException):
    """WebSocket communication errors"""
    
    def __init__(self, message: str = "WebSocket error", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details
        )


# Error code mappings for consistent error handling
ERROR_CODES = {
    # Authentication errors
    "AUTH_TOKEN_MISSING": "Missing authentication token",
    "AUTH_TOKEN_INVALID": "Invalid authentication token",
    "AUTH_TOKEN_EXPIRED": "Authentication token has expired",
    "AUTH_USER_NOT_FOUND": "User not found",
    "AUTH_REGISTRATION_FAILED": "User registration failed",
    
    # Authorization errors
    "AUTH_INSUFFICIENT_PERMISSIONS": "Insufficient permissions",
    "AUTH_ROLE_REQUIRED": "Required role not found",
    "AUTH_PATIENT_ACCESS_REQUIRED": "Patient access required",
    "AUTH_INSTITUTION_ACCESS_REQUIRED": "Institution access required",
    
    # Validation errors
    "VALIDATION_REQUIRED_FIELD": "Required field missing",
    "VALIDATION_INVALID_FORMAT": "Invalid data format",
    "VALIDATION_INVALID_VALUE": "Invalid field value",
    "VALIDATION_CONSTRAINT_VIOLATION": "Data constraint violation",
    
    # Resource errors
    "RESOURCE_NOT_FOUND": "Requested resource not found",
    "RESOURCE_ALREADY_EXISTS": "Resource already exists",
    "RESOURCE_CONFLICT": "Resource conflict detected",
    
    # PDF processing errors
    "PDF_UNSUPPORTED_FORMAT": "Unsupported PDF format",
    "PDF_CORRUPTED_FILE": "Corrupted PDF file",
    "PDF_PARSING_FAILED": "PDF parsing failed",
    "PDF_NO_TEXT_FOUND": "No extractable text found in PDF",
    
    # LLM analysis errors
    "LLM_API_UNAVAILABLE": "AI analysis service unavailable",
    "LLM_RATE_LIMIT": "AI analysis rate limit exceeded",
    "LLM_INVALID_RESPONSE": "Invalid AI analysis response",
    "LLM_TIMEOUT": "AI analysis timeout",
    
    # Database errors
    "DB_CONNECTION_FAILED": "Database connection failed",
    "DB_OPERATION_FAILED": "Database operation failed",
    "DB_CONSTRAINT_VIOLATION": "Database constraint violation",
    "DB_TIMEOUT": "Database operation timeout",
    
    # File handling errors
    "FILE_SIZE_EXCEEDED": "File size limit exceeded",
    "FILE_TYPE_UNSUPPORTED": "Unsupported file type",
    "FILE_UPLOAD_FAILED": "File upload failed",
    
    # WebSocket errors
    "WS_CONNECTION_FAILED": "WebSocket connection failed",
    "WS_MESSAGE_FAILED": "WebSocket message delivery failed",
    "WS_AUTHENTICATION_FAILED": "WebSocket authentication failed",
    
    # General errors
    "INTERNAL_SERVER_ERROR": "Internal server error",
    "SERVICE_UNAVAILABLE": "Service temporarily unavailable",
    "REQUEST_TIMEOUT": "Request timeout",
    "RATE_LIMIT_EXCEEDED": "Rate limit exceeded"
}


def get_error_message(code: str, default: str = "An error occurred") -> str:
    """Get standardized error message by code"""
    return ERROR_CODES.get(code, default)


def create_error_response(
    error_type: str,
    message: str,
    status_code: int,
    details: Optional[Union[str, Dict[str, Any], list]] = None,
    request_id: Optional[str] = None
) -> ErrorResponse:
    """Create standardized error response"""
    return ErrorResponse(
        error=error_type,
        message=message,
        status_code=status_code,
        details=details,
        request_id=request_id
    )