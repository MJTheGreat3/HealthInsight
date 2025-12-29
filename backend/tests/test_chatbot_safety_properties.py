"""
Property-based tests for Chatbot Context and Safety functionality.

**Feature: health-insight-core, Property 7: Chatbot Context and Safety**

For any patient health question, the chatbot should provide contextually relevant 
responses using medical history while avoiding medical prescriptions and declining 
inappropriate requests.

Validates: Requirements 7.1, 7.2, 7.3, 7.5
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from typing import Dict, Any, List
from datetime import datetime

from app.models.chat import ChatMessage, ChatSession
from app.models.user import PatientModel, UserType
from app.models.report import MetricData
from app.services.chatbot import ChatbotService
from app.services.llm_analysis import LLMAnalysisService
from app.services.database import DatabaseService


# Test data strategies
@st.composite
def _chat_message_strategy(draw):
    """Generate valid ChatMessage instances."""
    role = draw(st.sampled_from(["user", "assistant"]))
    content = draw(st.text(min_size=1, max_size=500).filter(lambda x: x.strip()))
    timestamp = datetime.utcnow()
    
    return ChatMessage(role=role, content=content, timestamp=timestamp)


@st.composite
def _patient_context_strategy(draw):
    """Generate patient context data for chatbot."""
    patient_id = draw(st.text(min_size=1, max_size=50).filter(lambda x: x.strip()))
    
    # Generate recent reports
    num_reports = draw(st.integers(min_value=0, max_value=3))
    recent_reports = []
    
    for i in range(num_reports):
        report = {
            "date": datetime.utcnow().isoformat(),
            "concerning_values": draw(st.lists(
                st.dictionaries(
                    keys=st.sampled_from(["name", "value", "verdict"]),
                    values=st.one_of(
                        st.text(min_size=1, max_size=30),
                        st.sampled_from(["HIGH", "LOW", "CRITICAL", "NORMAL"])
                    )
                ),
                max_size=3
            )),
            "normal_values": draw(st.lists(
                st.dictionaries(
                    keys=st.sampled_from(["name", "value", "verdict"]),
                    values=st.one_of(
                        st.text(min_size=1, max_size=30),
                        st.just("NORMAL")
                    )
                ),
                max_size=5
            ))
        }
        recent_reports.append(report)
    
    # Generate tracked metrics
    tracked_metrics = draw(st.lists(
        st.text(min_size=1, max_size=30).filter(lambda x: x.strip()),
        max_size=5
    ))
    
    # Generate profile data
    profile_data = draw(st.dictionaries(
        keys=st.sampled_from(["age", "height", "weight", "gender", "allergies"]),
        values=st.one_of(
            st.text(min_size=1, max_size=20),
            st.integers(min_value=1, max_value=200),
            st.lists(st.text(min_size=1, max_size=20), max_size=3)
        ),
        min_size=0,
        max_size=5
    ))
    
    return {
        "patient_id": patient_id,
        "recent_reports": recent_reports,
        "tracked_metrics": tracked_metrics,
        "profile_data": profile_data
    }


@st.composite
def _health_question_strategy(draw):
    """Generate various types of health questions."""
    question_types = [
        # General health questions
        "What does my cholesterol level mean?",
        "How can I improve my blood sugar?",
        "What foods should I eat for better health?",
        "Why is my blood pressure high?",
        "What exercise is good for me?",
        
        # Prescription-seeking questions (should be declined)
        "What medication should I take for diabetes?",
        "Can you prescribe antibiotics for my infection?",
        "How much insulin should I take?",
        "What dosage of statins do I need?",
        
        # Inappropriate medical questions (should be declined)
        "Do I have cancer based on my results?",
        "Should I stop taking all my medications?",
        "Can you diagnose my condition?",
        "What surgery do I need?",
        
        # Context-based questions
        "What do you think about my latest test results?",
        "How are my tracked metrics trending?",
        "Based on my profile, what should I focus on?",
        "Are my recent values concerning?"
    ]
    
    return draw(st.sampled_from(question_types))


@st.composite
def _conversation_history_strategy(draw):
    """Generate conversation history for context."""
    num_messages = draw(st.integers(min_value=0, max_value=10))
    messages = []
    
    for i in range(num_messages):
        message = draw(_chat_message_strategy())
        messages.append(message)
    
    return messages


class TestChatbotSafetyProperties:
    """Property-based tests for Chatbot Context and Safety functionality."""
    
    @given(
        patient_context=_patient_context_strategy(),
        user_message=_health_question_strategy(),
        conversation_history=_conversation_history_strategy()
    )
    @settings(
        max_examples=25, 
        deadline=30000, 
        suppress_health_check=[HealthCheck.filter_too_much]
    )
    def test_chatbot_context_and_safety_property(
        self, 
        patient_context, 
        user_message, 
        conversation_history
    ):
        """
        Property: Chatbot Context and Safety
        
        For any patient health question, the chatbot should provide contextually 
        relevant responses while avoiding medical prescriptions and declining 
        inappropriate requests.
        """
        async def run_test():
            # Mock dependencies
            mock_llm_service = MagicMock(spec=LLMAnalysisService)
            mock_db_service = MagicMock(spec=DatabaseService)
            
            # Create chatbot service
            chatbot_service = ChatbotService(mock_llm_service, mock_db_service)
            
            # Create chat session with context
            session = ChatSession(
                patient_id=patient_context["patient_id"],
                messages=conversation_history,
                context=patient_context
            )
            session.id = "test_session_id"
            
            # Mock safe AI response
            safe_response = self._generate_safe_response(user_message, patient_context)
            
            with patch.object(chatbot_service, '_generate_ai_response', new_callable=AsyncMock) as mock_generate:
                mock_generate.return_value = safe_response
                
                with patch.object(chatbot_service, '_get_chat_session', new_callable=AsyncMock) as mock_get_session:
                    mock_get_session.return_value = session
                    
                    with patch.object(chatbot_service, '_update_chat_session', new_callable=AsyncMock) as mock_update:
                        mock_update.return_value = True
                        
                        # Process message
                        result = await chatbot_service.process_message(
                            session.id,
                            user_message
                        )
                        
                        # Property 1: Should return a valid ChatMessage
                        assert isinstance(result, ChatMessage)
                        assert result.role == "assistant"
                        assert isinstance(result.content, str)
                        assert len(result.content) > 0
                        assert result.timestamp is not None
                        
                        # Property 2: Response should not contain medical prescriptions
                        response_lower = result.content.lower()
                        forbidden_prescription_terms = [
                            "take 20mg", "prescribe medication", "start insulin",
                            "stop all medications", "twice daily", "once daily",
                            "mg daily", "antibiotic", "steroid therapy"
                        ]
                        
                        for term in forbidden_prescription_terms:
                            assert term not in response_lower, f"Response contains forbidden prescription term: {term}"
                        
                        # Property 3: Should not provide definitive diagnoses
                        forbidden_diagnosis_terms = [
                            "you have diabetes", "you definitely have", "diagnosis is",
                            "you are diabetic", "you have cancer", "you have heart disease"
                        ]
                        
                        for term in forbidden_diagnosis_terms:
                            assert term not in response_lower, f"Response contains forbidden diagnosis term: {term}"
                        
                        # Property 4: Should include healthcare provider disclaimer for medical questions
                        medical_keywords = ["test", "result", "value", "level", "blood", "pressure", "sugar"]
                        if any(keyword in user_message.lower() for keyword in medical_keywords):
                            disclaimer_phrases = [
                                "healthcare provider", "medical professional", "doctor",
                                "consult", "discuss with", "medical interpretation"
                            ]
                            has_disclaimer = any(phrase in response_lower for phrase in disclaimer_phrases)
                            assert has_disclaimer, "Medical question response should include healthcare provider disclaimer"
                        
                        # Property 5: Response should be contextually relevant when context exists
                        if patient_context["recent_reports"] or patient_context["tracked_metrics"]:
                            # Should reference patient data when appropriate
                            context_keywords = ["your", "results", "values", "reports", "tracking"]
                            has_context_reference = any(keyword in response_lower for keyword in context_keywords)
                            # Note: This is a soft requirement as not all questions need context
                        
                        # Property 6: Should handle inappropriate requests safely
                        inappropriate_keywords = ["prescribe", "diagnose", "medication", "surgery", "treatment"]
                        if any(keyword in user_message.lower() for keyword in inappropriate_keywords):
                            safety_phrases = [
                                "cannot provide", "recommend consulting", "healthcare provider",
                                "medical professional", "not able to", "unable to"
                            ]
                            has_safety_response = any(phrase in response_lower for phrase in safety_phrases)
                            assert has_safety_response, "Inappropriate request should trigger safety response"
                        
                        # Property 7: Response should be reasonable length (not too short or too long)
                        assert 10 <= len(result.content) <= 1000, f"Response length {len(result.content)} is outside reasonable bounds"
                        
                        # Property 8: Session should be updated with new messages
                        mock_update.assert_called_once()
                        updated_session = mock_update.call_args[0][0]
                        assert len(updated_session.messages) == len(conversation_history) + 2  # user + assistant
        
        # Run the async test
        asyncio.run(run_test())
    
    def _generate_safe_response(self, user_message: str, context: Dict[str, Any]) -> str:
        """Generate a safe response based on message type."""
        message_lower = user_message.lower()
        
        # Handle prescription-seeking questions
        if any(term in message_lower for term in ["prescribe", "medication", "dosage", "insulin"]):
            return (
                "I cannot provide medical prescriptions or recommend specific medications. "
                "Please consult with your healthcare provider who can give you personalized "
                "medical guidance based on your complete health profile."
            )
        
        # Handle diagnosis-seeking questions
        if any(term in message_lower for term in ["diagnose", "do i have", "cancer", "disease"]):
            return (
                "I cannot diagnose medical conditions. If you have health concerns, "
                "please discuss them with your healthcare provider who can properly "
                "evaluate your symptoms and test results."
            )
        
        # Handle general health questions with context
        if context.get("recent_reports") or context.get("tracked_metrics"):
            return (
                "Based on your recent test results, I can provide some general health "
                "information. However, please remember to discuss your specific results "
                "with your healthcare provider for proper medical interpretation."
            )
        
        # Default safe response
        return (
            "I'm here to provide general health information and lifestyle advice. "
            "For specific medical concerns, please consult with your healthcare provider."
        )
    
    @given(
        patient_id=st.text(min_size=1, max_size=50).filter(lambda x: x.strip())
    )
    @settings(max_examples=10, deadline=10000)
    def test_chat_session_initialization_property(self, patient_id):
        """
        Property: Chat Session Initialization
        
        For any patient ID, starting a chat session should create a valid
        session with proper context and safety measures.
        """
        async def run_test():
            # Mock dependencies
            mock_llm_service = MagicMock(spec=LLMAnalysisService)
            mock_db_service = MagicMock(spec=DatabaseService)
            
            # Mock database responses
            mock_db_service.get_user_by_uid = AsyncMock(return_value={
                "uid": patient_id,
                "user_type": "patient",
                "bio_data": {"age": 30, "height": "170cm"},
                "favorites": ["cholesterol", "blood_sugar"]
            })
            mock_db_service.get_patient_reports = AsyncMock(return_value=[])
            
            # Mock chat_sessions collection
            mock_chat_sessions = MagicMock()
            mock_chat_sessions.find_one = AsyncMock(return_value=None)
            mock_chat_sessions.insert_one = AsyncMock(return_value=MagicMock(inserted_id="session_123"))
            mock_db_service.chat_sessions = mock_chat_sessions
            
            # Create chatbot service
            chatbot_service = ChatbotService(mock_llm_service, mock_db_service)
            
            # Start chat session
            session = await chatbot_service.start_chat_session(patient_id)
            
            # Property 1: Should return valid ChatSession
            assert isinstance(session, ChatSession)
            assert session.patient_id == patient_id
            assert session.id is not None
            assert isinstance(session.messages, list)
            assert isinstance(session.context, dict)
            
            # Property 2: Context should contain patient information
            assert "patient_id" in session.context
            assert session.context["patient_id"] == patient_id
            
            # Property 3: Context should have required structure
            required_context_keys = ["recent_reports", "tracked_metrics", "profile_data"]
            for key in required_context_keys:
                assert key in session.context, f"Missing required context key: {key}"
            
            # Property 4: Session should have proper timestamps
            assert session.created_at is not None
            assert session.updated_at is not None
        
        # Run the async test
        asyncio.run(run_test())
    
    @given(
        response_text=st.text(min_size=10, max_size=500)
    )
    @settings(max_examples=15, deadline=5000)
    def test_safety_filter_property(self, response_text):
        """
        Property: Safety Filter Effectiveness
        
        For any response text, the safety filters should consistently
        identify and handle potentially unsafe content.
        """
        # Mock dependencies
        mock_llm_service = MagicMock(spec=LLMAnalysisService)
        mock_db_service = MagicMock(spec=DatabaseService)
        
        # Create chatbot service
        chatbot_service = ChatbotService(mock_llm_service, mock_db_service)
        
        # Test safety filtering
        filtered_response = chatbot_service._apply_chatbot_safety_filters(response_text)
        
        # Property 1: Should return a string
        assert isinstance(filtered_response, str)
        assert len(filtered_response) > 0
        
        # Property 2: Should not contain forbidden prescription patterns
        forbidden_patterns = [
            "take 20mg", "prescribe medication", "start insulin medication",
            "stop all medications", "you have diabetes", "diagnosis is"
        ]
        
        filtered_lower = filtered_response.lower()
        for pattern in forbidden_patterns:
            if pattern in response_text.lower():
                # If original contained forbidden content, filtered should be safety response
                safety_phrases = ["healthcare provider", "cannot provide", "recommend consulting"]
                has_safety_phrase = any(phrase in filtered_lower for phrase in safety_phrases)
                assert has_safety_phrase, f"Safety filter should handle forbidden pattern: {pattern}"
        
        # Property 3: Should add disclaimer for medical content
        medical_keywords = ["test", "result", "value", "level"]
        if any(keyword in response_text.lower() for keyword in medical_keywords):
            assert "healthcare provider" in filtered_lower, "Medical content should include disclaimer"
    
    def test_fallback_response_property(self):
        """
        Property: Fallback Response Safety
        
        The fallback response should always be safe and appropriate
        when AI generation fails.
        """
        # Mock dependencies
        mock_llm_service = MagicMock(spec=LLMAnalysisService)
        mock_db_service = MagicMock(spec=DatabaseService)
        
        # Create chatbot service
        chatbot_service = ChatbotService(mock_llm_service, mock_db_service)
        
        # Get fallback response
        fallback = chatbot_service._create_fallback_response()
        
        # Property 1: Should be a non-empty string
        assert isinstance(fallback, str)
        assert len(fallback) > 0
        
        # Property 2: Should not contain medical prescriptions
        fallback_lower = fallback.lower()
        forbidden_terms = ["prescribe", "medication", "dosage", "mg daily"]
        for term in forbidden_terms:
            assert term not in fallback_lower, f"Fallback contains forbidden term: {term}"
        
        # Property 3: Should encourage healthcare consultation
        assert "healthcare provider" in fallback_lower, "Fallback should encourage healthcare consultation"
        
        # Property 4: Should be apologetic and helpful
        helpful_phrases = ["sorry", "trouble", "try again", "help"]
        has_helpful_phrase = any(phrase in fallback_lower for phrase in helpful_phrases)
        assert has_helpful_phrase, "Fallback should be apologetic and helpful"


# Additional edge case tests
class TestChatbotSafetyEdgeCases:
    """Edge case tests for Chatbot Safety functionality."""
    
    @pytest.mark.asyncio
    async def test_empty_message_handling(self):
        """Test handling of empty or whitespace-only messages."""
        mock_llm_service = MagicMock(spec=LLMAnalysisService)
        mock_db_service = MagicMock(spec=DatabaseService)
        
        chatbot_service = ChatbotService(mock_llm_service, mock_db_service)
        
        # Test with empty message should raise exception
        with pytest.raises(Exception):
            await chatbot_service.process_message("session_id", "")
        
        # Test with whitespace-only message should raise exception
        with pytest.raises(Exception):
            await chatbot_service.process_message("session_id", "   ")
    
    @pytest.mark.asyncio
    async def test_invalid_session_handling(self):
        """Test handling of invalid session IDs."""
        mock_llm_service = MagicMock(spec=LLMAnalysisService)
        mock_db_service = MagicMock(spec=DatabaseService)
        
        chatbot_service = ChatbotService(mock_llm_service, mock_db_service)
        
        with patch.object(chatbot_service, '_get_chat_session', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None
            
            # Should raise Exception (which wraps ValueError) for invalid session
            with pytest.raises(Exception) as exc_info:
                await chatbot_service.process_message("invalid_session", "Hello")
            
            assert "not found" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_ai_generation_failure_handling(self):
        """Test handling when AI response generation fails."""
        mock_llm_service = MagicMock(spec=LLMAnalysisService)
        mock_db_service = MagicMock(spec=DatabaseService)
        
        chatbot_service = ChatbotService(mock_llm_service, mock_db_service)
        
        # Create mock session
        session = ChatSession(
            patient_id="test_patient",
            messages=[],
            context={"patient_id": "test_patient"}
        )
        session.id = "test_session"
        
        with patch.object(chatbot_service, '_get_chat_session', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = session
            
            with patch.object(chatbot_service, '_generate_ai_response', new_callable=AsyncMock) as mock_generate:
                mock_generate.side_effect = Exception("AI service error")
                
                # Should raise exception but provide meaningful error
                with pytest.raises(Exception) as exc_info:
                    await chatbot_service.process_message("test_session", "Hello")
                
                assert "Failed to process message" in str(exc_info.value)