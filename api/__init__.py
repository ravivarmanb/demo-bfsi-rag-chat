from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
import sys
from pathlib import Path

# Add the parent directory to path so we can import from app
sys.path.append(str(Path(__file__).parent.parent))

# Import the main application
from app import app as fastapi_app

# Create a new FastAPI app instance
app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the main FastAPI app
app.mount("/api", fastapi_app)

@app.get("/")
async def root():
    return {"message": "RAG Chat API is running. Use /api/ for the chat endpoints."}
