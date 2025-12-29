"""
Property-based tests for tracked metrics management
"""

import pytest
import asyncio
from hypothesis import given, strategies as st, assume
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timedelta
from bson import ObjectId

from app.services.tracked_metrics import TrackedMetricsService
from app.services.database import DatabaseService
from app.models.report import MetricData


# Test strategies
patient_id_strategy = st.text(min_size=1, max_size=50).filter(lambda x: x.strip())
metric_name_strategy = st.text(min_size=1, max_size=100).filter(lambda x: x.strip())
metric_value_strategy = st.floats(min_value=0.1, max_value=1000.0, allow_nan=False, allow_infinity=False)
verdict_strategy = st.sampled_from(["NORMAL", "HIGH", "LOW", "CRITICAL"])
unit_strategy = st.sampled_from(["mg/dL", "g/L", "mmol/L", "IU/L", "%", "count"])

# Strategy for generating metric data with numeric values
numeric_metric_data_strategy = st.builds(
    MetricData,
    name=metric_name_strategy,
    value=metric_value_strategy.map(str),
    unit=unit_strategy,
    verdict=verdict_strategy,
    range=st.text(min_size=1, max_size=20),
    remark=st.one_of(st.none(), st.text(max_size=100))
)

# Strategy for generating reports with time series data
def generate_time_series_reports(patient_id, metric_name, num_reports=5):
    """Generate a list of reports with time series data for a metric"""
    reports = []
    base_date = datetime.utcnow() - timedelta(days=num_reports * 30)
    
    for i in range(num_reports):
        report_date = base_date + timedelta(days=i * 30)
        value = 50.0 + (i * 10)  # Increasing trend
        
        metric_data = MetricData(
            name=metric_name,
            value=str(value),
            unit="mg/dL",
            verdict="HIGH" if value > 70 else "NORMAL",
            range="0-60"
        )
        
        report = {
            "_id": str(ObjectId()),
            "report_id": f"report_{i}",
            "patient_id": patient_id,
            "processed_at": report_date,
            "attributes": {metric_name: metric_data.model_dump(exclude_none=True)}
        }
        reports.append(report)
    
    return reports


def create_mock_tracked_metrics_service():
    """Create a mock tracked metrics service for testing"""
    service = TrackedMetricsService()
    
    # Mock the database service
    service.db_service = MagicMock()
    service.db_service.get_user_by_uid = AsyncMock()
    service.db_service.update_user_favorites = AsyncMock()
    service.db_service.get_reports_by_patient_id = AsyncMock()
    
    return service


@given(
    patient_id=patient_id_strategy,
    metric_name=metric_name_strategy
)
@pytest.mark.asyncio
async def test_tracked_metrics_management_property(patient_id, metric_name):
    """
    Property 4: Tracked Metrics Management
    For any patient-selected concerning results, the system should add them to tracked metrics,
    display time-series visualizations, and generate trend analysis with actionable advice
    **Feature: health-insight-core, Property 4: Tracked Metrics Management**
    **Validates: Requirements 4.1, 4.2, 4.3, 4.4**
    """
    mock_service = create_mock_tracked_metrics_service()
    
    # Mock patient data without the metric initially tracked
    initial_patient_data = {
        "_id": str(ObjectId()),
        "uid": patient_id,
        "user_type": "patient",
        "name": "Test Patient",
        "favorites": []  # No metrics tracked initially
    }
    mock_service.db_service.get_user_by_uid.return_value = initial_patient_data
    mock_service.db_service.update_user_favorites.return_value = True
    
    # Test adding metric to tracking (Requirement 4.1)
    success = await mock_service.add_metric_to_tracking(patient_id, metric_name)
    
    # Verify metric was added to tracking
    assert success is True
    mock_service.db_service.update_user_favorites.assert_called_once_with(
        patient_id, [metric_name]
    )
    
    # Mock patient data with the metric now tracked
    updated_patient_data = {
        **initial_patient_data,
        "favorites": [metric_name]
    }
    mock_service.db_service.get_user_by_uid.return_value = updated_patient_data
    
    # Test getting tracked metrics
    tracked_metrics = await mock_service.get_tracked_metrics(patient_id)
    assert metric_name in tracked_metrics
    
    # Mock time series data for trend analysis (Requirements 4.2, 4.3)
    time_series_reports = generate_time_series_reports(patient_id, metric_name, 5)
    mock_service.db_service.get_reports_by_patient_id.return_value = time_series_reports
    
    # Test time series data retrieval
    time_series_data = await mock_service.get_metric_time_series_data(patient_id, metric_name)
    
    # Verify time series data structure and content
    assert len(time_series_data) == 5
    for i, data_point in enumerate(time_series_data):
        assert data_point["report_id"] == f"report_{i}"
        assert data_point["numeric_value"] is not None
        assert isinstance(data_point["numeric_value"], float)
        assert data_point["unit"] == "mg/dL"
    
    # Test trend analysis (Requirement 4.3)
    trend_analysis = await mock_service.analyze_metric_trend(patient_id, metric_name)
    
    # Verify trend analysis structure and logic
    assert trend_analysis["metric_name"] == metric_name
    assert trend_analysis["data_points"] == 5
    assert trend_analysis["numeric_data_points"] == 5
    assert trend_analysis["trend"] in ["increasing", "decreasing", "stable"]
    assert trend_analysis["latest_value"] is not None
    assert trend_analysis["earliest_value"] is not None
    
    # For our test data (increasing trend), verify trend detection
    assert trend_analysis["trend"] == "increasing"
    assert trend_analysis["change_percentage"] > 0
    
    # Test dashboard data compilation (Requirements 4.2, 4.4)
    dashboard_data = await mock_service.get_dashboard_data(patient_id)
    
    # Verify dashboard data structure
    assert dashboard_data["patient_id"] == patient_id
    assert metric_name in dashboard_data["tracked_metrics"]
    assert metric_name in dashboard_data["trends"]
    assert metric_name in dashboard_data["time_series"]
    assert "summary" in dashboard_data
    
    # Verify summary statistics
    summary = dashboard_data["summary"]
    assert summary["total_tracked"] == 1
    assert summary["improving"] + summary["worsening"] + summary["stable"] == 1
    
    # Test actionable advice generation (Requirement 4.4)
    advice = await mock_service.generate_actionable_advice(patient_id, limit_reports=5)
    
    # Verify advice is generated and relevant
    assert isinstance(advice, list)
    assert len(advice) > 0
    # For our test data with HIGH verdict and increasing trend, should generate relevant advice
    advice_text = " ".join(advice).lower()
    assert any(keyword in advice_text for keyword in ["high", "elevated", "worsening", "consult"])


@given(
    patient_id=patient_id_strategy,
    metric_names=st.lists(metric_name_strategy, min_size=2, max_size=5, unique=True)
)
@pytest.mark.asyncio
async def test_multiple_metrics_tracking_property(patient_id, metric_names):
    """
    Property 4: Tracked Metrics Management (Multiple metrics variant)
    For any set of patient-selected metrics, the system should manage all tracked metrics
    consistently and provide comprehensive dashboard data
    **Feature: health-insight-core, Property 4: Tracked Metrics Management**
    **Validates: Requirements 4.1, 4.2, 4.3, 4.4**
    """
    mock_service = create_mock_tracked_metrics_service()
    
    # Mock patient data
    patient_data = {
        "_id": str(ObjectId()),
        "uid": patient_id,
        "user_type": "patient",
        "name": "Test Patient",
        "favorites": []
    }
    mock_service.db_service.get_user_by_uid.return_value = patient_data
    mock_service.db_service.update_user_favorites.return_value = True
    
    # Add all metrics to tracking
    for metric_name in metric_names:
        success = await mock_service.add_metric_to_tracking(patient_id, metric_name)
        assert success is True
        
        # Update mock data to include the new metric
        patient_data["favorites"].append(metric_name)
        mock_service.db_service.get_user_by_uid.return_value = patient_data
    
    # Verify all metrics are tracked
    tracked_metrics = await mock_service.get_tracked_metrics(patient_id)
    assert len(tracked_metrics) == len(metric_names)
    for metric_name in metric_names:
        assert metric_name in tracked_metrics
    
    # Mock reports with data for all metrics
    all_reports = []
    for i in range(3):  # 3 reports
        report_date = datetime.utcnow() - timedelta(days=i * 30)
        attributes = {}
        
        for j, metric_name in enumerate(metric_names):
            value = 50.0 + (j * 10) + (i * 5)  # Different values for each metric and report
            metric_data = MetricData(
                name=metric_name,
                value=str(value),
                unit="mg/dL",
                verdict="NORMAL" if value < 70 else "HIGH"
            )
            attributes[metric_name] = metric_data.model_dump(exclude_none=True)
        
        report = {
            "_id": str(ObjectId()),
            "report_id": f"report_{i}",
            "patient_id": patient_id,
            "processed_at": report_date,
            "attributes": attributes
        }
        all_reports.append(report)
    
    mock_service.db_service.get_reports_by_patient_id.return_value = all_reports
    
    # Test dashboard data for multiple metrics
    dashboard_data = await mock_service.get_dashboard_data(patient_id)
    
    # Verify all metrics are included in dashboard
    assert len(dashboard_data["tracked_metrics"]) == len(metric_names)
    assert len(dashboard_data["trends"]) == len(metric_names)
    assert len(dashboard_data["time_series"]) == len(metric_names)
    
    # Verify each metric has proper trend analysis
    for metric_name in metric_names:
        assert metric_name in dashboard_data["trends"]
        trend = dashboard_data["trends"][metric_name]
        assert trend["metric_name"] == metric_name
        assert trend["data_points"] == 3
        
        assert metric_name in dashboard_data["time_series"]
        time_series = dashboard_data["time_series"][metric_name]
        assert len(time_series) == 3
    
    # Verify summary reflects all metrics
    summary = dashboard_data["summary"]
    assert summary["total_tracked"] == len(metric_names)


@given(
    patient_id=patient_id_strategy,
    metric_name=metric_name_strategy
)
@pytest.mark.asyncio
async def test_metric_removal_property(patient_id, metric_name):
    """
    Property 4: Tracked Metrics Management (Removal variant)
    For any tracked metric, the system should allow removal from tracking
    and update the tracked metrics list accordingly
    **Feature: health-insight-core, Property 4: Tracked Metrics Management**
    **Validates: Requirements 4.1, 4.2, 4.3, 4.4**
    """
    mock_service = create_mock_tracked_metrics_service()
    
    # Mock patient data with metric already tracked
    patient_data = {
        "_id": str(ObjectId()),
        "uid": patient_id,
        "user_type": "patient",
        "name": "Test Patient",
        "favorites": [metric_name]  # Metric already tracked
    }
    mock_service.db_service.get_user_by_uid.return_value = patient_data
    mock_service.db_service.update_user_favorites.return_value = True
    
    # Test removing metric from tracking
    success = await mock_service.remove_metric_from_tracking(patient_id, metric_name)
    
    # Verify metric was removed
    assert success is True
    mock_service.db_service.update_user_favorites.assert_called_once_with(
        patient_id, []  # Empty list after removal
    )
    
    # Mock updated patient data without the metric
    updated_patient_data = {
        **patient_data,
        "favorites": []
    }
    mock_service.db_service.get_user_by_uid.return_value = updated_patient_data
    
    # Verify metric is no longer tracked
    tracked_metrics = await mock_service.get_tracked_metrics(patient_id)
    assert metric_name not in tracked_metrics
    assert len(tracked_metrics) == 0


@given(
    patient_id=patient_id_strategy,
    metric_name=metric_name_strategy,
    days_back=st.integers(min_value=30, max_value=365)
)
@pytest.mark.asyncio
async def test_time_range_filtering_property(patient_id, metric_name, days_back):
    """
    Property 4: Tracked Metrics Management (Time range filtering)
    For any time range specification, the system should correctly filter
    time series data and trend analysis to the specified period
    **Feature: health-insight-core, Property 4: Tracked Metrics Management**
    **Validates: Requirements 4.1, 4.2, 4.3, 4.4**
    """
    mock_service = create_mock_tracked_metrics_service()
    
    # Generate reports spanning a longer period than the filter
    all_reports = []
    base_date = datetime.utcnow() - timedelta(days=days_back + 100)  # Older than filter
    
    for i in range(10):  # 10 reports over time
        report_date = base_date + timedelta(days=i * 50)  # Every 50 days
        value = 50.0 + (i * 5)
        
        metric_data = MetricData(
            name=metric_name,
            value=str(value),
            unit="mg/dL",
            verdict="NORMAL"
        )
        
        report = {
            "_id": str(ObjectId()),
            "report_id": f"report_{i}",
            "patient_id": patient_id,
            "processed_at": report_date,
            "attributes": {metric_name: metric_data.model_dump(exclude_none=True)}
        }
        all_reports.append(report)
    
    mock_service.db_service.get_reports_by_patient_id.return_value = all_reports
    
    # Test time series data with date filtering
    time_series_data = await mock_service.get_metric_time_series_data(
        patient_id, metric_name, days_back
    )
    
    # Verify only reports within the specified time range are included
    cutoff_date = datetime.utcnow() - timedelta(days=days_back)
    for data_point in time_series_data:
        assert data_point["date"] >= cutoff_date
    
    # Test trend analysis with the same time range
    trend_analysis = await mock_service.analyze_metric_trend(
        patient_id, metric_name, days_back
    )
    
    # Verify trend analysis uses only the filtered data
    assert trend_analysis["data_points"] == len(time_series_data)
    if time_series_data:
        assert trend_analysis["latest_date"] >= cutoff_date
        assert trend_analysis["earliest_date"] >= cutoff_date


@given(
    patient_id=patient_id_strategy,
    metric_name=metric_name_strategy
)
@pytest.mark.asyncio
async def test_no_data_handling_property(patient_id, metric_name):
    """
    Property 4: Tracked Metrics Management (No data handling)
    For any metric with no available data, the system should handle
    the absence gracefully and provide appropriate feedback
    **Feature: health-insight-core, Property 4: Tracked Metrics Management**
    **Validates: Requirements 4.1, 4.2, 4.3, 4.4**
    """
    mock_service = create_mock_tracked_metrics_service()
    
    # Mock empty reports (no data available)
    mock_service.db_service.get_reports_by_patient_id.return_value = []
    
    # Test time series data with no reports
    time_series_data = await mock_service.get_metric_time_series_data(patient_id, metric_name)
    assert len(time_series_data) == 0
    
    # Test trend analysis with no data
    trend_analysis = await mock_service.analyze_metric_trend(patient_id, metric_name)
    
    # Verify appropriate handling of no data scenario
    assert trend_analysis["metric_name"] == metric_name
    assert trend_analysis["trend"] == "no_data"
    assert trend_analysis["data_points"] == 0
    assert "no data available" in trend_analysis["message"].lower()
    
    # Test dashboard data with no reports
    patient_data = {
        "_id": str(ObjectId()),
        "uid": patient_id,
        "user_type": "patient",
        "favorites": [metric_name]
    }
    mock_service.db_service.get_user_by_uid.return_value = patient_data
    
    dashboard_data = await mock_service.get_dashboard_data(patient_id)
    
    # Verify dashboard handles no data gracefully
    assert dashboard_data["patient_id"] == patient_id
    assert metric_name in dashboard_data["tracked_metrics"]
    assert metric_name in dashboard_data["trends"]
    assert dashboard_data["trends"][metric_name]["trend"] == "no_data"
    
    # Test advice generation with no data
    advice = await mock_service.generate_actionable_advice(patient_id)
    assert isinstance(advice, list)
    assert len(advice) > 0
    # Should provide helpful message about no data
    advice_text = " ".join(advice).lower()
    assert any(keyword in advice_text for keyword in ["no", "data", "reports", "available"])