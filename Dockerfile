FROM python:3.13-slim

WORKDIR /app

# Копируем зависимости
COPY requirements.txt .

# Устанавливаем зависимости (патчи больше не нужны!)
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код сервиса
COPY morph_service.py .

# Создаем непривилегированного пользователя
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "morph_service:app", "--host", "0.0.0.0", "--port", "8000"]