from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class ChatRequest(BaseModel):
    message: str
    history: List[dict] = []

class ChatResponse(BaseModel):
    response: str
    source: str  # 'local_knowledge' or 'general_knowledge'

class DocumentInfo(BaseModel):
    filename: str
    size: int
    type: str

class DocumentListResponse(BaseModel):
    documents: List[DocumentInfo]
