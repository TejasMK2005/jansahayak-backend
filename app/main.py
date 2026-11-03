import os
import sys
import logging
from contextlib import asynccontextmanager

# Add project root and server directory to sys.path
_current_dir = os.path.dirname(os.path.abspath(__file__))
_server_dir = os.path.abspath(os.path.join(_current_dir, ".."))
_project_root = os.path.abspath(os.path.join(_server_dir, ".."))
if _server_dir not in sys.path:
    sys.path.insert(0, _server_dir)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.services.database import init_db, close_db
from app.services.seed_data import seed_initial_data

# Routes
from app.routes import auth, profile, schemes, eligibility, rag, admin, health

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("jansahayak.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up JanSahayak AI Server...")
    await init_db()
    await seed_initial_data()
    yield
    logger.info("Shutting down JanSahayak AI Server...")
    await close_db()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="AI Government Scheme Discovery and Eligibility Assistant using RAG",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(health.router, prefix=settings.API_V1_STR)
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(profile.router, prefix=settings.API_V1_STR)
app.include_router(schemes.router, prefix=settings.API_V1_STR)
app.include_router(eligibility.router, prefix=settings.API_V1_STR)
app.include_router(rag.router, prefix=settings.API_V1_STR)
app.include_router(admin.router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    return {
        "project": "JanSahayak AI",
        "tagline": "Discover Government Schemes You May Qualify For",
        "version": settings.VERSION,
        "docs": "/docs",
        "status": "online"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
