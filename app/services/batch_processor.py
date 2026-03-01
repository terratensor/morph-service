import asyncio
from asyncio.log import logger
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor
import time
from ..config import settings
from .detector import ScriptDetector, Script
from .analyzers.cyrillic import CyrillicAnalyzer
from .analyzers.latin import LatinAnalyzer
from ..utils.text_utils import split_sentences, tokenize
from ..cache.redis_client import RedisCache

class BatchProcessor:
    """Пакетный процессор для анализа множества текстов с кэшированием"""
    
    def __init__(self, max_workers: int = None, use_cache: bool = True):
        self.max_workers = max_workers or settings.THREAD_POOL_SIZE
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        self.use_cache = use_cache
        self.cache = RedisCache() if use_cache else None
        
        # Инициализируем анализаторы
        self.analyzers = {
            'cyrillic': {
                'ru': CyrillicAnalyzer('ru'),
            },
            'latin': {
                'en': LatinAnalyzer('en_core_web_sm'),
            }
        }
        
        self.detector = ScriptDetector()
        self.stats = {
            'texts_processed': 0,
            'total_time': 0.0,
            'cache_hits': 0,
            'cache_misses': 0,
        }
    
    async def ensure_cache_connection(self):
        """Убедиться, что соединение с кэшем установлено"""
        if self.use_cache and self.cache:
            try:
                await self.cache.connect()
                logger.info("Cache connection established")
            except Exception as e:
                logger.error(f"Failed to connect to cache: {e}")
                # Отключаем кэш при ошибке
                self.use_cache = False
                self.cache = None
    
    def get_analyzer(self, script: Script, language_hint: Optional[str] = None):
        """Получение подходящего анализатора по скрипту"""
        if script == Script.CYRILLIC:
            return self.analyzers['cyrillic']['ru']
        elif script == Script.LATIN:
            return self.analyzers['latin']['en']
        else:
            return None
    
    async def process_text(self, text: str, language_hint: Optional[str] = None) -> Dict[str, Any]:
        """Асинхронная обработка одного текста с кэшированием"""
        start_time = time.time()
        
        # Проверяем кэш
        if self.use_cache and self.cache:
            cached = await self.cache.get(text, language_hint)
            if cached:
                self.stats['cache_hits'] += 1                
                cached['from_cache'] = True  # Добавляем флаг
                return cached
        
        self.stats['cache_misses'] += 1
        
        # Определяем скрипт текста
        script = self.detector.detect(text)
        
        # Разбиваем на предложения
        sentences = split_sentences(text)
        
        # Получаем анализатор
        analyzer = self.get_analyzer(script, language_hint)
        
        all_words = []
        sentences_indices = []
        word_index = 0
        
        for sentence in sentences:
            # Токенизируем предложение
            tokens = tokenize(sentence)
            sentence_results = []
            
            for token in tokens:
                # Определяем скрипт токена (для смешанных текстов)
                token_script = self.detector.detect(token)
                
                # Если скрипт отличается от основного, используем соответствующий анализатор
                if token_script != script:
                    token_analyzer = self.get_analyzer(token_script)
                else:
                    token_analyzer = analyzer
                
                if token_analyzer:
                    # Анализируем слово
                    result = await asyncio.get_event_loop().run_in_executor(
                        self.executor,
                        token_analyzer._analyze_single,
                        token
                    )
                    
                    # Определяем начало предложения
                    result.is_sentence_start = (len(sentence_results) == 0)
                    
                    sentence_results.append(result.to_dict())
                    all_words.append(result.to_dict())
                else:
                    # Если нет подходящего анализатора, создаем базовый результат
                    from .analyzers.base import AnalysisResult
                    result = AnalysisResult(
                        word=token,
                        original=token,
                        pos='unknown',
                        pos_eng='UNKN',
                        normal_form=token.lower()
                    )
                    sentence_results.append(result.to_dict())
                    all_words.append(result.to_dict())
            
            if sentence_results:
                sentences_indices.append(list(range(word_index, word_index + len(sentence_results))))
                word_index += len(sentence_results)
        
        result = {
            'words': all_words,
            'sentences': sentences_indices,
            'text': text,
            'language': language_hint or self.detector.get_language_hint(text),
            'script': script.value,
            'processing_time_ms': (time.time() - start_time) * 1000,
            'from_cache': False,
        }
        
        # Сохраняем в кэш
        if self.use_cache and self.cache:
            await self.cache.set(text, result, language_hint)
        
        elapsed = time.time() - start_time
        self.stats['texts_processed'] += 1
        self.stats['total_time'] += elapsed
        
        return result
    
    async def process_batch(self, texts: List[str]) -> Dict[str, Any]:
        """Пакетная обработка множества текстов"""
        start_time = time.time()
        
        await self.ensure_cache_connection()
        
        tasks = [self.process_text(text) for text in texts]
        results = await asyncio.gather(*tasks)
        
        elapsed = time.time() - start_time
        
        return {
            'results': results,
            'total_time_ms': elapsed * 1000,
            'texts_processed': len(texts),
            'cache_stats': {
                'hits': self.stats['cache_hits'],
                'misses': self.stats['cache_misses'],
            }
        }
    
    async def invalidate_cache(self, text: str, language_hint: Optional[str] = None):
        """Инвалидация кэша для конкретного текста"""
        if self.use_cache and self.cache:
            await self.cache.invalidate(text, language_hint)
    
    async def clear_cache(self):
        """Очистка всего кэша"""
        if self.use_cache and self.cache:
            await self.cache.clear()
            self.stats['cache_hits'] = 0
            self.stats['cache_misses'] = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Статистика процессора"""
        base_stats = {
            **self.stats,
            'avg_time_per_text': self.stats['total_time'] / self.stats['texts_processed'] if self.stats['texts_processed'] > 0 else 0,
            'analyzers_loaded': {
                'cyrillic': list(self.analyzers['cyrillic'].keys()),
                'latin': list(self.analyzers['latin'].keys()),
            }
        }
        
        if self.use_cache and self.cache:
            base_stats['cache'] = self.cache.get_stats()
        
        return base_stats
    
    def reset_stats(self):
        """Сброс статистики"""
        self.stats = {
            'texts_processed': 0,
            'total_time': 0.0,
            'cache_hits': 0,
            'cache_misses': 0,
        }