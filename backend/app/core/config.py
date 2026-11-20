"""Application configuration.

All runtime configuration is sourced from environment variables (via a .env
file in local development, or real environment variables in containers).
Nothing here should ever contain a hardcoded secret or credential.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Strongly-typed application settings.

    Values are read from environment variables (case-insensitive) and,
    for local development, from a `.env` file at the backend project root.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- General ---
    APP_NAME: str = "ResearchGPT"
    APP_ENV: Literal["development", "production", "test"] = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"
    LOG_LEVEL: str = "INFO"

    # --- CORS ---
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    # --- Database (PostgreSQL) ---
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://researchgpt:researchgpt@postgres:5432/researchgpt",
        description="Async SQLAlchemy connection string.",
    )
    DATABASE_ECHO: bool = False

    # --- Auth / JWT ---
    JWT_SECRET_KEY: str = Field(
        default=...,
        description="Secret key used to sign JWTs. MUST be overridden via env var.",
    )
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # --- Vector store (ChromaDB) ---
    CHROMA_HOST: str = "chromadb"
    CHROMA_PORT: int = 8000
    CHROMA_COLLECTION_PREFIX: str = "researchgpt_user_"

    # --- Embeddings ---
    EMBEDDING_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DEVICE: str = "cpu"

    # --- LLM (OpenAI-compatible interface) ---
    LLM_PROVIDER: Literal["openai", "compatible"] = "openai"
    LLM_API_KEY: str = Field(default="", description="API key for the LLM provider.")
    LLM_BASE_URL: str = Field(
        default="https://api.openai.com/v1",
        description="Base URL for the OpenAI-compatible chat completions API.",
    )
    LLM_MODEL_NAME: str = "gpt-4o-mini"
    LLM_TEMPERATURE: float = 0.2
    LLM_MAX_TOKENS: int = 1024

    # --- Chunking defaults (overridable per-upload) ---
    DEFAULT_CHUNK_SIZE: int = 1000
    DEFAULT_CHUNK_OVERLAP: int = 200

    # --- RAG ---
    RAG_TOP_K: int = 5

    # --- File uploads ---
    UPLOAD_DIR: str = "/app/uploads"
    MAX_UPLOAD_SIZE_MB: int = 25
    ALLOWED_UPLOAD_EXTENSIONS: list[str] = [".pdf"]


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance.

    Using lru_cache ensures the .env file / environment is only parsed once
    per process, and lets FastAPI's dependency injection reuse the same
    instance across requests.
    """
    return Settings()
