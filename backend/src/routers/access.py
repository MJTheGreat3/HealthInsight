from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from bson import ObjectId
from src.db.mongoWrapper import getMongo
from src.auth.dependencies import get_current_user

router = APIRouter(prefix="/api/access")

# Hospital → request access
@router.post("/request")
async def request_access(data: dict, current_user=Depends(get_current_user)):
    mongo = await getMongo()

    # Ensure requester is a hospital
    hospital = await mongo.find_one(
        "Users",
        {"uid": current_user["uid"], "user_type": "institution"},
    )
    if not hospital:
        raise HTTPException(403, "Only hospitals can request access")

    if not data.get("email"):
        raise HTTPException(400, "Patient email required")

    doc = {
        "hospital_uid": current_user["uid"],
        "patient_email": data["email"],
        "status": "pending",
        "created_at": datetime.utcnow(),
    }

    await mongo.insert_one("AccessRequests", doc)
    return {"status": "pending"}


# Patient → list ALL access requests (pending / approved / revoked)
@router.get("/my-requests")
async def my_requests(current_user=Depends(get_current_user)):
    mongo = await getMongo()

    requests = await mongo.find_many(
        "AccessRequests",
        {"patient_email": current_user["email"]},
    )

    response = []

    for r in requests:
        hospital = await mongo.find_one(
            "Users",
            {
                "uid": r["hospital_uid"],
                "user_type": "institution",
            }
        )

        response.append({
            "_id": str(r["_id"]),
            "status": r.get("status"),
            "created_at": r.get("created_at"),
            "hospital_uid": r.get("hospital_uid"),
            "hospital_name": hospital.get("hospital_name") if hospital else None,
            "hospital_email": hospital.get("email") if hospital else None,
        })

    return response


# Patient → approve / reject / revoke
@router.post("/respond")
async def respond_request(data: dict, current_user=Depends(get_current_user)):
    mongo = await getMongo()

    request_id = data.get("request_id")
    action = data.get("action")

    if action not in ["approve", "reject", "revoke"]:
        raise HTTPException(400, "Invalid action")

    request = await mongo.find_one(
        "AccessRequests",
        {
            "_id": ObjectId(request_id),
            "patient_email": current_user["email"],
        },
    )

    if not request:
        raise HTTPException(404, "Request not found")

    if action == "approve":
        status = "approved"
    elif action == "reject":
        status = "rejected"
    elif action == "revoke":
        if request["status"] != "approved":
            raise HTTPException(400, "Only approved access can be revoked")
        status = "revoked"

    # Update request status
    await mongo.update_one(
        "AccessRequests",
        {"_id": ObjectId(request_id)},
        {
            "status": status,
            "updated_at": datetime.utcnow(),
        },
    )

    # IF APPROVED → LINK PATIENT TO HOSPITAL
    if action == "approve":
        await mongo.update_one(
            "Users",
            {"uid": request["hospital_uid"]},
            {"$addToSet": {"patient_list": current_user["uid"]}},
            raw=True,
        )

    # IF REVOKED → UNLINK PATIENT FROM HOSPITAL
    if action == "revoke":
        await mongo.update_one(
            "Users",
            {"uid": request["hospital_uid"]},
            {"$pull": {"patient_list": current_user["uid"]}},
            raw=True,
        )

    return {"status": status}


# Patient → list hospitals with ACTIVE access
@router.get("/active")
async def active_access(current_user=Depends(get_current_user)):
    mongo = await getMongo()

    requests = await mongo.find_many(
        "AccessRequests",
        {
            "patient_email": current_user["email"],
            "status": "approved",
        },
    )

    response = []

    for r in requests:
        hospital = await mongo.find_one(
            "Users",
            {
                "uid": r["hospital_uid"],
                "user_type": "institution",
            }
        )

        response.append({
            "request_id": str(r["_id"]),
            "hospital_uid": r["hospital_uid"],
            "hospital_name": hospital.get("hospital_name") if hospital else None,
            "hospital_email": hospital.get("email") if hospital else None,
            "approved_at": r.get("updated_at") or r.get("created_at"),
        })

    return response