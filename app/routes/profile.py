from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends
from bson import ObjectId
from app.models.schemas import CitizenProfileSchema
from app.services.database import get_db, in_memory_store
from app.middleware.auth_middleware import get_current_user

router = APIRouter(prefix="/profile", tags=["Citizen Profile"])

@router.get("")
async def get_profile(current_user: dict = Depends(get_current_user)):
    user_id = current_user.get("id") or str(current_user.get("_id"))
    db = get_db()

    profile = None
    if db is not None:
        try:
            profile = await db.profiles.find_one({"userId": user_id})
            if profile:
                profile["id"] = str(profile["_id"])
                profile.pop("_id", None)
        except Exception:
            profile = in_memory_store["profiles"].get(user_id)
    else:
        profile = in_memory_store["profiles"].get(user_id)

    return {"profile": profile}

@router.post("")
@router.put("")
async def save_profile(profile_data: CitizenProfileSchema, current_user: dict = Depends(get_current_user)):
    user_id = current_user.get("id") or str(current_user.get("_id"))
    db = get_db()

    profile_dict = profile_data.model_dump()
    profile_dict["userId"] = user_id
    profile_dict["updatedAt"] = datetime.now(timezone.utc)

    if db is not None:
        try:
            await db.profiles.update_one(
                {"userId": user_id},
                {"$set": profile_dict},
                upsert=True
            )
            saved = await db.profiles.find_one({"userId": user_id})
            if saved:
                saved["id"] = str(saved["_id"])
                saved.pop("_id", None)
                return {"message": "Profile saved successfully.", "profile": saved}
        except Exception as e:
            pass

    # In-memory update
    in_memory_store["profiles"][user_id] = profile_dict
    return {"message": "Profile saved successfully.", "profile": profile_dict}
