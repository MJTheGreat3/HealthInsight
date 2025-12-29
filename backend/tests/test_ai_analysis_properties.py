"""
Property-based tests for AI Analysis functionality.

**Feature: health-insight-core, Property 3: AI Analysis Completeness**

For any extracted test data, the AI analysis engine should generate comprehensive 
advice including lifestyle recommendations, nutritional guidance, symptom 
explanations, and next steps without medical prescriptions.

Validates: Requirements 3.1, 3.2, 3.3, 3.4, 2.5
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from typing import Dict, Any

from app.models.report import MetricData
from app.models.user import PatientModel, UserType
from app.services.llm_analysis import LLMAnalysisService


# Test data strategies
@st.composite
def _metric_data_strategy(draw):
    """Generate valid MetricData instances."""
    name = draw(st.text(min_size=1, max_size=50).filter(lambda x: x.strip()))
    value = draw(st.one_of(
        st.text(min_size=1, max_size=20).filter(lambda x: x.strip()),
        st.floats(min_value=0.1, max_value=1000.0).map(str),
        st.integers(min_value=1, max_value=1000).map(str)
    ))
    verdict = draw(st.sampled_from(["NORMAL", "HIGH", "LOW", "CRITICAL"]))
    unit = draw(st.one_of(
        st.just(None),
        st.sampled_from(["mg/dL", "g/dL", "mmol/L", "IU/L", "ng/mL", "%"])
    ))
    range_val = draw(st.one_of(
        st.just(None),
        st.text(min_size=3, max_size=20).filter(lambda x: "-" in x or "<" in x or ">" in x)
    ))
    remark = draw(st.one_of(st.just(None), st.text(max_size=100)))
    
    return MetricData(
        name=name,
        value=value,
        verdict=verdict,
        unit=unit,
        range=range_val,
        remark=remark
    )


@st.composite
def _test_data_strategy(draw):
    """Generate dictionary of test data with MetricData values."""
    num_metrics = draw(st.integers(min_value=1, max_value=10))
    test_data = {}
    
    for i in range(num_metrics):
        key = f"TEST_METRIC_{i}"
        metric = draw(_metric_data_strategy())
        test_data[key] = metric
    
    return test_data


@st.composite
def _patient_profile_strategy(draw):
    """Generate valid PatientModel instances."""
    name = draw(st.text(min_size=1, max_size=50).filter(lambda x: x.strip()))
    bio_data = draw(st.dictionaries(
        keys=st.sampled_from(["height", "weight", "age", "gender", "allergies"]),
        values=st.one_of(
            st.text(min_size=1, max_size=20),
            st.integers(min_value=1, max_value=200),
            st.lists(st.text(min_size=1, max_size=20), max_size=5)
        ),
        min_size=0,
        max_size=5
    ))
    
    return PatientModel(
        uid=f"patient_{draw(st.integers(min_value=1, max_value=1000))}",
        user_type=UserType.PATIENT,
        name=name,
        bio_data=bio_data
    )


class TestAIAnalysisProperties:
    """Property-based tests for AI Analysis functionality."""
    
    @given(
        patient_id=st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
        report_id=st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
        test_data=_test_data_strategy(),
        patient_profile=st.one_of(st.just(None), _patient_profile_strategy())
    )
    @settings(
        max_examples=20, 
        deadline=30000, 
        suppress_health_check=[HealthCheck.filter_too_much]
    )
    def test_analysis_completeness_property(
        self, 
        patient_id, 
        report_id, 
        test_data, 
        patient_profile
    ):
        """
        Property: AI Analysis Completeness
        
        For any valid test data, the AI analysis should generate comprehensive
        advice with all required components without medical prescriptions.
        """
        async def run_test():
            # Create service instance for each test
            llm_service = LLMAnalysisService()
            
            # Mock OpenAI API response
            mock_response = {
                "lifestyle_recommendations": [
                    "Maintain regular exercise routine",
                    "Ensure adequate sleep (7-9 hours nightly)"
                ],
                "nutritional_advice": [
                    "Include more leafy greens in diet",
                    "Reduce processed food intake"
                ],
                "symptom_explanations": [
                    "Elevated values may indicate metabolic changes",
                    "Multiple factors can influence test results"
                ],
                "next_steps": [
                    "Schedule follow-up with healthcare provider",
                    "Continue monitoring as recommended"
                ],
                "positive_aspects": [
                    "Several values are within normal ranges"
                ]
            }
            
            with patch.object(llm_service, '_call_openai_api', new_callable=AsyncMock) as mock_api:
                mock_api.return_value = str(mock_response).replace("'", '"')
                
                # Execute analysis
                result = await llm_service.analyze_test_results(
                    patient_id=patient_id,
                    report_id=report_id,
                    test_data=test_data,
                    patient_profile=patient_profile
                )
                
                # Property 1: Result should be a valid LLMReportModel
                assert result.patient_id == patient_id
                assert result.report_id == report_id
                assert result.time is not None
                assert isinstance(result.output, dict)
                assert isinstance(result.input, dict)
                
                # Property 2: Output should contain all required analysis components
                required_fields = [
                    "lifestyle_recommendations",
                    "nutritional_advice", 
                    "symptom_explanations",
                    "next_steps"
                ]
                
                for field in required_fields:
                    assert field in result.output, f"Missing required field: {field}"
                    assert isinstance(result.output[field], list), f"{field} should be a list"
                
                # Property 3: Should include safety disclaimer
                assert "disclaimer" in result.output
                assert "informational purposes only" in result.output["disclaimer"].lower()
                
                # Property 4: Input data should be preserved correctly
                assert "attributes" in result.input
                assert len(result.input["attributes"]) == len(test_data)
                
                # Property 5: No medical prescriptions should be present
                analysis_text = str(result.output).lower()
                forbidden_terms = [
                    "prescribe", "prescription", "medication", "drug", "dosage",
                    "mg daily", "take twice", "antibiotic", "steroid"
                ]
                
                for term in forbidden_terms:
                    assert term not in analysis_text, f"Found forbidden medical term: {term}"
        
        # Run the async test
        asyncio.run(run_test())
    
    @given(
        test_data=_test_data_strategy(),
        patient_profile=st.one_of(st.just(None), _patient_profile_strategy())
    )
    @settings(
        max_examples=10, 
        deadline=10000, 
        suppress_health_check=[HealthCheck.filter_too_much]
    )
    def test_prompt_generation_property(self, test_data, patient_profile):
        """
        Property: Prompt Generation Consistency
        
        For any test data and patient profile, the system should generate
        a well-structured prompt with all necessary components.
        """
        # Create service instance for each test
        llm_service = LLMAnalysisService()
        
        # Generate prompt
        prompt = llm_service._create_analysis_prompt(test_data, patient_profile)
        
        # Property 1: Prompt should be non-empty string
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        
        # Property 2: Should contain safety guidelines
        assert "DO NOT provide medical prescriptions" in prompt
        assert "DO NOT diagnose medical conditions" in prompt
        
        # Property 3: Should include test data
        if any(metric.verdict in ["HIGH", "LOW", "CRITICAL"] for metric in test_data.values()):
            assert "PROBLEMATIC TEST RESULTS" in prompt
        
        # Property 4: Should include patient context if provided
        if patient_profile and patient_profile.bio_data:
            assert "Patient Profile:" in prompt
        
        # Property 5: Should request JSON format
        assert "JSON format" in prompt
        assert "lifestyle_recommendations" in prompt
        assert "nutritional_advice" in prompt
    
    def test_fallback_analysis_property(self):
        """
        Property: Fallback Analysis Structure
        
        The fallback analysis should always provide a complete,
        safe response structure when AI generation fails.
        """
        # Create service instance for each test
        llm_service = LLMAnalysisService()
        
        # Get fallback analysis
        fallback = llm_service._create_fallback_analysis()
        
        # Property 1: Should contain all required fields
        required_fields = [
            "lifestyle_recommendations",
            "nutritional_advice",
            "symptom_explanations", 
            "next_steps",
            "positive_aspects",
            "disclaimer"
        ]
        
        for field in required_fields:
            assert field in fallback, f"Missing required field in fallback: {field}"
            assert isinstance(fallback[field], list) or isinstance(fallback[field], str)
        
        # Property 2: Should indicate it's a fallback
        assert "error_note" in fallback
        assert "temporarily unavailable" in fallback["error_note"].lower()
        
        # Property 3: Should provide safe, general advice
        advice_text = str(fallback).lower()
        assert "healthcare provider" in advice_text
        assert "consult" in advice_text
        
        # Property 4: Should not contain medical prescriptions
        forbidden_terms = ["prescribe", "medication", "drug", "dosage"]
        for term in forbidden_terms:
            assert term not in advice_text, f"Fallback contains forbidden term: {term}"


# Additional edge case tests
class TestAIAnalysisEdgeCases:
    """Edge case tests for AI Analysis functionality."""
    
    @pytest.mark.asyncio
    async def test_empty_test_data_handling(self):
        """Test handling of empty test data."""
        llm_service = LLMAnalysisService()
        
        with patch.object(llm_service, '_call_openai_api', new_callable=AsyncMock) as mock_api:
            mock_api.return_value = '{"lifestyle_recommendations": [], "nutritional_advice": [], "symptom_explanations": [], "next_steps": []}'
            
            result = await llm_service.analyze_test_results(
                patient_id="test",
                report_id="test",
                test_data={},
                patient_profile=None
            )
            
            assert result is not None
            assert result.patient_id == "test"
    
    @pytest.mark.asyncio
    async def test_malformed_api_response_handling(self):
        """Test handling of malformed API responses."""
        llm_service = LLMAnalysisService()
        test_data = {"TEST": MetricData(name="Test", value="10", verdict="NORMAL")}
        
        with patch.object(llm_service, '_call_openai_api', new_callable=AsyncMock) as mock_api:
            mock_api.return_value = "Invalid JSON response"
            
            result = await llm_service.analyze_test_results(
                patient_id="test",
                report_id="test", 
                test_data=test_data,
                patient_profile=None
            )
            
            # Should use fallback analysis
            assert "error_note" in result.output
            assert "temporarily unavailable" in result.output["error_note"].lower()
    
    @pytest.mark.asyncio
    async def test_api_failure_handling(self):
        """Test handling of API failures."""
        llm_service = LLMAnalysisService()
        test_data = {"TEST": MetricData(name="Test", value="10", verdict="NORMAL")}
        
        with patch.object(llm_service, '_call_openai_api', new_callable=AsyncMock) as mock_api:
            mock_api.side_effect = Exception("API Error")
            
            # Should raise exception but not crash
            with pytest.raises(Exception) as exc_info:
                await llm_service.analyze_test_results(
                    patient_id="test",
                    report_id="test",
                    test_data=test_data
                )
            
            # Property: Should provide meaningful error message
            assert "AI analysis generation failed" in str(exc_info.value)