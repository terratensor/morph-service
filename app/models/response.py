from pydantic import BaseModel
from typing import List, Optional

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

class BatchResponse(BaseModel):
    """Ответ на пакетный анализ"""
    results: List[AnalyzeResponse]
    total_time_ms: float = 0.0
    texts_processed: int

class HealthResponse(BaseModel):
    """Ответ на health check"""
    status: str
    version: str = "2.0.0"
    cache_available: bool = False
    workers: int = 4
    languages_supported: List[str] = ["ru", "uk", "be", "en"]
    analyzers_loaded: dict = {}

class StatsResponse(BaseModel):
    """Статистика сервиса"""
    cache_hits: int = 0
    cache_misses: int = 0
    texts_analyzed: int = 0
    avg_processing_time: float = 0.0
    uptime_seconds: float = 0.0