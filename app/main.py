from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import time
from typing import List, Optional

from .config import settings
from .models.request import AnalyzeRequest, BatchRequest
from .models.response import AnalyzeResponse, HealthResponse, StatsResponse, BatchResponse
from .services.batch_processor import BatchProcessor
from .cache.redis_client import RedisCache
from .utils.text_utils import normalize_text
from app.models.toponym import ToponymExtractResponse, ToponymWordAnalysis

# Настройка логирования
logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL))
logger = logging.getLogger(__name__)

# Глобальные объекты
processor = None
cache = None
start_time = time.time()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    global processor, cache
    
    logger.info("Starting Morphology Service v2...")
    
    # Инициализация кэша
    if settings.REDIS_URL:
        try:
            cache = RedisCache(settings.REDIS_URL)
            await cache.connect()
            logger.info("Redis cache initialized")
        except Exception as e:
            logger.warning(f"Redis cache not available: {e}")
            cache = None
    
    # Инициализация процессора
    processor = BatchProcessor(
        max_workers=settings.WORKERS,
        use_cache=cache is not None
    )
    if cache:
        processor.cache = cache
    
    logger.info(f"Batch processor initialized with {settings.WORKERS} workers")
    logger.info(f"Cache available: {cache is not None}")
    
    yield
    
    # Очистка при завершении
    if cache:
        await cache.close()
    logger.info("Shutdown complete")

# Создание приложения
app = FastAPI(
    title="Morphology Service",
    description="Multi-language morphological analysis for Russian, English, and more",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============= Эндпоинты =============

@app.get("/", tags=["Info"])
async def root():
    """Информация о сервисе"""
    return {
        "name": "Morphology Service v2",
        "version": "2.0.0",
        "status": "running",
        "documentation": "/docs" if settings.DEBUG else None,
    }

@app.get("/health", response_model=HealthResponse, tags=["Monitoring"])
async def health_check():
    """Проверка состояния сервиса"""
    global processor, cache
    
    return HealthResponse(
        status="ok",
        version="2.0.0",
        cache_available=cache is not None,
        workers=settings.WORKERS,
        languages_supported=["ru", "en"],  # Можно расширить
        analyzers_loaded=processor.get_stats()['analyzers_loaded'] if processor else {},
        uptime_seconds=time.time() - start_time,
    )

@app.post("/analyze", response_model=AnalyzeResponse, tags=["Analysis"])
async def analyze_text(request: AnalyzeRequest):
    """Анализ одного текста"""
    global processor
    
    if not processor:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    if len(request.text) > settings.MAX_TEXT_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"Text too long. Max {settings.MAX_TEXT_LENGTH} characters"
        )
    
    # Нормализация текста
    normalized_text = normalize_text(request.text)
    
    try:
        result = await processor.process_text(
            normalized_text,
            language_hint=request.language
        )
        return result
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/extract-toponyms", response_model=ToponymExtractResponse, tags=["Toponyms"])
async def extract_toponyms(request: AnalyzeRequest):
    """
    Извлечение топонимов с расчетом релевантности (формат MVP)
    
    Возвращает полный морфологический анализ с relevance_score для каждого слова.
    Для русского языка используется алгоритм из MVP сервиса.
    Для английского языка пока заглушка (все слова с relevance=0.5).
    """
    global processor
    
    if not processor:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    if len(request.text) > settings.MAX_TEXT_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"Text too long. Max {settings.MAX_TEXT_LENGTH} characters"
        )
    
    # Нормализация текста
    normalized_text = normalize_text(request.text)
    
    try:
        result = await processor.extract_toponyms(
            normalized_text,
            language_hint=request.language
        )
        return result
    except Exception as e:
        logger.error(f"Toponym extraction failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/batch", response_model=BatchResponse, tags=["Analysis"])
async def analyze_batch(request: BatchRequest):
    """Пакетный анализ множества текстов"""
    global processor
    
    if not processor:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    if len(request.texts) > settings.BATCH_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Too many texts. Max {settings.BATCH_SIZE}"
        )
    
    # Нормализация всех текстов
    normalized_texts = [normalize_text(t) for t in request.texts]
    
    try:
        result = await processor.process_batch(normalized_texts)
        return result
    except Exception as e:
        logger.error(f"Batch analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats", response_model=StatsResponse, tags=["Monitoring"])
async def get_statistics():
    """Статистика работы сервиса"""
    global processor, cache
    
    if not processor:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    processor_stats = processor.get_stats()
    cache_stats = cache.get_stats() if cache else None
    
    return StatsResponse(
        texts_processed=processor_stats['texts_processed'],
        total_time_seconds=processor_stats['total_time'],
        avg_time_per_text_ms=processor_stats['avg_time_per_text'] * 1000,
        cache_hits=cache_stats['hits'] if cache_stats else 0,
        cache_misses=cache_stats['misses'] if cache_stats else 0,
        cache_hit_rate=cache_stats['hit_rate'] if cache_stats else 0,
        analyzers_loaded=processor_stats['analyzers_loaded'],
        uptime_seconds=time.time() - start_time,
    )

@app.delete("/cache", tags=["Admin"])
async def clear_cache(background_tasks: BackgroundTasks):
    """Очистка кэша (только в development режиме)"""
    if not settings.DEBUG:
        raise HTTPException(status_code=403, detail="Only available in debug mode")
    
    if not cache:
        raise HTTPException(status_code=404, detail="Cache not available")
    
    background_tasks.add_task(cache.clear)
    return {"status": "clearing", "message": "Cache clearing started"}

@app.post("/cache/invalidate", tags=["Admin"])
async def invalidate_cache(text: str, language_hint: Optional[str] = None):
    """Инвалидация конкретного текста в кэше"""
    if not settings.DEBUG:
        raise HTTPException(status_code=403, detail="Only available in debug mode")
    
    if not cache:
        raise HTTPException(status_code=404, detail="Cache not available")
    
    await cache.invalidate(text, language_hint)
    return {"status": "ok", "message": "Cache invalidated"}

# ============= Эндпоинты для отладки =============

if settings.DEBUG:
    
    @app.get("/debug/config", tags=["Debug"])
    async def debug_config():
        """Параметры конфигурации (только для отладки)"""
        return {
            "env": settings.ENV,
            "workers": settings.WORKERS,
            "max_text_length": settings.MAX_TEXT_LENGTH,
            "batch_size": settings.BATCH_SIZE,
            "cache_ttl": settings.CACHE_TTL,
            "redis_url": settings.REDIS_URL,
        }
    
    @app.post("/debug/test", tags=["Debug"])
    async def debug_test(text: str):
        """Быстрый тест анализа (только для отладки)"""
        result = await processor.process_text(text)
        return result