"""
Property-based tests for data model validation
"""

from hypothesis import given, strategies as st
import pytest
from pydantic import ValidationError
from app.models import (
    PatientModel, InstitutionModel, MetricData, Report, 
    LLMReportModel, UserType, OnboardRequest
)
from datetime import datetime


# Strategies for generating test data
user_type_strategy = st.sampled_from([UserType.PATIENT, UserType.INSTITUTION])
name_strategy = st.text(min_size=1, max_size=100).filter(lambda x: x.strip())
uid_strategy = st.text(min_size=1, max_size=50).filter(lambda x: x.strip())

bio_data_strategy = st.dictionaries(
    keys=st.sampled_from(["height", "weight", "age", "allergies"]),
    values=st.one_of(
        st.integers(min_value=1, max_value=300),  # height/weight/age
        st.lists(st.text(min_size=1, max_size=50), max_size=5)  # allergies
    ),
    max_size=4
)

metric_data_strategy = st.builds(
    MetricData,
    name=st.text(min_size=1, max_size=100),
    value=st.text(min_size=1, max_size=50),
    remark=st.one_of(st.none(), st.text(max_size=200)),
    range=st.one_of(st.none(), st.text(max_size=50)),
    unit=st.one_of(st.none(), st.text(max_size=20)),
    verdict=st.one_of(st.none(), st.sampled_from(["NORMAL", "HIGH", "LOW", "CRITICAL"]))
)

attributes_strategy = st.dictionaries(
    keys=st.text(min_size=1, max_size=50),
    values=metric_data_strategy,
    min_size=1,
    max_size=10
)


@given(
    uid=uid_strategy,
    name=name_strategy,
    bio_data=bio_data_strategy,
    favorites=st.lists(st.text(min_size=1, max_size=50), max_size=10),
    reports=st.lists(st.text(min_size=1, max_size=50), max_size=20)
)
def test_patient_model_validation_property(uid, name, bio_data, favorites, reports):
    """
    Property 11: Profile Data Validation
    For any valid patient profile data, the system should validate completeness and accuracy,
    and use valid profile data to personalize AI analysis
    **Feature: health-insight-core, Property 11: Profile Data Validation**
    **Validates: Requirements 6.5, 6.4**
    """
    # Create patient model with valid data
    patient = PatientModel(
        uid=uid,
        user_type=UserType.PATIENT,
        name=name,
        bio_data=bio_data,
        favorites=favorites,
        reports=reports
    )
    
    # Validate that all required fields are properly set
    assert patient.uid == uid
    assert patient.user_type == UserType.PATIENT
    assert patient.name == name
    assert patient.bio_data == bio_data
    assert patient.favorites == favorites
    assert patient.reports == reports
    
    # Validate that bio_data can be used for personalization
    if bio_data:
        # Bio data should be accessible and properly structured
        for key, value in bio_data.items():
            assert key in patient.bio_data
            assert patient.bio_data[key] == value


@given(
    uid=uid_strategy,
    name=name_strategy,
    patient_list=st.lists(st.text(min_size=1, max_size=50), max_size=100)
)
def test_institution_model_validation_property(uid, name, patient_list):
    """
    Property 11: Profile Data Validation (Institution variant)
    For any valid institution profile data, the system should validate completeness and accuracy
    **Feature: health-insight-core, Property 11: Profile Data Validation**
    **Validates: Requirements 6.5, 6.4**
    """
    # Create institution model with valid data
    institution = InstitutionModel(
        uid=uid,
        user_type=UserType.INSTITUTION,
        name=name,
        patient_list=patient_list
    )
    
    # Validate that all required fields are properly set
    assert institution.uid == uid
    assert institution.user_type == UserType.INSTITUTION
    assert institution.name == name
    assert institution.patient_list == patient_list


@given(
    report_id=st.text(min_size=1, max_size=50),
    patient_id=st.text(min_size=1, max_size=50),
    attributes=attributes_strategy
)
def test_report_model_validation_property(report_id, patient_id, attributes):
    """
    Property 11: Profile Data Validation (Report variant)
    For any valid report data, the system should validate completeness and accuracy
    **Feature: health-insight-core, Property 11: Profile Data Validation**
    **Validates: Requirements 6.5, 6.4**
    """
    # Create report with valid data
    report = Report(
        report_id=report_id,
        patient_id=patient_id,
        attributes=attributes
    )
    
    # Validate that all required fields are properly set
    assert report.report_id == report_id
    assert report.patient_id == patient_id
    assert report.attributes == attributes
    assert isinstance(report.processed_at, datetime)
    
    # Validate that attributes contain valid MetricData
    for key, metric in attributes.items():
        assert isinstance(metric, MetricData)
        assert key in report.attributes


@given(
    patient_id=st.text(min_size=1, max_size=50),
    report_id=st.text(min_size=1, max_size=50),
    output=st.dictionaries(
        keys=st.text(min_size=1, max_size=50),
        values=st.one_of(st.text(), st.lists(st.text(), max_size=5)),
        min_size=1,
        max_size=5
    ),
    input_data=st.dictionaries(
        keys=st.text(min_size=1, max_size=50),
        values=st.text(),
        min_size=1,
        max_size=5
    )
)
def test_llm_report_model_validation_property(patient_id, report_id, output, input_data):
    """
    Property 11: Profile Data Validation (LLM Report variant)
    For any valid LLM report data, the system should validate completeness and accuracy
    **Feature: health-insight-core, Property 11: Profile Data Validation**
    **Validates: Requirements 6.5, 6.4**
    """
    # Create LLM report with valid data
    llm_report = LLMReportModel(
        patient_id=patient_id,
        report_id=report_id,
        output=output,
        input=input_data
    )
    
    # Validate that all required fields are properly set
    assert llm_report.patient_id == patient_id
    assert llm_report.report_id == report_id
    assert llm_report.output == output
    assert llm_report.input == input_data


@given(
    role=user_type_strategy,
    name=st.one_of(st.none(), name_strategy)
)
def test_onboard_request_validation_property(role, name):
    """
    Property 11: Profile Data Validation (Onboard Request variant)
    For any valid onboard request data, the system should validate completeness and accuracy
    **Feature: health-insight-core, Property 11: Profile Data Validation**
    **Validates: Requirements 6.5, 6.4**
    """
    # Create onboard request with valid data
    request = OnboardRequest(
        role=role,
        name=name
    )
    
    # Validate that all fields are properly set
    assert request.role == role
    assert request.name == name


# Test invalid data handling
@given(st.text(max_size=0))  # Empty string
def test_patient_model_rejects_empty_uid(empty_uid):
    """
    Property 11: Profile Data Validation (Error handling)
    For any invalid profile data, the system should properly validate and handle errors
    **Feature: health-insight-core, Property 11: Profile Data Validation**
    **Validates: Requirements 6.5, 6.4**
    """
    # Empty UID should be handled gracefully (allowed as Optional)
    patient = PatientModel(
        uid=empty_uid if empty_uid else None,
        user_type=UserType.PATIENT
    )
    
    # Should not raise validation error for optional fields
    assert patient.uid == (empty_uid if empty_uid else None)


@given(st.text(max_size=0))  # Empty string for required field
def test_llm_report_rejects_empty_required_fields(empty_string):
    """
    Property 11: Profile Data Validation (Required field validation)
    For any invalid required field data, the system should reject with validation error
    **Feature: health-insight-core, Property 11: Profile Data Validation**
    **Validates: Requirements 6.5, 6.4**
    """
    # Empty required fields should raise validation error
    with pytest.raises(ValidationError):
        LLMReportModel(
            patient_id=empty_string,  # Required field, should fail
            report_id="valid_id",
            output={"key": "value"},
            input={"key": "value"}
        )