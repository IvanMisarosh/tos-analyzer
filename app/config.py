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

    # Path to the uploads folder
    UPLOADS_FOLDER: Path = Path(__file__).parent.parent / "uploads"

    # Authentication settings
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
