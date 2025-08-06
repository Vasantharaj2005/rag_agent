
# core/config.py
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # API Configuration
    API_TOKEN: str
    LOG_LEVEL: str = "INFO"
    
    # Google Gemini Configuration
    GOOGLE_API_KEY: str
    GOOGLE_GEMINI_MODEL_NAME: str = "gemini-2.0-flash"
    DOCUMENTAI_PROCESSOR_NAME: Optional[str] = None  # Optional for Document AI integration
    
    # Pinecone Configuration
    PINECONE_API_KEY: str
    PINECONE_ENVIRONMENT: str
    PINECONE_INDEX_NAME: str = "agentic-rag-index"
    PINECONE_CLOUD: str
    
    # Vector Store Configuration
    EMBEDDING_MODEL: str = "models/embedding-001"
    VECTOR_DIMENSION: int = 768
    
    # Document Processing
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    
    # Retrieval Configuration
    TOP_K_RESULTS: int = 5
    SIMILARITY_THRESHOLD: float = 0.7
    
    class Config:
        env_file = ".env"

settings = Settings()
