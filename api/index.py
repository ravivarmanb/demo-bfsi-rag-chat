import os
import tempfile
import json
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_chroma import Chroma
from langchain.embeddings.sentence_transformer import SentenceTransformerEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
import chromadb
from chromadb.config import Settings

app = FastAPI()

# Configure CORS for Vercel
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# Initialize Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is required")

genai.configure(api_key=GEMINI_API_KEY)

# Initialize models globally (cached across requests)
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", temperature=0.7, google_api_key=GEMINI_API_KEY)
embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")

# In-memory storage for documents (will reset on cold starts)
# In production, you'd want to use a persistent database
documents_store = {}
vectorstore_cache = None

class ChatRequest(BaseModel):
    message: str
    history: List[dict] = []

class ChatResponse(BaseModel):
    response: str
    source: str

class DocumentInfo(BaseModel):
    filename: str
    size: int
    type: str
    content_preview: str

def get_vectorstore():
    """Get or create vectorstore with current documents."""
    global vectorstore_cache, documents_store
    
    if not documents_store:
        return None
    
    # Create documents from stored content
    docs = []
    for filename, content in documents_store.items():
        doc = Document(
            page_content=content,
            metadata={"source": filename}
        )
        docs.append(doc)
    
    # Split documents into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )
    chunks = text_splitter.split_documents(docs)
    
    if not chunks:
        return None
    
    # Create in-memory vectorstore
    # Using ephemeral client for serverless environment
    client = chromadb.EphemeralClient()
    vectorstore = Chroma(
        client=client,
        collection_name="documents",
        embedding_function=embeddings
    )
    
    # Add documents to vectorstore
    vectorstore.add_documents(chunks)
    
    return vectorstore

def get_response_from_local_knowledge(query: str) -> Optional[str]:
    """Get response from local knowledge base if relevant documents are found."""
    vectorstore = get_vectorstore()
    
    if not vectorstore:
        return None
    
    try:
        # Search for relevant documents
        docs = vectorstore.similarity_search(query, k=3)
        
        if not docs:
            return None
        
        # Format the context from relevant documents
        context = "\n\n".join([f"Document {i+1}:\n{doc.page_content}" for i, doc in enumerate(docs)])
        
        # Create a prompt that uses the context
        prompt = f"""You are a helpful assistant that answers questions based on the provided context.
        
        Context:
        {context}
        
        Question: {query}
        
        Please provide a concise and accurate answer based ONLY on the context above. 
        If the answer isn't in the context, just say "NO_ANSWER".
        Answer:"""
        
        response = llm.invoke(prompt)
        if "NO_ANSWER" in response.content.strip():
            return None
        return response.content
        
    except Exception as e:
        print(f"Error in get_response_from_local_knowledge: {str(e)}")
        return None

def get_general_knowledge_response(query: str) -> str:
    """Get response using Gemini's general knowledge."""
    try:
        response = llm.invoke(query)
        return response.content
    except Exception as e:
        return f"I'm sorry, I encountered an error: {str(e)}"

@app.post("/chat", response_model=ChatResponse)
async def chat(chat_request: ChatRequest):
    query = chat_request.message
    
    # First try to get response from local knowledge
    local_response = get_response_from_local_knowledge(query)
    
    if local_response:
        return ChatResponse(response=local_response, source="local_knowledge")
    
    # If no relevant local knowledge, use general knowledge
    general_response = get_general_knowledge_response(query)
    return ChatResponse(response=general_response, source="general_knowledge")

@app.post("/upload_document")
async def upload_document(
    file: UploadFile = File(...),
    filename: str = Form(...)
):
    """Upload a document to the in-memory knowledge base."""
    global documents_store
    
    try:
        # Validate file type
        if not filename.endswith(('.txt', '.pdf')):
            raise HTTPException(
                status_code=400,
                detail="Only .txt and .pdf files are allowed."
            )
        
        # Check if file already exists
        if filename in documents_store:
            raise HTTPException(
                status_code=400,
                detail=f"A file with the name '{filename}' already exists."
            )
        
        # Read file content
        content = await file.read()
        
        if filename.endswith('.pdf'):
            # For PDF files, you'd need to implement PDF text extraction
            # For now, we'll just store the filename and indicate it's a PDF
            text_content = f"[PDF File: {filename}]\nPDF text extraction not implemented in this serverless version."
        else:
            # For text files
            text_content = content.decode('utf-8')
        
        if not text_content.strip():
            raise HTTPException(
                status_code=400,
                detail="Uploaded file is empty"
            )
        
        # Store in memory
        documents_store[filename] = text_content
        
        return {
            "status": "success",
            "message": "Document uploaded successfully",
            "filename": filename,
            "size": len(content)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process file: {str(e)}"
        )

@app.get("/documents")
async def list_documents():
    """List all documents in the in-memory knowledge base."""
    global documents_store
    
    documents = []
    total_size = 0
    
    for filename, content in documents_store.items():
        size = len(content.encode('utf-8'))
        file_ext = filename.split('.')[-1] if '.' in filename else 'txt'
        
        documents.append({
            "filename": filename,
            "size": size,
            "type": file_ext,
            "content_preview": content[:100] + "..." if len(content) > 100 else content
        })
        
        total_size += size
    
    return {
        "documents": documents,
        "total_size": total_size,
        "total_documents": len(documents)
    }

@app.delete("/documents/{filename}")
async def delete_document(filename: str):
    """Delete a document from the in-memory knowledge base."""
    global documents_store
    
    if filename not in documents_store:
        raise HTTPException(
            status_code=404,
            detail="File not found"
        )
    
    del documents_store[filename]
    
    return {
        "status": "success",
        "message": "Document deleted successfully",
        "filename": filename
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "documents_count": len(documents_store),
        "gemini_configured": bool(GEMINI_API_KEY)
    }

# Export the app for Vercel
handler = app