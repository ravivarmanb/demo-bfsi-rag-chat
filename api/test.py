from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Test API is working", "status": "ok"}

@app.get("/health")
def health():
    return {"status": "healthy", "test": True}

# Export for Vercel
handler = app