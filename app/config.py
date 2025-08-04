from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "LLM-Powered Terms & Conditions Analyzer"
    DATABASE_URL: str
    GOOGLE_API_KEY: str

    MONGO_URI: str
    MONGO_DB_NAME: str = "tos_analyzer"
    CLAUSES_COLLECTION_NAME: str = "clauses"

    # Celery configuration
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str

    # Redis configuration
    REDIS_URL: str = "redis://localhost:6379/0"

    # Path to the uploads folder
    UPLOADS_FOLDER: Path = Path(__file__).parent.parent / "uploads"

    # Authentication settings
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # LLM settings
    LLM_MODEL_NAME: str = "gemini-2.0-flash"
    LLM_TEMPERATURE: float = 0.2
    LLM_MAX_CHUNK_LENGTH: int = 8000
    LLM_CHUNK_TEXT_OVERLAP: int = 150

    LLM_REQUESTS_PER_MINUTE: int = 15
    LLM_LIMIT_KEY: str = "llm"
    LLM_MAX_CONCURRENT_REQUESTS: int = 2
    MAX_RETRIES: int = 4
    RETRY_BACKOFF_BASE: int = 5

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
