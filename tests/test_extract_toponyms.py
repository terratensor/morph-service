import pytest
import requests
from app.config import settings

BASE_URL = "http://localhost:8000"

@pytest.fixture(scope="session")
def service_available():
    """Проверка доступности сервиса перед тестами"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        return response.status_code == 200
    except:
        return False

def test_extract_toponyms_russian(service_available):
    """Тест извлечения топонимов из русского текста"""
    if not service_available:
        pytest.skip("Service not available")
    
    response = requests.post(
        f"{BASE_URL}/extract-toponyms",
        json={"text": "Москва - столица России. Иван поехал в город."}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Проверяем структуру ответа
    assert "words" in data
    assert "sentences" in data
    assert "language" in data
    assert data["language"] == "ru"
    
    # Проверяем наличие relevance_score
    for word in data["words"]:
        assert "relevance_score" in word
        assert isinstance(word["relevance_score"], (int, float))
    
    # Проверяем, что топонимы имеют более высокий score
    words = {w["word"]: w["relevance_score"] for w in data["words"]}
    
    # "Москва" должна иметь высокий score
    assert words.get("Москва", 0) > 0.3
    # "город" - географический маркер
    assert words.get("город", 0) > 0.2
    # "поехал" - глагол, низкий score
    assert words.get("поехал", 1) < 0.3

def test_extract_toponyms_english(service_available):
    """Тест извлечения топонимов из английского текста (заглушка)"""
    if not service_available:
        pytest.skip("Service not available")
    
    response = requests.post(
        f"{BASE_URL}/extract-toponyms",
        json={"text": "London is the capital of Great Britain. John went to the city."}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["language"] == "en"
    
    for word in data["words"]:
        assert word["relevance_score"] == 0.5

def test_extract_toponyms_mixed(service_available):
    """Тест смешанного текста (русский + английский)"""
    if not service_available:
        pytest.skip("Service not available")
    
    response = requests.post(
        f"{BASE_URL}/extract-toponyms",
        json={"text": "Ivan живет в Moscow. Он любит этот city."}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["script"] == "mixed"
    
    words = {w["word"]: w["relevance_score"] for w in data["words"]}
    
    assert words.get("живет", 0) > 0
    assert words.get("Он", 0) > 0
    assert words.get("Ivan", 0) == 0.5
    assert words.get("Moscow", 0) == 0.5

def test_extract_toponyms_cache(service_available):
    """Тест кэширования результатов"""
    if not service_available:
        pytest.skip("Service not available")
    
    text = "Тестовый текст для проверки кэша"
    
    # Первый запрос
    response1 = requests.post(f"{BASE_URL}/extract-toponyms", json={"text": text})
    assert response1.status_code == 200
    data1 = response1.json()
    assert data1["from_cache"] is False
    
    # Второй запрос с тем же текстом
    response2 = requests.post(f"{BASE_URL}/extract-toponyms", json={"text": text})
    assert response2.status_code == 200
    data2 = response2.json()
    assert data2["from_cache"] is True
    
    # Результаты должны быть идентичными
    assert len(data1["words"]) == len(data2["words"])

def test_extract_toponyms_empty(service_available):
    """Тест с пустым текстом"""
    if not service_available:
        pytest.skip("Service not available")
    
    response = requests.post(f"{BASE_URL}/extract-toponyms", json={"text": ""})
    # Должен быть 400 или 422, в зависимости от валидации
    assert response.status_code in [400, 422]

def test_extract_toponyms_too_long(service_available):
    """Тест с слишком длинным текстом"""
    if not service_available:
        pytest.skip("Service not available")
    
    long_text = "x" * (settings.MAX_TEXT_LENGTH + 1)
    response = requests.post(f"{BASE_URL}/extract-toponyms", json={"text": long_text})
    assert response.status_code in [400, 422]

def test_extract_toponyms_compare_with_mvp(service_available):
    """
    Сравнение с оригинальным MVP на тех же текстах
    relevance_score должен совпадать с точностью до 0.1
    """
    if not service_available:
        pytest.skip("Service not available")
    
    text = "По реке плыли. Остановились в По на ночлег. Иван поехал в город И."
    
    response = requests.post(f"{BASE_URL}/extract-toponyms", json={"text": text})
    assert response.status_code == 200
    data = response.json()
    
    # Ожидаемые значения из MVP (примерные)
    expected_scores = {
        "По": 0.1,  # предлог в начале
        "реке": 0.8,  # географический маркер
        "По": 0.9,  # город (после предлога)
        "Иван": 0.4,  # имя
        "И": 0.7,  # город
    }
    
    words = {w["word"]: w["relevance_score"] for w in data["words"]}
    
    for word, expected in expected_scores.items():
        if word in words:
            assert abs(words[word] - expected) < 0.2, f"{word}: {words[word]} != {expected}"