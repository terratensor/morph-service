import pytest
import os

@pytest.fixture(autouse=True)
def setup_test_env():
    """Установка переменных окружения для тестов"""
    os.environ['REDIS_URL'] = 'redis://localhost:6379/1'
    os.environ['ENV'] = 'test'
    yield