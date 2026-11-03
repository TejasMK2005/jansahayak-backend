from fastapi import Depends, HTTPException, status, Header
from typing import Optional
from app.services.auth_service import decode_access_token
from app.services.database import get_db, in_memory_store
from bson import ObjectId

async def get_token_from_header(authorization: Optional[str] = Header(None)) -> Optional[str]:
    if not authorization:
        return None
    parts = authorization.split(" ")
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1]
    return None

async def get_current_user(token: Optional[str] = Depends(get_token_from_header)):
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token missing. Please log in.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or invalid token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload["sub"]
    db = get_db()
    
    user = None
    if db is not None:
        try:
            user = await db.users.find_one({"_id": ObjectId(user_id)})
            if user:
                user["id"] = str(user["_id"])
        except Exception:
            user = await db.users.find_one({"id": user_id})
    else:
        user = in_memory_store["users"].get(user_id)
        
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User associated with this token no longer exists.",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    return user

async def get_optional_user(token: Optional[str] = Depends(get_token_from_header)):
    if not token:
        return None
    try:
        return await get_current_user(token)
    except HTTPException:
        return None

async def require_admin(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required to access this resource."
        )
    return current_user
