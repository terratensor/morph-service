# Morphology Service v2

Production-ready микро-сервис для морфологического анализа текста с поддержкой русского и английского языков. 
Построен на FastAPI, использует pymorphy3 для русского языка и spaCy для английского.

## 🚀 Возможности

- 🌍 **Мультиязычность**: русский (pymorphy3) и английский (spaCy)
- ⚡ **Высокая производительность**: асинхронная обработка, кэширование Redis
- 📦 **Пакетная обработка**: до 1000 текстов за запрос
- 🎯 **Детектор письменности**: автоопределение языка по Unicode-диапазонам
- 💾 **Кэширование**: Redis с автоматическим fallback
- 🐳 **Docker-ready**: multi-stage сборка, docker-compose
- 📊 **Мониторинг**: статистика, health checks, метрики
- 🔧 **Graceful degradation**: работает даже без Redis

## 🏗 Архитектура

```
morph-service/
├── app/
│   ├── main.py                 # FastAPI приложение
│   ├── config.py                # Конфигурация
│   ├── models/                  # Pydantic модели
│   ├── services/
│   │   ├── detector.py          # Детектор письменности
│   │   ├── batch_processor.py   # Пакетный процессор
│   │   └── analyzers/           # Анализаторы языков
│   │       ├── base.py
│   │       ├── cyrillic.py      # pymorphy3
│   │       └── latin.py         # spaCy
│   ├── cache/
│   │   └── redis_client.py      # Redis клиент
│   └── utils/
│       └── text_utils.py        # Утилиты
├── tests/                       # Тесты
├── docker/                      # Docker файлы
└── requirements/                # Зависимости
```

## 📋 Требования

- Python 3.13+
- Redis 7+ (опционально)
- Docker 24+ (для контейнеризации)

## 🔧 Быстрый старт

### Локальный запуск

```bash
# Клонирование
git clone <repository>
cd morph-service

# Создание виртуального окружения
python3.13 -m venv venv
source venv/bin/activate

# Установка зависимостей
pip install -r requirements/dev.txt

# Скачивание моделей spaCy
python -m spacy download en_core_web_sm

# Запуск
uvicorn app.main:app --reload --port 8000
```

### Запуск через Docker

```bash
# Development режим
make dev-up

# Production режим
make prod-up

# Просмотр логов
make logs

# Остановка
make down
```

## 📚 API Endpoints

### Базовые endpoints

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/` | Информация о сервисе |
| GET | `/health` | Проверка состояния |
| GET | `/stats` | Статистика работы |

### Анализ текста

| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | `/analyze` | Анализ одного текста |
| POST | `/batch` | Пакетный анализ |

**Пример запроса:**
```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "Москва - столица России"}'
```

**Пример ответа:**
```json
{
  "words": [
    {
      "word": "Москва",
      "pos": "существительное",
      "pos_eng": "NOUN",
      "case": "именительный",
      "is_uppercase": true,
      "is_sentence_start": true,
      "normal_form": "москва"
    }
  ],
  "language": "ru",
  "script": "cyrillic",
  "processing_time_ms": 1.5,
  "from_cache": false
}
```

### Управление кэшем

| Метод | Endpoint | Описание |
|-------|----------|----------|
| DELETE | `/cache` | Очистка всего кэша (debug mode) |
| POST | `/cache/invalidate` | Инвалидация конкретного текста |

### Debug endpoints (только development)

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/debug/config` | Параметры конфигурации |
| POST | `/debug/test` | Быстрый тест анализа |

## ⚙️ Конфигурация

Переменные окружения (`.env`):

```env
# Environment
ENV=development
DEBUG=true

# Server
HOST=0.0.0.0
PORT=8000
WORKERS=4

# Redis
REDIS_URL=redis://localhost:6379/0
CACHE_TTL=3600

# Limits
MAX_TEXT_LENGTH=100000
BATCH_SIZE=1000

# Analyzers
ENABLE_CYRILLIC=true
ENABLE_LATIN=true
LATIN_MODEL=en_core_web_sm
```

## 🧪 Тестирование

```bash
# Запуск всех тестов
pytest tests/ -v

# С покрытием
pytest tests/ --cov=app --cov-report=html

# Конкретный модуль
pytest tests/test_detector.py -v
```

## 📊 Производительность

- **Одиночный запрос**: 1-5 ms (с кэшем), 10-50 ms (без кэша)
- **Пакет 100 текстов**: 100-500 ms
- **Пропускная способность**: ~1000 запросов/сек на 4 воркерах

## 🐳 Docker Compose

Сервис включает:
- **morph-service**: основное приложение
- **redis**: кэширование
- **redis-commander**: UI для Redis (dev режим)

```bash
# Полный стек
docker-compose --profile dev up -d

# Доступные сервисы:
# - API: http://localhost:8000
# - Redis Commander: http://localhost:8081
# - Документация: http://localhost:8000/docs
```

## 🤝 Интеграция с Yii2

Пример клиента для Yii2:

```php
class MorphologyClient extends Component
{
    public string $baseUrl = 'http://morph-service:8000';
    
    public function analyze(string $text): array
    {
        $response = $this->httpClient->post('/analyze', [
            'text' => $text
        ])->send();
        
        return $response->data;
    }
    
    public function batch(array $texts): array
    {
        $response = $this->httpClient->post('/batch', [
            'texts' => $texts
        ])->send();
        
        return $response->data;
    }
}
```

## 📈 Мониторинг

```bash
# Health check
curl http://localhost:8000/health

# Статистика
curl http://localhost:8000/stats

# Метрики кэша
curl http://localhost:8000/stats | jq '.cache_hit_rate'
```

## 🛠 Траблшутинг

### Redis не доступен
Сервис автоматически отключает кэш и продолжает работу:
```
Cache available: False
```

### Медленные запросы
Проверьте статистику:
```bash
curl http://localhost:8000/stats
```

### Ошибки памяти
Уменьшите `BATCH_SIZE` в конфигурации.

## 📄 Лицензия

MIT
