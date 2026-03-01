import pytest
import asyncio
from app.services.batch_processor import BatchProcessor
from app.services.detector import Script

@pytest.fixture
def processor():
    """Создаем процессор БЕЗ кэша для тестов"""
    return BatchProcessor(max_workers=2, use_cache=False)  # Важно: use_cache=False

@pytest.mark.asyncio
async def test_process_single_russian(processor):
    """Тест обработки одного русского текста"""
    text = "Москва - столица России. Река Волга впадает в Каспийское море."
    
    result = await processor.process_text(text)
    
    assert result['text'] == text
    assert result['language'] == 'ru'
    assert result['script'] == Script.CYRILLIC.value
    assert len(result['words']) > 0
    assert len(result['sentences']) == 2
    
    # Проверяем первое слово
    first_word = result['words'][0]
    assert first_word['word'] == 'Москва'
    assert first_word['pos'] == 'существительное'
    assert first_word['is_uppercase'] is True
    assert first_word['is_sentence_start'] is True

@pytest.mark.asyncio
async def test_process_single_english(processor):
    """Тест обработки одного английского текста"""
    text = "London is the capital of Great Britain. The Thames flows through the city."
    
    result = await processor.process_text(text)
    
    assert result['text'] == text
    assert result['language'] == 'en'
    assert result['script'] == Script.LATIN.value
    assert len(result['words']) > 0
    assert len(result['sentences']) == 2
    
    # Проверяем первое слово
    first_word = result['words'][0]
    assert first_word['word'] == 'London'
    assert first_word['pos'] in ['PROPN', 'NOUN']
    assert first_word['is_uppercase'] is True
    assert first_word['is_sentence_start'] is True

@pytest.mark.asyncio
async def test_process_mixed_text(processor):
    """Тест обработки смешанного текста (русский + английский)"""
    text = "Ivan живет в Moscow. Он любит этот city."
    
    result = await processor.process_text(text)
    
    assert result['script'] == Script.MIXED.value
    
    # Проверяем, что слова определились правильно
    words = result['words']
    
    # Ищем русские и английские слова
    russian_words = [w for w in words if w['word'] in ['живет', 'в', 'Он', 'любит', 'этот']]
    english_words = [w for w in words if w['word'] in ['Ivan', 'Moscow', 'city']]
    
    assert len(russian_words) > 0
    assert len(english_words) > 0

@pytest.mark.asyncio
async def test_process_batch(processor):
    """Тест пакетной обработки"""
    texts = [
        "Привет, мир!",
        "Hello, world!",
        "Тестовый текст."
    ]
    
    result = await processor.process_batch(texts)
    
    assert result['texts_processed'] == 3
    assert len(result['results']) == 3
    assert result['total_time_ms'] > 0
    
    # Проверяем, что языки определились правильно
    assert result['results'][0]['language'] == 'ru'
    assert result['results'][1]['language'] == 'en'
    assert result['results'][2]['language'] == 'ru'

@pytest.mark.asyncio
async def test_stats(processor):
    """Тест статистики процессора"""
    processor.reset_stats()
    
    await processor.process_text("Тестовый текст")
    await processor.process_batch(["Text1", "Text2"])
    
    stats = processor.get_stats()
    
    assert stats['texts_processed'] == 3  # 1 + 2
    assert stats['total_time'] > 0
    assert stats['avg_time_per_text'] > 0
    assert 'analyzers_loaded' in stats
    assert 'cyrillic' in stats['analyzers_loaded']
    assert 'latin' in stats['analyzers_loaded']

@pytest.mark.asyncio
async def test_empty_text(processor):
    """Тест обработки пустого текста"""
    result = await processor.process_text("")
    
    assert len(result['words']) == 0
    assert len(result['sentences']) == 0
    assert result['processing_time_ms'] >= 0

@pytest.mark.asyncio
async def test_unicode_text(processor):
    """Тест обработки текста с Unicode символами"""
    text = "Café Müllerstraße 北京"
    
    result = await processor.process_text(text)
    
    # Не должен упасть с ошибкой кодировки
    assert result['text'] == text
    assert len(result['words']) > 0