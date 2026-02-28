FROM python:3.13-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements/base.txt .
RUN pip install --user --no-cache-dir -r base.txt

FROM python:3.13-slim

WORKDIR /app

COPY --from=builder /root/.local /root/.local
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages

COPY app/ ./app/
COPY .env.example .env

ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]