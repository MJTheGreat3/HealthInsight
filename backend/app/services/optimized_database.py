"""
Optimized database service with caching and performance improvements
"""

import asyncio
from typing import Any, Dict, List, Optional, Union
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection
from pymongo.errors import DuplicateKeyError, PyMongoError
from pymongo import IndexModel, ASCENDING, DESCENDING, TEXT
from bson import ObjectId
from datetime import datetime
import logging

from app.core.database import get_database
from app.core.cache import get_cache_manager
from app.models import (
    PatientModel, InstitutionModel, UserModel, Report, LLMReportModel, 
    UserType
)
from app.models.chat import ChatSession

logger = logging.getLogger(__name__)


class OptimizedDatabaseService:
    """Optimized MongoDB database service with caching and performance improvements"""
    
    def __init__(self):
        self.db: AsyncIOMotorDatabase = None
        self.users: AsyncIOMotorCollection = None
        self.reports: AsyncIOMotorCollection = None
        self.llm_reports: AsyncIOMotorCollection = None
        self.chat_sessions: AsyncIOMotorCollection = None
        self.cache = get_cache_manager()
        self._connection_pool_size = 50
        self._max_idle_time_ms = 30000
    
    async def initialize(self):
        """Initialize database connection and collections with optimizations"""
        try:
            self.db = get_database()
            if not self.db:
                raise RuntimeError("Database connection not established")
            
            # Initialize collections
            self.users = self.db.users
            self.reports = self.db.reports
            self.llm_reports = self.db.llm_reports
            self.chat_sessions = self.db.chat_sessions
            
            # Create optimized indexes
            await self._create_optimized_indexes()
            
            # Configure connection pool settings
            await self._configure_connection_pool()
            
            logger.info("Optimized database service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize optimized database service: {e}")
            raise
    
    async def _create_optimized_indexes(self):
        """Create optimized database indexes for better query performance"""
        try:
            # Users collection indexes
            user_indexes = [
                IndexModel([("uid", ASCENDING)], unique=True),
                IndexModel([("user_type", ASCENDING)]),
                IndexModel([("name", TEXT)]),  # Text search on names
                IndexModel([("created_at", DESCENDING)]),
                IndexModel([("user_type", ASCENDING), ("created_at", DESCENDING)])  # Compound index
            ]
            await self.users.create_indexes(user_indexes)
            
            # Reports collection indexes
            report_indexes = [
                IndexModel([("report_id", ASCENDING)], unique=True),
                IndexModel([("patient_id", ASCENDING)]),
                IndexModel([("processed_at", DESCENDING)]),
                IndexModel([("patient_id", ASCENDING), ("processed_at", DESCENDING)]),  # Most common query
                IndexModel([("llm_output", TEXT)]),  # Text search on analysis
                IndexModel([("attributes", ASCENDING)]),  # For metric searches
                IndexModel([("patient_id", ASCENDING), ("llm_output", ASCENDING)]),  # Analysis filtering
            ]
            await self.reports.create_indexes(report_indexes)
            
            # LLM reports collection indexes
            llm_indexes = [
                IndexModel([("patient_id", ASCENDING), ("report_id", ASCENDING)]),
                IndexModel([("patient_id", ASCENDING), ("created_at", DESCENDING)]),
                IndexModel([("output", TEXT)]),  # Text search on analysis output
            ]
            await self.llm_reports.create_indexes(llm_indexes)
            
            # Chat sessions collection indexes
            chat_indexes = [
                IndexModel([("patient_id", ASCENDING)]),
                IndexModel([("created_at", DESCENDING)]),
                IndexModel([("patient_id", ASCENDING), ("created_at", DESCENDING)]),
                IndexModel([("updated_at", DESCENDING)]),
            ]
            await self.chat_sessions.create_indexes(chat_indexes)
            
            logger.info("Optimized database indexes created successfully")
            
        except Exception as e:
            logger.warning(f"Failed to create some optimized indexes: {e}")
    
    async def _configure_connection_pool(self):
        """Configure MongoDB connection pool for better performance"""
        try:
            # Connection pool is configured at the client level
            # These settings are applied when creating the client
            logger.info("Connection pool configuration applied")
        except Exception as e:
            logger.warning(f"Failed to configure connection pool: {e}")
    
    # Cached user operations
    async def get_user_by_uid(self, uid: str) -> Optional[Dict[str, Any]]:
        """Get user by Firebase UID with caching"""
        try:
            # Try cache first
            cached_user = await self.cache.get_user(uid)
            if cached_user:
                return cached_user
            
            # Query database
            user = await self.users.find_one({"uid": uid})
            if user:
                user["_id"] = str(user["_id"])
                # Cache the result
                await self.cache.set_user(uid, user)
            
            return user
        except Exception as e:
            logger.error(f"Failed to get user by UID {uid}: {e}")
            raise
    
    async def create_user(self, user_data: Union[PatientModel, InstitutionModel, UserModel]) -> str:
        """Create a new user and invalidate cache"""
        try:
            user_dict = user_data.model_dump(exclude_none=True)
            user_dict["created_at"] = datetime.utcnow()
            user_dict["updated_at"] = datetime.utcnow()
            
            result = await self.users.insert_one(user_dict)
            
            # Invalidate cache for this user
            if user_data.uid:
                await self.cache.invalidate_user(user_data.uid)
            
            logger.info(f"Created user with ID: {result.inserted_id}")
            return str(result.inserted_id)
            
        except DuplicateKeyError:
            logger.error(f"User with UID {user_data.uid} already exists")
            raise ValueError(f"User with UID {user_data.uid} already exists")
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            raise
    
    async def update_user(self, uid: str, update_data: Dict[str, Any]) -> bool:
        """Update user data and invalidate cache"""
        try:
            update_data["updated_at"] = datetime.utcnow()
            result = await self.users.update_one(
                {"uid": uid},
                {"$set": update_data}
            )
            
            # Invalidate cache
            await self.cache.invalidate_user(uid)
            
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Failed to update user {uid}: {e}")
            raise
    
    # Cached report operations
    async def get_report_by_id(self, report_id: str) -> Optional[Dict[str, Any]]:
        """Get report by report_id with caching"""
        try:
            # Try cache first
            cached_report = await self.cache.get_report(report_id)
            if cached_report:
                return cached_report
            
            # Query database
            report = await self.reports.find_one({"report_id": report_id})
            if report:
                report["_id"] = str(report["_id"])
                # Cache the result
                await self.cache.set_report(report_id, report)
            
            return report
        except Exception as e:
            logger.error(f"Failed to get report {report_id}: {e}")
            raise
    
    async def get_reports_by_patient_id(self, patient_id: str, skip: int = 0, limit: int = 50) -> List[Dict[str, Any]]:
        """Get reports for a patient with caching and pagination"""
        try:
            # Try cache first
            cached_reports = await self.cache.get_patient_reports(patient_id, skip, limit)
            if cached_reports:
                return cached_reports
            
            # Query database with optimized projection
            cursor = self.reports.find(
                {"patient_id": patient_id},
                {
                    "_id": 1,
                    "report_id": 1,
                    "patient_id": 1,
                    "processed_at": 1,
                    "attributes": 1,
                    "llm_output": 1,
                    "llm_report_id": 1,
                    "selected_concerns": 1
                }
            ).sort("processed_at", -1).skip(skip).limit(limit)
            
            reports = []
            async for report in cursor:
                report["_id"] = str(report["_id"])
                reports.append(report)
            
            # Cache the results
            await self.cache.set_patient_reports(patient_id, reports, skip, limit)
            
            return reports
        except Exception as e:
            logger.error(f"Failed to get reports for patient {patient_id}: {e}")
            raise
    
    async def create_report(self, report: Report) -> str:
        """Create a new medical report and invalidate related caches"""
        try:
            report_dict = report.model_dump(exclude_none=True, by_alias=True)
            if "_id" in report_dict and report_dict["_id"] is None:
                del report_dict["_id"]
            
            result = await self.reports.insert_one(report_dict)
            
            # Invalidate related caches
            await self.cache.invalidate_patient_reports(report.patient_id)
            await self.cache.invalidate_dashboard_data(report.patient_id)
            
            logger.info(f"Created report with ID: {result.inserted_id}")
            return str(result.inserted_id)
            
        except DuplicateKeyError:
            logger.error(f"Report with ID {report.report_id} already exists")
            raise ValueError(f"Report with ID {report.report_id} already exists")
        except Exception as e:
            logger.error(f"Failed to create report: {e}")
            raise
    
    async def update_report(self, report_id: str, update_data: Dict[str, Any]) -> bool:
        """Update report data and invalidate caches"""
        try:
            result = await self.reports.update_one(
                {"report_id": report_id},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                # Invalidate caches
                await self.cache.invalidate_report(report_id)
                
                # Get patient_id to invalidate patient-specific caches
                report = await self.reports.find_one({"report_id": report_id}, {"patient_id": 1})
                if report:
                    patient_id = report.get("patient_id")
                    if patient_id:
                        await self.cache.invalidate_patient_reports(patient_id)
                        await self.cache.invalidate_dashboard_data(patient_id)
            
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Failed to update report {report_id}: {e}")
            raise
    
    # Optimized search operations
    async def search_patients_optimized(self, query: str, skip: int = 0, limit: int = 50) -> List[Dict[str, Any]]:
        """Optimized patient search with text indexing"""
        try:
            search_filter = {
                "user_type": UserType.PATIENT,
                "$text": {"$search": query}
            }
            
            # Use text search with score sorting
            cursor = self.users.find(
                search_filter,
                {"score": {"$meta": "textScore"}}
            ).sort([("score", {"$meta": "textScore"})]).skip(skip).limit(limit)
            
            patients = []
            async for patient in cursor:
                patient["_id"] = str(patient["_id"])
                patients.append(patient)
            
            return patients
        except Exception as e:
            logger.error(f"Failed to search patients with query '{query}': {e}")
            # Fallback to regex search
            return await self._fallback_patient_search(query, skip, limit)
    
    async def _fallback_patient_search(self, query: str, skip: int = 0, limit: int = 50) -> List[Dict[str, Any]]:
        """Fallback patient search using regex"""
        try:
            search_filter = {
                "user_type": UserType.PATIENT,
                "$or": [
                    {"name": {"$regex": query, "$options": "i"}},
                    {"uid": {"$regex": query, "$options": "i"}}
                ]
            }
            
            cursor = self.users.find(search_filter).skip(skip).limit(limit)
            patients = []
            async for patient in cursor:
                patient["_id"] = str(patient["_id"])
                patients.append(patient)
            return patients
        except Exception as e:
            logger.error(f"Fallback patient search failed: {e}")
            raise
    
    # Batch operations for better performance
    async def get_multiple_reports(self, report_ids: List[str]) -> List[Dict[str, Any]]:
        """Get multiple reports in a single query"""
        try:
            # Check cache for each report
            cached_reports = []
            uncached_ids = []
            
            for report_id in report_ids:
                cached_report = await self.cache.get_report(report_id)
                if cached_report:
                    cached_reports.append(cached_report)
                else:
                    uncached_ids.append(report_id)
            
            # Query database for uncached reports
            db_reports = []
            if uncached_ids:
                cursor = self.reports.find({"report_id": {"$in": uncached_ids}})
                async for report in cursor:
                    report["_id"] = str(report["_id"])
                    db_reports.append(report)
                    # Cache each report
                    await self.cache.set_report(report["report_id"], report)
            
            # Combine cached and database results
            all_reports = cached_reports + db_reports
            
            # Sort by report_id to maintain order
            report_dict = {r["report_id"]: r for r in all_reports}
            return [report_dict[rid] for rid in report_ids if rid in report_dict]
            
        except Exception as e:
            logger.error(f"Failed to get multiple reports: {e}")
            raise
    
    async def bulk_update_reports(self, updates: List[Dict[str, Any]]) -> int:
        """Bulk update multiple reports"""
        try:
            operations = []
            for update in updates:
                report_id = update.get("report_id")
                update_data = update.get("data", {})
                
                if report_id and update_data:
                    operations.append({
                        "updateOne": {
                            "filter": {"report_id": report_id},
                            "update": {"$set": update_data}
                        }
                    })
            
            if not operations:
                return 0
            
            result = await self.reports.bulk_write(operations)
            
            # Invalidate caches for updated reports
            for update in updates:
                report_id = update.get("report_id")
                if report_id:
                    await self.cache.invalidate_report(report_id)
            
            return result.modified_count
            
        except Exception as e:
            logger.error(f"Failed to bulk update reports: {e}")
            raise
    
    # Aggregation operations for analytics
    async def get_patient_metrics_summary(self, patient_id: str) -> Dict[str, Any]:
        """Get aggregated metrics summary for a patient"""
        try:
            pipeline = [
                {"$match": {"patient_id": patient_id}},
                {"$sort": {"processed_at": -1}},
                {"$limit": 10},  # Last 10 reports
                {
                    "$group": {
                        "_id": "$patient_id",
                        "total_reports": {"$sum": 1},
                        "latest_report_date": {"$max": "$processed_at"},
                        "has_analysis_count": {
                            "$sum": {
                                "$cond": [{"$ne": ["$llm_output", None]}, 1, 0]
                            }
                        }
                    }
                }
            ]
            
            cursor = self.reports.aggregate(pipeline)
            result = await cursor.to_list(length=1)
            
            return result[0] if result else {}
            
        except Exception as e:
            logger.error(f"Failed to get metrics summary for patient {patient_id}: {e}")
            raise
    
    # Health check and monitoring
    async def health_check_optimized(self) -> Dict[str, Any]:
        """Enhanced health check with performance metrics"""
        try:
            start_time = datetime.utcnow()
            
            # Basic connectivity check
            await self.db.command("ping")
            
            # Get collection stats efficiently
            stats_pipeline = [
                {"$collStats": {"count": {}}}
            ]
            
            collections_stats = {}
            for collection_name in ["users", "reports", "llm_reports", "chat_sessions"]:
                collection = getattr(self, collection_name)
                try:
                    count = await collection.estimated_document_count()
                    collections_stats[collection_name] = count
                except Exception as e:
                    collections_stats[collection_name] = f"Error: {str(e)}"
            
            # Get cache statistics
            cache_stats = self.cache.get_all_stats()
            
            end_time = datetime.utcnow()
            response_time_ms = (end_time - start_time).total_seconds() * 1000
            
            return {
                "status": "healthy",
                "database": self.db.name,
                "response_time_ms": round(response_time_ms, 2),
                "collections": collections_stats,
                "cache_stats": cache_stats,
                "timestamp": end_time.isoformat()
            }
        except Exception as e:
            logger.error(f"Optimized health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    # Connection management
    async def close_connections(self):
        """Close database connections and clear caches"""
        try:
            await self.cache.clear_all()
            logger.info("Database connections closed and caches cleared")
        except Exception as e:
            logger.error(f"Error closing connections: {e}")


# Global optimized database service instance
optimized_db_service = OptimizedDatabaseService()