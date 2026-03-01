import pytest
from app.services.analyzers.cyrillic import CyrillicAnalyzer
from app.services.analyzers.latin import LatinAnalyzer

@pytest.fixture
def ru_analyzer():
    return CyrillicAnalyzer('ru')

@pytest.fixture
def en_analyzer():
    return LatinAnalyzer('en_core_web_sm')

def test_cyrillic_basic(ru_analyzer):
    """Базовый тест кириллического анализатора"""
    result = ru_analyzer.analyze_word("Москва")
    
    assert result.word == "Москва"
    assert result.pos == "существительное"
    assert result.pos_eng == "NOUN"
    assert result.case in ["именительный", ""]
    assert result.score > 0

def test_cyrillic_preposition(ru_analyzer):
    """Тест предлогов"""
    result = ru_analyzer.analyze_word("в")
    
    assert result.word == "в"
    assert result.pos == "предлог"
    assert result.pos_eng == "PREP"

def test_cyrillic_uppercase(ru_analyzer):
    """Тест определения заглавных букв"""
    result = ru_analyzer.analyze_word("Москва")
    assert result.is_uppercase is True
    
    result = ru_analyzer.analyze_word("город")
    assert result.is_uppercase is False

def test_cyrillic_geo_markers(ru_analyzer):
    """Тест географических маркеров"""
    result = ru_analyzer.analyze_word("город")
    assert result.is_geo_marker is True
    
    result = ru_analyzer.analyze_word("стол")
    assert result.is_geo_marker is False

def test_cyrillic_batch(ru_analyzer):
    """Тест пакетной обработки"""
    words = ["Москва", "город", "река", "в"]
    results = ru_analyzer.analyze_batch(words)
    
    assert len(results) == 4
    assert results[0].word == "Москва"
    assert results[1].word == "город"
    assert results[3].pos == "предлог"

def test_latin_basic(en_analyzer):
    """Базовый тест латинского анализатора"""
    result = en_analyzer.analyze_word("London")
    
    assert result.word == "London"
    assert result.pos in ["PROPN", "NOUN"]
    assert result.normal_form in ["London", "london"]

def test_latin_verb(en_analyzer):
    """Тест глаголов в английском"""
    result = en_analyzer.analyze_word("running")
    
    assert result.word == "running"
    assert result.pos == "VERB"
    assert result.normal_form == "run"

def test_latin_batch(en_analyzer):
    """Тест пакетной обработки английского"""
    words = ["London", "is", "a", "big", "city"]
    results = en_analyzer.analyze_batch(words)
    
    assert len(results) == 5
    assert results[0].pos in ["PROPN", "NOUN"]
    assert results[1].pos == "AUX" or results[1].pos == "VERB"

def test_analyzer_stats(ru_analyzer):
    """Тест статистики анализатора"""
    ru_analyzer.reset_stats()
    
    ru_analyzer.analyze_word("тест")
    ru_analyzer.analyze_batch(["слово1", "слово2"])
    
    stats = ru_analyzer.get_stats()
    assert stats['words_processed'] == 3
    assert stats['batches_processed'] == 2
    assert stats['total_time'] > 0