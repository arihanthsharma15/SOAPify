from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # App
    PROJECT_NAME: str = "SOAPify"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"  # development | production

    # Database (Neon)
    DATABASE_URL: str

    # JWT Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    # LLM Provider Switch
    LLM_PROVIDER: str = "groq"  # groq | ollama

    # Groq (Production)
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "llama3-70b-8192"

    # Ollama (Local only)
    OLLAMA_BASE_URL: Optional[str] = None
    OLLAMA_MODEL: Optional[str] = None

    # ChromaDB (Ephemeral)
    CHROMA_PERSIST_DIR: str = "./chroma"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
