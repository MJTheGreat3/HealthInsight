"""
Global exception handlers for FastAPI application
"""

import uuid
from typing import Union
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import (
    HealthInsightException,
    ErrorResponse,
    AuthenticationError,
    AuthorizationError,
    ValidationError as CustomValidationError,
    NotFoundError,
    ConflictError,
    PDFProcessingError,
    LLMAnalysisError,
    DatabaseError,
    RateLimitError,
    FileSizeError,
    TimeoutError,
    WebSocketError,
    create_error_response
)
from app.core.error_logging import error_logger


def setup_exception_handlers(app: FastAPI) -> None:
    """Setup global exception handlers for the FastAPI application"""
    
    @app.exception_handler(HealthInsightException)
    async def health_insight_exception_handler(request: Request, exc: HealthInsightException):
        """Handle custom HealthInsight exceptions"""
        error_id = error_logger.log_error(exc, request)
        
        # Use request ID from middleware if available
        request_id = getattr(request.state, 'request_id', error_id)
        
        error_response = create_error_response(
            error_type=type(exc).__name__,
            message=exc.message,
            status_code=exc.status_code,
            details=exc.details,
            request_id=request_id
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response.model_dump()
        )
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handle FastAPI HTTP exceptions"""
        error_id = error_logger.log_error(exc, request)
        
        # Use request ID from middleware if available
        request_id = getattr(request.state, 'request_id', error_id)
        
        error_response = create_error_response(
            error_type="HTTPException",
            message=exc.detail,
            status_code=exc.status_code,
            request_id=request_id
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response.model_dump()
        )
    
    @app.exception_handler(StarletteHTTPException)
    async def starlette_http_exception_handler(request: Request, exc: StarletteHTTPException):
        """Handle Starlette HTTP exceptions"""
        error_id = error_logger.log_error(exc, request)
        
        error_response = create_error_response(
            error_type="HTTPException",
            message=exc.detail,
            status_code=exc.status_code,
            request_id=error_id
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response.model_dump()
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle Pydantic validation errors"""
        error_id = error_logger.log_error(exc, request)
        
        # Use request ID from middleware if available
        request_id = getattr(request.state, 'request_id', error_id)
        
        # Format validation errors for better user experience
        validation_errors = []
        for error in exc.errors():
            field_path = " -> ".join(str(loc) for loc in error["loc"])
            validation_errors.append({
                "field": field_path,
                "message": error["msg"],
                "type": error["type"],
                "input": error.get("input")
            })
        
        error_response = create_error_response(
            error_type="ValidationError",
            message="Request validation failed",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details={"validation_errors": validation_errors},
            request_id=request_id
        )
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=error_response.model_dump()
        )
    
    @app.exception_handler(ValidationError)
    async def pydantic_validation_exception_handler(request: Request, exc: ValidationError):
        """Handle Pydantic model validation errors"""
        error_id = error_logger.log_error(exc, request)
        
        # Format validation errors
        validation_errors = []
        for error in exc.errors():
            field_path = " -> ".join(str(loc) for loc in error["loc"])
            validation_errors.append({
                "field": field_path,
                "message": error["msg"],
                "type": error["type"]
            })
        
        error_response = create_error_response(
            error_type="ValidationError",
            message="Data validation failed",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details={"validation_errors": validation_errors},
            request_id=error_id
        )
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=error_response.model_dump()
        )
    
    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        """Handle ValueError exceptions"""
        error_id = error_logger.log_error(exc, request)
        
        error_response = create_error_response(
            error_type="ValueError",
            message="Invalid value provided",
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"original_error": str(exc)},
            request_id=error_id
        )
        
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error_response.model_dump()
        )
    
    @app.exception_handler(KeyError)
    async def key_error_handler(request: Request, exc: KeyError):
        """Handle KeyError exceptions"""
        error_id = error_logger.log_error(exc, request)
        
        error_response = create_error_response(
            error_type="KeyError",
            message="Required key not found",
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"missing_key": str(exc)},
            request_id=error_id
        )
        
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error_response.model_dump()
        )
    
    @app.exception_handler(FileNotFoundError)
    async def file_not_found_error_handler(request: Request, exc: FileNotFoundError):
        """Handle FileNotFoundError exceptions"""
        error_id = error_logger.log_error(exc, request)
        
        error_response = create_error_response(
            error_type="FileNotFoundError",
            message="File not found",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"file_path": str(exc)},
            request_id=error_id
        )
        
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=error_response.model_dump()
        )
    
    @app.exception_handler(PermissionError)
    async def permission_error_handler(request: Request, exc: PermissionError):
        """Handle PermissionError exceptions"""
        error_id = error_logger.log_error(exc, request)
        
        error_response = create_error_response(
            error_type="PermissionError",
            message="Permission denied",
            status_code=status.HTTP_403_FORBIDDEN,
            details={"original_error": str(exc)},
            request_id=error_id
        )
        
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content=error_response.model_dump()
        )
    
    @app.exception_handler(ConnectionError)
    async def connection_error_handler(request: Request, exc: ConnectionError):
        """Handle ConnectionError exceptions (database, external APIs)"""
        error_id = error_logger.log_error(exc, request)
        
        error_response = create_error_response(
            error_type="ConnectionError",
            message="Service connection failed",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details={"original_error": str(exc)},
            request_id=error_id
        )
        
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=error_response.model_dump()
        )
    
    @app.exception_handler(TimeoutError)
    async def timeout_error_handler(request: Request, exc: TimeoutError):
        """Handle timeout exceptions"""
        # Check if it's our custom TimeoutError or Python's built-in
        if hasattr(exc, 'status_code'):
            # It's our custom TimeoutError
            error_id = error_logger.log_error(exc, request)
            error_response = create_error_response(
                error_type="TimeoutError",
                message=exc.message,
                status_code=exc.status_code,
                details=exc.details,
                request_id=error_id
            )
            return JSONResponse(
                status_code=exc.status_code,
                content=error_response.model_dump()
            )
        else:
            # It's Python's built-in TimeoutError
            error_id = error_logger.log_error(exc, request)
            error_response = create_error_response(
                error_type="TimeoutError",
                message="Request timeout",
                status_code=status.HTTP_408_REQUEST_TIMEOUT,
                details={"original_error": str(exc)},
                request_id=error_id
            )
            return JSONResponse(
                status_code=status.HTTP_408_REQUEST_TIMEOUT,
                content=error_response.model_dump()
            )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle all other unhandled exceptions"""
        error_id = error_logger.log_error(exc, request)
        
        # Log security event for unhandled exceptions
        error_logger.log_security_event(
            event_type="unhandled_exception",
            description=f"Unhandled exception: {type(exc).__name__}",
            request=request,
            severity="error"
        )
        
        error_response = create_error_response(
            error_type="InternalServerError",
            message="An internal server error occurred",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details={"error_id": error_id},
            request_id=error_id
        )
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response.model_dump()
        )


def create_error_middleware():
    """Create middleware for error handling and request tracking"""
    
    async def error_middleware(request: Request, call_next):
        """Middleware to add request ID and handle errors"""
        # Add request ID for tracking
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        try:
            response = await call_next(request)
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as exc:
            # This should be caught by exception handlers, but just in case
            error_id = error_logger.log_error(exc, request)
            
            error_response = create_error_response(
                error_type="UnhandledException",
                message="An unexpected error occurred",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                request_id=error_id
            )
            
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=error_response.model_dump(),
                headers={"X-Request-ID": request_id}
            )
    
    return error_middleware


# Utility functions for raising specific errors with proper logging
def raise_authentication_error(
    message: str = "Authentication failed",
    request: Request = None,
    details: dict = None
):
    """Raise authentication error with logging"""
    error = AuthenticationError(message, details)
    if request:
        error_logger.log_authentication_error(error, request)
    raise error


def raise_authorization_error(
    message: str = "Access forbidden",
    request: Request = None,
    user_id: str = None,
    details: dict = None
):
    """Raise authorization error with logging"""
    error = AuthorizationError(message, details)
    if request:
        error_logger.log_error(error, request, user_id)
    raise error


def raise_validation_error(
    message: str = "Validation failed",
    request: Request = None,
    user_id: str = None,
    details: dict = None
):
    """Raise validation error with logging"""
    error = CustomValidationError(message, details)
    if request:
        error_logger.log_error(error, request, user_id)
    raise error


def raise_not_found_error(
    message: str = "Resource not found",
    request: Request = None,
    user_id: str = None,
    details: dict = None
):
    """Raise not found error with logging"""
    error = NotFoundError(message, details)
    if request:
        error_logger.log_error(error, request, user_id)
    raise error


def raise_database_error(
    message: str = "Database operation failed",
    operation: str = "unknown",
    collection: str = None,
    user_id: str = None,
    details: dict = None
):
    """Raise database error with logging"""
    error = DatabaseError(message, details)
    error_logger.log_database_error(error, operation, collection, user_id)
    raise error


def raise_pdf_processing_error(
    message: str = "PDF processing failed",
    request: Request = None,
    user_id: str = None,
    file_info: dict = None,
    details: dict = None
):
    """Raise PDF processing error with logging"""
    error = PDFProcessingError(message, details)
    if request:
        error_logger.log_pdf_processing_error(error, request, user_id, file_info)
    raise error


def raise_llm_analysis_error(
    message: str = "AI analysis failed",
    request: Request = None,
    user_id: str = None,
    analysis_context: dict = None,
    details: dict = None
):
    """Raise LLM analysis error with logging"""
    error = LLMAnalysisError(message, details)
    if request:
        error_logger.log_llm_analysis_error(error, request, user_id, analysis_context)
    raise error