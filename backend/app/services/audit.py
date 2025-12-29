"""
Audit logging service for tracking user access and actions
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any, Union
from enum import Enum

from app.models.user import UserType, UserModel, PatientModel, InstitutionModel
from app.services.database import DatabaseService


class AuditAction(str, Enum):
    """Enumeration of audit actions"""
    LOGIN = "login"
    LOGOUT = "logout"
    ACCESS_PATIENT_DATA = "access_patient_data"
    VIEW_PATIENT_DASHBOARD = "view_patient_dashboard"
    SEARCH_PATIENTS = "search_patients"
    VIEW_PATIENT_REPORTS = "view_patient_reports"
    ACCESS_PATIENT_PROFILE = "access_patient_profile"
    UPLOAD_REPORT = "upload_report"
    GENERATE_ANALYSIS = "generate_analysis"
    UPDATE_PROFILE = "update_profile"
    DELETE_REPORT = "delete_report"
    EXPORT_DATA = "export_data"


class AuditLevel(str, Enum):
    """Enumeration of audit levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditService:
    """Service for audit logging and compliance tracking"""
    
    def __init__(self):
        self.db_service = DatabaseService()
        self.logger = logging.getLogger("audit")
        
        # Configure audit logger
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - AUDIT - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    async def log_user_action(
        self,
        user: Union[UserModel, PatientModel, InstitutionModel],
        action: AuditAction,
        level: AuditLevel = AuditLevel.INFO,
        details: Optional[Dict[str, Any]] = None,
        patient_id: Optional[str] = None,
        resource_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> None:
        """
        Log user action for audit purposes
        
        Args:
            user: User performing the action
            action: Type of action being performed
            level: Severity level of the audit log
            details: Additional details about the action
            patient_id: ID of patient being accessed (for hospital users)
            resource_id: ID of resource being accessed
            ip_address: IP address of the user
            user_agent: User agent string
        """
        try:
            # Initialize database service if needed
            if not self.db_service.db:
                await self.db_service.initialize()
            
            # Create audit log entry
            audit_entry = {
                "timestamp": datetime.utcnow(),
                "user_id": user.uid,
                "user_type": user.user_type.value if user.user_type else "unknown",
                "user_name": getattr(user, 'name', 'Unknown'),
                "action": action.value,
                "level": level.value,
                "details": details or {},
                "patient_id": patient_id,
                "resource_id": resource_id,
                "ip_address": ip_address,
                "user_agent": user_agent
            }
            
            # Store in database
            await self._store_audit_log(audit_entry)
            
            # Log to application logger
            log_message = self._format_log_message(audit_entry)
            
            if level == AuditLevel.INFO:
                self.logger.info(log_message)
            elif level == AuditLevel.WARNING:
                self.logger.warning(log_message)
            elif level == AuditLevel.ERROR:
                self.logger.error(log_message)
            elif level == AuditLevel.CRITICAL:
                self.logger.critical(log_message)
            
        except Exception as e:
            # Ensure audit logging failures don't break the application
            self.logger.error(f"Failed to log audit entry: {str(e)}")
    
    async def log_hospital_patient_access(
        self,
        hospital_user: Union[InstitutionModel, UserModel],
        patient_id: str,
        action: AuditAction,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> None:
        """
        Log hospital user access to patient data (compliance requirement)
        
        Args:
            hospital_user: Hospital user accessing patient data
            patient_id: ID of patient being accessed
            action: Type of access being performed
            details: Additional details about the access
            ip_address: IP address of the hospital user
            user_agent: User agent string
        """
        # Ensure this is a hospital user
        if hospital_user.user_type != UserType.INSTITUTION:
            await self.log_user_action(
                hospital_user,
                action,
                AuditLevel.WARNING,
                {"error": "Non-hospital user attempting patient access", "patient_id": patient_id},
                patient_id=patient_id,
                ip_address=ip_address,
                user_agent=user_agent
            )
            return
        
        # Log the patient access
        audit_details = {
            "compliance_log": True,
            "access_type": "patient_data",
            **(details or {})
        }
        
        await self.log_user_action(
            hospital_user,
            action,
            AuditLevel.INFO,
            audit_details,
            patient_id=patient_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    async def log_authentication_event(
        self,
        user: Union[UserModel, PatientModel, InstitutionModel],
        action: AuditAction,
        success: bool = True,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        error_details: Optional[str] = None
    ) -> None:
        """
        Log authentication events (login/logout)
        
        Args:
            user: User performing authentication
            action: LOGIN or LOGOUT
            success: Whether the authentication was successful
            ip_address: IP address of the user
            user_agent: User agent string
            error_details: Error details if authentication failed
        """
        level = AuditLevel.INFO if success else AuditLevel.WARNING
        details = {
            "success": success,
            "error": error_details if not success else None
        }
        
        await self.log_user_action(
            user,
            action,
            level,
            details,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    async def get_user_audit_logs(
        self,
        user_id: str,
        limit: int = 100,
        action_filter: Optional[AuditAction] = None
    ) -> list[Dict[str, Any]]:
        """
        Retrieve audit logs for a specific user
        
        Args:
            user_id: User ID to retrieve logs for
            limit: Maximum number of logs to retrieve
            action_filter: Optional filter by action type
            
        Returns:
            List of audit log entries
        """
        try:
            if not self.db_service.db:
                await self.db_service.initialize()
            
            # Build query filter
            query_filter = {"user_id": user_id}
            if action_filter:
                query_filter["action"] = action_filter.value
            
            # Query audit logs collection
            audit_logs = self.db_service.db.audit_logs
            cursor = audit_logs.find(query_filter).sort("timestamp", -1).limit(limit)
            
            logs = []
            async for log in cursor:
                log["_id"] = str(log["_id"])
                logs.append(log)
            
            return logs
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve audit logs for user {user_id}: {str(e)}")
            return []
    
    async def get_patient_access_logs(
        self,
        patient_id: str,
        limit: int = 100
    ) -> list[Dict[str, Any]]:
        """
        Retrieve audit logs for patient data access (compliance)
        
        Args:
            patient_id: Patient ID to retrieve access logs for
            limit: Maximum number of logs to retrieve
            
        Returns:
            List of patient access audit log entries
        """
        try:
            if not self.db_service.db:
                await self.db_service.initialize()
            
            # Query for patient access logs
            query_filter = {
                "patient_id": patient_id,
                "user_type": UserType.INSTITUTION.value
            }
            
            audit_logs = self.db_service.db.audit_logs
            cursor = audit_logs.find(query_filter).sort("timestamp", -1).limit(limit)
            
            logs = []
            async for log in cursor:
                log["_id"] = str(log["_id"])
                logs.append(log)
            
            return logs
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve patient access logs for {patient_id}: {str(e)}")
            return []
    
    async def _store_audit_log(self, audit_entry: Dict[str, Any]) -> None:
        """Store audit log entry in database"""
        try:
            audit_logs = self.db_service.db.audit_logs
            await audit_logs.insert_one(audit_entry)
        except Exception as e:
            self.logger.error(f"Failed to store audit log in database: {str(e)}")
    
    def _format_log_message(self, audit_entry: Dict[str, Any]) -> str:
        """Format audit entry for logging"""
        return (
            f"User: {audit_entry['user_name']} ({audit_entry['user_id']}) | "
            f"Action: {audit_entry['action']} | "
            f"Type: {audit_entry['user_type']} | "
            f"Patient: {audit_entry.get('patient_id', 'N/A')} | "
            f"IP: {audit_entry.get('ip_address', 'N/A')} | "
            f"Details: {audit_entry.get('details', {})}"
        )


# Global audit service instance
audit_service = AuditService()