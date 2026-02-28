# Morphology Service v2

Multi-language morphological analysis service for Russian, English, and more.

## Features

- 🌍 Multi-language support (Russian, English, Ukrainian, etc.)
- 🚀 Async batch processing
- 💾 Redis caching
- 🐳 Docker-ready
- 📊 Health checks and monitoring

## Quick Start

```bash
# Install dependencies
pip install -r requirements/dev.txt

# Download spaCy models
python -m spacy download en_core_web_sm

# Run with uvicorn
uvicorn app.main:app --reload
```

## API Endpoints

- `GET /health` - Service health check
- `POST /analyze` - Analyze single text
- `POST /batch` - Analyze multiple texts
- `GET /stats` - Cache statistics

## Development

```bash
# Install dev dependencies
pip install -r requirements/dev.txt

# Run tests
pytest

# Format code
black app/ tests/
isort app/ tests/
```

## Docker

```bash
# Build
docker build -f docker/Dockerfile -t morph-service .

# Run with docker-compose
docker-compose up
```
