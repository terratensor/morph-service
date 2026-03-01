from asyncio.log import logger

import redis.asyncio as redis
import pickle
from typing import Optional, Any
import hashlib
from ..config import settings

class RedisCache:
    """Асинхронный клиент Redis с поддержкой сериализации"""
    
    def __init__(self, redis_url: str = None):
        if redis_url is None:
            redis_url = getattr(settings, 'REDIS_URL', None)
        if redis_url is None:
            redis_url = "redis://localhost:6379/0"
        self.redis_url = redis_url
        self.redis = None
        self.stats = {
            'hits': 0,
            'misses': 0,
            'errors': 0,
        }
        logger.info(f"RedisCache initialized with URL: {self.redis_url}")
    
    async def connect(self):
        """Подключение к Redis"""
        if not self.redis:
            try:
                logger.info(f"Attempting to connect to Redis at {self.redis_url}")
                self.redis = await redis.from_url(
                    self.redis_url,
                    decode_responses=False,
                    max_connections=10,
                    socket_connect_timeout=2,
                    socket_timeout=2,
                    health_check_interval=2
                )
                # Проверяем соединение
                await self.redis.ping()
                logger.info("Successfully connected to Redis")
            except Exception as e:
                logger.error(f"Redis connection failed: {e}")
                self.redis = None
                raise  # Пробрасываем ошибку наверх
    
    async def close(self):
        """Закрытие соединения"""
        if self.redis:
            await self.redis.close()
            self.redis = None
            logger.info("Redis connection closed")
    
    
    def _make_key(self, text: str, language_hint: Optional[str] = None) -> str:
        """Генерация ключа для кэша"""
        key_data = f"{text}:{language_hint or ''}"
        return f"morph:{hashlib.md5(key_data.encode()).hexdigest()}"
    
    async def get(self, text: str, language_hint: Optional[str] = None) -> Optional[Any]:
        """Получение результата из кэша"""
        if not self.redis:
            return None  # Пропускаем кэш, если нет соединения
        
        try:
            key = self._make_key(text, language_hint)
            data = await self.redis.get(key)
            
            if data:
                self.stats['hits'] += 1
                return pickle.loads(data)
            else:
                self.stats['misses'] += 1
                return None
                
        except Exception as e:
            self.stats['errors'] += 1
            return None
    
    async def set(self, text: str, result: Any, language_hint: Optional[str] = None, ttl: int = None):
        """Сохранение результата в кэш"""
        if not self.redis:
            return  # Пропускаем кэш, если нет соединения
        
        try:
            key = self._make_key(text, language_hint)
            data = pickle.dumps(result)
            ttl = ttl or settings.CACHE_TTL
            await self.redis.setex(key, ttl, data)
        except Exception as e:
            self.stats['errors'] += 1
    
    async def invalidate(self, text: str, language_hint: Optional[str] = None):
        """Инвалидация кэша для конкретного текста"""
        if not self.redis:
            return
        
        key = self._make_key(text, language_hint)
        await self.redis.delete(key)
    
    async def clear(self):
        """Очистка всего кэша"""
        if not self.redis:
            return
        
        await self.redis.flushdb()
    
    def get_stats(self):
        """Статистика кэша"""
        return {
            **self.stats,
            'hit_rate': self.stats['hits'] / (self.stats['hits'] + self.stats['misses']) 
                       if (self.stats['hits'] + self.stats['misses']) > 0 else 0
        }