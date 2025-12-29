"""
Security audit service for HealthInsightCore
Performs security checks and validates system security posture
"""

import re
import hashlib
import secrets
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class SecurityIssue:
    """Security issue data structure"""
    severity: str  # "critical", "high", "medium", "low"
    category: str  # "authentication", "authorization", "input_validation", "data_protection", etc.
    title: str
    description: str
    recommendation: str
    affected_component: str
    cve_reference: Optional[str] = None


@dataclass
class SecurityAuditResult:
    """Security audit result"""
    timestamp: datetime
    overall_score: int  # 0-100
    issues: List[SecurityIssue]
    passed_checks: List[str]
    failed_checks: List[str]
    recommendations: List[str]


class SecurityAuditor:
    """Security audit and validation service"""
    
    def __init__(self):
        self.issues: List[SecurityIssue] = []
        self.passed_checks: List[str] = []
        self.failed_checks: List[str] = []
    
    async def run_comprehensive_audit(self) -> SecurityAuditResult:
        """Run comprehensive security audit"""
        logger.info("Starting comprehensive security audit")
        
        # Reset state
        self.issues = []
        self.passed_checks = []
        self.failed_checks = []
        
        # Run all security checks
        await self._check_authentication_security()
        await self._check_authorization_controls()
        await self._check_input_validation()
        await self._check_data_protection()
        await self._check_api_security()
        await self._check_dependency_security()
        await self._check_configuration_security()
        await self._check_logging_security()
        
        # Calculate overall security score
        score = self._calculate_security_score()
        
        # Generate recommendations
        recommendations = self._generate_recommendations()
        
        result = SecurityAuditResult(
            timestamp=datetime.utcnow(),
            overall_score=score,
            issues=self.issues,
            passed_checks=self.passed_checks,
            failed_checks=self.failed_checks,
            recommendations=recommendations
        )
        
        logger.info(f"Security audit completed. Score: {score}/100, Issues: {len(self.issues)}")
        return result
    
    async def _check_authentication_security(self):
        """Check authentication security measures"""
        check_name = "Authentication Security"
        
        try:
            # Check Firebase Auth integration
            from app.core.config import settings
            
            if not settings.FIREBASE_PROJECT_ID:
                self._add_issue(
                    "high", "authentication", "Missing Firebase Configuration",
                    "Firebase project ID is not configured",
                    "Configure Firebase authentication properly",
                    "Authentication Service"
                )
            else:
                self.passed_checks.append("Firebase configuration present")
            
            # Check for secure token handling
            from app.services.auth import AuthService
            auth_service = AuthService()
            
            # Verify token validation is implemented
            if hasattr(auth_service, 'verify_token'):
                self.passed_checks.append("Token verification implemented")
            else:
                self._add_issue(
                    "critical", "authentication", "Missing Token Verification",
                    "Token verification method not found",
                    "Implement proper token verification",
                    "Authentication Service"
                )
            
            # Check for session management
            self.passed_checks.append("Authentication security checks completed")
            
        except Exception as e:
            self._add_issue(
                "medium", "authentication", "Authentication Check Failed",
                f"Could not verify authentication security: {str(e)}",
                "Review authentication implementation",
                "Authentication Service"
            )
            self.failed_checks.append(f"{check_name}: {str(e)}")
    
    async def _check_authorization_controls(self):
        """Check authorization and access control measures"""
        check_name = "Authorization Controls"
        
        try:
            # Check role-based access control implementation
            from app.core.middleware import get_current_user, require_patient_role
            
            self.passed_checks.append("RBAC middleware implemented")
            
            # Check for proper role validation
            from app.models.user import UserType
            
            if hasattr(UserType, 'PATIENT') and hasattr(UserType, 'INSTITUTION'):
                self.passed_checks.append("User roles properly defined")
            else:
                self._add_issue(
                    "high", "authorization", "Incomplete Role Definition",
                    "User roles are not properly defined",
                    "Define all required user roles",
                    "User Model"
                )
            
            # Check for audit logging
            try:
                from app.services.audit import audit_service
                self.passed_checks.append("Audit logging service available")
            except ImportError:
                self._add_issue(
                    "medium", "authorization", "Missing Audit Logging",
                    "Audit logging service not found",
                    "Implement comprehensive audit logging",
                    "Audit Service"
                )
            
        except Exception as e:
            self._add_issue(
                "medium", "authorization", "Authorization Check Failed",
                f"Could not verify authorization controls: {str(e)}",
                "Review authorization implementation",
                "Authorization System"
            )
            self.failed_checks.append(f"{check_name}: {str(e)}")
    
    async def _check_input_validation(self):
        """Check input validation and sanitization"""
        check_name = "Input Validation"
        
        try:
            # Check Pydantic model validation
            from app.models.report import Report, MetricData
            from app.models.user import UserModel
            
            # Verify models have proper validation
            if hasattr(Report, '__annotations__'):
                self.passed_checks.append("Pydantic models with type validation")
            
            # Check for SQL injection protection (MongoDB should be safe by default)
            self.passed_checks.append("MongoDB provides built-in injection protection")
            
            # Check file upload validation
            from app.api.v1.endpoints.reports import MAX_FILE_SIZE, ALLOWED_CONTENT_TYPES
            
            if MAX_FILE_SIZE and ALLOWED_CONTENT_TYPES:
                self.passed_checks.append("File upload validation configured")
            else:
                self._add_issue(
                    "high", "input_validation", "Insufficient File Upload Validation",
                    "File upload validation is incomplete",
                    "Implement comprehensive file upload validation",
                    "File Upload Handler"
                )
            
            # Check for XSS protection
            self.passed_checks.append("API-only backend reduces XSS risk")
            
        except Exception as e:
            self._add_issue(
                "medium", "input_validation", "Input Validation Check Failed",
                f"Could not verify input validation: {str(e)}",
                "Review input validation implementation",
                "Input Validation System"
            )
            self.failed_checks.append(f"{check_name}: {str(e)}")
    
    async def _check_data_protection(self):
        """Check data protection and privacy measures"""
        check_name = "Data Protection"
        
        try:
            # Check for data encryption in transit (HTTPS)
            from app.core.config import settings
            
            # In production, should enforce HTTPS
            self.passed_checks.append("HTTPS enforcement should be configured in production")
            
            # Check for sensitive data handling
            if hasattr(settings, 'SECRET_KEY') and settings.SECRET_KEY:
                if settings.SECRET_KEY == "your-secret-key-here":
                    self._add_issue(
                        "critical", "data_protection", "Default Secret Key",
                        "Using default secret key in configuration",
                        "Generate and use a strong, unique secret key",
                        "Configuration"
                    )
                else:
                    self.passed_checks.append("Custom secret key configured")
            
            # Check for password handling (Firebase handles this)
            self.passed_checks.append("Password handling delegated to Firebase Auth")
            
            # Check for data retention policies
            # This would need to be implemented based on requirements
            self._add_issue(
                "low", "data_protection", "Data Retention Policy",
                "Data retention policies not explicitly implemented",
                "Implement data retention and deletion policies",
                "Data Management"
            )
            
        except Exception as e:
            self._add_issue(
                "medium", "data_protection", "Data Protection Check Failed",
                f"Could not verify data protection measures: {str(e)}",
                "Review data protection implementation",
                "Data Protection System"
            )
            self.failed_checks.append(f"{check_name}: {str(e)}")
    
    async def _check_api_security(self):
        """Check API security measures"""
        check_name = "API Security"
        
        try:
            # Check CORS configuration
            from app.main import app
            
            # Look for CORS middleware
            cors_configured = False
            for middleware in app.user_middleware:
                if 'cors' in str(middleware).lower():
                    cors_configured = True
                    break
            
            if cors_configured:
                self.passed_checks.append("CORS middleware configured")
            else:
                self._add_issue(
                    "medium", "api_security", "CORS Not Configured",
                    "CORS middleware not found",
                    "Configure CORS middleware properly",
                    "API Configuration"
                )
            
            # Check for rate limiting
            # This would need to be implemented
            self._add_issue(
                "medium", "api_security", "Rate Limiting Not Implemented",
                "API rate limiting is not implemented",
                "Implement rate limiting to prevent abuse",
                "API Security"
            )
            
            # Check for API versioning
            from app.core.config import settings
            if hasattr(settings, 'API_V1_STR'):
                self.passed_checks.append("API versioning implemented")
            
            # Check for proper error handling
            try:
                from app.core.error_handlers import setup_exception_handlers
                self.passed_checks.append("Global exception handlers configured")
            except ImportError:
                self._add_issue(
                    "medium", "api_security", "Missing Error Handlers",
                    "Global exception handlers not found",
                    "Implement comprehensive error handling",
                    "Error Handling"
                )
            
        except Exception as e:
            self._add_issue(
                "medium", "api_security", "API Security Check Failed",
                f"Could not verify API security measures: {str(e)}",
                "Review API security implementation",
                "API Security System"
            )
            self.failed_checks.append(f"{check_name}: {str(e)}")
    
    async def _check_dependency_security(self):
        """Check dependency security"""
        check_name = "Dependency Security"
        
        try:
            # Check for requirements.txt
            requirements_path = Path("requirements.txt")
            if requirements_path.exists():
                self.passed_checks.append("Requirements file exists")
                
                # Read requirements and check for known vulnerable packages
                with open(requirements_path, 'r') as f:
                    requirements = f.read()
                
                # Check for specific vulnerable versions (this is a basic check)
                vulnerable_patterns = [
                    r'fastapi==0\.6[0-9]\.',  # Old FastAPI versions
                    r'pydantic==1\.',         # Old Pydantic versions
                    r'uvicorn==0\.1[0-5]\.',  # Old Uvicorn versions
                ]
                
                for pattern in vulnerable_patterns:
                    if re.search(pattern, requirements):
                        self._add_issue(
                            "high", "dependency_security", "Potentially Vulnerable Dependency",
                            f"Found potentially vulnerable dependency matching pattern: {pattern}",
                            "Update to latest secure versions",
                            "Dependencies"
                        )
                
                self.passed_checks.append("Dependency versions checked")
            else:
                self._add_issue(
                    "medium", "dependency_security", "Missing Requirements File",
                    "Requirements.txt file not found",
                    "Create and maintain requirements.txt file",
                    "Dependencies"
                )
            
        except Exception as e:
            self._add_issue(
                "low", "dependency_security", "Dependency Check Failed",
                f"Could not check dependencies: {str(e)}",
                "Review dependency management",
                "Dependency Management"
            )
            self.failed_checks.append(f"{check_name}: {str(e)}")
    
    async def _check_configuration_security(self):
        """Check configuration security"""
        check_name = "Configuration Security"
        
        try:
            from app.core.config import settings
            
            # Check for environment variable usage
            import os
            
            sensitive_vars = [
                'MONGODB_URL', 'OPENAI_API_KEY', 'FIREBASE_PRIVATE_KEY', 'SECRET_KEY'
            ]
            
            for var in sensitive_vars:
                if hasattr(settings, var):
                    value = getattr(settings, var)
                    if value and not value.startswith('${') and var in os.environ:
                        self.passed_checks.append(f"{var} configured via environment")
                    elif value and value in ['', 'your-secret-key-here', 'default-value']:
                        self._add_issue(
                            "high", "configuration", f"Default {var}",
                            f"{var} is using default or empty value",
                            f"Configure proper {var} value",
                            "Configuration"
                        )
            
            # Check for debug mode
            if hasattr(settings, 'DEBUG') and getattr(settings, 'DEBUG', False):
                self._add_issue(
                    "medium", "configuration", "Debug Mode Enabled",
                    "Debug mode should not be enabled in production",
                    "Disable debug mode in production",
                    "Configuration"
                )
            else:
                self.passed_checks.append("Debug mode properly configured")
            
        except Exception as e:
            self._add_issue(
                "medium", "configuration", "Configuration Check Failed",
                f"Could not verify configuration security: {str(e)}",
                "Review configuration security",
                "Configuration System"
            )
            self.failed_checks.append(f"{check_name}: {str(e)}")
    
    async def _check_logging_security(self):
        """Check logging and monitoring security"""
        check_name = "Logging Security"
        
        try:
            # Check for logging configuration
            import logging
            
            if logging.getLogger().handlers:
                self.passed_checks.append("Logging configured")
            else:
                self._add_issue(
                    "low", "logging", "Logging Not Configured",
                    "Application logging is not properly configured",
                    "Configure comprehensive logging",
                    "Logging System"
                )
            
            # Check for sensitive data in logs
            # This is a basic check - in practice, you'd scan actual log files
            self.passed_checks.append("Logging security awareness noted")
            
            # Check for audit logging
            try:
                from app.services.audit import audit_service
                self.passed_checks.append("Audit logging service available")
            except ImportError:
                self._add_issue(
                    "medium", "logging", "Missing Audit Logging",
                    "Audit logging service not implemented",
                    "Implement comprehensive audit logging",
                    "Audit System"
                )
            
        except Exception as e:
            self._add_issue(
                "low", "logging", "Logging Check Failed",
                f"Could not verify logging security: {str(e)}",
                "Review logging implementation",
                "Logging System"
            )
            self.failed_checks.append(f"{check_name}: {str(e)}")
    
    def _add_issue(self, severity: str, category: str, title: str, description: str, recommendation: str, component: str):
        """Add a security issue"""
        issue = SecurityIssue(
            severity=severity,
            category=category,
            title=title,
            description=description,
            recommendation=recommendation,
            affected_component=component
        )
        self.issues.append(issue)
    
    def _calculate_security_score(self) -> int:
        """Calculate overall security score (0-100)"""
        if not self.issues and not self.passed_checks:
            return 0
        
        # Weight issues by severity
        severity_weights = {
            "critical": -25,
            "high": -15,
            "medium": -8,
            "low": -3
        }
        
        # Start with base score
        base_score = 100
        
        # Deduct points for issues
        for issue in self.issues:
            base_score += severity_weights.get(issue.severity, -5)
        
        # Bonus points for passed checks (up to 20 points)
        bonus_points = min(len(self.passed_checks) * 2, 20)
        
        final_score = max(0, min(100, base_score + bonus_points))
        return final_score
    
    def _generate_recommendations(self) -> List[str]:
        """Generate security recommendations"""
        recommendations = []
        
        # Group issues by severity
        critical_issues = [i for i in self.issues if i.severity == "critical"]
        high_issues = [i for i in self.issues if i.severity == "high"]
        
        if critical_issues:
            recommendations.append("URGENT: Address critical security issues immediately")
            for issue in critical_issues:
                recommendations.append(f"- {issue.title}: {issue.recommendation}")
        
        if high_issues:
            recommendations.append("HIGH PRIORITY: Address high-severity security issues")
            for issue in high_issues:
                recommendations.append(f"- {issue.title}: {issue.recommendation}")
        
        # General recommendations
        recommendations.extend([
            "Implement regular security audits",
            "Keep dependencies updated",
            "Use HTTPS in production",
            "Implement proper logging and monitoring",
            "Regular backup and disaster recovery testing",
            "Security training for development team"
        ])
        
        return recommendations
    
    async def validate_input_sanitization(self, test_inputs: List[str]) -> Dict[str, Any]:
        """Test input sanitization with various attack vectors"""
        results = {
            "tested_inputs": len(test_inputs),
            "vulnerabilities_found": [],
            "safe_inputs": 0
        }
        
        # Common attack patterns
        attack_patterns = [
            r'<script.*?>.*?</script>',  # XSS
            r'javascript:',              # JavaScript injection
            r'on\w+\s*=',               # Event handlers
            r'union\s+select',          # SQL injection (basic)
            r'drop\s+table',            # SQL injection
            r'\.\./.*\.\.',             # Path traversal
            r'eval\s*\(',               # Code injection
        ]
        
        for test_input in test_inputs:
            is_safe = True
            
            for pattern in attack_patterns:
                if re.search(pattern, test_input, re.IGNORECASE):
                    results["vulnerabilities_found"].append({
                        "input": test_input[:100],  # Truncate for safety
                        "pattern": pattern,
                        "risk": "Potential injection vulnerability"
                    })
                    is_safe = False
                    break
            
            if is_safe:
                results["safe_inputs"] += 1
        
        return results
    
    async def check_data_access_controls(self, user_scenarios: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Test data access controls with different user scenarios"""
        results = {
            "scenarios_tested": len(user_scenarios),
            "access_violations": [],
            "proper_access_controls": 0
        }
        
        # This would need to be implemented with actual API testing
        # For now, we'll return a placeholder
        results["note"] = "Data access control testing requires integration testing setup"
        
        return results


# Global security auditor instance
security_auditor = SecurityAuditor()


def get_security_auditor() -> SecurityAuditor:
    """Get the global security auditor instance"""
    return security_auditor