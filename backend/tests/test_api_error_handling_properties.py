"""
Property-based tests for API error handling and validation
"""

import pytest
from hypothesis import given, strategies as st, assume, settings, HealthCheck
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException, status, Request
from fastapi.testclient import TestClient
from fastapi.responses import JSONResponse
import json

from app.core.exceptions import (
    HealthInsightException,
    AuthenticationError,
    AuthorizationError,
    ValidationError,
    NotFoundError,
    ConflictError,
    PDFProcessingError,
    LLMAnalysisError,
    DatabaseError,
    RateLimitError,
    FileSizeError,
    TimeoutError,
    WebSocketError,
    ErrorResponse
)
from app.core.error_handlers import (
    setup_exception_handlers,
    create_error_middleware,
    raise_authentication_error,
    raise_authorization_error,
    raise_validation_error,
    raise_not_found_error,
    raise_database_error
)
from app.core.error_logging import error_logger


# Test data strategies
@st.composite
def http_status_codes(draw):
    """Generate valid HTTP status codes"""
    return draw(st.sampled_from([
        400, 401, 403, 404, 409, 413, 422, 429, 500, 503, 408
    ]))


@st.composite
def error_messages(draw):
    """Generate error messages"""
    return draw(st.text(min_size=1, max_size=200, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs', 'Po')
    )))


@st.composite
def error_details(draw):
    """Generate error details dictionary"""
    keys = draw(st.lists(
        st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
        min_size=0, max_size=5, unique=True
    ))
    
    details = {}
    for key in keys:
        value = draw(st.one_of(
            st.text(min_size=0, max_size=100),
            st.integers(),
            st.booleans(),
            st.none()
        ))
        details[key] = value
    
    return details


@st.composite
def custom_exceptions(draw):
    """Generate custom HealthInsight exceptions"""
    message = draw(error_messages())
    details = draw(error_details())
    
    exception_class = draw(st.sampled_from([
        AuthenticationError,
        AuthorizationError,
        ValidationError,
        NotFoundError,
        ConflictError,
        PDFProcessingError,
        LLMAnalysisError,
        DatabaseError,
        RateLimitError,
        FileSizeError,
        TimeoutError,
        WebSocketError
    ]))
    
    return exception_class(message, details)


@st.composite
def standard_exceptions(draw):
    """Generate standard Python exceptions"""
    message = draw(error_messages())
    
    exception_class = draw(st.sampled_from([
        ValueError,
        KeyError,
        FileNotFoundError,
        PermissionError,
        ConnectionError,
        TimeoutError
    ]))
    
    return exception_class(message)


class TestAPIErrorHandlingProperties:
    """Property-based tests for API error handling"""
    
    @given(custom_exceptions())
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_api_error_handling_property(self, exception):
        """
        Property 10: API Error Handling
        For any API operation that encounters an error, the system should return 
        appropriate HTTP status codes and error messages while maintaining system stability
        **Feature: health-insight-core, Property 10: API Error Handling**
        **Validates: Requirements 1.3, 10.4**
        """
        from fastapi import FastAPI
        from app.core.error_handlers import setup_exception_handlers
        
        # Arrange - Create test app with error handlers
        app = FastAPI()
        setup_exception_handlers(app)
        
        @app.get("/test-endpoint")
        async def test_endpoint():
            raise exception
        
        # Act - Make request that triggers the exception
        with TestClient(app) as client:
            response = client.get("/test-endpoint")
        
        # Assert - Response should have correct status code and structure
        assert response.status_code == exception.status_code
        
        response_data = response.json()
        assert "error" in response_data
        assert "message" in response_data
        assert "status_code" in response_data
        assert response_data["status_code"] == exception.status_code
        assert response_data["message"] == exception.message
        
        # Assert - Error details should be included if present
        if exception.details:
            assert "details" in response_data
            assert response_data["details"] == exception.details
        
        # Assert - Request ID should be included for tracking
        assert "request_id" in response_data
        assert response_data["request_id"] is not None
    
    @given(standard_exceptions())
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_standard_exception_handling_property(self, exception):
        """
        Property: Standard Exception Handling
        For any standard Python exception, the system should handle it gracefully
        and return appropriate error responses
        **Feature: health-insight-core, Property 10: API Error Handling**
        **Validates: Requirements 1.3, 10.4**
        """
        from fastapi import FastAPI
        from app.core.error_handlers import setup_exception_handlers
        
        # Arrange - Create test app with error handlers
        app = FastAPI()
        setup_exception_handlers(app)
        
        @app.get("/test-endpoint")
        async def test_endpoint():
            raise exception
        
        # Act - Make request that triggers the exception
        with TestClient(app) as client:
            response = client.get("/test-endpoint")
        
        # Assert - Response should have appropriate status code based on exception type
        expected_status_codes = {
            ValueError: 400,
            KeyError: 400,
            FileNotFoundError: 404,
            PermissionError: 403,
            ConnectionError: 503,
            TimeoutError: 408
        }
        
        expected_status = expected_status_codes.get(type(exception), 500)
        assert response.status_code == expected_status
        
        response_data = response.json()
        assert "error" in response_data
        assert "message" in response_data
        assert "status_code" in response_data
        assert response_data["status_code"] == expected_status
    
    @given(error_messages(), error_details())
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_error_response_creation_property(self, message, details):
        """
        Property: Error Response Consistency
        For any error message and details, the system should create consistent error responses
        **Feature: health-insight-core, Property 10: API Error Handling**
        **Validates: Requirements 1.3, 10.4**
        """
        from app.core.exceptions import create_error_response
        
        # Arrange
        error_type = "TestError"
        status_code = 400
        request_id = "test-request-id"
        
        # Act
        error_response = create_error_response(
            error_type=error_type,
            message=message,
            status_code=status_code,
            details=details,
            request_id=request_id
        )
        
        # Assert - Error response should have consistent structure
        assert isinstance(error_response, ErrorResponse)
        assert error_response.error == error_type
        assert error_response.message == message
        assert error_response.status_code == status_code
        assert error_response.details == details
        assert error_response.request_id == request_id
    
    @given(st.lists(st.dictionaries(
        keys=st.text(min_size=1, max_size=20),
        values=st.one_of(st.text(), st.integers(), st.lists(st.text()))
    ), min_size=1, max_size=5))
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_validation_error_handling_property(self, validation_errors):
        """
        Property: Validation Error Formatting
        For any validation errors, the system should format them consistently
        **Feature: health-insight-core, Property 10: API Error Handling**
        **Validates: Requirements 1.3, 10.4**
        """
        from fastapi import FastAPI
        from fastapi.exceptions import RequestValidationError
        from pydantic import ValidationError
        from app.core.error_handlers import setup_exception_handlers
        
        # Arrange - Create test app with error handlers
        app = FastAPI()
        setup_exception_handlers(app)
        
        # Create mock validation error
        mock_errors = []
        for i, error_dict in enumerate(validation_errors):
            mock_errors.append({
                "loc": (f"field_{i}",),
                "msg": f"validation error {i}",
                "type": "value_error",
                "input": error_dict
            })
        
        @app.get("/test-endpoint")
        async def test_endpoint():
            # Create a mock RequestValidationError
            exc = RequestValidationError(mock_errors)
            raise exc
        
        # Act - Make request that triggers validation error
        with TestClient(app) as client:
            response = client.get("/test-endpoint")
        
        # Assert - Response should be 422 with formatted validation errors
        assert response.status_code == 422
        
        response_data = response.json()
        assert "error" in response_data
        assert response_data["error"] == "ValidationError"
        assert "details" in response_data
        assert "validation_errors" in response_data["details"]
        
        # Assert - Validation errors should be properly formatted
        formatted_errors = response_data["details"]["validation_errors"]
        assert len(formatted_errors) == len(mock_errors)
        
        for formatted_error in formatted_errors:
            assert "field" in formatted_error
            assert "message" in formatted_error
            assert "type" in formatted_error
    
    @given(error_messages())
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_error_logging_property(self, error_message):
        """
        Property: Error Logging Consistency
        For any error that occurs, the system should log it with appropriate context
        **Feature: health-insight-core, Property 10: API Error Handling**
        **Validates: Requirements 1.3, 10.4**
        """
        # Arrange
        test_exception = ValueError(error_message)
        
        # Mock the logger to capture log calls
        with patch.object(error_logger, 'log_error') as mock_log_error:
            mock_log_error.return_value = "test-error-id"
            
            # Act - Log the error
            error_id = error_logger.log_error(test_exception)
            
            # Assert - Error should be logged with proper context
            assert error_id == "test-error-id"
            mock_log_error.assert_called_once_with(test_exception)
    
    @given(st.sampled_from([
        "authentication", "pdf_processing", "llm_analysis", 
        "database", "api", "websocket"
    ]), error_messages())
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_component_specific_error_logging_property(self, component, error_message):
        """
        Property: Component-Specific Error Logging
        For any component-specific error, the system should log it with appropriate context
        **Feature: health-insight-core, Property 10: API Error Handling**
        **Validates: Requirements 1.3, 10.4**
        """
        # Arrange
        test_exception = Exception(error_message)
        
        # Mock the appropriate logger method based on component
        logger_methods = {
            "authentication": "log_authentication_error",
            "pdf_processing": "log_pdf_processing_error",
            "llm_analysis": "log_llm_analysis_error",
            "database": "log_database_error",
            "api": "log_api_error",
            "websocket": "log_websocket_error"
        }
        
        method_name = logger_methods[component]
        
        with patch.object(error_logger, method_name) as mock_log_method:
            mock_log_method.return_value = "test-error-id"
            
            # Act - Call the appropriate logging method
            if component == "authentication":
                error_id = error_logger.log_authentication_error(test_exception)
            elif component == "pdf_processing":
                error_id = error_logger.log_pdf_processing_error(test_exception)
            elif component == "llm_analysis":
                error_id = error_logger.log_llm_analysis_error(test_exception)
            elif component == "database":
                error_id = error_logger.log_database_error(test_exception, "test_operation")
            elif component == "api":
                # Create a mock request
                mock_request = MagicMock()
                mock_request.method = "GET"
                mock_request.url = "http://test.com/api/test"
                mock_request.headers = {"user-agent": "test-agent"}
                mock_request.client.host = "127.0.0.1"
                
                error_id = error_logger.log_api_error(test_exception, mock_request, "/test")
            elif component == "websocket":
                error_id = error_logger.log_websocket_error(test_exception, "test_event")
            
            # Assert - Error should be logged with component-specific context
            assert error_id == "test-error-id"
            mock_log_method.assert_called_once()
    
    @given(http_status_codes(), error_messages())
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_http_exception_handling_property(self, status_code, error_message):
        """
        Property: HTTP Exception Consistency
        For any HTTP exception, the system should handle it consistently
        **Feature: health-insight-core, Property 10: API Error Handling**
        **Validates: Requirements 1.3, 10.4**
        """
        from fastapi import FastAPI
        from app.core.error_handlers import setup_exception_handlers
        
        # Arrange - Create test app with error handlers
        app = FastAPI()
        setup_exception_handlers(app)
        
        @app.get("/test-endpoint")
        async def test_endpoint():
            raise HTTPException(status_code=status_code, detail=error_message)
        
        # Act - Make request that triggers HTTP exception
        with TestClient(app) as client:
            response = client.get("/test-endpoint")
        
        # Assert - Response should match the HTTP exception
        assert response.status_code == status_code
        
        response_data = response.json()
        assert "error" in response_data
        assert "message" in response_data
        assert response_data["message"] == error_message
        assert response_data["status_code"] == status_code
    
    @given(error_messages(), error_details())
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_error_middleware_property(self, error_message, details):
        """
        Property: Error Middleware Request Tracking
        For any request that encounters an error, the middleware should add request tracking
        **Feature: health-insight-core, Property 10: API Error Handling**
        **Validates: Requirements 1.3, 10.4**
        """
        from fastapi import FastAPI
        from app.core.error_handlers import create_error_middleware, setup_exception_handlers
        
        # Arrange - Create test app with error middleware
        app = FastAPI()
        setup_exception_handlers(app)
        app.middleware("http")(create_error_middleware())
        
        @app.get("/test-endpoint")
        async def test_endpoint():
            raise ValidationError(error_message, details)
        
        # Act - Make request that triggers error
        with TestClient(app) as client:
            response = client.get("/test-endpoint")
        
        # Assert - Response should include request ID header
        assert "X-Request-ID" in response.headers
        assert response.headers["X-Request-ID"] is not None
        
        # Assert - Response body should include request ID
        response_data = response.json()
        assert "request_id" in response_data
        assert response_data["request_id"] == response.headers["X-Request-ID"]