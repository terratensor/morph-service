from pydantic_settings import BaseSettings
from typing import Optional, List
import os

class Settings(BaseSettings):
    # Environment
    ENV: str = "development"
    DEBUG: bool = False
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4
    
    # Redis
    REDIS_URL: Optional[str] = None
    CACHE_TTL: int = 3600
    
    # Limits
    MAX_TEXT_LENGTH: int = 100000
    BATCH_SIZE: int = 1000
    MAX_BATCH_TOTAL_LENGTH: int = 10_000_000
    
    # Analyzers
    ENABLE_CYRILLIC: bool = True
    ENABLE_LATIN: bool = True
    LATIN_MODELS: List[str] = ["en_core_web_sm"]  # Было LATIN_MODELS
    LATIN_MODEL: str = "en_core_web_sm"  # Добавляем для обратной совместимости
    
    # Cyrillic languages
    CYRILLIC_LANGUAGES: List[str] = ["ru", "uk", "be"] # ["ru", "uk", "be"]
    
    # Performance
    THREAD_POOL_SIZE: int = 8
    REQUEST_TIMEOUT: int = 30
    BATCH_TIMEOUT: int = 300
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Игнорировать лишние поля из env

settings = Settings()