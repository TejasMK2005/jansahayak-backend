from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from bson import ObjectId
from app.services.database import get_db, in_memory_store

router = APIRouter(prefix="/schemes", tags=["Government Schemes"])

@router.get("")
async def list_schemes(
    category: Optional[str] = None,
    state: Optional[str] = None,
    occupation: Optional[str] = None,
    search: Optional[str] = None
):
    db = get_db()
    all_schemes = []

    if db is not None:
        try:
            cursor = db.schemes.find({})
            async for doc in cursor:
                doc["id"] = str(doc["_id"])
                doc.pop("_id", None)
                all_schemes.append(doc)
        except Exception:
            pass

    if not all_schemes:
        all_schemes = list(in_memory_store["schemes"].values())

    # Apply filters
    filtered = all_schemes
    if category and category != "All":
        filtered = [s for s in filtered if category.lower() in s.get("category", "").lower()]
    if state and state != "All":
        filtered = [s for s in filtered if s.get("state") in [state, "All India"]]
    if occupation and occupation != "All":
        filtered = [
            s for s in filtered
            if "All" in s.get("eligibilityRules", {}).get("eligibleOccupations", ["All"]) or
            any(occupation.lower() in o.lower() for o in s.get("eligibilityRules", {}).get("eligibleOccupations", []))
        ]
    if search:
        q = search.lower()
        filtered = [
            s for s in filtered
            if q in s.get("schemeName", "").lower() or
            q in s.get("description", "").lower() or
            q in s.get("governmentDepartment", "").lower()
        ]

    return {"count": len(filtered), "schemes": filtered}

@router.get("/{scheme_id}")
async def get_scheme_by_id(scheme_id: str):
    db = get_db()
    scheme = None

    if db is not None:
        try:
            scheme = await db.schemes.find_one({"_id": ObjectId(scheme_id)})
            if scheme:
                scheme["id"] = str(scheme["_id"])
                scheme.pop("_id", None)
        except Exception:
            scheme = await db.schemes.find_one({"id": scheme_id})

    if not scheme:
        scheme = in_memory_store["schemes"].get(scheme_id)

    if not scheme:
        # Check by id field inside values
        for s in in_memory_store["schemes"].values():
            if str(s.get("id")) == str(scheme_id):
                scheme = s
                break

    if not scheme:
        raise HTTPException(status_code=404, detail="Scheme not found.")

    return {"scheme": scheme}

@router.post("/search")
async def search_schemes(body: dict):
    query = body.get("query", "")
    category = body.get("category", "All")
    state = body.get("state", "All")
    occupation = body.get("occupation", "All")

    return await list_schemes(category=category, state=state, occupation=occupation, search=query)
