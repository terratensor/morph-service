import pytest
from app.services.detector import ScriptDetector, Script

@pytest.fixture
def detector():
    return ScriptDetector()

def test_cyrillic_detection(detector):
    """Тест определения кириллицы"""
    text = "Привет, как дела?"
    assert detector.detect(text) == Script.CYRILLIC
    
    text = "Русский текст с цифрами 123"
    assert detector.detect(text) == Script.CYRILLIC

def test_latin_detection(detector):
    """Тест определения латиницы"""
    text = "Hello, how are you?"
    assert detector.detect(text) == Script.LATIN
    
    text = "English text with numbers 123"
    assert detector.detect(text) == Script.LATIN

def test_cjk_detection(detector):
    """Тест определения CJK символов"""
    # Китайский
    text = "你好，世界"
    assert detector.detect(text) == Script.CJK
    
    # Японский
    text = "こんにちは"
    assert detector.detect(text) == Script.CJK
    
    # Корейский
    text = "안녕하세요"
    assert detector.detect(text) == Script.CJK
    
    # Тайский
    text = "สวัสดี"
    assert detector.detect(text) == Script.CJK

def test_arabic_detection(detector):
    """Тест определения арабского"""
    text = "مرحبا بالعالم"
    assert detector.detect(text) == Script.ARABIC

def test_mixed_script(detector):
    """Тест смешанной письменности"""
    # Русский + английский
    text = "Привет, how are you?"
    # Если больше 70% одного - определится как он
    # Этот текст примерно 50/50
    result = detector.detect(text)
    assert result == Script.MIXED

def test_empty_text(detector):
    """Тест пустого текста"""
    assert detector.detect("") == Script.UNKNOWN
    assert detector.detect("   ") == Script.UNKNOWN

def test_word_by_word(detector):
    """Тест определения по словам"""
    text = "Привет world! Здравствуйте everyone."
    results = detector.detect_by_word(text)
    
    assert len(results) > 0
    # Проверяем, что русские слова определены как кириллица
    for word, script in results:
        if word in ["Привет", "Здравствуйте"]:
            assert script == Script.CYRILLIC
        elif word in ["world", "everyone"]:
            assert script == Script.LATIN

def test_get_language_hint(detector):
    """Тест подсказок языка"""
    assert detector.get_language_hint("Привет") == "ru"
    assert detector.get_language_hint("Hello") == "en"
    assert detector.get_language_hint("你好") == "zh"
    assert detector.get_language_hint("مرحبا") == "ar"
    assert detector.get_language_hint("123") == "unknown"

def test_cache(detector):
    """Тест кэширования"""
    text = "Привет мир"
    
    # Первый вызов - заполнение кэша
    result1 = detector.detect(text)
    
    # Второй вызов - из кэша
    result2 = detector.detect(text)
    
    assert result1 == result2
    assert text in detector.cache

def test_clear_cache(detector):
    """Тест очистки кэша"""
    text = "Привет мир"
    detector.detect(text)
    assert text in detector.cache
    
    detector.clear_cache()
    assert text not in detector.cache