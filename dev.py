#!/usr/bin/env python3
"""
Development server script for local testing
"""
import subprocess
import sys
import os
from pathlib import Path

def run_fastapi():
    """Run the FastAPI server"""
    os.chdir(Path(__file__).parent)
    subprocess.run([
        sys.executable, "-m", "uvicorn", 
        "api.index:app", 
        "--host", "127.0.0.1", 
        "--port", "8000", 
        "--reload"
    ])

if __name__ == "__main__":
    print("Starting FastAPI development server...")
    print("Make sure to run 'cd my-app && npm run dev' in another terminal")
    run_fastapi()