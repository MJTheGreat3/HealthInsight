"""
Security audit and validation tests
"""

import pytest
from app.services.security_audit import SecurityAuditor, SecurityIssue
from app.core.security import InputSanitizer, SecurityValidator


class TestSecurityAuditor:
    """Test security audit functionality"""
    
    @pytest.fixture
    def auditor(self):
        """Create security auditor instance"""
        return SecurityAuditor()
    
    @pytest.mark.asyncio
    async def test_comprehensive_audit(self, auditor):
        """Test comprehensive security audit"""
        result = await auditor.run_comprehensive_audit()
        
        assert result is not None
        assert hasattr(result, 'overall_score')
        assert hasattr(result, 'issues')
        assert hasattr(result, 'passed_checks')
        assert hasattr(result, 'failed_checks')
        assert hasattr(result, 'recommendations')
        
        # Score should be between 0 and 100
        assert 0 <= result.overall_score <= 100
        
        # Should have some checks
        assert len(result.passed_checks) > 0 or len(result.failed_checks) > 0
    
    @pytest.mark.asyncio
    async def test_authentication_security_check(self, auditor):
        """Test authentication security checks"""
        await auditor._check_authentication_security()
        
        # Should have some results
        assert len(auditor.passed_checks) > 0 or len(auditor.issues) > 0
    
    @pytest.mark.asyncio
    async def test_input_validation_check(self, auditor):
        """Test input validation checks"""
        await auditor._check_input_validation()
        
        # Should have some results
        assert len(auditor.passed_checks) > 0 or len(auditor.issues) > 0
    
    @pytest.mark.asyncio
    async def test_validate_input_sanitization(self, auditor):
        """Test input sanitization validation"""
        test_inputs = [
            "normal text",
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "' OR 1=1 --",
            "../../../etc/passwd",
            "eval('malicious code')"
        ]
        
        result = await auditor.validate_input_sanitization(test_inputs)
        
        assert result["tested_inputs"] == len(test_inputs)
        assert "vulnerabilities_found" in result
        assert "safe_inputs" in result
        
        # Should detect some vulnerabilities
        assert len(result["vulnerabilities_found"]) > 0
        assert result["safe_inputs"] < len(test_inputs)


class TestInputSanitizer:
    """Test input sanitization functionality"""
    
    def test_sanitize_string_basic(self):
        """Test basic string sanitization"""
        # Normal text should pass through
        assert InputSanitizer.sanitize_string("Hello World") == "Hello World"
        
        # HTML should be escaped
        result = InputSanitizer.sanitize_string("<script>alert('xss')</script>")
        assert "<script>" not in result
        assert "&lt;script&gt;" in result
    
    def test_sanitize_string_length_limit(self):
        """Test string length limiting"""
        long_string = "a" * 1000
        result = InputSanitizer.sanitize_string(long_string, max_length=100)
        assert len(result) == 100
    
    def test_sanitize_string_malicious_patterns(self):
        """Test malicious pattern removal"""
        malicious_inputs = [
            "javascript:alert('xss')",
            "onclick='alert(1)'",
            "eval('code')",
            "setTimeout('code', 1000)"
        ]
        
        for malicious_input in malicious_inputs:
            result = InputSanitizer.sanitize_string(malicious_input)
            # Should not contain the original malicious content
            assert result != malicious_input
    
    def test_validate_email(self):
        """Test email validation"""
        valid_emails = [
            "user@example.com",
            "test.email+tag@domain.co.uk",
            "user123@test-domain.org"
        ]
        
        invalid_emails = [
            "invalid-email",
            "@domain.com",
            "user@",
            "user@domain",
            "javascript:alert('xss')@domain.com"
        ]
        
        for email in valid_emails:
            assert InputSanitizer.validate_email(email), f"Should be valid: {email}"
        
        for email in invalid_emails:
            assert not InputSanitizer.validate_email(email), f"Should be invalid: {email}"
    
    def test_validate_url(self):
        """Test URL validation"""
        valid_urls = [
            "https://example.com",
            "http://test.domain.org/path",
            "https://subdomain.example.com/path?query=value"
        ]
        
        invalid_urls = [
            "javascript:alert('xss')",
            "ftp://example.com",
            "data:text/html,<script>alert('xss')</script>",
            "not-a-url",
            "http://"
        ]
        
        for url in valid_urls:
            assert InputSanitizer.validate_url(url), f"Should be valid: {url}"
        
        for url in invalid_urls:
            assert not InputSanitizer.validate_url(url), f"Should be invalid: {url}"
    
    def test_sanitize_filename(self):
        """Test filename sanitization"""
        test_cases = [
            ("normal_file.txt", "normal_file.txt"),
            ("../../../etc/passwd", "passwd"),
            ("file<>name.txt", "file__name.txt"),
            ("file|with|pipes.txt", "file_with_pipes.txt"),
            ("", "sanitized_file"),
            ("   ", "sanitized_file")
        ]
        
        for input_filename, expected_pattern in test_cases:
            result = InputSanitizer.sanitize_filename(input_filename)
            if expected_pattern == "sanitized_file":
                assert result == expected_pattern
            else:
                assert expected_pattern in result or result == expected_pattern
    
    def test_check_sql_injection(self):
        """Test SQL injection detection"""
        sql_injection_attempts = [
            "' OR 1=1 --",
            "'; DROP TABLE users; --",
            "UNION SELECT * FROM passwords",
            "admin'/*",
            "1' AND 1=1 --"
        ]
        
        safe_inputs = [
            "normal text",
            "user@example.com",
            "search query",
            "file.txt"
        ]
        
        for injection in sql_injection_attempts:
            assert InputSanitizer.check_sql_injection(injection), f"Should detect SQL injection: {injection}"
        
        for safe_input in safe_inputs:
            assert not InputSanitizer.check_sql_injection(safe_input), f"Should be safe: {safe_input}"
    
    def test_sanitize_dict(self):
        """Test dictionary sanitization"""
        test_dict = {
            "normal_key": "normal value",
            "html_key": "<script>alert('xss')</script>",
            "nested_dict": {
                "inner_key": "javascript:alert('xss')",
                "safe_key": "safe value"
            },
            "list_key": ["safe item", "<script>alert('xss')</script>"],
            "number_key": 123,
            "boolean_key": True,
            "null_key": None
        }
        
        result = InputSanitizer.sanitize_dict(test_dict)
        
        # Check that structure is preserved
        assert "normal_key" in result
        assert "nested_dict" in result
        assert "list_key" in result
        
        # Check that malicious content is sanitized
        assert "<script>" not in str(result)
        assert "javascript:" not in str(result)
        
        # Check that safe values are preserved
        assert result["normal_key"] == "normal value"
        assert result["number_key"] == 123
        assert result["boolean_key"] is True
        assert result["null_key"] is None


class TestSecurityValidator:
    """Test security validation functionality"""
    
    def test_validate_user_input(self):
        """Test user input validation"""
        test_data = {
            "safe_field": "normal text",
            "xss_field": "<script>alert('xss')</script>",
            "sql_field": "' OR 1=1 --",
            "path_field": "../../../etc/passwd",
            "js_field": "javascript:alert('xss')"
        }
        
        errors = SecurityValidator.validate_user_input(test_data)
        
        # Should have no errors for safe field
        assert "safe_field" not in errors
        
        # Should have errors for malicious fields
        assert "xss_field" in errors
        assert "sql_field" in errors
        assert "path_field" in errors
        assert "js_field" in errors
    
    def test_validate_file_upload(self):
        """Test file upload validation"""
        # Test valid file
        errors = SecurityValidator.validate_file_upload(
            "document.pdf", "application/pdf", 1024 * 1024
        )
        assert len(errors) == 0
        
        # Test dangerous file extension
        errors = SecurityValidator.validate_file_upload(
            "malware.exe", "application/octet-stream", 1024
        )
        assert len(errors) > 0
        assert any("not allowed" in error for error in errors)
        
        # Test file too large
        errors = SecurityValidator.validate_file_upload(
            "large.pdf", "application/pdf", 20 * 1024 * 1024
        )
        assert len(errors) > 0
        assert any("too large" in error for error in errors)
        
        # Test invalid content type
        errors = SecurityValidator.validate_file_upload(
            "document.pdf", "application/x-malware", 1024
        )
        assert len(errors) > 0
        assert any("not allowed" in error for error in errors)
        
        # Test path traversal in filename
        errors = SecurityValidator.validate_file_upload(
            "../../../malicious.pdf", "application/pdf", 1024
        )
        assert len(errors) > 0
        assert any("traversal" in error for error in errors)


@pytest.mark.asyncio
async def test_security_integration():
    """Test security components working together"""
    auditor = SecurityAuditor()
    
    # Run audit
    result = await auditor.run_comprehensive_audit()
    
    # Test input sanitization
    malicious_inputs = [
        "<script>alert('xss')</script>",
        "javascript:alert('xss')",
        "' OR 1=1 --",
        "../../../etc/passwd"
    ]
    
    sanitization_result = await auditor.validate_input_sanitization(malicious_inputs)
    
    # Should detect vulnerabilities
    assert len(sanitization_result["vulnerabilities_found"]) > 0
    
    # Audit should complete successfully
    assert result.overall_score >= 0
    assert len(result.recommendations) > 0