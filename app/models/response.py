from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class WordAnalysis(BaseModel):
    """Анализ одного слова"""
    word: str
    original: str
    pos: str
    pos_eng: str
    case: str
    number: str
    gender: str
    is_geo_marker: bool
    is_uppercase: bool
    is_sentence_start: bool
    normal_form: str
    score: float
    relevance_score: float = 0.0

class AnalyzeResponse(BaseModel):
    """Ответ на анализ текста"""
    words: List[WordAnalysis]
    sentences: List[List[int]]
    text: str
    language: Optional[str] = None
    script: str = "unknown"
    processing_time_ms: float = 0.0
    from_cache: bool = False

class BatchResponse(BaseModel):
    """Ответ на пакетный анализ"""
    results: List[AnalyzeResponse]
    total_time_ms: float = 0.0
    texts_processed: int
    cache_stats: Dict[str, int] = {}

class HealthResponse(BaseModel):
    """Ответ на health check"""
    status: str
    version: str = "2.0.0"
    cache_available: bool = False
    workers: int = 4
    languages_supported: List[str] = ["ru", "en"]
    analyzers_loaded: Dict[str, List[str]] = {}
    uptime_seconds: float = 0.0

class StatsResponse(BaseModel):
    """Статистика сервиса"""
    texts_processed: int = 0
    total_time_seconds: float = 0.0
    avg_time_per_text_ms: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    cache_hit_rate: float = 0.0
    analyzers_loaded: Dict[str, List[str]] = {}
    uptime_seconds: float = 0.0