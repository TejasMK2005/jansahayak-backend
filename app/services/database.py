import os
import json
import logging
from typing import Dict, Any, List, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from app.config import settings

logger = logging.getLogger("jansahayak.database")

client: Optional[AsyncIOMotorClient] = None
db = None

# In-memory store fallback in case local MongoDB is paused
in_memory_store = {
    "users": {},
    "profiles": {},
    "schemes": {},
    "chat_history": [],
    "documents": {}
}

async def init_db():
    global client, db
    try:
        client = AsyncIOMotorClient(
            settings.MONGODB_URI,
            serverSelectionTimeoutMS=2000
        )
        # Test connection
        await client.admin.command('ping')
        db = client[settings.DATABASE_NAME]
        logger.info(f"Connected successfully to MongoDB at {settings.MONGODB_URI}")
    except (ConnectionFailure, ServerSelectionTimeoutError, Exception) as e:
        logger.warning(f"Could not connect to MongoDB ({e}). Operating with persistent fallback store.")
        client = None
        db = None

def get_db():
    return db

async def close_db():
    global client
    if client:
        client.close()
        logger.info("MongoDB connection closed.")
