import pytest
import pytest_asyncio
from app.services.batch_processor import BatchProcessor
import logging
logging.basicConfig(level=logging.INFO)

@pytest_asyncio.fixture
async def processor_with_cache():
    """Фикстура с кэшем"""
    proc = BatchProcessor(max_workers=2, use_cache=True)
    # Принудительно подключаемся к Redis
    await proc.ensure_cache_connection()
    # Убедимся, что кэш действительно работает
    assert proc.cache is not None, "Redis should be available"
    assert proc.cache.redis is not None, "Redis connection failed"
    yield proc
    # Очищаем после тестов
    if proc.cache and proc.cache.redis:
        await proc.clear_cache()
        await proc.cache.close()

@pytest.fixture
def processor_without_cache():
    """Фикстура без кэша"""
    return BatchProcessor(max_workers=2, use_cache=False)

@pytest.mark.asyncio
async def test_cache_hit(processor_with_cache):
    """Тест попадания в кэш"""
    text = "Тестовый текст для кэширования"
    
    # Первый запрос - должен быть кэш-мисс
    result1 = await processor_with_cache.process_text(text)
    assert 'from_cache' not in result1 or not result1.get('from_cache', False)
    
    stats1 = processor_with_cache.get_stats()
    assert stats1['cache_misses'] >= 1
    
    # Второй запрос с тем же текстом - должен быть кэш-хит
    result2 = await processor_with_cache.process_text(text)
    
    stats2 = processor_with_cache.get_stats()
    assert stats2['cache_hits'] >= 1
    assert stats2['cache_misses'] >= 1

@pytest.mark.asyncio
async def test_cache_different_texts(processor_with_cache):
    """Тест разных текстов - разные ключи кэша"""
    text1 = "Первый текст"
    text2 = "Второй текст"
    
    await processor_with_cache.process_text(text1)
    await processor_with_cache.process_text(text2)
    
    stats = processor_with_cache.get_stats()
    assert stats['cache_misses'] >= 2
    assert stats['cache_hits'] == 0

@pytest.mark.asyncio
async def test_cache_invalidation(processor_with_cache):
    """Тест инвалидации кэша"""
    text = "Текст для инвалидации"
    
    # Кэшируем
    await processor_with_cache.process_text(text)
    misses_before = processor_with_cache.get_stats()['cache_misses']
    
    # Инвалидируем
    await processor_with_cache.invalidate_cache(text)
    
    # Должен быть мисс
    await processor_with_cache.process_text(text)
    stats = processor_with_cache.get_stats()
    assert stats['cache_misses'] >= misses_before + 1

@pytest.mark.asyncio
async def test_cache_clear(processor_with_cache):
    """Тест полной очистки кэша"""
    texts = ["Текст 1", "Текст 2", "Текст 3"]
    
    for text in texts:
        await processor_with_cache.process_text(text)
    
    misses_before = processor_with_cache.get_stats()['cache_misses']
    assert misses_before >= 3
    
    await processor_with_cache.clear_cache()
    
    # Сбросим статистику после очистки
    processor_with_cache.reset_stats()
    
    for text in texts:
        await processor_with_cache.process_text(text)
    
    stats = processor_with_cache.get_stats()
    assert stats['cache_misses'] >= 3
    assert stats['cache_hits'] == 0

@pytest.mark.asyncio
async def test_cache_disabled(processor_without_cache):
    """Тест с отключенным кэшем"""
    text = "Тест без кэша"
    
    await processor_without_cache.process_text(text)
    await processor_without_cache.process_text(text)
    
    stats = processor_without_cache.get_stats()
    assert stats['cache_misses'] == 2
    assert stats['cache_hits'] == 0