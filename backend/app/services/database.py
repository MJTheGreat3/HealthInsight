"""
MongoDB database service with CRUD operations
"""

from typing import Any, Dict, List, Optional, Union
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection
from pymongo.errors import DuplicateKeyError, PyMongoError
from bson import ObjectId
from datetime import datetime
import logging

from app.core.database import get_database
from app.models import (
    PatientModel, InstitutionModel, UserModel, Report, LLMReportModel, 
    UserType
)
from app.models.chat import ChatSession

logger = logging.getLogger(__name__)


class DatabaseService:
    """MongoDB database service with async CRUD operations"""
    
    def __init__(self):
        self.db: AsyncIOMotorDatabase = None
        self.users: AsyncIOMotorCollection = None
        self.reports: AsyncIOMotorCollection = None
        self.llm_reports: AsyncIOMotorCollection = None
        self.chat_sessions: AsyncIOMotorCollection = None
    
    async def initialize(self):
        """Initialize database connection and collections"""
        try:
            self.db = get_database()
            if not self.db:
                raise RuntimeError("Database connection not established")
            
            # Initialize collections
            self.users = self.db.users
            self.reports = self.db.reports
            self.llm_reports = self.db.llm_reports
            self.chat_sessions = self.db.chat_sessions
            
            # Create indexes for better performance
            await self._create_indexes()
            logger.info("Database service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database service: {e}")
            raise
    
    async def _create_indexes(self):
        """Create database indexes for better query performance"""
        try:
            # Users collection indexes
            await self.users.create_index("uid", unique=True)
            await self.users.create_index("user_type")
            
            # Reports collection indexes
            await self.reports.create_index("report_id", unique=True)
            await self.reports.create_index("patient_id")
            await self.reports.create_index("processed_at")
            
            # LLM reports collection indexes
            await self.llm_reports.create_index([("patient_id", 1), ("report_id", 1)])
            
            # Chat sessions collection indexes
            await self.chat_sessions.create_index("patient_id")
            await self.chat_sessions.create_index("created_at")
            
            logger.info("Database indexes created successfully")
            
        except Exception as e:
            logger.warning(f"Failed to create some indexes: {e}")
    
    # User CRUD operations
    async def create_user(self, user_data: Union[PatientModel, InstitutionModel, UserModel]) -> str:
        """Create a new user (patient or institution)"""
        try:
            user_dict = user_data.model_dump(exclude_none=True)
            user_dict["created_at"] = datetime.utcnow()
            user_dict["updated_at"] = datetime.utcnow()
            
            result = await self.users.insert_one(user_dict)
            logger.info(f"Created user with ID: {result.inserted_id}")
            return str(result.inserted_id)
            
        except DuplicateKeyError:
            logger.error(f"User with UID {user_data.uid} already exists")
            raise ValueError(f"User with UID {user_data.uid} already exists")
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            raise
    
    async def get_user_by_uid(self, uid: str) -> Optional[Dict[str, Any]]:
        """Get user by Firebase UID"""
        try:
            user = await self.users.find_one({"uid": uid})
            if user:
                user["_id"] = str(user["_id"])
            return user
        except Exception as e:
            logger.error(f"Failed to get user by UID {uid}: {e}")
            raise
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by MongoDB ObjectId"""
        try:
            if not ObjectId.is_valid(user_id):
                return None
            
            user = await self.users.find_one({"_id": ObjectId(user_id)})
            if user:
                user["_id"] = str(user["_id"])
            return user
        except Exception as e:
            logger.error(f"Failed to get user by ID {user_id}: {e}")
            raise
    
    async def update_user(self, uid: str, update_data: Dict[str, Any]) -> bool:
        """Update user data"""
        try:
            update_data["updated_at"] = datetime.utcnow()
            result = await self.users.update_one(
                {"uid": uid},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Failed to update user {uid}: {e}")
            raise
    
    async def delete_user(self, uid: str) -> bool:
        """Delete user by UID"""
        try:
            result = await self.users.delete_one({"uid": uid})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Failed to delete user {uid}: {e}")
            raise
    
    async def get_all_patients(self) -> List[Dict[str, Any]]:
        """Get all patients for hospital interface"""
        try:
            cursor = self.users.find({"user_type": UserType.PATIENT})
            patients = []
            async for patient in cursor:
                patient["_id"] = str(patient["_id"])
                patients.append(patient)
            return patients
        except Exception as e:
            logger.error(f"Failed to get all patients: {e}")
            raise
    
    # Report CRUD operations
    async def create_report(self, report: Report) -> str:
        """Create a new medical report"""
        try:
            report_dict = report.model_dump(exclude_none=True, by_alias=True)
            if "_id" in report_dict and report_dict["_id"] is None:
                del report_dict["_id"]
            
            result = await self.reports.insert_one(report_dict)
            logger.info(f"Created report with ID: {result.inserted_id}")
            return str(result.inserted_id)
            
        except DuplicateKeyError:
            logger.error(f"Report with ID {report.report_id} already exists")
            raise ValueError(f"Report with ID {report.report_id} already exists")
        except Exception as e:
            logger.error(f"Failed to create report: {e}")
            raise
    
    async def get_report_by_id(self, report_id: str) -> Optional[Dict[str, Any]]:
        """Get report by report_id"""
        try:
            report = await self.reports.find_one({"report_id": report_id})
            if report:
                report["_id"] = str(report["_id"])
            return report
        except Exception as e:
            logger.error(f"Failed to get report {report_id}: {e}")
            raise
    
    async def get_reports_by_patient_id(self, patient_id: str, skip: int = 0, limit: int = 50) -> List[Dict[str, Any]]:
        """Get reports for a patient with pagination"""
        try:
            cursor = self.reports.find({"patient_id": patient_id}).sort("processed_at", -1).skip(skip).limit(limit)
            reports = []
            async for report in cursor:
                report["_id"] = str(report["_id"])
                reports.append(report)
            return reports
        except Exception as e:
            logger.error(f"Failed to get reports for patient {patient_id}: {e}")
            raise
    
    async def count_reports_by_patient_id(self, patient_id: str) -> int:
        """Count total reports for a patient"""
        try:
            return await self.reports.count_documents({"patient_id": patient_id})
        except Exception as e:
            logger.error(f"Failed to count reports for patient {patient_id}: {e}")
            raise
    
    async def get_reports_by_patient_ids(self, patient_ids: List[str], skip: int = 0, limit: int = 50) -> List[Dict[str, Any]]:
        """Get reports for multiple patients with pagination"""
        try:
            cursor = self.reports.find({"patient_id": {"$in": patient_ids}}).sort("processed_at", -1).skip(skip).limit(limit)
            reports = []
            async for report in cursor:
                report["_id"] = str(report["_id"])
                reports.append(report)
            return reports
        except Exception as e:
            logger.error(f"Failed to get reports for patients {patient_ids}: {e}")
            raise
    
    async def count_reports_by_patient_ids(self, patient_ids: List[str]) -> int:
        """Count total reports for multiple patients"""
        try:
            return await self.reports.count_documents({"patient_id": {"$in": patient_ids}})
        except Exception as e:
            logger.error(f"Failed to count reports for patients {patient_ids}: {e}")
            raise
    
    async def add_report_to_patient(self, patient_id: str, report_id: str) -> bool:
        """Add report ID to patient's reports list"""
        try:
            result = await self.users.update_one(
                {"uid": patient_id, "user_type": UserType.PATIENT},
                {"$addToSet": {"reports": report_id}, "$set": {"updated_at": datetime.utcnow()}}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Failed to add report {report_id} to patient {patient_id}: {e}")
            raise
    
    async def update_report(self, report_id: str, update_data: Dict[str, Any]) -> bool:
        """Update report data"""
        try:
            result = await self.reports.update_one(
                {"report_id": report_id},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Failed to update report {report_id}: {e}")
            raise
    
    async def delete_report(self, report_id: str) -> bool:
        """Delete report by report_id"""
        try:
            result = await self.reports.delete_one({"report_id": report_id})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Failed to delete report {report_id}: {e}")
            raise
    
    # LLM Report CRUD operations
    async def create_llm_report(self, llm_report: LLMReportModel) -> str:
        """Create a new LLM analysis report"""
        try:
            llm_dict = llm_report.model_dump(exclude_none=True)
            llm_dict["created_at"] = datetime.utcnow()
            
            result = await self.llm_reports.insert_one(llm_dict)
            logger.info(f"Created LLM report with ID: {result.inserted_id}")
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"Failed to create LLM report: {e}")
            raise
    
    async def get_llm_report(self, patient_id: str, report_id: str) -> Optional[Dict[str, Any]]:
        """Get LLM report by patient and report ID"""
        try:
            llm_report = await self.llm_reports.find_one({
                "patient_id": patient_id,
                "report_id": report_id
            })
            if llm_report:
                llm_report["_id"] = str(llm_report["_id"])
            return llm_report
        except Exception as e:
            logger.error(f"Failed to get LLM report for patient {patient_id}, report {report_id}: {e}")
            raise
    
    # Chat Session CRUD operations
    async def create_chat_session(self, chat_session: ChatSession) -> str:
        """Create a new chat session"""
        try:
            chat_dict = chat_session.model_dump(exclude_none=True, by_alias=True)
            if "_id" in chat_dict and chat_dict["_id"] is None:
                del chat_dict["_id"]
            
            result = await self.chat_sessions.insert_one(chat_dict)
            logger.info(f"Created chat session with ID: {result.inserted_id}")
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"Failed to create chat session: {e}")
            raise
    
    async def get_chat_session(self, patient_id: str) -> Optional[Dict[str, Any]]:
        """Get latest chat session for a patient"""
        try:
            chat_session = await self.chat_sessions.find_one(
                {"patient_id": patient_id},
                sort=[("created_at", -1)]
            )
            if chat_session:
                chat_session["_id"] = str(chat_session["_id"])
            return chat_session
        except Exception as e:
            logger.error(f"Failed to get chat session for patient {patient_id}: {e}")
            raise
    
    async def update_chat_session(self, session_id: str, update_data: Dict[str, Any]) -> bool:
        """Update chat session"""
        try:
            if not ObjectId.is_valid(session_id):
                return False
            
            update_data["updated_at"] = datetime.utcnow()
            result = await self.chat_sessions.update_one(
                {"_id": ObjectId(session_id)},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Failed to update chat session {session_id}: {e}")
            raise
    
    # Search and filtering operations
    async def search_patients(self, query: str) -> List[Dict[str, Any]]:
        """Search patients by name or other criteria"""
        try:
            search_filter = {
                "user_type": UserType.PATIENT,
                "$or": [
                    {"name": {"$regex": query, "$options": "i"}},
                    {"uid": {"$regex": query, "$options": "i"}}
                ]
            }
            
            cursor = self.users.find(search_filter)
            patients = []
            async for patient in cursor:
                patient["_id"] = str(patient["_id"])
                patients.append(patient)
            return patients
        except Exception as e:
            logger.error(f"Failed to search patients with query '{query}': {e}")
            raise
    
    async def search_reports(self, patient_id: str, query: str) -> List[Dict[str, Any]]:
        """Search reports for a patient"""
        try:
            search_filter = {
                "patient_id": patient_id,
                "$or": [
                    {"report_id": {"$regex": query, "$options": "i"}},
                    {"llm_output": {"$regex": query, "$options": "i"}}
                ]
            }
            
            cursor = self.reports.find(search_filter).sort("processed_at", -1)
            reports = []
            async for report in cursor:
                report["_id"] = str(report["_id"])
                reports.append(report)
            return reports
        except Exception as e:
            logger.error(f"Failed to search reports for patient {patient_id} with query '{query}': {e}")
            raise
    
    # Health check and utility methods
    async def health_check(self) -> Dict[str, Any]:
        """Check database connection health"""
        try:
            # Simple ping to check connection
            await self.db.command("ping")
            
            # Get collection stats
            users_count = await self.users.count_documents({})
            reports_count = await self.reports.count_documents({})
            
            return {
                "status": "healthy",
                "database": self.db.name,
                "collections": {
                    "users": users_count,
                    "reports": reports_count,
                    "llm_reports": await self.llm_reports.count_documents({}),
                    "chat_sessions": await self.chat_sessions.count_documents({})
                }
            }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def update_user_favorites(self, user_id: str, favorites: List[str]) -> bool:
        """Update user's favorite/tracked metrics"""
        try:
            result = await self.users.update_one(
                {"uid": user_id},
                {"$set": {"favorites": favorites}}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Failed to update favorites for user {user_id}: {e}")
            raise


# Global database service instance
db_service = DatabaseService()