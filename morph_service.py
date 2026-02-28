#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Морфологический сервис для анализа русского текста
Использует pymorphy3 для определения частей речи, падежей и т.д.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pymorphy3
from typing import List, Dict, Optional
import uvicorn
import re
import logging
from collections import Counter

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Morphology Service", description="Морфологический анализ русского текста")

# Разрешаем CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Инициализация морфологического анализатора
try:
    morph = pymorphy3.MorphAnalyzer(lang='ru')
    logger.info("pymorphy3 успешно инициализирован")
except Exception as e:
    logger.error(f"Ошибка инициализации pymorphy3: {e}")
    raise

class TextRequest(BaseModel):
    text: str
    language: str = "ru"

class WordAnalysis(BaseModel):
    word: str
    original: str
    pos: str
    pos_eng: str
    case: str
    number: str
    gender: str
    is_geo_marker: bool
    is_uppercase: bool
    is_sentence_start: bool
    normal_form: str
    score: float
    relevance_score: float = 0.0  # Добавляем поле для релевантности

class AnalysisResponse(BaseModel):
    words: List[WordAnalysis]
    sentences: List[List[int]]
    text: str

# Географические маркеры
GEO_MARKERS = {
    'город', 'города', 'городу', 'городом', 'городе', 'городы', 'городов', 'г.',
    'река', 'реки', 'реке', 'реку', 'рекой', 'рекою', 'рек',
    'озеро', 'озера', 'озеру', 'озером', 'озере', 'озёра', 'озёр',
    'посёлок', 'посёлка', 'посёлку', 'посёлком', 'посёлке', 'посёлки', 'посёлков',
    'деревня', 'деревни', 'деревне', 'деревню', 'деревней', 'деревнею', 'деревень',
    'село', 'села', 'селу', 'селом', 'селе', 'сёла', 'сёл',
    'гора', 'горы', 'горе', 'гору', 'горой', 'горою', 'гор',
    'край', 'края', 'краю', 'краем', 'крае', 'краи', 'краёв',
    'область', 'области', 'областью', 'областей',
    'район', 'района', 'району', 'районом', 'районе', 'районы', 'районов',
    'столица', 'столицы', 'столице', 'столицу', 'столицей', 'столицею',
    'страна', 'страны', 'стране', 'страну', 'страной', 'страною', 'стран',
}

# Предлоги места
PLACE_PREPOSITIONS = {'в', 'во', 'на', 'у', 'из', 'до', 'около', 'возле', 'близ', 'под', 'над'}

# Падежи, требующиеся после предлогов места
PREPOSITION_CASES = {
    'в': ['предложный', 'винительный'],
    'во': ['предложный', 'винительный'],
    'на': ['предложный', 'винительный'],
    'у': ['родительный'],
    'из': ['родительный'],
    'до': ['родительный'],
    'около': ['родительный'],
    'возле': ['родительный'],
    'близ': ['родительный'],
    'под': ['творительный', 'винительный'],
    'над': ['творительный'],
}

POS_TAGS_RU = {
    'NOUN': 'существительное',
    'ADJF': 'прилагательное',
    'ADJS': 'прилагательное-краткое',
    'COMP': 'сравнительное',
    'VERB': 'глагол',
    'INFN': 'инфинитив',
    'PRTF': 'причастие',
    'PRTS': 'причастие-краткое',
    'GRND': 'деепричастие',
    'NUMR': 'числительное',
    'ADVB': 'наречие',
    'NPRO': 'местоимение',
    'PRED': 'предикатив',
    'PREP': 'предлог',
    'CONJ': 'союз',
    'PRCL': 'частица',
    'INTJ': 'междометие',
}

POS_TAGS_ENG = {
    'NOUN': 'noun',
    'ADJF': 'adj',
    'ADJS': 'adj',
    'COMP': 'comp',
    'VERB': 'verb',
    'INFN': 'verb',
    'PRTF': 'part',
    'PRTS': 'part',
    'GRND': 'adv',
    'NUMR': 'num',
    'ADVB': 'adv',
    'NPRO': 'pron',
    'PRED': 'pred',
    'PREP': 'prep',
    'CONJ': 'conj',
    'PRCL': 'part',
    'INTJ': 'intj',
}

CASES_RU = {
    'nomn': 'именительный',
    'gent': 'родительный',
    'datv': 'дательный',
    'accs': 'винительный',
    'ablt': 'творительный',
    'loct': 'предложный',
    'voct': 'звательный',
    'gen2': 'второй родительный',
    'acc2': 'второй винительный',
    'loc2': 'второй предложный',
}

NUMBERS_RU = {
    'sing': 'единственное',
    'plur': 'множественное',
}

GENDERS_RU = {
    'masc': 'мужской',
    'femn': 'женский',
    'neut': 'средний',
    'ms-f': 'общий',
}

def split_sentences(text: str) -> List[str]:
    """Простое разбиение на предложения по знакам препинания"""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]

def calculate_relevance_score(word: WordAnalysis, words: List[WordAnalysis], idx: int) -> float:
    """
    Расчет релевантности слова как потенциального топонима
    Возвращает score от 0 до 1
    """
    score = 0.0
    
    # 1. Часть речи (макс 0.3)
    if word.pos == 'существительное':
        score += 0.3
    elif word.pos == 'прилагательное':
        score += 0.2
    elif word.pos == 'числительное':
        score += 0.1
    
    # 2. Регистр (макс 0.2)
    if word.is_uppercase and not word.is_sentence_start:
        score += 0.2
    elif word.is_uppercase and word.is_sentence_start:
        score += 0.1  # В начале предложения менее информативно
    
    # 3. Наличие географического маркера поблизости (макс 0.3)
    # Смотрим 3 слова назад и 2 вперед
    start = max(0, idx - 3)
    end = min(len(words), idx + 3)
    for j in range(start, end):
        if j != idx and words[j].is_geo_marker:
            # Чем ближе маркер, тем больше вес
            distance = abs(j - idx)
            if distance <= 1:
                score += 0.3
            elif distance <= 2:
                score += 0.2
            else:
                score += 0.1
            break
    
    # 4. Предлог места перед словом (макс 0.2)
    if idx > 0 and words[idx-1].word in PLACE_PREPOSITIONS:
        # Проверяем падеж
        prep = words[idx-1].word
        if word.case in PREPOSITION_CASES.get(prep, []):
            score += 0.2
        else:
            score += 0.1  # Предлог есть, но падеж не тот
    
    # Ограничиваем максимум 1.0
    return min(score, 1.0)

def post_process_context(words: List[WordAnalysis]) -> List[WordAnalysis]:
    """
    Пост-обработка на основе контекста предложения
    Переопределяет разбор морфологии там, где контекст явно указывает на топоним
    """
    for i, word in enumerate(words):
        # 1. Предлог места + слово с большой буквы
        if (i > 0 and 
            words[i-1].word in PLACE_PREPOSITIONS and 
            word.is_uppercase):
            
            # Проверяем падеж
            prep = words[i-1].word
            expected_cases = PREPOSITION_CASES.get(prep, [])
            
            if word.case in expected_cases:
                # Это топоним
                word.pos = 'существительное'
                word.pos_eng = 'noun'
                word.relevance_score += 0.5
            else:
                # Слово с большой буквы, но не в том падеже - возможно не топоним
                word.relevance_score -= 0.2
        
        # 2. Слово с большой буквы и есть гео-маркер рядом
        if word.is_uppercase:
            # Ищем гео-маркеры в пределах 3 слов
            found_marker = False
            for j in range(max(0, i-3), min(len(words), i+4)):
                if j != i and words[j].is_geo_marker:
                    found_marker = True
                    break
            
            if found_marker and word.pos in ['предлог', 'союз', 'частица']:
                word.pos = 'существительное'
                word.pos_eng = 'noun'
    
    # Рассчитываем финальный score релевантности
    for i, word in enumerate(words):
        word.relevance_score = calculate_relevance_score(word, words, i)
    
    return words

@app.get("/")
async def root():
    return {
        "service": "Morphology Service",
        "version": "1.1",
        "description": "Морфологический анализ русского текста с контекстной пост-обработкой",
        "endpoints": {
            "/analyze": "POST - анализ текста",
            "/health": "GET - проверка состояния"
        }
    }

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "morphology",
        "pymorphy3": "loaded"
    }

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_text(request: TextRequest):
    """
    Анализ текста: морфологический разбор + контекстная пост-обработка
    """
    logger.info(f"Получен запрос на анализ текста длиной {len(request.text)} символов")
    
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Текст не может быть пустым")
    
    # Разбиваем на предложения
    sentences_text = split_sentences(request.text)
    
    words_result = []
    sentences_indices = []
    word_index = 0
    
    for sentence_idx, sentence in enumerate(sentences_text):
        sentence_indices = []
        
        # Токенизация
        tokens = re.findall(r'[\w\-]+|[.,!?;:"()\[\]{}]', sentence)
        
        for token_idx, token in enumerate(tokens):
            # Пропускаем знаки препинания
            if token in '.,!?;:"()[]{}':
                continue
            
            clean_word = token.strip('.,!?;:"()[]{}')
            if not clean_word:
                continue
            
            # Морфологический анализ
            parsed = morph.parse(clean_word)[0]
            
            pos_tag = parsed.tag.POS if parsed.tag.POS else 'UNKN'
            pos_ru = POS_TAGS_RU.get(pos_tag, 'неизвестно')
            pos_eng = POS_TAGS_ENG.get(pos_tag, 'unknown')
            
            case_tag = parsed.tag.case if parsed.tag.case else ''
            case_ru = CASES_RU.get(case_tag, '')
            
            number_tag = parsed.tag.number if parsed.tag.number else ''
            number_ru = NUMBERS_RU.get(number_tag, '')
            
            gender_tag = parsed.tag.gender if parsed.tag.gender else ''
            gender_ru = GENDERS_RU.get(gender_tag, '')
            
            is_geo = clean_word.lower() in GEO_MARKERS
            is_upper = clean_word[0].isupper() if clean_word else False
            is_sentence_start = (token_idx == 0)
            normal_form = parsed.normal_form
            score = parsed.score
            
            word_analysis = WordAnalysis(
                word=clean_word,
                original=token,
                pos=pos_ru,
                pos_eng=pos_eng,
                case=case_ru,
                number=number_ru,
                gender=gender_ru,
                is_geo_marker=is_geo,
                is_uppercase=is_upper,
                is_sentence_start=is_sentence_start,
                normal_form=normal_form,
                score=score,
                relevance_score=0.0
            )
            
            words_result.append(word_analysis)
            sentence_indices.append(word_index)
            word_index += 1
        
        if sentence_indices:
            sentences_indices.append(sentence_indices)
    
    # Пост-обработка контекста
    words_result = post_process_context(words_result)
    
    logger.info(f"Анализ завершен: {len(words_result)} слов, {len(sentences_indices)} предложений")
    
    return AnalysisResponse(
        words=words_result,
        sentences=sentences_indices,
        text=request.text
    )

@app.post("/test")
async def test_analysis():
    """Тестовый эндпоинт с предопределенным текстом"""
    test_text = "По реке плыли. Остановились в По на ночлег. Иван поехал в город И."
    request = TextRequest(text=test_text)
    return await analyze_text(request)

if __name__ == "__main__":
    uvicorn.run(
        "morph_service:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )