from pydantic import BaseModel
from typing import List, Optional

class ToponymWordAnalysis(BaseModel):
    """Анализ слова с релевантностью (формат MVP)"""
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

class ToponymExtractResponse(BaseModel):
    """Ответ на запрос извлечения топонимов (формат MVP)"""
    words: List[ToponymWordAnalysis]
    sentences: List[List[int]]
    text: str
    language: Optional[str] = None
    script: str = "unknown"
    processing_time_ms: float = 0.0
    from_cache: bool = False