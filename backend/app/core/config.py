from typing import Any
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "LedgerPilot"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    # Database
    DB_PROVIDER: str = "sqlite"  # sqlite | postgres
    DATABASE_URL: str = "sqlite+aiosqlite:///./ledgerpilot.db"

    # Storage
    STORAGE_PROVIDER: str = "local"  # local | supabase
    UPLOAD_DIR: str = "./uploads"

    # Vector store
    VECTOR_PROVIDER: str = "chroma"  # chroma | pinecone
    CHROMA_PERSIST_DIR: str = "./chroma_db"

    # Extraction
    EXTRACTION_PROVIDER: str = "mock"  # groq | cohere | mock
    GROQ_API_KEY: str = ""
    GROQ_VISION_MODEL: str = "llama-3.2-11b-vision-preview"
    COHERE_API_KEY: str = ""

    # Auth
    CLERK_SECRET_KEY: str = ""
    CLERK_JWKS_URL: str = ""

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug(cls, v: Any) -> bool:
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            return v.strip().lower() in ("true", "1", "yes", "t", "enabled")
        return False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
