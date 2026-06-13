"""
FastAPI Application — Main entry point for the backend.

Configures CORS, mounts routes, and initializes the database.
Run with: uvicorn backend.api.main:app --reload
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.database.db import init_db
from backend.api.routes import router
from backend.rag.embeddings import build_knowledge_base


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup and shutdown events.
    - Creates database tables on startup
    - Builds RAG knowledge base on startup
    """
    # Startup
    print("🚀 Initializing database...")
    await init_db()

    print("📚 Building RAG knowledge base...")
    try:
        build_knowledge_base()
        print("✅ Knowledge base ready")
    except Exception as e:
        print(f"⚠️ RAG initialization failed (non-critical): {e}")

    print("🔍 AI Reconnaissance Platform is ready!")
    yield
    # Shutdown
    print("Shutting down...")


# ============================================================
# Create the FastAPI app
# ============================================================

app = FastAPI(
    title="AI Reconnaissance Platform",
    description=(
        "AI-powered reconnaissance and attack surface assessment platform. "
        "Uses LangGraph for orchestration, Ollama for local LLM inference, "
        "and RAG for CVE/CWE enrichment."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# ============================================================
# CORS — Allow the React frontend to connect
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# Mount routes
# ============================================================

app.include_router(router)


# ============================================================
# Health check (no prefix)
# ============================================================

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "AI Reconnaissance Platform"}
