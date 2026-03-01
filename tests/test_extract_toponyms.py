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
    words = {w["word"]: w["relevance_score"] for w in data["words"] if w["word"]}
    
    # "Москва" должна иметь высокий score
    assert words.get("Москва", 0) >= 0.3
    # "город" - географический маркер
    assert words.get("город", 0) >= 0.2
    # "поехал" - глагол, низкий score (должен быть < 0.4)
    assert words.get("поехал", 1) < 0.4

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
    
    # Сейчас все слова имеют 0.5, но это может измениться
    for word in data["words"]:
        assert word["relevance_score"] >= 0

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
    
    assert data["script"] in ["mixed", "cyrillic", "latin"]
    
    words = {w["word"]: w["relevance_score"] for w in data["words"] if w["word"]}
    
    # Русские слова должны иметь score > 0
    if "живет" in words:
        assert words["живет"] >= 0
    if "Он" in words:
        assert words["Он"] >= 0
    
    # Английские слова должны иметь score >= 0
    if "Ivan" in words:
        assert words["Ivan"] >= 0
    if "Moscow" in words:
        assert words["Moscow"] >= 0

def test_extract_toponyms_cache(service_available):
    """Тест кэширования результатов"""
    if not service_available:
        pytest.skip("Service not available")
    
    text = "Тестовый текст для проверки кэша"
    
    # Очищаем кэш перед тестом (если есть эндпоинт)
    try:
        requests.delete(f"{BASE_URL}/cache")
    except:
        pass
    
    # Первый запрос
    response1 = requests.post(f"{BASE_URL}/extract-toponyms", json={"text": text})
    assert response1.status_code == 200
    data1 = response1.json()
    
    # Второй запрос с тем же текстом
    response2 = requests.post(f"{BASE_URL}/extract-toponyms", json={"text": text})
    assert response2.status_code == 200
    data2 = response2.json()
    
    # Проверяем, что результаты одинаковые
    assert len(data1["words"]) == len(data2["words"])
    # Кэш может не отражать from_cache, но результаты должны совпадать
    for w1, w2 in zip(data1["words"], data2["words"]):
        assert w1["word"] == w2["word"]
        assert abs(w1["relevance_score"] - w2["relevance_score"]) < 0.01

def test_extract_toponyms_empty(service_available):
    """Тест с пустым текстом"""
    if not service_available:
        pytest.skip("Service not available")
    
    response = requests.post(f"{BASE_URL}/extract-toponyms", json={"text": ""})
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
    Не строгое сравнение, а проверка что значения в разумных пределах
    """
    if not service_available:
        pytest.skip("Service not available")
    
    text = "По реке плыли. Остановились в По на ночлег. Иван поехал в город И."
    
    response = requests.post(f"{BASE_URL}/extract-toponyms", json={"text": text})
    assert response.status_code == 200
    data = response.json()
    
    words = {w["word"]: w["relevance_score"] for w in data["words"] if w["word"]}
    
    # Проверяем разумные диапазоны
    # Первое "По" - предлог в начале
    if "По" in words:
        assert 0 <= words["По"] <= 0.4
    
    # "реке" - географический маркер
    if "реке" in words:
        assert words["реке"] >= 0.3
    
    # Второе "По" - город
    # В ответе может быть два разных объекта с ключом "По", тест выше
    
    # "Иван" - имя
    if "Иван" in words:
        assert 0.2 <= words["Иван"] <= 0.8
    
    # "И" - город
    if "И" in words:
        assert 0.2 <= words["И"] <= 0.9