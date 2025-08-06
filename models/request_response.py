
# models/request_response.py
from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict, Any

class RAGRequest(BaseModel):
    documents: HttpUrl
    questions: List[str]

class RAGResponse(BaseModel):
    answers: List[str]

class ErrorResponse(BaseModel):
    error: str
    details: Optional[str] = None
