"""
Application configuration.
Central place for all settings - model names, paths, timeouts, etc.
"""

from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """All app settings. Override via environment variables."""

    # --- LLM Configuration ---
    # Ollama is the default local LLM provider (using phi3 for lower RAM usage)
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "phi3"  # Changed from llama3.1:8b for 8GB RAM machines
    ollama_temperature: float = 0.1  # Low temperature for consistent output

    # Gemini Fallback (if set, overrides Ollama for better performance)
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-1.5-flash"

    # --- Database ---
    database_url: str = "sqlite+aiosqlite:///./recon.db"

    # --- RAG ---
    # Sentence-transformers model for local embeddings
    embedding_model: str = "all-MiniLM-L6-v2"
    chroma_persist_dir: str = "./chroma_db"
    knowledge_dir: str = str(Path(__file__).parent / "rag" / "knowledge")

    # --- Tool Execution ---
    # Maximum time (seconds) a single tool can run before being killed
    tool_timeout: int = 300  # 5 minutes
    # Maximum number of tools to run concurrently
    max_concurrent_tools: int = 5

    # --- API ---
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    class Config:
        env_file = ".env"
        env_prefix = "RECON_"


# Singleton settings instance
settings = Settings()
