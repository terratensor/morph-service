import re
from typing import List, Tuple, Dict
from enum import Enum
from ..utils.text_utils import is_cyrillic, is_latin

class Script(Enum):
    """Типы письменности"""
    CYRILLIC = "cyrillic"
    LATIN = "latin"
    CJK = "cjk"  # Китайский, японский, корейский
    ARABIC = "arabic"
    OTHER = "other"
    MIXED = "mixed"
    UNKNOWN = "unknown"

# Unicode диапазоны для разных письменностей
# Данные из Go-функции, которую вы показали
SCRIPTS_RANGES = {
    Script.CJK: [
        # CJK Unified Ideographs
        (0x4E00, 0x9FFF),
        # CJK Extension A
        (0x3400, 0x4DBF),
        # Extension B
        (0x20000, 0x2A6DF),
        # Extension C
        (0x2A700, 0x2B73F),
        # Extension D
        (0x2B820, 0x2CEAF),
        # Extension E
        (0x2CEB0, 0x2EBEF),
        # Extension F
        (0x2CEB0, 0x2EBEF),
        # CJK Symbols and Punctuation
        (0x3000, 0x303F),
        # Hiragana
        (0x3040, 0x309F),
        # Katakana
        (0x30A0, 0x30FF),
        # Katakana Phonetic Extensions
        (0x31F0, 0x31FF),
        # Halfwidth and Fullwidth Forms
        (0xFF00, 0xFFEF),
        # Hangul Jamo
        (0x1100, 0x11FF),
        # Hangul Compatibility Jamo
        (0x3130, 0x318F),
        # Hangul Jamo Extended-A
        (0xA960, 0xA97F),
        # Hangul Jamo Extended-B
        (0xD7B0, 0xD7FF),
        # Hangul Syllables
        (0xAC00, 0xD7AF),
        # Thai
        (0x0E00, 0x0E7F),
        # Lao
        (0x0E80, 0x0EFF),
    ],
    Script.ARABIC: [
        # Основной арабский блок
        (0x0600, 0x06FF),
        # Arabic Supplement
        (0x0750, 0x077F),
        # Arabic Extended-A
        (0x08A0, 0x08FF),
        # Arabic Extended-B
        (0x0870, 0x089F),
        # Arabic Presentation Forms-A
        (0xFB50, 0xFDFF),
        # Arabic Presentation Forms-B
        (0xFE70, 0xFEFF),
    ],
    Script.CYRILLIC: [
        # Cyrillic
        (0x0400, 0x04FF),
        # Cyrillic Supplement
        (0x0500, 0x052F),
        # Cyrillic Extended-A
        (0x2DE0, 0x2DFF),
        # Cyrillic Extended-B
        (0xA640, 0xA69F),
    ],
    Script.LATIN: [
        # Basic Latin (A-Z a-z)
        (0x0041, 0x005A),
        (0x0061, 0x007A),
        # Latin-1 Supplement
        (0x00C0, 0x00FF),
        # Latin Extended-A
        (0x0100, 0x017F),
        # Latin Extended-B
        (0x0180, 0x024F),
        # Latin Extended Additional
        (0x1E00, 0x1EFF),
    ]
}

class ScriptDetector:
    """Детектор письменности текста на основе Unicode диапазонов"""
    
    def __init__(self):
        self.cache: Dict[str, Script] = {}
    
    @staticmethod
    def get_script(char: str) -> Script:
        """Определяет письменность одного символа"""
        code = ord(char)
        
        # Пропускаем пробелы и цифры
        if char.isspace() or char.isdigit():
            return Script.OTHER
        
        for script, ranges in SCRIPTS_RANGES.items():
            for start, end in ranges:
                if start <= code <= end:
                    return script
        
        return Script.OTHER
    
    def detect(self, text: str, use_cache: bool = True) -> Script:
        """
        Определяет доминирующую письменность текста
        
        Args:
            text: Анализируемый текст
            use_cache: Использовать кэш (для повторяющихся текстов)
        
        Returns:
            Script: Тип письменности
        """
        if not text or not text.strip():
            return Script.UNKNOWN
        
        # Проверяем кэш
        if use_cache and text in self.cache:
            return self.cache[text]
        
        # Подсчитываем количество символов каждой письменности
        script_counts = {}
        total_chars = 0
        
        for char in text:
            if char.isspace() or char.isdigit():
                continue
            
            script = self.get_script(char)
            script_counts[script] = script_counts.get(script, 0) + 1
            total_chars += 1
        
        if total_chars == 0:
            result = Script.UNKNOWN
        else:
            # Находим доминирующую письменность
            dominant = max(script_counts.items(), key=lambda x: x[1])
            dominant_script, dominant_count = dominant
            
            # Если больше 70% текста в одной письменности
            if dominant_count / total_chars > 0.7:
                result = dominant_script
            else:
                result = Script.MIXED
        
        # Сохраняем в кэш
        if use_cache:
            self.cache[text] = result
        
        return result
    
    def detect_by_word(self, text: str) -> List[Tuple[str, Script]]:
        """
        Определяет письменность для каждого слова
        
        Returns:
            List of (word, script)
        """
        if not text:
            return []
        
        words = text.split()
        result = []
        
        for word in words:
            # Очищаем слово от пунктуации для анализа
            clean_word = ''.join(c for c in word if c.isalpha())
            if not clean_word:
                script = Script.OTHER
            else:
                script = self.detect(clean_word, use_cache=True)
            result.append((word, script))
        
        return result
    
    def get_language_hint(self, text: str) -> str:
        """
        Возвращает подсказку о языке на основе письменности
        """
        script = self.detect(text)
        
        hints = {
            Script.CYRILLIC: "ru",  # По умолчанию русский
            Script.LATIN: "en",      # По умолчанию английский
            Script.CJK: "zh",        # По умолчанию китайский
            Script.ARABIC: "ar",     # Арабский
        }
        
        return hints.get(script, "unknown")
    
    def clear_cache(self):
        """Очищает кэш детектора"""
        self.cache.clear()
        self.cache = {}
    
    def get_stats(self) -> dict:
        """Возвращает статистику кэша"""
        return {
            'cache_size': len(self.cache),
            'cache_hits': 0,  # TODO: добавить счетчики
            'cache_misses': 0,
        }

# Создаем глобальный экземпляр детектора
detector = ScriptDetector()