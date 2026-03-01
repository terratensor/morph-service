import asyncio
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor
import time
from ..config import settings
from .detector import ScriptDetector, Script
from .analyzers.cyrillic import CyrillicAnalyzer
from .analyzers.latin import LatinAnalyzer
from ..utils.text_utils import split_sentences, tokenize

class BatchProcessor:
    """Пакетный процессор для анализа множества текстов"""
    
    def __init__(self, max_workers: int = None):
        self.max_workers = max_workers or settings.THREAD_POOL_SIZE
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        
        # Инициализируем анализаторы - только для установленных языков
        self.analyzers = {
            'cyrillic': {
                'ru': CyrillicAnalyzer('ru'),  # Только русский
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
        }
    
    def get_analyzer(self, script: Script, language_hint: Optional[str] = None):
        """Получение подходящего анализатора по скрипту"""
        if script == Script.CYRILLIC:
            # Для кириллицы используем русский (единственный доступный)
            return self.analyzers['cyrillic']['ru']
        elif script == Script.LATIN:
            # Для латиницы используем английский
            return self.analyzers['latin']['en']
        else:
            return None
    
    
    async def process_text(self, text: str, language_hint: Optional[str] = None) -> Dict[str, Any]:
        """Асинхронная обработка одного текста"""
        start_time = time.time()
        
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
                    
                    sentence_results.append(result)
                    all_words.append(result)
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
                    sentence_results.append(result)
                    all_words.append(result)
            
            if sentence_results:
                sentences_indices.append(list(range(word_index, word_index + len(sentence_results))))
                word_index += len(sentence_results)
        
        elapsed = time.time() - start_time
        self.stats['texts_processed'] += 1
        self.stats['total_time'] += elapsed
        
        return {
            'words': [w.to_dict() for w in all_words],
            'sentences': sentences_indices,
            'text': text,
            'language': language_hint or self.detector.get_language_hint(text),
            'script': script.value,
            'processing_time_ms': elapsed * 1000,
        }
    
    async def process_batch(self, texts: List[str]) -> List[Dict[str, Any]]:
        """Пакетная обработка множества текстов"""
        start_time = time.time()
        
        tasks = [self.process_text(text) for text in texts]
        results = await asyncio.gather(*tasks)
        
        elapsed = time.time() - start_time
        
        return {
            'results': results,
            'total_time_ms': elapsed * 1000,
            'texts_processed': len(texts),
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Статистика процессора"""
        return {
            **self.stats,
            'avg_time_per_text': self.stats['total_time'] / self.stats['texts_processed'] if self.stats['texts_processed'] > 0 else 0,
            'analyzers_loaded': {
                'cyrillic': list(self.analyzers['cyrillic'].keys()),
                'latin': list(self.analyzers['latin'].keys()),
            }
        }
    
    def reset_stats(self):
        """Сброс статистики"""
        self.stats = {
            'texts_processed': 0,
            'total_time': 0.0,
            'cache_hits': 0,
        }