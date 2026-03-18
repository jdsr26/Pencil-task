"""
FastAPI Application Entry Point
================================
Exposes the pipeline as a REST API for the React frontend.
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from backend.api.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    print("🚀 Dr. Jart+ AI Content Pipeline API starting...")
    print(f"   API Key configured: {'Yes' if os.getenv('ANTHROPIC_API_KEY') else 'NO — set ANTHROPIC_API_KEY in .env'}")
    yield
    print("Pipeline API shutting down.")


app = FastAPI(
    title="Dr. Jart+ AI Content Pipeline",
    description="Inspectable, self-correcting creative workflow engine",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.get("/")
def root():
    return {
        "name": "Dr. Jart+ AI Content Pipeline",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running",
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("BACKEND_PORT", 8000))
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port, reload=True)
