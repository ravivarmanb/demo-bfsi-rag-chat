import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Minimal API is working", "status": "ok"}

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "env_vars": len(os.environ),
        "gemini_key_exists": bool(os.getenv("GEMINI_API_KEY"))
    }

@app.get("/documents")
async def documents():
    return {
        "documents": [],
        "total_size": 0,
        "total_documents": 0
    }

# Export for Vercel
handler = app