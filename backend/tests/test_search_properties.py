"""
Property-based tests for search and filtering functionality
"""

import pytest
from hypothesis import given, strategies as st, assume, settings, HealthCheck
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
from typing import Dict, Any, List

from app.services.search import search_service, SearchFilters, SortOrder, SearchType
from app.models.user import UserType, PatientModel, InstitutionModel
from app.models.report import MetricData


# Test data strategies
@st.composite
def patient_data(draw):
    """Generate patient data for testing"""
    uid = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
    name = draw(st.text(min_size=1, max_size=100, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs'))))
    
    return {
        "_id": f"patient_{uid}",
        "uid": uid,
        "user_type": UserType.PATIENT.value,
        "name": name,
        "favorites": draw(st.lists(st.text(min_size=1, max_size=20), max_size=5)),
        "bio_data": {
            "height": draw(st.integers(min_value=100, max_value=250)),
            "weight": draw(st.integers(min_value=30, max_value=200)),
            "allergies": draw(st.lists(st.text(min_size=1, max_size=20), max_size=3))
        },
        "reports": draw(st.lists(st.text(min_size=1, max_size=20), max_size=10)),
        "created_at": draw(st.datetimes(min_value=datetime(2020, 1, 1), max_value=datetime(2024, 12, 31)))
    }


@st.composite
def institution_data(draw):
    """Generate institution data for testing"""
    uid = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
    name = draw(st.text(min_size=1, max_size=100, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs'))))
    
    return {
        "_id": f"institution_{uid}",
        "uid": uid,
        "user_type": UserType.INSTITUTION.value,
        "name": name,
        "patient_list": draw(st.lists(st.text(min_size=1, max_size=20), max_size=20))
    }


@st.composite
def metric_data(draw):
    """Generate metric data for testing"""
    name = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs'))))
    value = draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Nd', 'Po'))))
    verdict = draw(st.sampled_from(["NORMAL", "HIGH", "LOW", "CRITICAL"]))
    
    return {
        "name": name,
        "value": value,
        "remark": draw(st.one_of(st.none(), st.text(max_size=100))),
        "range": draw(st.one_of(st.none(), st.text(max_size=20))),
        "unit": draw(st.one_of(st.none(), st.text(max_size=10))),
        "verdict": verdict
    }


@st.composite
def report_data(draw):
    """Generate report data for testing"""
    report_id = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
    patient_id = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
    
    # Generate attributes (metrics)
    num_attributes = draw(st.integers(min_value=1, max_value=10))
    attributes = {}
    for i in range(num_attributes):
        metric_key = f"METRIC_{i}"
        attributes[metric_key] = draw(metric_data())
    
    return {
        "_id": f"report_{report_id}",
        "report_id": report_id,
        "patient_id": patient_id,
        "processed_at": draw(st.datetimes(min_value=datetime(2020, 1, 1), max_value=datetime(2024, 12, 31))),
        "attributes": attributes,
        "llm_output": draw(st.one_of(st.none(), st.text(min_size=10, max_size=500))),
        "llm_report_id": draw(st.one_of(st.none(), st.text(min_size=1, max_size=50))),
        "selected_concerns": draw(st.one_of(st.none(), st.lists(st.text(min_size=1, max_size=20), max_size=5)))
    }


@st.composite
def search_filters_data(draw):
    """Generate search filters for testing"""
    return SearchFilters(
        query=draw(st.one_of(st.none(), st.text(min_size=1, max_size=50))),
        date_from=draw(st.one_of(st.none(), st.datetimes(min_value=datetime(2020, 1, 1), max_value=datetime(2023, 12, 31)))),
        date_to=draw(st.one_of(st.none(), st.datetimes(min_value=datetime(2023, 1, 1), max_value=datetime(2024, 12, 31)))),
        metric_names=draw(st.one_of(st.none(), st.lists(st.text(min_size=1, max_size=20), max_size=5))),
        verdict_types=draw(st.one_of(st.none(), st.lists(st.sampled_from(["NORMAL", "HIGH", "LOW", "CRITICAL"]), max_size=4))),
        has_analysis=draw(st.one_of(st.none(), st.booleans())),
        sort_by=draw(st.sampled_from(["processed_at", "report_id", "name", "created_at"])),
        sort_order=draw(st.sampled_from([SortOrder.ASC, SortOrder.DESC])),
        skip=draw(st.integers(min_value=0, max_value=100)),
        limit=draw(st.integers(min_value=1, max_value=100))
    )


def create_mock_search_service():
    """Create SearchService instance with mocked dependencies"""
    with patch('app.services.search.db_service') as mock_db_service:
        # Mock database service
        mock_db_instance = AsyncMock()
        mock_db_service.return_value = mock_db_instance
        
        # Mock collections
        mock_db_instance.db = MagicMock()
        mock_db_instance.users = MagicMock()
        mock_db_instance.reports = MagicMock()
        mock_db_instance.initialize = AsyncMock()
        
        service = search_service
        service.db_service = mock_db_instance
        return service


class TestSearchProperties:
    """Property-based tests for search and filter functionality"""
    
    @given(st.text(min_size=1, max_size=100), st.lists(patient_data(), min_size=0, max_size=20))
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_search_and_filter_functionality_property(self, search_query, patient_list):
        """
        Property 6: Search and Filter Functionality
        For any search query on patient data or reports, the system should return 
        correctly filtered results based on the search criteria
        **Feature: health-insight-core, Property 6: Search and Filter Functionality**
        **Validates: Requirements 5.4, 9.2**
        """
        # Arrange
        search_svc = create_mock_search_service()
        
        # Create mock institution user
        institution_user = InstitutionModel(
            uid="test_institution",
            user_type=UserType.INSTITUTION,
            name="Test Hospital",
            patient_list=[p["uid"] for p in patient_list]
        )
        
        # Mock database responses
        def mock_find_patients(*args, **kwargs):
            """Mock patient search results"""
            search_filter = args[0] if args else {}
            
            # Filter patients based on search criteria
            filtered_patients = []
            for patient in patient_list:
                # Check if patient matches search query
                if search_query.lower() in patient["name"].lower() or search_query.lower() in patient["uid"].lower():
                    filtered_patients.append(patient)
            
            # Create mock cursor that properly handles async iteration and method chaining
            class MockCursor:
                def __init__(self, data):
                    self.data = data
                    
                def __aiter__(self):
                    return self
                    
                async def __anext__(self):
                    if not hasattr(self, '_iter'):
                        self._iter = iter(self.data)
                    try:
                        return next(self._iter)
                    except StopIteration:
                        raise StopAsyncIteration
                
                def sort(self, *args, **kwargs):
                    return self
                    
                def skip(self, *args, **kwargs):
                    return self
                    
                def limit(self, *args, **kwargs):
                    return self
            
            return MockCursor(filtered_patients)
        
        search_svc.db_service.users.find = mock_find_patients
        search_svc.db_service.users.count_documents = AsyncMock(return_value=len([
            p for p in patient_list 
            if search_query.lower() in p["name"].lower() or search_query.lower() in p["uid"].lower()
        ]))
        
        # Act
        result = await search_svc.search_patients(
            query=search_query,
            requesting_user=institution_user,
            filters=None
        )
        
        # Assert - Search should return correctly filtered results
        assert result is not None
        assert result.search_type == SearchType.PATIENTS
        assert isinstance(result.items, list)
        assert isinstance(result.total, int)
        assert result.total >= 0
        assert len(result.items) <= result.total
        
        # Assert - All returned items should match search criteria
        for item in result.items:
            assert search_query.lower() in item["name"].lower() or search_query.lower() in item["uid"].lower()
        
        # Assert - Execution time should be recorded
        assert result.execution_time_ms >= 0
        
        # Assert - Filters applied should be recorded
        assert "query" in result.filters_applied
        assert result.filters_applied["query"] == search_query
    
    @given(st.text(min_size=1, max_size=50), st.lists(report_data(), min_size=0, max_size=20), search_filters_data())
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_report_search_with_filters_property(self, patient_id, report_list, filters):
        """
        Property: Report Search Filtering
        For any patient ID and search filters, the system should return reports 
        that match all specified criteria
        **Feature: health-insight-core, Property 6: Search and Filter Functionality**
        **Validates: Requirements 5.4, 9.2**
        """
        # Arrange
        search_svc = create_mock_search_service()
        
        # Ensure reports belong to the patient
        for report in report_list:
            report["patient_id"] = patient_id
        
        # Create mock patient user
        patient_user = PatientModel(
            uid=patient_id,
            user_type=UserType.PATIENT,
            name="Test Patient"
        )
        
        # Mock database responses
        def mock_find_reports(*args, **kwargs):
            """Mock report search results"""
            search_filter = args[0] if args else {}
            
            # Filter reports based on search criteria
            filtered_reports = []
            for report in report_list:
                matches = True
                
                # Check patient ID match
                if report["patient_id"] != patient_id:
                    matches = False
                
                # Check text query match
                if filters.query and matches:
                    query_lower = filters.query.lower()
                    if (query_lower not in report["report_id"].lower() and 
                        (not report.get("llm_output") or query_lower not in report["llm_output"].lower())):
                        matches = False
                
                # Check date filters
                if matches and (filters.date_from or filters.date_to):
                    report_date = report["processed_at"]
                    if filters.date_from and report_date < filters.date_from:
                        matches = False
                    if filters.date_to and report_date > filters.date_to:
                        matches = False
                
                # Check analysis filter
                if matches and filters.has_analysis is not None:
                    has_analysis = bool(report.get("llm_output"))
                    if has_analysis != filters.has_analysis:
                        matches = False
                
                if matches:
                    filtered_reports.append(report)
            
            # Create mock cursor that properly handles async iteration and method chaining
            class MockCursor:
                def __init__(self, data):
                    self.data = data
                    
                def __aiter__(self):
                    return self
                    
                async def __anext__(self):
                    if not hasattr(self, '_iter'):
                        self._iter = iter(self.data)
                    try:
                        return next(self._iter)
                    except StopIteration:
                        raise StopAsyncIteration
                
                def sort(self, *args, **kwargs):
                    return self
                    
                def skip(self, *args, **kwargs):
                    return self
                    
                def limit(self, *args, **kwargs):
                    return self
            
            return MockCursor(filtered_reports)
        
        search_svc.db_service.reports.find = mock_find_reports
        search_svc.db_service.reports.count_documents = AsyncMock(return_value=len(report_list))
        
        # Act
        result = await search_svc.search_reports(
            patient_id=patient_id,
            query=filters.query,
            requesting_user=patient_user,
            filters=filters
        )
        
        # Assert - Search should return correctly filtered results
        assert result is not None
        assert result.search_type == SearchType.REPORTS
        assert isinstance(result.items, list)
        assert isinstance(result.total, int)
        assert result.total >= 0
        
        # Assert - All returned items should belong to the patient
        for item in result.items:
            assert item["patient_id"] == patient_id
        
        # Assert - If query specified, all items should match
        if filters.query:
            for item in result.items:
                query_lower = filters.query.lower()
                assert (query_lower in item["report_id"].lower() or 
                       (item.get("llm_output") and query_lower in item["llm_output"].lower()))
        
        # Assert - If analysis filter specified, all items should match
        if filters.has_analysis is not None:
            for item in result.items:
                has_analysis = bool(item.get("llm_output"))
                assert has_analysis == filters.has_analysis
        
        # Assert - Filters applied should be recorded
        assert "patient_id" in result.filters_applied
        assert result.filters_applied["patient_id"] == patient_id
    
    @given(st.text(min_size=1, max_size=50), st.lists(st.text(min_size=1, max_size=20), min_size=1, max_size=5), st.lists(report_data(), min_size=0, max_size=15))
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_metric_search_property(self, patient_id, metric_names, report_list):
        """
        Property: Metric Search Accuracy
        For any patient ID and list of metric names, the system should return 
        only reports containing those specific metrics
        **Feature: health-insight-core, Property 6: Search and Filter Functionality**
        **Validates: Requirements 5.4, 9.2**
        """
        # Arrange
        search_svc = create_mock_search_service()
        
        # Ensure reports belong to the patient and add some metrics
        for report in report_list:
            report["patient_id"] = patient_id
            # Add some of the requested metrics to some reports
            for i, metric_name in enumerate(metric_names[:3]):  # Add up to 3 metrics
                if i < len(report["attributes"]):
                    report["attributes"][metric_name] = {
                        "name": metric_name,
                        "value": "test_value",
                        "verdict": "NORMAL"
                    }
        
        # Create mock patient user
        patient_user = PatientModel(
            uid=patient_id,
            user_type=UserType.PATIENT,
            name="Test Patient"
        )
        
        # Mock database responses
        def mock_find_reports(*args, **kwargs):
            """Mock report search results for metrics"""
            search_filter = args[0] if args else {}
            
            # Filter reports that contain any of the requested metrics
            filtered_reports = []
            for report in report_list:
                if report["patient_id"] != patient_id:
                    continue
                
                # Check if report contains any of the requested metrics
                has_metric = False
                for metric_name in metric_names:
                    if metric_name in report["attributes"]:
                        has_metric = True
                        break
                
                if has_metric:
                    filtered_reports.append(report)
            
            # Create mock cursor that properly handles async iteration and method chaining
            class MockCursor:
                def __init__(self, data):
                    self.data = data
                    
                def __aiter__(self):
                    return self
                    
                async def __anext__(self):
                    if not hasattr(self, '_iter'):
                        self._iter = iter(self.data)
                    try:
                        return next(self._iter)
                    except StopIteration:
                        raise StopAsyncIteration
                
                def sort(self, *args, **kwargs):
                    return self
                    
                def skip(self, *args, **kwargs):
                    return self
                    
                def limit(self, *args, **kwargs):
                    return self
            
            return MockCursor(filtered_reports)
        
        search_svc.db_service.reports.find = mock_find_reports
        search_svc.db_service.reports.count_documents = AsyncMock(return_value=len(report_list))
        
        # Act
        result = await search_svc.search_metrics(
            patient_id=patient_id,
            metric_names=metric_names,
            requesting_user=patient_user,
            filters=None
        )
        
        # Assert - Search should return correctly filtered results
        assert result is not None
        assert result.search_type == SearchType.METRICS
        assert isinstance(result.items, list)
        assert isinstance(result.total, int)
        assert result.total >= 0
        
        # Assert - All returned items should contain requested metrics
        for item in result.items:
            assert "metrics" in item
            assert isinstance(item["metrics"], dict)
            
            # At least one requested metric should be present
            has_requested_metric = False
            for metric_name in metric_names:
                if metric_name in item["metrics"]:
                    has_requested_metric = True
                    break
            assert has_requested_metric
        
        # Assert - Filters applied should be recorded
        assert "patient_id" in result.filters_applied
        assert "metric_names" in result.filters_applied
        assert result.filters_applied["patient_id"] == patient_id
        assert result.filters_applied["metric_names"] == metric_names
    
    @given(st.lists(patient_data(), min_size=0, max_size=10))
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_patient_access_control_property(self, patient_list):
        """
        Property: Patient Search Access Control
        For any patient user, attempting to search other patients should be denied
        **Feature: health-insight-core, Property 6: Search and Filter Functionality**
        **Validates: Requirements 5.4, 9.2**
        """
        # Arrange
        search_svc = create_mock_search_service()
        
        # Create mock patient user (not institution)
        patient_user = PatientModel(
            uid="test_patient",
            user_type=UserType.PATIENT,
            name="Test Patient"
        )
        
        # Act & Assert - Patient users should not be able to search patients
        with pytest.raises(ValueError) as exc_info:
            await search_svc.search_patients(
                query="test",
                requesting_user=patient_user,
                filters=None
            )
        
        assert "Only hospital users can search patients" in str(exc_info.value)
    
    @given(st.text(min_size=1, max_size=50), st.text(min_size=1, max_size=50))
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_report_access_control_property(self, patient_id, other_patient_id):
        """
        Property: Report Search Access Control
        For any patient user, attempting to search another patient's reports should be denied
        **Feature: health-insight-core, Property 6: Search and Filter Functionality**
        **Validates: Requirements 5.4, 9.2**
        """
        assume(patient_id != other_patient_id)  # Ensure different patients
        
        # Arrange
        search_svc = create_mock_search_service()
        
        # Create mock patient user
        patient_user = PatientModel(
            uid=patient_id,
            user_type=UserType.PATIENT,
            name="Test Patient"
        )
        
        # Act & Assert - Patient should not be able to search other patient's reports
        with pytest.raises(ValueError) as exc_info:
            await search_svc.search_reports(
                patient_id=other_patient_id,
                query="test",
                requesting_user=patient_user,
                filters=None
            )
        
        assert "Access denied" in str(exc_info.value)
        assert "You can only search your own reports" in str(exc_info.value)
    
    @given(st.text(min_size=1, max_size=50), st.lists(st.text(min_size=1, max_size=20), min_size=1, max_size=5))
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_institution_patient_access_property(self, patient_id, institution_patient_list):
        """
        Property: Institution Patient Access Control
        For any institution user, they should only be able to search reports for patients in their patient list
        **Feature: health-insight-core, Property 6: Search and Filter Functionality**
        **Validates: Requirements 5.4, 9.2**
        """
        assume(patient_id not in institution_patient_list)  # Ensure patient not in list
        
        # Arrange
        search_svc = create_mock_search_service()
        
        # Create mock institution user
        institution_user = InstitutionModel(
            uid="test_institution",
            user_type=UserType.INSTITUTION,
            name="Test Hospital",
            patient_list=institution_patient_list
        )
        
        # Act & Assert - Institution should not access reports of patients not in their list
        with pytest.raises(ValueError) as exc_info:
            await search_svc.search_reports(
                patient_id=patient_id,
                query="test",
                requesting_user=institution_user,
                filters=None
            )
        
        assert "Access denied" in str(exc_info.value)
        assert "Patient is not in your institution's patient list" in str(exc_info.value)