from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from app.models.schemas import RagQueryRequest, RagQueryResponse, RagSourceItem
from app.services.database import get_db, in_memory_store
from app.middleware.auth_middleware import get_optional_user
from rag.retrieval.vectorstore import vector_store
from rag.generation.llm import generator

router = APIRouter(prefix="/rag", tags=["RAG & AI Chatbot"])

@router.post("/ask", response_model=RagQueryResponse)
async def ask_rag(req: RagQueryRequest, current_user: dict = Depends(get_optional_user)):
    user_id = "guest"
    if current_user:
        user_id = current_user.get("id") or str(current_user.get("_id", "guest"))

    # 1. Retrieve most relevant chunks from ChromaDB / Vector Store
    chunks = vector_store.search(
        query=req.question,
        top_k=4,
        category=req.category,
        state=req.state,
        similarity_threshold=0.15
    )

    # 2. Generate grounded answer
    answer, follow_ups = generator.generate_response(
        question=req.question,
        retrieved_chunks=chunks,
        language=req.language or "English"
    )

    # 3. Format source citations
    sources = []
    for c in chunks:
        meta = c.get("metadata", {})
        sources.append(RagSourceItem(
            schemeName=meta.get("schemeName", "Government Scheme"),
            documentName=meta.get("documentName", ""),
            category=meta.get("category", ""),
            state=meta.get("state", ""),
            officialURL=meta.get("sourceURL", ""),
            snippet=c.get("content", "")[:300],
            score=c.get("score", 0.0)
        ))

    # 4. Save to Chat History
    chat_entry = {
        "userId": user_id,
        "question": req.question,
        "answer": answer,
        "sources": [s.model_dump() for s in sources],
        "createdAt": datetime.now(timezone.utc)
    }

    db = get_db()
    if db is not None:
        try:
            await db.chat_history.insert_one(chat_entry)
        except Exception:
            pass
    in_memory_store["chat_history"].append(chat_entry)

    return RagQueryResponse(
        answer=answer,
        sources=sources,
        followUpQuestions=follow_ups
    )

@router.get("/sources")
async def get_rag_sources():
    db = get_db()
    docs = []
    if db is not None:
        try:
            cursor = db.documents.find({})
            async for d in cursor:
                d["id"] = str(d["_id"])
                docs.append(d)
        except Exception:
            pass

    if not docs:
        docs = list(in_memory_store["documents"].values())

    return {
        "totalChunks": vector_store.count(),
        "totalDocuments": len(docs),
        "documents": docs
    }
