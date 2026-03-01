# Билдер
FROM python:3.13-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Копируем все requirements файлы
COPY requirements/ ./requirements/

# Устанавливаем зависимости (без --user, в системную папку)
RUN pip install --no-cache-dir -r requirements/prod.txt

# Скачиваем модели spaCy
RUN python -c "import spacy; spacy.load('en_core_web_sm')" || \
    python -m spacy download en_core_web_sm

# Финальный образ
FROM python:3.13-slim

WORKDIR /app

# Копируем системные пакеты из билдера
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Копируем код приложения
COPY app/ ./app/
COPY .env.example .env

# Создаем непривилегированного пользователя
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Проверка здоровья
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

# Запуск с gunicorn для продакшена
CMD ["gunicorn", "app.main:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]