import os
import uuid
import shutil
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from bson import ObjectId
from app.config import settings
from app.services.database import get_db, in_memory_store
from app.middleware.auth_middleware import require_admin
from rag.ingestion.loader import document_loader
from rag.processing.chunker import chunker
from rag.retrieval.vectorstore import vector_store

logger = logging.getLogger("jansahayak.admin")
router = APIRouter(prefix="/admin", tags=["Admin Operations"])

@router.get("/documents")
async def list_documents(admin_user: dict = Depends(require_admin)):
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

    return {"count": len(docs), "documents": docs}

@router.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    schemeName: str = Form(...),
    category: str = Form(...),
    state: str = Form(...),
    governmentDepartment: str = Form(""),
    officialURL: str = Form(...),
    admin_user: dict = Depends(require_admin)
):
    # Ensure category directory exists
    cat_dir = os.path.join(settings.SCHEMES_DATA_PATH, category.lower())
    os.makedirs(cat_dir, exist_ok=True)

    file_path = os.path.join(cat_dir, file.filename)
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save uploaded file: {e}")

    # Process document
    metadata = {
        "schemeName": schemeName,
        "category": category,
        "state": state,
        "governmentDepartment": governmentDepartment,
        "sourceURL": officialURL,
        "documentName": file.filename,
        "verificationDate": "October 2026"
    }

    try:
        pages = document_loader.load_file(file_path, metadata)
        all_chunks = []
        for p in pages:
            c_list = chunker.chunk_document(p["text"], p["metadata"])
            all_chunks.extend(c_list)

        vector_store.add_documents(all_chunks)

        doc_record = {
            "id": str(uuid.uuid4()),
            "documentName": file.filename,
            "schemeName": schemeName,
            "category": category,
            "state": state,
            "governmentDepartment": governmentDepartment,
            "sourceURL": officialURL,
            "localFilePath": file_path,
            "processingStatus": "Vectorized",
            "chunkCount": len(all_chunks),
            "uploadedAt": datetime.now(timezone.utc),
            "verifiedAt": "October 2026"
        }

        db = get_db()
        if db is not None:
            try:
                res = await db.documents.insert_one(doc_record)
                doc_record["id"] = str(res.inserted_id)
            except Exception:
                pass
        
        in_memory_store["documents"][doc_record["id"]] = doc_record

        return {
            "message": f"Document '{file.filename}' processed and indexed into ChromaDB successfully.",
            "chunkCount": len(all_chunks),
            "document": doc_record
        }
    except Exception as e:
        logger.error(f"Error processing uploaded document: {e}")
        raise HTTPException(status_code=500, detail=f"Document processing error: {e}")

@router.post("/documents/ingest")
async def trigger_full_ingest(admin_user: dict = Depends(require_admin)):
    """
    Scans entire data/schemes repository, extracts text, chunks, and indexes into ChromaDB.
    """
    total_chunks = 0
    total_docs = 0
    scanned_records = []

    schemes_dir = settings.SCHEMES_DATA_PATH
    if not os.path.exists(schemes_dir):
        raise HTTPException(status_code=404, detail="Schemes data directory not found.")

    for root, _, files in os.walk(schemes_dir):
        for f in files:
            if f.lower().endswith((".pdf", ".md", ".txt")):
                file_path = os.path.join(root, f)
                try:
                    pages = document_loader.load_file(file_path)
                    all_chunks = []
                    for p in pages:
                        c_list = chunker.chunk_document(p["text"], p["metadata"])
                        all_chunks.extend(c_list)

                    vector_store.add_documents(all_chunks)
                    total_chunks += len(all_chunks)
                    total_docs += 1

                    first_meta = pages[0]["metadata"] if pages else {}
                    rec = {
                        "id": str(uuid.uuid4()),
                        "documentName": f,
                        "schemeName": first_meta.get("schemeName", f),
                        "category": first_meta.get("category", "General"),
                        "state": first_meta.get("state", "All India"),
                        "governmentDepartment": first_meta.get("governmentDepartment", ""),
                        "sourceURL": first_meta.get("sourceURL", ""),
                        "localFilePath": file_path,
                        "processingStatus": "Vectorized",
                        "chunkCount": len(all_chunks),
                        "uploadedAt": datetime.now(timezone.utc),
                        "verifiedAt": "October 2026"
                    }
                    scanned_records.append(rec)
                    in_memory_store["documents"][rec["id"]] = rec
                except Exception as e:
                    logger.error(f"Error ingesting {f}: {e}")

    db = get_db()
    if db is not None:
        try:
            for rec in scanned_records:
                await db.documents.update_one(
                    {"documentName": rec["documentName"]},
                    {"$set": rec},
                    upsert=True
                )
        except Exception:
            pass

    return {
        "message": "Full repository ingestion completed successfully.",
        "documentsProcessed": total_docs,
        "chunksIndexed": total_chunks
    }

@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str, admin_user: dict = Depends(require_admin)):
    db = get_db()
    doc_name = None

    if db is not None:
        try:
            doc = await db.documents.find_one({"_id": ObjectId(doc_id)})
            if doc:
                doc_name = doc.get("documentName")
                await db.documents.delete_one({"_id": ObjectId(doc_id)})
        except Exception:
            pass

    if not doc_name and doc_id in in_memory_store["documents"]:
        doc_name = in_memory_store["documents"][doc_id].get("documentName")
        del in_memory_store["documents"][doc_id]

    if doc_name:
        vector_store.delete_document(doc_name)
        return {"message": f"Document '{doc_name}' and its vector embeddings deleted."}

    raise HTTPException(status_code=404, detail="Document not found.")
