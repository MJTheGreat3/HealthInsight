"""
Search and filtering service for patients and reports
"""

from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
from enum import Enum
import logging
import re

from app.services.database import db_service
from app.models.user import UserType, PatientModel, InstitutionModel
from app.models.report import MetricData

logger = logging.getLogger(__name__)


class SearchType(str, Enum):
    """Search type enumeration"""
    PATIENTS = "patients"
    REPORTS = "reports"
    METRICS = "metrics"


class SortOrder(str, Enum):
    """Sort order enumeration"""
    ASC = "asc"
    DESC = "desc"


class SearchFilters:
    """Search filters for advanced search functionality"""
    
    def __init__(
        self,
        query: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        metric_names: Optional[List[str]] = None,
        verdict_types: Optional[List[str]] = None,
        has_analysis: Optional[bool] = None,
        sort_by: str = "processed_at",
        sort_order: SortOrder = SortOrder.DESC,
        skip: int = 0,
        limit: int = 50
    ):
        self.query = query
        self.date_from = date_from
        self.date_to = date_to
        self.metric_names = metric_names or []
        self.verdict_types = verdict_types or []
        self.has_analysis = has_analysis
        self.sort_by = sort_by
        self.sort_order = sort_order
        self.skip = skip
        self.limit = limit


class SearchResult:
    """Search result container"""
    
    def __init__(
        self,
        items: List[Dict[str, Any]],
        total: int,
        search_type: SearchType,
        filters_applied: Dict[str, Any],
        execution_time_ms: float
    ):
        self.items = items
        self.total = total
        self.search_type = search_type
        self.filters_applied = filters_applied
        self.execution_time_ms = execution_time_ms


class SearchService:
    """Advanced search and filtering service"""
    
    def __init__(self):
        self.db_service = db_service
    
    async def search_patients(
        self,
        query: str,
        requesting_user: Union[PatientModel, InstitutionModel],
        filters: Optional[SearchFilters] = None
    ) -> SearchResult:
        """
        Search patients with advanced filtering (for hospitals only)
        
        Args:
            query: Search query string
            requesting_user: User making the search request
            filters: Additional search filters
            
        Returns:
            SearchResult with matching patients
            
        Raises:
            ValueError: If patient user tries to search patients
            Exception: If search fails
        """
        start_time = datetime.utcnow()
        
        try:
            # Only institutions can search patients
            if not isinstance(requesting_user, InstitutionModel):
                raise ValueError("Only hospital users can search patients")
            
            # Initialize database if needed
            if not self.db_service.db:
                await self.db_service.initialize()
            
            # Build search filter
            search_filter = self._build_patient_search_filter(query, filters)
            
            # Execute search with pagination
            cursor = self.db_service.users.find(search_filter)
            
            # Apply sorting
            if filters:
                sort_direction = 1 if filters.sort_order == SortOrder.ASC else -1
                cursor = cursor.sort(filters.sort_by, sort_direction)
                cursor = cursor.skip(filters.skip).limit(filters.limit)
            
            # Get results
            patients = []
            async for patient in cursor:
                patient["_id"] = str(patient["_id"])
                patients.append(patient)
            
            # Get total count
            total = await self.db_service.users.count_documents(search_filter)
            
            # Calculate execution time
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # Build filters applied summary
            filters_applied = {
                "query": query,
                "total_filters": self._count_active_filters(filters)
            }
            
            if filters:
                filters_applied.update({
                    "date_range": bool(filters.date_from or filters.date_to),
                    "sort_by": filters.sort_by,
                    "sort_order": filters.sort_order.value
                })
            
            logger.info(f"Patient search completed: {len(patients)} results in {execution_time:.2f}ms")
            
            return SearchResult(
                items=patients,
                total=total,
                search_type=SearchType.PATIENTS,
                filters_applied=filters_applied,
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            logger.error(f"Patient search failed: {str(e)}")
            raise
    
    async def search_reports(
        self,
        patient_id: str,
        query: Optional[str] = None,
        requesting_user: Union[PatientModel, InstitutionModel] = None,
        filters: Optional[SearchFilters] = None
    ) -> SearchResult:
        """
        Search reports with advanced filtering
        
        Args:
            patient_id: Patient ID to search reports for
            query: Search query string
            requesting_user: User making the search request
            filters: Additional search filters
            
        Returns:
            SearchResult with matching reports
            
        Raises:
            ValueError: If access denied
            Exception: If search fails
        """
        start_time = datetime.utcnow()
        
        try:
            # Initialize database if needed
            if not self.db_service.db:
                await self.db_service.initialize()
            
            # Verify access permissions
            if requesting_user:
                await self._verify_report_access(patient_id, requesting_user)
            
            # Build search filter
            search_filter = self._build_report_search_filter(patient_id, query, filters)
            
            # Execute search with pagination
            cursor = self.db_service.reports.find(search_filter)
            
            # Apply sorting
            if filters:
                sort_direction = 1 if filters.sort_order == SortOrder.ASC else -1
                cursor = cursor.sort(filters.sort_by, sort_direction)
                cursor = cursor.skip(filters.skip).limit(filters.limit)
            else:
                cursor = cursor.sort("processed_at", -1)
            
            # Get results
            reports = []
            async for report in cursor:
                report["_id"] = str(report["_id"])
                reports.append(report)
            
            # Get total count
            total = await self.db_service.reports.count_documents(search_filter)
            
            # Calculate execution time
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # Build filters applied summary
            filters_applied = {
                "patient_id": patient_id,
                "query": query,
                "total_filters": self._count_active_filters(filters)
            }
            
            if filters:
                filters_applied.update({
                    "date_range": bool(filters.date_from or filters.date_to),
                    "metric_filters": len(filters.metric_names),
                    "verdict_filters": len(filters.verdict_types),
                    "has_analysis_filter": filters.has_analysis is not None,
                    "sort_by": filters.sort_by,
                    "sort_order": filters.sort_order.value
                })
            
            logger.info(f"Report search completed: {len(reports)} results in {execution_time:.2f}ms")
            
            return SearchResult(
                items=reports,
                total=total,
                search_type=SearchType.REPORTS,
                filters_applied=filters_applied,
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            logger.error(f"Report search failed: {str(e)}")
            raise
    
    async def search_metrics(
        self,
        patient_id: str,
        metric_names: List[str],
        requesting_user: Union[PatientModel, InstitutionModel],
        filters: Optional[SearchFilters] = None
    ) -> SearchResult:
        """
        Search for specific metrics across multiple reports
        
        Args:
            patient_id: Patient ID to search metrics for
            metric_names: List of metric names to search for
            requesting_user: User making the search request
            filters: Additional search filters
            
        Returns:
            SearchResult with matching metric data
            
        Raises:
            ValueError: If access denied
            Exception: If search fails
        """
        start_time = datetime.utcnow()
        
        try:
            # Initialize database if needed
            if not self.db_service.db:
                await self.db_service.initialize()
            
            # Verify access permissions
            await self._verify_report_access(patient_id, requesting_user)
            
            # Build search filter for reports containing the metrics
            search_filter = {
                "patient_id": patient_id,
                "$or": [
                    {f"attributes.{metric_name}": {"$exists": True}}
                    for metric_name in metric_names
                ]
            }
            
            # Add date filters if provided
            if filters and (filters.date_from or filters.date_to):
                date_filter = {}
                if filters.date_from:
                    date_filter["$gte"] = filters.date_from
                if filters.date_to:
                    date_filter["$lte"] = filters.date_to
                search_filter["processed_at"] = date_filter
            
            # Execute search
            cursor = self.db_service.reports.find(search_filter)
            
            # Apply sorting and pagination
            if filters:
                sort_direction = 1 if filters.sort_order == SortOrder.ASC else -1
                cursor = cursor.sort(filters.sort_by, sort_direction)
                cursor = cursor.skip(filters.skip).limit(filters.limit)
            else:
                cursor = cursor.sort("processed_at", -1)
            
            # Process results to extract metric data
            metric_results = []
            async for report in cursor:
                report["_id"] = str(report["_id"])
                
                # Extract requested metrics from this report
                report_metrics = {}
                attributes = report.get("attributes", {})
                
                for metric_name in metric_names:
                    if metric_name in attributes:
                        report_metrics[metric_name] = attributes[metric_name]
                
                if report_metrics:
                    metric_results.append({
                        "report_id": report["report_id"],
                        "processed_at": report["processed_at"],
                        "metrics": report_metrics,
                        "has_analysis": bool(report.get("llm_output"))
                    })
            
            # Get total count
            total = await self.db_service.reports.count_documents(search_filter)
            
            # Calculate execution time
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # Build filters applied summary
            filters_applied = {
                "patient_id": patient_id,
                "metric_names": metric_names,
                "total_filters": self._count_active_filters(filters)
            }
            
            if filters:
                filters_applied.update({
                    "date_range": bool(filters.date_from or filters.date_to),
                    "sort_by": filters.sort_by,
                    "sort_order": filters.sort_order.value
                })
            
            logger.info(f"Metric search completed: {len(metric_results)} results in {execution_time:.2f}ms")
            
            return SearchResult(
                items=metric_results,
                total=total,
                search_type=SearchType.METRICS,
                filters_applied=filters_applied,
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            logger.error(f"Metric search failed: {str(e)}")
            raise
    
    def _build_patient_search_filter(
        self,
        query: str,
        filters: Optional[SearchFilters] = None
    ) -> Dict[str, Any]:
        """Build MongoDB filter for patient search"""
        search_filter = {
            "user_type": UserType.PATIENT
        }
        
        # Add text search
        if query and query.strip():
            query = query.strip()
            search_filter["$or"] = [
                {"name": {"$regex": re.escape(query), "$options": "i"}},
                {"uid": {"$regex": re.escape(query), "$options": "i"}},
                {"bio_data.allergies": {"$regex": re.escape(query), "$options": "i"}}
            ]
        
        # Add date filters if provided
        if filters and (filters.date_from or filters.date_to):
            date_filter = {}
            if filters.date_from:
                date_filter["$gte"] = filters.date_from
            if filters.date_to:
                date_filter["$lte"] = filters.date_to
            search_filter["created_at"] = date_filter
        
        return search_filter
    
    def _build_report_search_filter(
        self,
        patient_id: str,
        query: Optional[str] = None,
        filters: Optional[SearchFilters] = None
    ) -> Dict[str, Any]:
        """Build MongoDB filter for report search"""
        search_filter = {
            "patient_id": patient_id
        }
        
        # Add text search
        if query and query.strip():
            query = query.strip()
            search_filter["$or"] = [
                {"report_id": {"$regex": re.escape(query), "$options": "i"}},
                {"llm_output": {"$regex": re.escape(query), "$options": "i"}}
            ]
        
        if not filters:
            return search_filter
        
        # Add date filters
        if filters.date_from or filters.date_to:
            date_filter = {}
            if filters.date_from:
                date_filter["$gte"] = filters.date_from
            if filters.date_to:
                date_filter["$lte"] = filters.date_to
            search_filter["processed_at"] = date_filter
        
        # Add metric name filters
        if filters.metric_names:
            metric_conditions = []
            for metric_name in filters.metric_names:
                metric_conditions.append({f"attributes.{metric_name}": {"$exists": True}})
            
            if metric_conditions:
                if "$or" in search_filter:
                    # Combine with existing OR conditions
                    search_filter = {
                        "$and": [
                            search_filter,
                            {"$or": metric_conditions}
                        ]
                    }
                else:
                    search_filter["$or"] = metric_conditions
        
        # Add verdict type filters
        if filters.verdict_types:
            verdict_conditions = []
            for verdict in filters.verdict_types:
                verdict_conditions.append({
                    "attributes": {
                        "$elemMatch": {
                            "verdict": {"$regex": re.escape(verdict), "$options": "i"}
                        }
                    }
                })
            
            if verdict_conditions:
                if "$and" in search_filter:
                    search_filter["$and"].append({"$or": verdict_conditions})
                else:
                    search_filter["$and"] = [search_filter, {"$or": verdict_conditions}]
        
        # Add analysis filter
        if filters.has_analysis is not None:
            if filters.has_analysis:
                search_filter["llm_output"] = {"$exists": True, "$ne": None, "$ne": ""}
            else:
                search_filter["$or"] = [
                    {"llm_output": {"$exists": False}},
                    {"llm_output": None},
                    {"llm_output": ""}
                ]
        
        return search_filter
    
    async def _verify_report_access(
        self,
        patient_id: str,
        requesting_user: Union[PatientModel, InstitutionModel]
    ):
        """Verify user has access to patient's reports"""
        if isinstance(requesting_user, PatientModel):
            # Patients can only access their own reports
            if patient_id != requesting_user.uid:
                raise ValueError("Access denied. You can only search your own reports.")
        elif isinstance(requesting_user, InstitutionModel):
            # Institutions can access reports of their patients
            if patient_id not in requesting_user.patient_list:
                raise ValueError("Access denied. Patient is not in your institution's patient list.")
        else:
            raise ValueError("Invalid user type for report access")
    
    def _count_active_filters(self, filters: Optional[SearchFilters]) -> int:
        """Count number of active filters"""
        if not filters:
            return 0
        
        count = 0
        if filters.query:
            count += 1
        if filters.date_from or filters.date_to:
            count += 1
        if filters.metric_names:
            count += 1
        if filters.verdict_types:
            count += 1
        if filters.has_analysis is not None:
            count += 1
        
        return count


# Global search service instance
search_service = SearchService()