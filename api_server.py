"""
AutoDataPrep API Server Entry Point
Run this to start the FastAPI backend.
"""

import uvicorn
from api.main import app

if __name__ == "__main__":
    print("Starting AutoDataPrep API Server...")
    print("API Documentation available at: http://127.0.0.1:8008/docs")
    uvicorn.run("api.main:app", host="127.0.0.1", port=8008, reload=False)
