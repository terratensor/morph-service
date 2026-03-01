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
    assert result.pos_eng == "NOUN"  # Теперь будет NOUN, а не noun
    assert result.case in ["именительный", ""]
    assert result.score > 0

def test_cyrillic_preposition(ru_analyzer):
    """Тест предлогов"""
    result = ru_analyzer.analyze_word("в")
    
    assert result.word == "в"
    assert result.pos == "предлог"
    assert result.pos_eng == "PREP"  # Теперь будет PREP, а не prep

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
    assert results[3].pos_eng == "PREP"

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
    assert results[1].pos in ["AUX", "VERB"]

def test_analyzer_stats(ru_analyzer):
    """Тест статистики анализатора"""
    ru_analyzer.reset_stats()
    
    ru_analyzer.analyze_word("тест")  # Это не батч, а одиночное слово
    ru_analyzer.analyze_batch(["слово1", "слово2"])  # Это один батч из 2 слов
    
    stats = ru_analyzer.get_stats()
    assert stats['words_processed'] == 3  # 1 + 2 = 3
    assert stats['batches_processed'] == 1  # Только один батч, analyze_word не увеличивает batches
    assert stats['total_time'] > 0

def test_analyzer_stats_multiple_batches(ru_analyzer):
    """Тест статистики с несколькими батчами"""
    ru_analyzer.reset_stats()
    
    ru_analyzer.analyze_batch(["слово1", "слово2"])
    ru_analyzer.analyze_batch(["слово3", "слово4"])
    
    stats = ru_analyzer.get_stats()
    assert stats['words_processed'] == 4
    assert stats['batches_processed'] == 2

def test_analyzer_stats_reset(ru_analyzer):
    """Тест сброса статистики"""
    ru_analyzer.analyze_word("тест")
    ru_analyzer.reset_stats()
    
    stats = ru_analyzer.get_stats()
    assert stats['words_processed'] == 0
    assert stats['batches_processed'] == 0
    assert stats['total_time'] == 0