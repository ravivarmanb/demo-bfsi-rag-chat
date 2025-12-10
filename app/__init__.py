import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import sys
from pathlib import Path
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_chroma import Chroma
from langchain.embeddings.sentence_transformer import SentenceTransformerEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_core.documents import Document
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI()

# Configuration
LOCAL_KNOWLEDGE_DIR = "local_knowledge"
PERSIST_DIRECTORY = "/tmp/chroma"  # This will be persistent in Vercel's /tmp directory
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# Initialize Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable not set")

genai.configure(api_key=GEMINI_API_KEY)

# Initialize models
try:
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.7, google_api_key=GEMINI_API_KEY)
    embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
except Exception as e:
    print(f"Error initializing models: {str(e)}")
    raise

class ChatRequest(BaseModel):
    message: str
    history: List[dict] = []

class ChatResponse(BaseModel):
    response: str
    source: str  # 'local_knowledge' or 'general_knowledge'

def load_documents():
    """Load documents from the local knowledge directory."""
    if not os.path.exists(LOCAL_KNOWLEDGE_DIR):
        os.makedirs(LOCAL_KNOWLEDGE_DIR, exist_ok=True)
        return []
    
    try:
        loader = DirectoryLoader(
            LOCAL_KNOWLEDGE_DIR,
            glob="**/*.txt",
            loader_cls=TextLoader,
            show_progress=True,
            use_multithreading=True,
        )
        return loader.load()
    except Exception as e:
        print(f"Error loading documents: {str(e)}")
        return []

def initialize_vectorstore():
    """Initialize or load the Chroma vector store with persistent storage."""
    try:
        # Create the directory if it doesn't exist
        os.makedirs(PERSIST_DIRECTORY, exist_ok=True)
        
        # Try to load existing vector store
        if os.path.exists(PERSIST_DIRECTORY) and os.path.exists(os.path.join(PERSIST_DIRECTORY, 'chroma.sqlite3')):
            print("Loading existing vector store...")
            return Chroma(
                persist_directory=PERSIST_DIRECTORY,
                embedding_function=embeddings
            )
        
        # Otherwise, create a new one
        print("Creating new vector store...")
        documents = load_documents()
        
        if not documents:
            print("No documents found in the local knowledge directory.")
            return None
            
        # Split documents into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP
        )
        chunks = text_splitter.split_documents(documents)
        
        # Create and persist the vector store
        print(f"Creating new vector store with {len(chunks)} chunks...")
        vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory=PERSIST_DIRECTORY
        )
        
        # Explicitly persist the data
        vectorstore.persist()
        
        return vectorstore
        
    except Exception as e:
        print(f"Error initializing vector store: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

# Initialize the vector store on startup
vectorstore = initialize_vectorstore()

def get_response_from_local_knowledge(query: str) -> Optional[str]:
    """Get response from local knowledge base if relevant documents are found."""
    global vectorstore
    if not vectorstore:
        print("Initializing vector store...")
        vectorstore = initialize_vectorstore()
        if not vectorstore:
            print("Failed to initialize vector store.")
            return None
    
    try:
        # Search for relevant documents
        print(f"Searching local knowledge for: {query}")
        docs = vectorstore.similarity_search(query, k=3)
        
        if not docs:
            print("No relevant documents found in local knowledge.")
            return None
        
        print(f"Found {len(docs)} relevant document(s).")
        
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
        
        print("Generating response from local knowledge...")
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
        if "quota" in str(e).lower() or "429" in str(e):
            return "I'm currently experiencing high demand. Please try again in a few moments. If the issue persists, you may have reached the free tier limit for today."
        return f"I'm sorry, I encountered an error: {str(e)}"

@app.post("/chat")
async def chat(chat_request: ChatRequest):
    query = chat_request.message
    
    # First try to get response from local knowledge
    local_response = get_response_from_local_knowledge(query)
    
    if local_response:
        return ChatResponse(response=local_response, source="local_knowledge")
    
    # If no relevant local knowledge, use general knowledge
    general_response = get_general_knowledge_response(query)
    return ChatResponse(response=general_response, source="general_knowledge")

@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "RAG Chat API is healthy"}
