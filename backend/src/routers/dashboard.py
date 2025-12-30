from fastapi import APIRouter, Depends
from bson import ObjectId
from src.db.mongoWrapper import getMongo
from src.auth.dependencies import get_current_user
from src.llm_agent import LLMReportAgent

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/actionable-suggestions")
async def get_actionable_suggestions(current_user=Depends(get_current_user)):
    mongo = await getMongo()
    user_id = current_user["uid"]

    # Fetch Up TO last 5 reports (not exactly 5)
    reports = await mongo.find_many(
        "Reports",
        {"patient_id": user_id}
    )

    # Sort in Python (newest first)
    reports = sorted(
        reports,
        key=lambda r: r.get("time", ""),
        reverse=True
    )[:5]


    # Case: No reports at all
    if not reports:
        return {
            "actionable_suggestions": [],
            "note": "No reports available yet"
        }

    # Fetch corresponding LLM outputs
    report_ids = [r["_id"] for r in reports]

    llm_reports = await mongo.find_many(
        "LLMReports",
        {"report_id": {"$in": report_ids}}
    )

    llm_map = {
        r["report_id"]: r
        for r in llm_reports
    }

    # Prepare meta-input
    meta_input = {
        "report_count": 0,
        "reports": []
    }

    for r in reports:  # already sorted newest → oldest
        llm = llm_map.get(r["_id"])
        if not llm:
            continue

        meta_input["reports"].append({
            "report_id": str(r["_id"]),
            "time": r.get("time"),
            "analysis": llm.get("output")
        })

    meta_input["report_count"] = len(meta_input["reports"])

    if meta_input["report_count"] == 0:
        return {
            "actionable_suggestions": [],
            "note": "Reports uploaded but analysis pending"
        }

    
    # Call meta-LLM (works for 1–5 reports)
    agent = LLMReportAgent()
    result = await agent.generate_actionable_suggestions(meta_input)

    return result
