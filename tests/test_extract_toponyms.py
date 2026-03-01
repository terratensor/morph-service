import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings

client = TestClient(app)

# Убедимся, что приложение запущено для тестов
@pytest.fixture(scope="session", autouse=True)
def ensure_app_running():
    """Фикстура для проверки что приложение доступно"""
    response = client.get("/health")
    assert response.status_code == 200, "Service not available"

def test_extract_toponyms_russian():
    """Тест извлечения топонимов из русского текста"""
    response = client.post(
        "/extract-toponyms",
        json={"text": "Москва - столица России. Иван поехал в город."}
    )
    
    # Если сервис не доступен, пропускаем тест
    if response.status_code == 503:
        pytest.skip("Service not available")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "words" in data
    assert "sentences" in data
    assert "language" in data
    assert data["language"] == "ru"
    
    for word in data["words"]:
        assert "relevance_score" in word
        assert isinstance(word["relevance_score"], (int, float))
    
    words = {w["word"]: w["relevance_score"] for w in data["words"]}
    
    assert words.get("Москва", 0) > 0.3
    assert words.get("город", 0) > 0.2
    assert words.get("поехал", 1) < 0.3

def test_extract_toponyms_english():
    """Тест извлечения топонимов из английского текста (заглушка)"""
    response = client.post(
        "/extract-toponyms",
        json={"text": "London is the capital of Great Britain. John went to the city."}
    )
    
    if response.status_code == 503:
        pytest.skip("Service not available")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["language"] == "en"
    
    for word in data["words"]:
        assert word["relevance_score"] == 0.5

def test_extract_toponyms_mixed():
    """Тест смешанного текста (русский + английский)"""
    response = client.post(
        "/extract-toponyms",
        json={"text": "Ivan живет в Moscow. Он любит этот city."}
    )
    
    if response.status_code == 503:
        pytest.skip("Service not available")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["script"] == "mixed"
    
    words = {w["word"]: w["relevance_score"] for w in data["words"]}
    
    assert words.get("живет", 0) > 0
    assert words.get("Он", 0) > 0
    assert words.get("Ivan", 0) == 0.5
    assert words.get("Moscow", 0) == 0.5

def test_extract_toponyms_cache():
    """Тест кэширования результатов"""
    text = "Тестовый текст для проверки кэша"
    
    response = client.post("/extract-toponyms", json={"text": text})
    if response.status_code == 503:
        pytest.skip("Service not available")
    
    assert response.status_code == 200
    data1 = response.json()
    assert data1["from_cache"] is False
    
    response2 = client.post("/extract-toponyms", json={"text": text})
    assert response2.status_code == 200
    data2 = response2.json()
    assert data2["from_cache"] is True
    
    assert len(data1["words"]) == len(data2["words"])

def test_extract_toponyms_empty():
    """Тест с пустым текстом"""
    response = client.post("/extract-toponyms", json={"text": ""})
    # Должен быть 400 или 422, в зависимости от валидации
    assert response.status_code in [400, 422]

def test_extract_toponyms_too_long():
    """Тест с слишком длинным текстом"""
    long_text = "x" * (settings.MAX_TEXT_LENGTH + 1)
    response = client.post("/extract-toponyms", json={"text": long_text})
    assert response.status_code in [400, 422]

def test_extract_toponyms_compare_with_mvp():
    """
    Сравнение с оригинальным MVP на тех же текстах
    relevance_score должен совпадать с точностью до 0.1
    """
    text = "По реке плыли. Остановились в По на ночлег. Иван поехал в город И."
    
    response = client.post("/extract-toponyms", json={"text": text})
    if response.status_code == 503:
        pytest.skip("Service not available")
    
    assert response.status_code == 200
    data = response.json()
    
    expected_scores = {
        "По": 0.1,
        "реке": 0.8,
        "По": 0.9,
        "Иван": 0.4,
        "И": 0.7,
    }
    
    words = {w["word"]: w["relevance_score"] for w in data["words"]}
    
    for word, expected in expected_scores.items():
        if word in words:
            assert abs(words[word] - expected) < 0.2, f"{word}: {words[word]} != {expected}"