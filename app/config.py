from pydantic_settings import BaseSettings
from typing import Optional, List
import os

class Settings(BaseSettings):
    # Environment
    ENV: str = "development"  # development/production
    DEBUG: bool = False
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4
    
    # Redis
    REDIS_URL: Optional[str] = None
    CACHE_TTL: int = 3600  # 1 hour
    
    # Limits
    MAX_TEXT_LENGTH: int = 100000  # characters
    BATCH_SIZE: int = 1000  # max texts per batch
    MAX_BATCH_TOTAL_LENGTH: int = 10_000_000  # 10M chars total
    
    # Analyzers
    ENABLE_CYRILLIC: bool = True
    ENABLE_LATIN: bool = True
    LATIN_MODELS: List[str] = ["en_core_web_sm"]
    
    # Cyrillic languages (pymorphy3 supports)
    CYRILLIC_LANGUAGES: List[str] = ["ru", "uk", "be"]
    
    # Performance
    THREAD_POOL_SIZE: int = 8
    REQUEST_TIMEOUT: int = 30  # seconds
    BATCH_TIMEOUT: int = 300  # seconds
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Глобальный экземпляр настроек
settings = Settings()

# Настройка логирования
import logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format=settings.LOG_FORMAT
)