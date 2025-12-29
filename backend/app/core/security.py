"""
Security utilities for input sanitization and validation
"""

import re
import html
import bleach
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)


class InputSanitizer:
    """Input sanitization and validation utilities"""
    
    # Allowed HTML tags for rich text (if needed)
    ALLOWED_TAGS = ['p', 'br', 'strong', 'em', 'u', 'ol', 'ul', 'li']
    ALLOWED_ATTRIBUTES = {}
    
    # Common malicious patterns
    MALICIOUS_PATTERNS = [
        r'<script.*?>.*?</script>',      # Script tags
        r'javascript:',                  # JavaScript protocol
        r'on\w+\s*=',                   # Event handlers
        r'data:text/html',              # Data URLs with HTML
        r'vbscript:',                   # VBScript protocol
        r'expression\s*\(',             # CSS expressions
        r'@import',                     # CSS imports
        r'binding\s*:',                 # CSS binding
        r'eval\s*\(',                   # JavaScript eval
        r'setTimeout\s*\(',             # JavaScript setTimeout
        r'setInterval\s*\(',            # JavaScript setInterval
    ]
    
    # SQL injection patterns (for additional protection)
    SQL_INJECTION_PATTERNS = [
        r'union\s+select',
        r'drop\s+table',
        r'delete\s+from',
        r'insert\s+into',
        r'update\s+.*\s+set',
        r'exec\s*\(',
        r'sp_\w+',
        r'xp_\w+',
        r'--\s*$',
        r'/\*.*?\*/',
        r"'\s*/\*",  # SQL comment injection
        r"'\s*or\s+",  # OR injection
        r"'\s*and\s+",  # AND injection
    ]
    
    # Path traversal patterns
    PATH_TRAVERSAL_PATTERNS = [
        r'\.\./.*\.\.',
        r'\.\.\\.*\.\.',
        r'%2e%2e%2f',
        r'%2e%2e\\',
        r'\.\.%2f',
        r'\.\.%5c',
    ]
    
    @classmethod
    def sanitize_string(cls, value: str, max_length: Optional[int] = None) -> str:
        """
        Sanitize a string input by removing malicious content
        
        Args:
            value: Input string to sanitize
            max_length: Maximum allowed length
            
        Returns:
            Sanitized string
        """
        if not isinstance(value, str):
            return str(value)
        
        # Trim whitespace
        sanitized = value.strip()
        
        # Enforce length limit
        if max_length and len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        # HTML escape to prevent XSS
        sanitized = html.escape(sanitized)
        
        # Remove null bytes
        sanitized = sanitized.replace('\x00', '')
        
        # Check for malicious patterns
        for pattern in cls.MALICIOUS_PATTERNS:
            if re.search(pattern, sanitized, re.IGNORECASE):
                logger.warning(f"Malicious pattern detected and removed: {pattern}")
                sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)
        
        return sanitized
    
    @classmethod
    def sanitize_html(cls, value: str, allowed_tags: Optional[List[str]] = None) -> str:
        """
        Sanitize HTML content using bleach
        
        Args:
            value: HTML string to sanitize
            allowed_tags: List of allowed HTML tags
            
        Returns:
            Sanitized HTML string
        """
        if not isinstance(value, str):
            return str(value)
        
        tags = allowed_tags or cls.ALLOWED_TAGS
        
        # Use bleach to clean HTML
        sanitized = bleach.clean(
            value,
            tags=tags,
            attributes=cls.ALLOWED_ATTRIBUTES,
            strip=True
        )
        
        return sanitized
    
    @classmethod
    def validate_email(cls, email: str) -> bool:
        """
        Validate email format
        
        Args:
            email: Email string to validate
            
        Returns:
            True if valid email format
        """
        if not isinstance(email, str):
            return False
        
        # Basic email regex (not perfect but good enough for most cases)
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_pattern, email))
    
    @classmethod
    def validate_url(cls, url: str, allowed_schemes: Optional[List[str]] = None) -> bool:
        """
        Validate URL format and scheme
        
        Args:
            url: URL string to validate
            allowed_schemes: List of allowed URL schemes
            
        Returns:
            True if valid URL
        """
        if not isinstance(url, str):
            return False
        
        allowed_schemes = allowed_schemes or ['http', 'https']
        
        try:
            parsed = urlparse(url)
            return (
                parsed.scheme in allowed_schemes and
                parsed.netloc and
                not any(re.search(pattern, url, re.IGNORECASE) 
                       for pattern in cls.MALICIOUS_PATTERNS)
            )
        except Exception:
            return False
    
    @classmethod
    def sanitize_filename(cls, filename: str) -> str:
        """
        Sanitize filename to prevent path traversal and other attacks
        
        Args:
            filename: Filename to sanitize
            
        Returns:
            Sanitized filename
        """
        if not isinstance(filename, str):
            return "unknown_file"
        
        # Remove path components
        sanitized = filename.split('/')[-1].split('\\')[-1]
        
        # Remove dangerous characters
        sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', sanitized)
        
        # Check for path traversal patterns
        for pattern in cls.PATH_TRAVERSAL_PATTERNS:
            if re.search(pattern, sanitized, re.IGNORECASE):
                logger.warning(f"Path traversal pattern detected in filename: {pattern}")
                sanitized = re.sub(pattern, '_', sanitized, flags=re.IGNORECASE)
        
        # Ensure filename is not empty and not too long
        if not sanitized or sanitized.isspace():
            sanitized = "sanitized_file"
        
        if len(sanitized) > 255:
            sanitized = sanitized[:255]
        
        return sanitized
    
    @classmethod
    def check_sql_injection(cls, value: str) -> bool:
        """
        Check if string contains potential SQL injection patterns
        
        Args:
            value: String to check
            
        Returns:
            True if potential SQL injection detected
        """
        if not isinstance(value, str):
            return False
        
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                logger.warning(f"Potential SQL injection pattern detected: {pattern}")
                return True
        
        return False
    
    @classmethod
    def sanitize_dict(cls, data: Dict[str, Any], max_string_length: int = 1000) -> Dict[str, Any]:
        """
        Recursively sanitize dictionary values
        
        Args:
            data: Dictionary to sanitize
            max_string_length: Maximum length for string values
            
        Returns:
            Sanitized dictionary
        """
        if not isinstance(data, dict):
            return {}
        
        sanitized = {}
        
        for key, value in data.items():
            # Sanitize key
            clean_key = cls.sanitize_string(str(key), max_length=100)
            
            # Sanitize value based on type
            if isinstance(value, str):
                sanitized[clean_key] = cls.sanitize_string(value, max_string_length)
            elif isinstance(value, dict):
                sanitized[clean_key] = cls.sanitize_dict(value, max_string_length)
            elif isinstance(value, list):
                sanitized[clean_key] = cls.sanitize_list(value, max_string_length)
            elif isinstance(value, (int, float, bool)) or value is None:
                sanitized[clean_key] = value
            else:
                # Convert other types to string and sanitize
                sanitized[clean_key] = cls.sanitize_string(str(value), max_string_length)
        
        return sanitized
    
    @classmethod
    def sanitize_list(cls, data: List[Any], max_string_length: int = 1000) -> List[Any]:
        """
        Recursively sanitize list values
        
        Args:
            data: List to sanitize
            max_string_length: Maximum length for string values
            
        Returns:
            Sanitized list
        """
        if not isinstance(data, list):
            return []
        
        sanitized = []
        
        for item in data:
            if isinstance(item, str):
                sanitized.append(cls.sanitize_string(item, max_string_length))
            elif isinstance(item, dict):
                sanitized.append(cls.sanitize_dict(item, max_string_length))
            elif isinstance(item, list):
                sanitized.append(cls.sanitize_list(item, max_string_length))
            elif isinstance(item, (int, float, bool)) or item is None:
                sanitized.append(item)
            else:
                sanitized.append(cls.sanitize_string(str(item), max_string_length))
        
        return sanitized


class SecurityValidator:
    """Security validation utilities"""
    
    @staticmethod
    def validate_user_input(data: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Validate user input for security issues
        
        Args:
            data: User input data to validate
            
        Returns:
            Dictionary with validation errors
        """
        errors = {}
        
        for key, value in data.items():
            field_errors = []
            
            if isinstance(value, str):
                # Check for malicious patterns
                for pattern in InputSanitizer.MALICIOUS_PATTERNS:
                    if re.search(pattern, value, re.IGNORECASE):
                        field_errors.append(f"Contains potentially malicious content: {pattern}")
                
                # Check for SQL injection
                if InputSanitizer.check_sql_injection(value):
                    field_errors.append("Contains potential SQL injection patterns")
                
                # Check for path traversal
                for pattern in InputSanitizer.PATH_TRAVERSAL_PATTERNS:
                    if re.search(pattern, value, re.IGNORECASE):
                        field_errors.append("Contains path traversal patterns")
            
            if field_errors:
                errors[key] = field_errors
        
        return errors
    
    @staticmethod
    def validate_file_upload(filename: str, content_type: str, file_size: int) -> List[str]:
        """
        Validate file upload for security
        
        Args:
            filename: Name of uploaded file
            content_type: MIME type of file
            file_size: Size of file in bytes
            
        Returns:
            List of validation errors
        """
        errors = []
        
        # Validate filename
        if not filename or filename.isspace():
            errors.append("Filename is required")
        else:
            # Check for dangerous filename patterns
            dangerous_extensions = [
                '.exe', '.bat', '.cmd', '.com', '.pif', '.scr', '.vbs', '.js',
                '.jar', '.php', '.asp', '.aspx', '.jsp', '.py', '.rb', '.pl'
            ]
            
            filename_lower = filename.lower()
            for ext in dangerous_extensions:
                if filename_lower.endswith(ext):
                    errors.append(f"File type not allowed: {ext}")
                    break
            
            # Check for path traversal in filename
            for pattern in InputSanitizer.PATH_TRAVERSAL_PATTERNS:
                if re.search(pattern, filename, re.IGNORECASE):
                    errors.append("Filename contains path traversal patterns")
        
        # Validate content type
        allowed_content_types = [
            'application/pdf',
            'image/jpeg',
            'image/png',
            'image/gif',
            'text/plain',
            'application/json'
        ]
        
        if content_type not in allowed_content_types:
            errors.append(f"Content type not allowed: {content_type}")
        
        # Validate file size (10MB limit)
        max_size = 10 * 1024 * 1024
        if file_size > max_size:
            errors.append(f"File too large: {file_size} bytes (max: {max_size})")
        
        return errors


# Security middleware for automatic input sanitization
class SecurityMiddleware:
    """Middleware for automatic security checks"""
    
    def __init__(self, sanitize_inputs: bool = True, validate_inputs: bool = True):
        self.sanitize_inputs = sanitize_inputs
        self.validate_inputs = validate_inputs
    
    async def __call__(self, request, call_next):
        """Process request with security checks"""
        
        # Skip security checks for certain endpoints
        skip_paths = ['/health', '/metrics', '/docs', '/openapi.json']
        if any(request.url.path.startswith(path) for path in skip_paths):
            return await call_next(request)
        
        # Validate and sanitize request data if needed
        if self.validate_inputs or self.sanitize_inputs:
            try:
                # This would need to be implemented based on request type
                # For now, we'll just log the security check
                logger.debug(f"Security check for {request.method} {request.url.path}")
            except Exception as e:
                logger.error(f"Security middleware error: {e}")
        
        response = await call_next(request)
        return response


# Global instances
input_sanitizer = InputSanitizer()
security_validator = SecurityValidator()


def get_input_sanitizer() -> InputSanitizer:
    """Get the global input sanitizer instance"""
    return input_sanitizer


def get_security_validator() -> SecurityValidator:
    """Get the global security validator instance"""
    return security_validator