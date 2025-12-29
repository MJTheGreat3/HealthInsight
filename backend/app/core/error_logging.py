"""
Error logging and monitoring for HealthInsightCore
"""

import logging
import traceback
import uuid
from datetime import datetime
from typing import Any, Dict, Optional, Union
from fastapi import Request
from app.core.exceptions import HealthInsightException, ErrorResponse


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/healthinsight.log'),
        logging.StreamHandler()
    ]
)

# Create loggers for different components
app_logger = logging.getLogger("healthinsight.app")
auth_logger = logging.getLogger("healthinsight.auth")
pdf_logger = logging.getLogger("healthinsight.pdf")
llm_logger = logging.getLogger("healthinsight.llm")
db_logger = logging.getLogger("healthinsight.database")
api_logger = logging.getLogger("healthinsight.api")
websocket_logger = logging.getLogger("healthinsight.websocket")


class ErrorLogger:
    """Centralized error logging and monitoring"""
    
    def __init__(self):
        self.logger = app_logger
    
    def log_error(
        self,
        error: Union[Exception, HealthInsightException],
        request: Optional[Request] = None,
        user_id: Optional[str] = None,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Log error with context information
        
        Args:
            error: Exception that occurred
            request: FastAPI request object
            user_id: ID of user associated with error
            additional_context: Additional context information
            
        Returns:
            Unique error ID for tracking
        """
        error_id = str(uuid.uuid4())
        
        # Build error context
        context = {
            "error_id": error_id,
            "timestamp": datetime.utcnow().isoformat(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "user_id": user_id,
        }
        
        # Add request context if available
        if request:
            context.update({
                "method": request.method,
                "url": str(request.url),
                "client_ip": self._get_client_ip(request),
                "user_agent": request.headers.get("user-agent"),
                "headers": dict(request.headers),
            })
        
        # Add custom exception details
        if isinstance(error, HealthInsightException):
            context.update({
                "status_code": error.status_code,
                "details": error.details,
            })
        
        # Add additional context
        if additional_context:
            context.update(additional_context)
        
        # Add stack trace for debugging
        context["traceback"] = traceback.format_exc()
        
        # Log based on error severity
        if isinstance(error, HealthInsightException):
            if error.status_code >= 500:
                self.logger.error(f"Server Error [{error_id}]: {error.message}", extra=context)
            elif error.status_code >= 400:
                self.logger.warning(f"Client Error [{error_id}]: {error.message}", extra=context)
            else:
                self.logger.info(f"Info [{error_id}]: {error.message}", extra=context)
        else:
            self.logger.error(f"Unhandled Error [{error_id}]: {str(error)}", extra=context)
        
        return error_id
    
    def log_authentication_error(
        self,
        error: Exception,
        request: Optional[Request] = None,
        attempted_uid: Optional[str] = None
    ) -> str:
        """Log authentication-specific errors"""
        context = {
            "component": "authentication",
            "attempted_uid": attempted_uid,
        }
        
        auth_logger.warning(f"Authentication failed: {str(error)}")
        return self.log_error(error, request, attempted_uid, context)
    
    def log_pdf_processing_error(
        self,
        error: Exception,
        request: Optional[Request] = None,
        user_id: Optional[str] = None,
        file_info: Optional[Dict[str, Any]] = None
    ) -> str:
        """Log PDF processing errors"""
        context = {
            "component": "pdf_processing",
            "file_info": file_info or {},
        }
        
        pdf_logger.error(f"PDF processing failed: {str(error)}")
        return self.log_error(error, request, user_id, context)
    
    def log_llm_analysis_error(
        self,
        error: Exception,
        request: Optional[Request] = None,
        user_id: Optional[str] = None,
        analysis_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Log LLM analysis errors"""
        context = {
            "component": "llm_analysis",
            "analysis_context": analysis_context or {},
        }
        
        llm_logger.error(f"LLM analysis failed: {str(error)}")
        return self.log_error(error, request, user_id, context)
    
    def log_database_error(
        self,
        error: Exception,
        operation: str,
        collection: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> str:
        """Log database operation errors"""
        context = {
            "component": "database",
            "operation": operation,
            "collection": collection,
        }
        
        db_logger.error(f"Database operation failed [{operation}]: {str(error)}")
        return self.log_error(error, None, user_id, context)
    
    def log_api_error(
        self,
        error: Exception,
        request: Request,
        endpoint: str,
        user_id: Optional[str] = None
    ) -> str:
        """Log API endpoint errors"""
        context = {
            "component": "api",
            "endpoint": endpoint,
        }
        
        api_logger.error(f"API error at {endpoint}: {str(error)}")
        return self.log_error(error, request, user_id, context)
    
    def log_websocket_error(
        self,
        error: Exception,
        event: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> str:
        """Log WebSocket communication errors"""
        context = {
            "component": "websocket",
            "event": event,
            "session_id": session_id,
        }
        
        websocket_logger.error(f"WebSocket error [{event}]: {str(error)}")
        return self.log_error(error, None, user_id, context)
    
    def log_performance_warning(
        self,
        operation: str,
        duration: float,
        threshold: float,
        request: Optional[Request] = None,
        user_id: Optional[str] = None
    ):
        """Log performance warnings for slow operations"""
        context = {
            "component": "performance",
            "operation": operation,
            "duration": duration,
            "threshold": threshold,
        }
        
        if request:
            context.update({
                "method": request.method,
                "url": str(request.url),
                "client_ip": self._get_client_ip(request),
            })
        
        self.logger.warning(
            f"Slow operation detected: {operation} took {duration:.2f}s (threshold: {threshold}s)",
            extra=context
        )
    
    def log_security_event(
        self,
        event_type: str,
        description: str,
        request: Optional[Request] = None,
        user_id: Optional[str] = None,
        severity: str = "warning"
    ):
        """Log security-related events"""
        context = {
            "component": "security",
            "event_type": event_type,
            "description": description,
            "severity": severity,
        }
        
        if request:
            context.update({
                "method": request.method,
                "url": str(request.url),
                "client_ip": self._get_client_ip(request),
                "user_agent": request.headers.get("user-agent"),
            })
        
        if severity == "critical":
            self.logger.critical(f"Security Event [{event_type}]: {description}", extra=context)
        elif severity == "error":
            self.logger.error(f"Security Event [{event_type}]: {description}", extra=context)
        else:
            self.logger.warning(f"Security Event [{event_type}]: {description}", extra=context)
    
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


# Global error logger instance
error_logger = ErrorLogger()


# Utility functions for common logging patterns
def log_and_raise_error(
    error_class: type,
    message: str,
    request: Optional[Request] = None,
    user_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> None:
    """Log error and raise custom exception"""
    error = error_class(message, details=details)
    error_logger.log_error(error, request, user_id)
    raise error


def log_unhandled_exception(
    error: Exception,
    request: Optional[Request] = None,
    user_id: Optional[str] = None
) -> str:
    """Log unhandled exceptions with full context"""
    return error_logger.log_error(error, request, user_id, {"unhandled": True})


def create_error_response_with_logging(
    error: Union[Exception, HealthInsightException],
    request: Optional[Request] = None,
    user_id: Optional[str] = None
) -> ErrorResponse:
    """Create error response and log the error"""
    error_id = error_logger.log_error(error, request, user_id)
    
    if isinstance(error, HealthInsightException):
        return ErrorResponse(
            error=type(error).__name__,
            message=error.message,
            status_code=error.status_code,
            details=error.details,
            request_id=error_id
        )
    else:
        return ErrorResponse(
            error="InternalServerError",
            message="An internal server error occurred",
            status_code=500,
            details={"original_error": str(error)},
            request_id=error_id
        )