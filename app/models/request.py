from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from ..config import settings

class AnalyzeRequest(BaseModel):
    """Запрос на анализ одного текста"""
    text: str = Field(..., min_length=1, max_length=settings.MAX_TEXT_LENGTH)
    language: Optional[str] = None  # Опциональное указание языка
    
    @field_validator('text')
    @classmethod
    def text_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('Text cannot be empty')
        return v.strip()

class BatchRequest(BaseModel):
    """Запрос на пакетный анализ"""
    texts: List[str] = Field(..., min_length=1, max_length=settings.BATCH_SIZE)
    
    @field_validator('texts')
    @classmethod
    def validate_batch_size(cls, v: List[str]) -> List[str]:
        # Проверка общего размера
        total_length = sum(len(t) for t in v)
        if total_length > settings.MAX_BATCH_TOTAL_LENGTH:
            raise ValueError(f'Total batch size too large: {total_length} > {settings.MAX_BATCH_TOTAL_LENGTH}')
        
        # Очистка каждого текста
        return [t.strip() for t in v if t.strip()]