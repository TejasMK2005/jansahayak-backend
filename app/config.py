import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "JanSahayak AI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    
    # Environment Variables
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://127.0.0.1:27017/jansahayak")
    DATABASE_NAME: str = "jansahayak"
    JWT_SECRET: str = os.getenv("JWT_SECRET", "jansahayak_super_secure_jwt_secret_key_2026_india")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    CHROMA_DB_PATH: str = os.getenv("CHROMA_DB_PATH", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "rag", "vectorstore", "chroma_db")))
    SCHEMES_DATA_PATH: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "schemes"))

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
