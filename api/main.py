"""
Module: api/main.py
Description: FastAPI application with CORS configuration and session management.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from api.session import session_store


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan."""
    # Startup
    session_store.clear()
    yield
    # Shutdown
    session_store.clear()


app = FastAPI(
    title="AutoDataPrep API",
    description="API for AutoDataPrep - Intelligent Data Preparation Studio",
    version="2.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "AutoDataPrep API",
        "version": "2.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# Include routers
from api.routes import dataset, analysis, cleaning, transforms, ml, export

app.include_router(dataset.router, prefix="/api/dataset", tags=["Dataset"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["Analysis"])
app.include_router(cleaning.router, prefix="/api/cleaning", tags=["Cleaning"])
app.include_router(transforms.router, prefix="/api/transforms", tags=["Transforms"])
app.include_router(ml.router, prefix="/api/ml", tags=["ML"])
app.include_router(export.router, prefix="/api/export", tags=["Export"])
