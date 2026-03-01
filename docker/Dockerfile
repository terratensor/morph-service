FROM pytorch/pytorch:2.10.0-cuda13.0-cudnn9-runtime

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    git \
    net-tools \
    curl \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

# Создаём venv
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Копируем requirements и устанавливаем
COPY requirements/base.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt && \
    pip list

# Копируем код
COPY app/ ./app/
COPY .env .env

# Проверяем структуру
RUN ls -la && ls -la app/

# Порт
EXPOSE 8080

# Запуск с логированием
CMD ["/opt/venv/bin/python", "-m", "app.main"]