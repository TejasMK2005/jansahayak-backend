from fastapi import APIRouter
from app.services.database import get_db
from rag.retrieval.vectorstore import vector_store

router = APIRouter(tags=["Health"])

@router.get("/health")
async def health_check():
    db = get_db()
    db_status = "connected" if db is not None else "in_memory_fallback"
    return {
        "status": "healthy",
        "service": "JanSahayak AI Backend",
        "database": db_status,
        "vectorStore": {
            "chunksIndexed": vector_store.count(),
            "chromaStatus": "active" if vector_store.collection is not None else "fallback_active"
        }
    }
