from fastapi import APIRouter, Depends, HTTPException
from src.db.mongoWrapper import getMongo
from bson import ObjectId
from bson.json_util import dumps
import json

from src.auth.dependencies import get_current_user
from src.schemas import OnboardRequest

router = APIRouter()


# AUTH CHECK (ROLE + UID)
@router.get("/auth/me")
async def auth_me(current_user=Depends(get_current_user)):
    mongo = await getMongo()

    user = await mongo.find_one(
        "Users",
        {"uid": current_user["uid"]}
    )

    if not user:
        raise HTTPException(status_code=404, detail="User not onboarded")

    return {
        "uid": current_user["uid"],
        "email": current_user["email"],
        "role": user["user_type"]
    }


# CURRENT USER PROFILE
@router.get("/user/me")
async def read_me(current_user=Depends(get_current_user)):
    mongo = await getMongo()

    user = await mongo.find_one(
        "Users",
        {"uid": current_user["uid"]}
    )

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Sync email if it was missing in DB
    if not user.get("email"):
        await mongo.update_one(
            "Users",
            {"uid": current_user["uid"]},
            {"email": current_user["email"]}
        )
        user["email"] = current_user["email"]

    return {
        "uid": user["uid"],
        "email": user["email"],
        "user_type": user["user_type"],
        "name": user.get("name", ""),
        "hospital_name": user.get("hospital_name"),
        "BioData": user.get("BioData", {}),
        "Favorites": user.get("Favorites", [])        
    }


# USER CREATION (ONBOARD)
@router.post("/user")
async def upload_user(
    data: dict,
    current_user=Depends(get_current_user)
):
    mongo = await getMongo()

    user_type = data.get("user_type")
    if user_type not in ["patient", "institution"]:
        raise HTTPException(status_code=400, detail="Invalid user_type")

    # Prevent duplicate onboarding
    existing = await mongo.find_one("Users", {"uid": current_user["uid"]})
    if existing:
        return {
            "_id": str(existing["_id"]),
            "user_type": existing["user_type"]
        }

    # Base user document
    user_doc = {
        "uid": current_user["uid"],
        "email": current_user["email"],
        "user_type": user_type,
    }

    # Patient-specific fields
    if user_type == "patient":
        user_doc.update({
            "name": "",
            "BioData": {},
            "Favorites": [],
            "Reports": [],
        })

    # Institution-specific fields
    if user_type == "institution":
        hospital_name = data.get("hospital_name")

        if not hospital_name:
            raise HTTPException(
                status_code=400,
                detail="hospital_name is required for institution registration"
            )

        user_doc.update({
            "hospital_name": hospital_name
        })


    inserted_id = await mongo.insert_one("Users", user_doc)

    return {
        "_id": str(inserted_id),
        "user_type": user_type
    }


# UPDATE PATIENT PROFILE
@router.patch("/user/me")
async def update_me(
    data: dict,
    current_user=Depends(get_current_user)
):
    mongo = await getMongo()

    user = await mongo.find_one(
        "Users",
        {"uid": current_user["uid"]}
    )

    if not user or user.get("user_type")!= "patient":
        raise HTTPException(
            status_code=403,
            detail="Only patients can update profile"
        )

    update_doc = {}

    if "name" in data:
        update_doc["name"] = data.pop("name")

    if data:
        update_doc["BioData"] = data

    await mongo.update_one(
        "Users",
        {"uid": current_user["uid"]},
        update_doc
    )

    return {"status": "updated"}


# FAVORITES MANAGEMENT
@router.post("/user/favorites")
async def add_favorite_marker(
    data: dict,
    current_user=Depends(get_current_user)
):
    import re
    
    mongo = await getMongo()
    
    user = await mongo.find_one(
        "Users",
        {"uid": current_user["uid"], "user_type": "patient"}
    )
    
    if not user:
        raise HTTPException(status_code=404, detail="Patient user not found")
    
    marker = data.get("marker", "").strip()
    if not marker:
        raise HTTPException(status_code=400, detail="Marker name is required")
    
    # Sanitize marker: convert to title case, remove extra spaces, normalize characters
    marker = re.sub(r'\s+', ' ', marker.strip())  # Replace multiple spaces with single space
    marker = marker.title()  # Convert to title case (e.g., "hemoglobin a1c" -> "Hemoglobin A1c")
    marker = re.sub(r'[^a-zA-Z0-9\s\-_()]', '', marker)  # Remove special characters except spaces, hyphens, underscores, parentheses
    marker = marker.strip()  # Remove leading/trailing spaces again
    
    if not marker:
        raise HTTPException(status_code=400, detail="Invalid marker name after sanitization")
    
    print(f"Adding marker: '{marker}' for user: {current_user['uid']}")
    
    # Add to favorites if not already present (case-insensitive check)
    current_favorites = user.get("Favorites", [])
    normalized_marker = marker.lower()
    existing_normalized = [fav.lower() for fav in current_favorites]
    
    if normalized_marker not in existing_normalized:
        result = await mongo.update_one(
            "Users",
            {"uid": current_user["uid"]},
            {"$addToSet": {"Favorites": marker}},
            raw=True
        )
        print(f"MongoDB update result: {result}")
    
    # Return updated favorites
    updated_user = await mongo.find_one("Users", {"uid": current_user["uid"]})
    favorites = updated_user.get("Favorites", []) if updated_user else current_favorites
    print(f"Updated favorites: {favorites}")
    
    return {"favorites": favorites}


@router.delete("/user/favorites")
async def remove_favorite_marker(
    data: dict,
    current_user=Depends(get_current_user)
):
    import re
    
    mongo = await getMongo()
    
    user = await mongo.find_one(
        "Users",
        {"uid": current_user["uid"], "user_type": "patient"}
    )
    
    if not user:
        raise HTTPException(status_code=404, detail="Patient user not found")
    
    marker = data.get("marker", "").strip()
    if not marker:
        raise HTTPException(status_code=400, detail="Marker name is required")
    
    # Sanitize marker the same way as in add
    marker = re.sub(r'\s+', ' ', marker.strip())
    marker = marker.title()
    marker = re.sub(r'[^a-zA-Z0-9\s\-_()]', '', marker)
    marker = marker.strip()
    
    if not marker:
        raise HTTPException(status_code=400, detail="Invalid marker name after sanitization")
    
    print(f"Removing marker: '{marker}' for user: {current_user['uid']}")
    
    # Remove from favorites (case-insensitive matching)
    # First, get current favorites and remove manually
    user_favorites = user.get("Favorites", [])
    normalized_marker = marker.lower()
    updated_favorites = [fav for fav in user_favorites if fav.lower() != normalized_marker]
    
    result = await mongo.update_one(
        "Users",
        {"uid": current_user["uid"]},
        {"$set": {"Favorites": updated_favorites}},
        raw=True
    )
    print(f"MongoDB delete result: {result}")
    
    # Return updated favorites
    updated_user = await mongo.find_one("Users", {"uid": current_user["uid"]})
    favorites = updated_user.get("Favorites", []) if updated_user else []
    print(f"Updated favorites after removal: {favorites}")
    
    return {"favorites": favorites}


# GET USER FAVORITES
@router.get("/user/favorites")
async def get_user_favorites(current_user=Depends(get_current_user)):
    mongo = await getMongo()
    user = await mongo.find_one("Users", {"uid": current_user["uid"]})
    favorites = user.get("Favorites", []) if user else []
    return {"favorites": favorites}


# GET USER BY OBJECT ID
@router.get("/user/{user_id}")
async def get_user(user_id: str):
    mongo = await getMongo()
    user = await mongo.find_one("Users", {"_id": ObjectId(user_id)})
    return json.loads(dumps(user))



# HOSPITAL → APPROVED PATIENTS
@router.get("/hospital/patients")
async def get_hospital_patients(
    current_user=Depends(get_current_user)
):
    mongo = await getMongo()

    # Ensure caller is a hospital
    hospital = await mongo.find_one(
        "Users",
        {"uid": current_user["uid"], "user_type": "institution"}
    )

    if not hospital:
        return []

    # Fetch approved access requests
    requests = await mongo.find_many(
        "AccessRequests",
        {
            "hospital_uid": current_user["uid"],
            "status": "approved"
        }
    )

    patient_emails = [r["patient_email"] for r in requests]

    if not patient_emails:
        return []

    # Fetch patient user records
    patients = await mongo.find_many(
        "Users",
        {
            "user_type": "patient",
            "email": {"$in": patient_emails}
        }
    )

    # Convert ObjectId → string for frontend
    for p in patients:
        p["_id"] = str(p["_id"])

    print("FETCH HOSPITAL UID:", current_user["uid"])

    return patients



# HOSPITAL → VIEW A SPECIFIC PATIENT (READ ONLY)
@router.get("/hospital/patient/{patient_uid}")
async def get_patient_for_hospital(
    patient_uid: str,
    current_user=Depends(get_current_user)
):
    mongo = await getMongo()

    # 1. Ensure requester is a hospital
    hospital = await mongo.find_one(
        "Users",
        {"uid": current_user["uid"], "user_type": "institution"}
    )
    if not hospital:
        raise HTTPException(status_code=403, detail="Not a hospital")

    # 2. Get patient user
    patient = await mongo.find_one(
        "Users",
        {"uid": patient_uid, "user_type": "patient"}
    )
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # 3. Check approved access
    access = await mongo.find_one(
        "AccessRequests",
        {
            "hospital_uid": current_user["uid"],
            "patient_email": patient["email"],
            "status": "approved"
        }
    )
    if not access:
        raise HTTPException(status_code=403, detail="Access not approved")

    # 4. Return patient data (safe fields only)
    patient["_id"] = str(patient["_id"])

    return {
        "uid": patient["uid"],
        "email": patient.get("email"),
        "name": patient.get("name", ""),
        "BioData": patient.get("BioData", {}),
        "Reports": patient.get("Reports", [])
    }