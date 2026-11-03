from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from app.models.schemas import EligibilityCheckRequest
from app.services.database import get_db, in_memory_store
from rag.eligibility.engine import eligibility_engine

router = APIRouter(prefix="/eligibility", tags=["Eligibility Engine"])

@router.post("/check")
async def check_eligibility(req: EligibilityCheckRequest):
    profile = req.profile
    scheme_id = req.schemeId
    db = get_db()

    # Load schemes
    all_schemes = []
    if db is not None:
        try:
            cursor = db.schemes.find({})
            async for s in cursor:
                s["id"] = str(s["_id"])
                all_schemes.append(s)
        except Exception:
            pass

    if not all_schemes:
        all_schemes = list(in_memory_store["schemes"].values())

    if scheme_id:
        target = [s for s in all_schemes if str(s.get("id")) == str(scheme_id) or str(s.get("_id")) == str(scheme_id)]
        if not target:
            raise HTTPException(status_code=404, detail="Target scheme not found for eligibility evaluation.")
        result = eligibility_engine.evaluate_scheme(profile, target[0])
        return {"results": {scheme_id: result}}

    results = eligibility_engine.evaluate_all(profile, all_schemes)
    return {"results": results}
