import re
from typing import List, Tuple

def split_sentences(text: str) -> List[str]:
    """
    Разбиение текста на предложения по знакам препинания
    Поддерживает русские и английские сокращения
    """
    # Паттерн для разбиения с учетом сокращений (г-н, т.д., etc.)
    sentence_endings = r'(?<=[.!?])\s+(?=[А-ЯA-Z])'
    
    # Временная замена сокращений
    abbreviations = {
        'г-н': 'г@н',
        'г-жа': 'г@жа',
        'т.д.': 'т@д@',
        'т.п.': 'т@п@',
        'etc.': 'etc@',
        'et al.': 'et al@',
    }
    
    text_processed = text
    for abbr, placeholder in abbreviations.items():
        text_processed = text_processed.replace(abbr, placeholder)
    
    # Разбиваем
    raw_sentences = re.split(sentence_endings, text_processed)
    
    # Восстанавливаем сокращения
    sentences = []
    for s in raw_sentences:
        for abbr, placeholder in abbreviations.items():
            s = s.replace(placeholder, abbr)
        sentences.append(s.strip())
    
    return [s for s in sentences if s]

def is_cyrillic(char: str) -> bool:
    """Проверка, является ли символ кириллическим"""
    code = ord(char)
    return (0x0400 <= code <= 0x04FF) or \
           (0x0500 <= code <= 0x052F) or \
           (0x2DE0 <= code <= 0x2DFF) or \
           (0xA640 <= code <= 0xA69F)

def is_latin(char: str) -> bool:
    """Проверка, является ли символ латинским"""
    code = ord(char)
    return (0x0041 <= code <= 0x005A) or \
           (0x0061 <= code <= 0x007A) or \
           (0x00C0 <= code <= 0x00FF)

def is_punctuation(char: str) -> bool:
    """Проверка, является ли символ пунктуацией"""
    return char in '.,!?;:"()[]{}<>-—–…\'\'""'

def clean_word(word: str) -> str:
    """Очистка слова от пунктуации"""
    return word.strip('.,!?;:"()[]{}<>-—–…\'\'""')

def tokenize(text: str) -> List[str]:
    """Простая токенизация на слова"""
    # Разбиваем по пробелам, но сохраняем пунктуацию для контекста
    tokens = re.findall(r'[\w\-]+|[.,!?;:"()\[\]{}<>]', text)
    return tokens

def normalize_text(text: str) -> str:
    """Нормализация текста (лишние пробелы, переносы)"""
    # Заменяем множественные пробелы на один
    text = re.sub(r'\s+', ' ', text)
    # Убираем пробелы перед пунктуацией
    text = re.sub(r'\s+([.,!?;:])', r'\1', text)
    return text.strip()