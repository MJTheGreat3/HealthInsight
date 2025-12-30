from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from src.auth.dependencies import get_current_user
from src.llm_agent import LLMReportAgent
from src.db.mongoWrapper import getMongo
from src.llm_chat import generate_chat_response
from bson import ObjectId

router = APIRouter(prefix="/api", tags=["Chat"])

class ChatMessage(BaseModel):
  from_user: str
  text: str

class ChatRequest(BaseModel):
  message: str
  user_id: str
  conversation_history: Optional[List[dict]] = []
  # added 
  report_id: str

class ChatResponse(BaseModel):
  response: str
  timestamp: str

@router.post("/chat", response_model=ChatResponse)
async def chat_with_ai(
  request: ChatRequest,
  current_user=Depends(get_current_user)
):
  """
    Chat endpoint for interacting with LLM about health reports
    """
  try:
    #   # Verify the user_id matches current user
    if request.user_id != current_user["uid"]:
        raise HTTPException(status_code=403, detail="Unauthorized")


    # Prepare context from conversation history
    context = {
      "user_id": current_user["uid"],
      "user_email": current_user["email"],
      "current_message": request.message,
      "conversation_history": request.conversation_history or [],
    }

    # Fetch user's recent reports for context
    mongo = await getMongo()
    user_report = await mongo.find_one("LLMReports", {"_id": ObjectId(request.report_id)})

    if user_report:
      context["medical_report"] = user_report.get('input', '')
      context["suggestion_list"] = user_report.get('output', '')
      # Generate response using LLM agent
      # For now, we'll use a simple chat response
      # In production, this would integrate with the LLM agent's chat capabilities

      # Simple rule-based responses for common health questions
      # response = generate_health_response(request.message, context)
      print(context)
      response = generate_chat_response(context)
      from datetime import datetime, UTC
      timestamp = datetime.now(UTC).isoformat()

      return ChatResponse(
        response=response,
        timestamp=timestamp
      )
    
    else : 
      from datetime import datetime, UTC
      timestamp = datetime.now(UTC).isoformat()
      return ChatResponse(
        response="You have not uploaded any medical reports yet. Please upload your reports to have personalized query responses on analysis.",
        timestamp=timestamp
      )

  except Exception as e:
    raise HTTPException(
      status_code=500,
      detail=f"Chat service error: {str(e)}"
    )

