"""
Unit tests for AI safety filters and edge cases.

Tests various scenarios to ensure the AI analysis system properly filters
out medical prescriptions and handles edge cases safely.

Validates: Requirements 3.4
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import json

from app.models.report import MetricData
from app.models.user import PatientModel, UserType
from app.services.llm_analysis import LLMAnalysisService


class TestAISafetyFilters:
    """Unit tests for AI safety filters and medical prescription detection."""
    
    @pytest.fixture
    def llm_service(self):
        """Create LLM service instance for testing."""
        return LLMAnalysisService()
    
    @pytest.fixture
    def sample_test_data(self):
        """Sample test data with concerning values."""
        return {
            "CHOLESTEROL_TOTAL": MetricData(
                name="CHOLESTEROL, TOTAL",
                value="280",
                verdict="HIGH",
                range="< 200",
                unit="mg/dL",
                remark="Elevated"
            ),
            "GLUCOSE": MetricData(
                name="GLUCOSE",
                value="150",
                verdict="HIGH", 
                range="70-100",
                unit="mg/dL",
                remark="Fasting"
            )
        }
    
    @pytest.fixture
    def sample_patient(self):
        """Sample patient profile."""
        return PatientModel(
            uid="test_patient_123",
            user_type=UserType.PATIENT,
            name="Test Patient",
            bio_data={
                "age": 45,
                "gender": "Male",
                "height": "5'10\"",
                "weight": "180 lbs",
                "allergies": ["Penicillin"]
            }
        )
    
    @pytest.mark.asyncio
    async def test_medical_prescription_filtering(self, llm_service, sample_test_data, sample_patient):
        """Test that medical prescriptions are filtered out from AI responses."""
        
        # Mock OpenAI response containing medical prescriptions (should be filtered)
        mock_response_with_prescriptions = {
            "lifestyle_recommendations": [
                "Take 20mg of Lipitor daily",  # Medical prescription - should be filtered
                "Exercise regularly for 30 minutes daily",
                "Prescribe metformin 500mg twice daily"  # Medical prescription - should be filtered
            ],
            "nutritional_advice": [
                "Reduce saturated fat intake",
                "Take prescribed medication with meals"  # Reference to medication - should be filtered
            ],
            "symptom_explanations": [
                "High cholesterol may indicate cardiovascular risk"
            ],
            "next_steps": [
                "Consult your doctor about statin therapy",
                "Schedule follow-up in 3 months"
            ]
        }
        
        with patch.object(llm_service, '_call_openai_api', new_callable=AsyncMock) as mock_api:
            mock_api.return_value = json.dumps(mock_response_with_prescriptions)
            
            result = await llm_service.analyze_test_results(
                patient_id="test_patient",
                report_id="test_report",
                test_data=sample_test_data,
                patient_profile=sample_patient
            )
            
            # Check that medical prescriptions are not present in the output
            analysis_text = json.dumps(result.output).lower()
            
            # These terms should not appear in the final output
            forbidden_terms = [
                "lipitor", "metformin", "20mg", "500mg", "twice daily",
                "prescribe", "prescribed medication"
            ]
            
            for term in forbidden_terms:
                assert term not in analysis_text, f"Found forbidden medical term: {term}"
            
            # Safe advice should still be present
            assert "exercise regularly" in analysis_text
            assert "reduce saturated fat" in analysis_text
            assert "consult with your healthcare provider" in analysis_text or "schedule follow-up" in analysis_text
    
    @pytest.mark.asyncio
    async def test_inappropriate_content_detection(self, llm_service, sample_test_data):
        """Test detection and filtering of inappropriate medical content."""
        
        # Mock response with inappropriate medical advice
        mock_inappropriate_response = {
            "lifestyle_recommendations": [
                "Stop taking all your current medications immediately",  # Dangerous advice
                "Increase exercise gradually"
            ],
            "nutritional_advice": [
                "Avoid all carbohydrates completely",  # Extreme dietary advice
                "Drink more water"
            ],
            "symptom_explanations": [
                "You definitely have diabetes and need insulin",  # Medical diagnosis
                "High glucose can indicate various conditions"
            ],
            "next_steps": [
                "Start insulin therapy right away",  # Medical prescription
                "Schedule appointment with healthcare provider"
            ]
        }
        
        with patch.object(llm_service, '_call_openai_api', new_callable=AsyncMock) as mock_api:
            mock_api.return_value = json.dumps(mock_inappropriate_response)
            
            result = await llm_service.analyze_test_results(
                patient_id="test_patient",
                report_id="test_report", 
                test_data=sample_test_data
            )
            
            # Check that inappropriate content is filtered
            analysis_text = json.dumps(result.output).lower()
            
            inappropriate_terms = [
                "stop taking all", "definitely have diabetes", "need insulin",
                "start insulin therapy", "avoid all carbohydrates completely"
            ]
            
            for term in inappropriate_terms:
                assert term not in analysis_text, f"Found inappropriate content: {term}"
    
    @pytest.mark.asyncio
    async def test_empty_or_invalid_api_response(self, llm_service, sample_test_data):
        """Test handling of empty or invalid API responses."""
        
        # Test cases that should trigger fallback analysis
        fallback_cases = [
            "",  # Empty response
            "Invalid JSON",  # Invalid JSON
        ]
        
        for invalid_response in fallback_cases:
            with patch.object(llm_service, '_call_openai_api', new_callable=AsyncMock) as mock_api:
                mock_api.return_value = invalid_response
                
                result = await llm_service.analyze_test_results(
                    patient_id="test_patient",
                    report_id="test_report",
                    test_data=sample_test_data
                )
                
                # Should fall back to safe default analysis
                assert "error_note" in result.output
                assert "temporarily unavailable" in result.output["error_note"].lower()
        
        # Test cases that parse but have missing fields
        incomplete_cases = [
            "{}",  # Empty JSON object
            '{"incomplete": "response"}',  # Missing required fields
        ]
        
        for incomplete_response in incomplete_cases:
            with patch.object(llm_service, '_call_openai_api', new_callable=AsyncMock) as mock_api:
                mock_api.return_value = incomplete_response
                
                result = await llm_service.analyze_test_results(
                    patient_id="test_patient",
                    report_id="test_report",
                    test_data=sample_test_data
                )
                
                # Should have all required fields (added as empty lists if missing)
                required_fields = [
                    "lifestyle_recommendations", "nutritional_advice",
                    "symptom_explanations", "next_steps", "disclaimer"
                ]
                
                for field in required_fields:
                    assert field in result.output
                    assert isinstance(result.output[field], (list, str))
    
    @pytest.mark.asyncio
    async def test_api_error_handling(self, llm_service, sample_test_data):
        """Test handling of various API errors."""
        
        error_scenarios = [
            ConnectionError("Network error"),
            TimeoutError("Request timeout"),
            Exception("Unexpected error")
        ]
        
        for error in error_scenarios:
            with patch.object(llm_service, '_call_openai_api', new_callable=AsyncMock) as mock_api:
                mock_api.side_effect = error
                
                # Should raise exception with appropriate message
                with pytest.raises(Exception) as exc_info:
                    await llm_service.analyze_test_results(
                        patient_id="test_patient",
                        report_id="test_report",
                        test_data=sample_test_data
                    )
                
                assert "AI analysis generation failed" in str(exc_info.value)
    
    def test_prompt_safety_guidelines(self, llm_service, sample_test_data, sample_patient):
        """Test that generated prompts contain proper safety guidelines."""
        
        prompt = llm_service._create_analysis_prompt(sample_test_data, sample_patient)
        
        # Check for safety guidelines in prompt
        safety_guidelines = [
            "DO NOT provide medical prescriptions",
            "DO NOT diagnose medical conditions", 
            "Focus on lifestyle modifications",
            "Suggest consulting healthcare providers"
        ]
        
        for guideline in safety_guidelines:
            assert guideline in prompt, f"Missing safety guideline: {guideline}"
        
        # Check that prompt requests JSON format
        assert "JSON format" in prompt
        assert "lifestyle_recommendations" in prompt
        assert "nutritional_advice" in prompt
    
    def test_fallback_analysis_safety(self, llm_service):
        """Test that fallback analysis is safe and appropriate."""
        
        fallback = llm_service._create_fallback_analysis()
        
        # Check structure
        required_fields = [
            "lifestyle_recommendations", "nutritional_advice",
            "symptom_explanations", "next_steps", "disclaimer"
        ]
        
        for field in required_fields:
            assert field in fallback
        
        # Check content safety
        fallback_text = json.dumps(fallback).lower()
        
        # Should not contain medical prescriptions
        forbidden_terms = [
            "prescribe", "medication", "drug", "dosage", "mg daily",
            "take twice", "antibiotic", "steroid", "insulin"
        ]
        
        for term in forbidden_terms:
            assert term not in fallback_text, f"Fallback contains forbidden term: {term}"
        
        # Should contain safe advice
        safe_terms = [
            "healthcare provider", "consult", "balanced diet", 
            "exercise", "monitor", "follow-up"
        ]
        
        for term in safe_terms:
            assert term in fallback_text, f"Fallback missing safe term: {term}"
    
    @pytest.mark.asyncio
    async def test_large_file_size_limits(self, llm_service):
        """Test handling of very large test data inputs."""
        
        # Create large test data set
        large_test_data = {}
        for i in range(100):  # 100 metrics
            large_test_data[f"METRIC_{i}"] = MetricData(
                name=f"Test Metric {i}",
                value=str(i * 10),
                verdict="NORMAL",
                unit="mg/dL"
            )
        
        with patch.object(llm_service, '_call_openai_api', new_callable=AsyncMock) as mock_api:
            mock_api.return_value = '{"lifestyle_recommendations": [], "nutritional_advice": [], "symptom_explanations": [], "next_steps": []}'
            
            result = await llm_service.analyze_test_results(
                patient_id="test_patient",
                report_id="test_report",
                test_data=large_test_data
            )
            
            # Should handle large inputs gracefully
            assert result is not None
            assert result.patient_id == "test_patient"
            
            # Check that prompt was generated (API was called)
            mock_api.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_special_characters_handling(self, llm_service):
        """Test handling of special characters in test data."""
        
        special_char_data = {
            "SPECIAL_TEST": MetricData(
                name="Test with Special Chars: <>&\"'",
                value="10.5",
                verdict="NORMAL",
                remark="Contains special chars: <script>alert('test')</script>",
                unit="μg/dL"  # Unicode character
            )
        }
        
        with patch.object(llm_service, '_call_openai_api', new_callable=AsyncMock) as mock_api:
            mock_api.return_value = '{"lifestyle_recommendations": [], "nutritional_advice": [], "symptom_explanations": [], "next_steps": []}'
            
            result = await llm_service.analyze_test_results(
                patient_id="test_patient",
                report_id="test_report",
                test_data=special_char_data
            )
            
            # Should handle special characters without errors
            assert result is not None
            assert result.patient_id == "test_patient"
    
    def test_patient_profile_data_validation(self, llm_service, sample_test_data):
        """Test validation of patient profile data."""
        
        # Test with various patient profile scenarios
        test_profiles = [
            None,  # No profile
            PatientModel(uid="test", user_type=UserType.PATIENT, bio_data={}),  # Empty bio_data
            PatientModel(uid="test", user_type=UserType.PATIENT, bio_data={
                "invalid_field": "should_be_ignored",
                "age": "not_a_number",
                "allergies": "not_a_list"
            })
        ]
        
        for profile in test_profiles:
            # Should not raise exceptions with any profile data
            prompt = llm_service._create_analysis_prompt(sample_test_data, profile)
            assert isinstance(prompt, str)
            assert len(prompt) > 0
    
    @pytest.mark.asyncio
    async def test_concurrent_analysis_requests(self, llm_service, sample_test_data):
        """Test handling of concurrent analysis requests."""
        
        import asyncio
        
        with patch.object(llm_service, '_call_openai_api', new_callable=AsyncMock) as mock_api:
            mock_api.return_value = '{"lifestyle_recommendations": [], "nutritional_advice": [], "symptom_explanations": [], "next_steps": []}'
            
            # Create multiple concurrent requests
            tasks = []
            for i in range(5):
                task = llm_service.analyze_test_results(
                    patient_id=f"patient_{i}",
                    report_id=f"report_{i}",
                    test_data=sample_test_data
                )
                tasks.append(task)
            
            # Execute concurrently
            results = await asyncio.gather(*tasks)
            
            # All should complete successfully
            assert len(results) == 5
            for i, result in enumerate(results):
                assert result.patient_id == f"patient_{i}"
                assert result.report_id == f"report_{i}"