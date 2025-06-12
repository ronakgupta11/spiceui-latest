from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

from app.routers import ingest, generate, modify

app = FastAPI(
    title="SpiceUI",
    description="Convert UI designs to React code using component libraries",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(ingest.router, prefix="/api/v1", tags=["Component Ingestion"])
app.include_router(generate.router, prefix="/api/v1", tags=["Code Generation"])
app.include_router(modify.router, prefix="/api/v1", tags=["Code Modification"])

@app.get("/")
async def root():
    return {
        "message": "Welcome to SpiceUI API",
        "version": "1.0.0",
        "endpoints": {
            "ingest": "/api/v1/ingest-component",
            "annotate": "/api/v1/annotate",
            "generate": "/api/v1/generate",
            "modify": "/api/v1/modify"
        }
    } 