from fastapi import APIRouter
from src.db.mongoWrapper import getMongo
from typing import Any, Dict, List, Optional
from bson import ObjectId
import json
from bson.json_util import dumps
from datetime import datetime

from src.llm_agent import LLMReportAgent
from src.schemas import ReportModel

router = APIRouter(prefix="/api")


@router.get("/LLMReport/{report_id}")
async def get_report(report_id: str):
  mongo = await getMongo()
  report = await mongo.find_one("LLMReports", {"_id": ObjectId(report_id)})
  return json.loads(dumps(report)) 


@router.post("/LLMReport")
async def upload_report(report: ReportModel):
  mongo = await getMongo()

  patient_id = report.model_dump().get("patient_id")
  payload = report.model_dump()

  selected_concerns = payload.get("selected_concerns") or []
  has_attributes = bool(payload.get("Attributes"))
  
  report_id = payload.get("report_id")
  time = payload.get("time") or datetime.utcnow().isoformat()

  
  # CASE 1: User is only selecting concern options (no LLM generation)
  if selected_concerns and not has_attributes:
      try:
          user_obj_id = ObjectId(patient_id)
          await mongo.update_one(
              "Users",
              {"_id": user_obj_id},
              {
                  "$addToSet": {
                      "Favorites": {
                          "$each": selected_concerns
                      }
                  }
              }
          )
      except Exception as e:
          return {"error": "failed_to_update_favorites", "message": str(e)}

      return {
          "status": "favorites_updated",
          "favorites_added": selected_concerns
      }

  user = None
  if patient_id:
    try:
      user = await mongo.find_one("Users", {"_id": ObjectId(patient_id)})
    except Exception:
      user = None

  if user:
    favorites = user.get("Favorites") or []
    biodata = user.get("BioData") or {}
  else:
    favorites = []
    biodata = {}

  
  input_parsed = payload.get("Attributes")
  # CASE 2: LLM generation requires Attributes
  if not has_attributes:
      return {"error": "Invalid request: no Attributes or selected_concerns provided"}


  try:
    agent = LLMReportAgent()
    agent_input = {
      "report_id": report_id,
      "patient_id": patient_id,
      "time": time,
      "input": input_parsed,
      "favorites": favorites,
      "biodata": biodata,
    }
    analysis = await agent.analyze(agent_input)

  except Exception as e:
    analysis = {"error": "agent_failed", "message": str(e)}

  llm_doc = {
    "patient_id": patient_id,
    "report_id": report_id,
    "time":datetime.utcnow().isoformat(),
    "output": analysis,
    "input" : input_parsed,
  }

  llm_inserted = await mongo.insert_one("LLMReports", llm_doc)

  # adding llm report id to report document
  try:
    if report_id:
      await mongo.update_one("Reports", {"_id": ObjectId(report_id)}, {"llm_report_id": llm_inserted})
  except Exception:
    pass

  return {"llm_report_id": llm_inserted, "analysis": analysis}

