"""
Chatbot Service for context-aware health conversations.

This service provides AI-powered chatbot functionality that uses patient medical history
and test results to provide contextual health information without medical prescriptions.
"""

import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from app.models.chat import ChatMessage, ChatSession
from app.models.user import PatientModel
from app.services.llm_analysis import LLMAnalysisService
from app.services.database import DatabaseService

logger = logging.getLogger(__name__)


class ChatbotService:
    """Service for managing AI-powered health conversations."""
    
    def __init__(self, llm_service: LLMAnalysisService, db_service: DatabaseService):
        """Initialize the Chatbot Service."""
        self.llm_service = llm_service
        self.db_service = db_service
        self.max_context_messages = 10  # Keep last 10 messages for context
        self.max_reports_context = 3    # Use last 3 reports for context
    
    async def start_chat_session(self, patient_id: str) -> ChatSession:
        """
        Start a new chat session or retrieve existing active session.
        
        Args:
            patient_id: Unique patient identifier
            
        Returns:
            ChatSession object with initialized context
        """
        try:
            # Check for existing active session (within last 24 hours)
            existing_session = await self._get_active_session(patient_id)
            if existing_session:
                logger.info(f"Retrieved existing chat session for patient {patient_id}")
                return existing_session
            
            # Create new session with context
            context = await self._build_patient_context(patient_id)
            
            new_session = ChatSession(
                patient_id=patient_id,
                messages=[],
                context=context
            )
            
            # Save to database
            session_id = await self._save_chat_session(new_session)
            new_session.id = session_id
            
            logger.info(f"Created new chat session {session_id} for patient {patient_id}")
            return new_session
            
        except Exception as e:
            logger.error(f"Failed to start chat session for patient {patient_id}: {str(e)}")
            raise Exception(f"Failed to start chat session: {str(e)}")
    
    async def process_message(
        self, 
        session_id: str, 
        user_message: str
    ) -> ChatMessage:
        """
        Process user message and generate AI response.
        
        Args:
            session_id: Chat session identifier
            user_message: User's message content
            
        Returns:
            ChatMessage with AI assistant response
        """
        try:
            # Get chat session
            session = await self._get_chat_session(session_id)
            if not session:
                raise ValueError(f"Chat session {session_id} not found")
            
            # Add user message to session
            user_msg = ChatMessage(
                role="user",
                content=user_message,
                timestamp=datetime.utcnow()
            )
            session.messages.append(user_msg)
            
            # Generate AI response
            ai_response = await self._generate_ai_response(session, user_message)
            
            # Add AI response to session
            ai_msg = ChatMessage(
                role="assistant",
                content=ai_response,
                timestamp=datetime.utcnow()
            )
            session.messages.append(ai_msg)
            
            # Update session in database
            await self._update_chat_session(session)
            
            logger.info(f"Processed message in session {session_id}")
            return ai_msg
            
        except Exception as e:
            logger.error(f"Failed to process message in session {session_id}: {str(e)}")
            raise Exception(f"Failed to process message: {str(e)}")
    
    async def get_chat_history(self, session_id: str) -> List[ChatMessage]:
        """
        Get chat history for a session.
        
        Args:
            session_id: Chat session identifier
            
        Returns:
            List of ChatMessage objects
        """
        try:
            session = await self._get_chat_session(session_id)
            if not session:
                return []
            
            return session.messages
            
        except Exception as e:
            logger.error(f"Failed to get chat history for session {session_id}: {str(e)}")
            return []
    
    async def end_chat_session(self, session_id: str) -> bool:
        """
        End a chat session and clean up resources.
        
        Args:
            session_id: Chat session identifier
            
        Returns:
            True if session was ended successfully
        """
        try:
            # Update session with end timestamp
            session = await self._get_chat_session(session_id)
            if session:
                session.updated_at = datetime.utcnow()
                await self._update_chat_session(session)
            
            logger.info(f"Ended chat session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to end chat session {session_id}: {str(e)}")
            return False
    
    async def _get_active_session(self, patient_id: str) -> Optional[ChatSession]:
        """Get active chat session for patient (within last 24 hours)."""
        try:
            # Query database for recent session
            from datetime import timedelta
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            
            session_data = await self.db_service.chat_sessions.find_one({
                "patient_id": patient_id,
                "updated_at": {"$gte": cutoff_time}
            }, sort=[("updated_at", -1)])
            
            if session_data:
                session_data["_id"] = str(session_data["_id"])
                return ChatSession(**session_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get active session for patient {patient_id}: {str(e)}")
            return None
    
    async def _build_patient_context(self, patient_id: str) -> Dict[str, Any]:
        """Build context from patient's medical history and profile."""
        try:
            context = {
                "patient_id": patient_id,
                "recent_reports": [],
                "tracked_metrics": [],
                "profile_data": {}
            }
            
            # Get patient profile
            patient_data = await self.db_service.get_user_by_uid(patient_id)
            if patient_data and patient_data.get("user_type") == "patient":
                context["profile_data"] = patient_data.get("bio_data", {})
                context["tracked_metrics"] = patient_data.get("favorites", [])
            
            # Get recent reports
            recent_reports = await self.db_service.get_patient_reports(
                patient_id, 
                limit=self.max_reports_context
            )
            
            # Simplify report data for context
            for report in recent_reports:
                simplified_report = {
                    "date": report.get("processed_at"),
                    "concerning_values": [],
                    "normal_values": []
                }
                
                attributes = report.get("attributes", {})
                for key, metric in attributes.items():
                    metric_info = {
                        "name": metric.get("name", key),
                        "value": metric.get("value"),
                        "verdict": metric.get("verdict")
                    }
                    
                    if metric.get("verdict") in ["HIGH", "LOW", "CRITICAL"]:
                        simplified_report["concerning_values"].append(metric_info)
                    else:
                        simplified_report["normal_values"].append(metric_info)
                
                context["recent_reports"].append(simplified_report)
            
            return context
            
        except Exception as e:
            logger.error(f"Failed to build context for patient {patient_id}: {str(e)}")
            return {"patient_id": patient_id}
    
    async def _generate_ai_response(self, session: ChatSession, user_message: str) -> str:
        """Generate AI response using LLM service with context."""
        try:
            # Build conversation context
            recent_messages = session.messages[-self.max_context_messages:]
            conversation_history = []
            
            for msg in recent_messages:
                conversation_history.append({
                    "role": msg.role,
                    "content": msg.content
                })
            
            # Create chatbot prompt
            prompt = self._create_chatbot_prompt(
                user_message,
                session.context,
                conversation_history
            )
            
            # Call LLM service
            response = await self.llm_service._call_openai_api(prompt)
            
            # Parse and filter response
            parsed_response = self._parse_chatbot_response(response)
            
            return parsed_response
            
        except Exception as e:
            logger.error(f"Failed to generate AI response: {str(e)}")
            return self._create_fallback_response()
    
    def _create_chatbot_prompt(
        self,
        user_message: str,
        context: Dict[str, Any],
        conversation_history: List[Dict[str, str]]
    ) -> str:
        """Create prompt for chatbot conversation."""
        
        # Build context summary
        context_summary = ""
        
        if context.get("recent_reports"):
            context_summary += "\nRECENT TEST RESULTS:\n"
            for i, report in enumerate(context["recent_reports"][:2]):  # Last 2 reports
                context_summary += f"Report {i+1} ({report.get('date', 'Unknown date')}):\n"
                
                if report.get("concerning_values"):
                    context_summary += "  Concerning values:\n"
                    for value in report["concerning_values"][:3]:  # Top 3 concerning
                        context_summary += f"    - {value['name']}: {value['value']} ({value['verdict']})\n"
                
                if report.get("normal_values"):
                    context_summary += f"  Normal values: {len(report['normal_values'])} metrics in normal range\n"
        
        if context.get("tracked_metrics"):
            context_summary += f"\nTRACKED METRICS: {', '.join(context['tracked_metrics'][:5])}\n"
        
        if context.get("profile_data"):
            profile = context["profile_data"]
            context_summary += f"\nPATIENT PROFILE:\n"
            if profile.get("age"):
                context_summary += f"  Age: {profile['age']}\n"
            if profile.get("height"):
                context_summary += f"  Height: {profile['height']}\n"
            if profile.get("weight"):
                context_summary += f"  Weight: {profile['weight']}\n"
        
        # Build conversation history
        history_text = ""
        if conversation_history:
            history_text = "\nCONVERSATION HISTORY:\n"
            for msg in conversation_history[-5:]:  # Last 5 messages
                history_text += f"{msg['role'].title()}: {msg['content'][:100]}...\n"
        
        prompt = f"""
You are a helpful health assistant chatbot. You have access to the patient's medical history and test results.

IMPORTANT GUIDELINES:
- Provide general health information and lifestyle advice
- Reference the patient's test results and trends when relevant
- DO NOT provide medical prescriptions or diagnose conditions
- DO NOT recommend specific medications or treatments
- Suggest consulting healthcare providers for medical concerns
- Be supportive, encouraging, and informative
- If asked about concerning test results, explain what they might indicate generally
- Focus on lifestyle modifications, nutrition, and wellness advice

{context_summary}
{history_text}

CURRENT USER MESSAGE: {user_message}

Provide a helpful, contextual response that references relevant information from the patient's medical history when appropriate. Keep responses conversational and supportive.
"""
        
        return prompt
    
    def _parse_chatbot_response(self, response: str) -> str:
        """Parse and filter chatbot response for safety."""
        try:
            # Apply basic safety filtering
            filtered_response = self._apply_chatbot_safety_filters(response)
            
            # Ensure response is not too long
            if len(filtered_response) > 1000:
                filtered_response = filtered_response[:997] + "..."
            
            return filtered_response
            
        except Exception as e:
            logger.error(f"Failed to parse chatbot response: {str(e)}")
            return self._create_fallback_response()
    
    def _apply_chatbot_safety_filters(self, response: str) -> str:
        """Apply safety filters to prevent medical prescriptions."""
        import re
        
        # Define forbidden patterns
        forbidden_patterns = [
            r'\btake\s+\d+\s*mg\b',  # "take 20mg"
            r'\bprescribe\s+\w+\b',  # "prescribe medication"
            r'\bstart\s+\w+\s+medication\b',  # "start insulin medication"
            r'\bstop\s+all\s+medications?\b',  # "stop all medications"
            r'\byou\s+have\s+\w+\s+disease\b',  # "you have diabetes"
            r'\byou\s+definitely\s+have\b',  # "you definitely have"
            r'\bdiagnosis\s+is\b',  # "diagnosis is"
        ]
        
        # Check for forbidden content
        response_lower = response.lower()
        for pattern in forbidden_patterns:
            if re.search(pattern, response_lower):
                logger.warning(f"Filtered chatbot response containing: {pattern}")
                return self._create_safety_response()
        
        # Add disclaimer if discussing test results
        if any(word in response_lower for word in ["test", "result", "value", "level"]):
            response += "\n\nPlease remember to discuss your test results with your healthcare provider for proper medical interpretation."
        
        return response
    
    def _create_safety_response(self) -> str:
        """Create safe response when content is filtered."""
        return (
            "I understand you're looking for health information. While I can provide general "
            "wellness advice based on your test results, I recommend discussing specific "
            "medical concerns with your healthcare provider who can give you personalized "
            "medical guidance. Is there anything else about general health and wellness "
            "I can help you with?"
        )
    
    def _create_fallback_response(self) -> str:
        """Create fallback response when AI generation fails."""
        return (
            "I'm sorry, I'm having trouble processing your request right now. "
            "For any health concerns, please consult with your healthcare provider. "
            "You can also try asking your question again in a moment."
        )
    
    async def _save_chat_session(self, session: ChatSession) -> str:
        """Save chat session to database."""
        try:
            session_dict = session.model_dump(exclude={"id"})
            result = await self.db_service.chat_sessions.insert_one(session_dict)
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Failed to save chat session: {str(e)}")
            raise
    
    async def _get_chat_session(self, session_id: str) -> Optional[ChatSession]:
        """Get chat session from database."""
        try:
            from bson import ObjectId
            
            if not ObjectId.is_valid(session_id):
                return None
            
            session_data = await self.db_service.chat_sessions.find_one({
                "_id": ObjectId(session_id)
            })
            
            if session_data:
                session_data["_id"] = str(session_data["_id"])
                return ChatSession(**session_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get chat session {session_id}: {str(e)}")
            return None
    
    async def _update_chat_session(self, session: ChatSession) -> bool:
        """Update chat session in database."""
        try:
            from bson import ObjectId
            
            if not session.id or not ObjectId.is_valid(session.id):
                return False
            
            session.updated_at = datetime.utcnow()
            session_dict = session.model_dump(exclude={"id"})
            
            result = await self.db_service.chat_sessions.update_one(
                {"_id": ObjectId(session.id)},
                {"$set": session_dict}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Failed to update chat session: {str(e)}")
            return False


# Global service instance will be initialized in main.py
chatbot_service: Optional[ChatbotService] = None


def initialize_chatbot_service(llm_service: LLMAnalysisService, db_service: DatabaseService) -> ChatbotService:
    """Initialize the global chatbot service instance."""
    global chatbot_service
    chatbot_service = ChatbotService(llm_service, db_service)
    return chatbot_service