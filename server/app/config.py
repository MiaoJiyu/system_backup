from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    APP_NAME: str = "SmartBackup System v2.0"
    DEBUG: bool = True
    SECRET_KEY: str = "change-me-in-production-use-random-64-char-string"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # Database - defaults to SQLite for development
    DATABASE_URL: str = "sqlite+aiosqlite:///./smart_backup.db"
    # For MySQL: DATABASE_URL = "mysql+aiomysql://user:password@localhost:3306/backup_db"

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # WebSocket
    WS_HEARTBEAT_INTERVAL: int = 30  # seconds
    WS_HEARTBEAT_TIMEOUT: int = 90   # seconds, mark offline after 3 missed heartbeats

    # Upload
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE: int = 500 * 1024 * 1024  # 500MB

    # Credential TTL
    CREDENTIAL_TTL: int = 600  # 10 minutes for presigned URLs / temp accounts

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "allow"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()
