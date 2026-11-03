import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status, Depends
from bson import ObjectId
from app.models.schemas import UserRegister, UserLogin, UserResponse, TokenResponse
from app.services.auth_service import hash_password, verify_password, create_access_token
from app.services.database import get_db, in_memory_store
from app.middleware.auth_middleware import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=TokenResponse)
async def register(user_data: UserRegister):
    db = get_db()
    email_clean = user_data.email.lower().strip()

    # Check if user already exists
    if db is not None:
        existing = await db.users.find_one({"email": email_clean})
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An account with this email already exists."
            )
        
        user_doc = {
            "name": user_data.name.strip(),
            "email": email_clean,
            "passwordHash": hash_password(user_data.password),
            "role": user_data.role if user_data.role in ["citizen", "admin"] else "citizen",
            "createdAt": datetime.now(timezone.utc)
        }
        res = await db.users.insert_one(user_doc)
        user_id = str(res.inserted_id)
        user_doc["id"] = user_id
    else:
        for u in in_memory_store["users"].values():
            if u["email"] == email_clean:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="An account with this email already exists."
                )
        user_id = str(uuid.uuid4())
        user_doc = {
            "id": user_id,
            "name": user_data.name.strip(),
            "email": email_clean,
            "passwordHash": hash_password(user_data.password),
            "role": user_data.role if user_data.role in ["citizen", "admin"] else "citizen",
            "createdAt": datetime.now(timezone.utc)
        }
        in_memory_store["users"][user_id] = user_doc

    token = create_access_token({"sub": user_id, "email": email_clean, "role": user_doc["role"]})
    return {
        "token": token,
        "user": UserResponse(
            id=user_id,
            name=user_doc["name"],
            email=user_doc["email"],
            role=user_doc["role"],
            createdAt=user_doc.get("createdAt")
        )
    }

@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    db = get_db()
    email_clean = credentials.email.lower().strip()

    user = None
    if db is not None:
        user = await db.users.find_one({"email": email_clean})
        if user:
            user["id"] = str(user["_id"])
    else:
        for u in in_memory_store["users"].values():
            if u["email"] == email_clean:
                user = u
                break

    if not user or not verify_password(credentials.password, user.get("passwordHash", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password. Please try again."
        )

    user_id = user["id"]
    token = create_access_token({"sub": user_id, "email": email_clean, "role": user.get("role", "citizen")})
    return {
        "token": token,
        "user": UserResponse(
            id=user_id,
            name=user["name"],
            email=user["email"],
            role=user.get("role", "citizen"),
            createdAt=user.get("createdAt")
        )
    }

@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return {
        "user": {
            "id": current_user.get("id") or str(current_user.get("_id")),
            "name": current_user.get("name"),
            "email": current_user.get("email"),
            "role": current_user.get("role", "citizen")
        }
    }
