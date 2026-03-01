from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime

class AnalysisResult:
    """Результат анализа одного слова"""
    def __init__(
        self,
        word: str,
        original: str,
        pos: str,
        pos_eng: str,
        case: str = "",
        number: str = "",
        gender: str = "",
        normal_form: str = "",
        score: float = 1.0,
        is_geo_marker: bool = False,
        is_uppercase: bool = False,
        is_sentence_start: bool = False,
    ):
        self.word = word
        self.original = original
        self.pos = pos
        self.pos_eng = pos_eng
        self.case = case
        self.number = number
        self.gender = gender
        self.normal_form = normal_form or word.lower()
        self.score = score
        self.is_geo_marker = is_geo_marker
        self.is_uppercase = is_uppercase
        self.is_sentence_start = is_sentence_start
        self.relevance_score = 0.0
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Конвертация в словарь для JSON"""
        return {
            'word': self.word,
            'original': self.original,
            'pos': self.pos,
            'pos_eng': self.pos_eng,
            'case': self.case,
            'number': self.number,
            'gender': self.gender,
            'is_geo_marker': self.is_geo_marker,
            'is_uppercase': self.is_uppercase,
            'is_sentence_start': self.is_sentence_start,
            'normal_form': self.normal_form,
            'score': self.score,
            'relevance_score': self.relevance_score,
        }

class BaseAnalyzer(ABC):
    """Базовый класс для всех анализаторов"""
    
    def __init__(self, language: str):
        self.language = language
        self.stats = {
            'words_processed': 0,
            'batches_processed': 0,
            'total_time': 0.0,
        }
    
    @abstractmethod
    def analyze_word(self, word: str, context: Optional[List[str]] = None) -> AnalysisResult:
        """Анализ одного слова"""
        pass
    
    @abstractmethod
    def analyze_batch(self, words: List[str]) -> List[AnalysisResult]:
        """Пакетный анализ слов"""
        pass
    
    def get_supported_languages(self) -> List[str]:
        """Список поддерживаемых языков"""
        return [self.language]
    
    def reset_stats(self):
        """Сброс статистики"""
        self.stats = {
            'words_processed': 0,
            'batches_processed': 0,
            'total_time': 0.0,
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Получение статистики"""
        return self.stats.copy()
    
    def _update_stats(self, word_count: int, batch_time: float):
        """Обновление статистики"""
        self.stats['words_processed'] += word_count
        self.stats['batches_processed'] += 1
        self.stats['total_time'] += batch_time