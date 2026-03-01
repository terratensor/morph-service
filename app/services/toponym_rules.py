"""
Правила определения релевантности топонимов для русского языка
Перенесено из MVP морфологического сервиса
"""

from typing import List, Dict, Set

# Географические маркеры (из MVP)
GEO_MARKERS_RU: Set[str] = {
    'город', 'города', 'городу', 'городом', 'городе', 'городы', 'городов', 
    'г.',  # ← Добавлено!
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

# Предлоги места (из MVP)
PLACE_PREPOSITIONS_RU: Set[str] = {'в', 'во', 'на', 'у', 'из', 'до', 'около', 'возле', 'близ', 'под', 'над'}

# Падежи после предлогов (из MVP)
PREPOSITION_CASES_RU: Dict[str, List[str]] = {
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

def calculate_relevance_score_ru(
    word_pos: str,
    is_uppercase: bool,
    is_sentence_start: bool,
    word_case: str,
    nearby_geo_markers: List[bool],
    prev_word: str = None
) -> float:
    """
    Расчет релевантности слова как потенциального топонима (русский язык)
    Возвращает score от 0 до 1
    
    Args:
        word_pos: часть речи
        is_uppercase: слово с большой буквы
        is_sentence_start: начало предложения
        word_case: падеж слова
        nearby_geo_markers: список булевых значений, есть ли гео-маркер рядом
        prev_word: предыдущее слово (для проверки предлогов)
    """
    score = 0.0
    
    # 1. Часть речи (макс 0.3)
    if word_pos == 'существительное':
        score += 0.3
    elif word_pos == 'прилагательное':
        score += 0.2
    elif word_pos == 'числительное':
        score += 0.1
    
    # 2. Регистр (макс 0.2)
    if is_uppercase and not is_sentence_start:
        score += 0.2
    elif is_uppercase and is_sentence_start:
        score += 0.1  # В начале предложения менее информативно
    
    # 3. Наличие географического маркера поблизости (макс 0.3)
    for has_marker in nearby_geo_markers:
        if has_marker:
            score += 0.3
            break
    
    # 4. Предлог места перед словом (макс 0.2)
    if prev_word and prev_word in PLACE_PREPOSITIONS_RU:
        # Проверяем падеж
        if word_case in PREPOSITION_CASES_RU.get(prev_word, []):
            score += 0.2
        else:
            score += 0.1  # Предлог есть, но падеж не тот
    
    # Ограничиваем максимум 1.0
    return min(score, 1.0)


def post_process_context_ru(words: List[dict]) -> List[dict]:
    """
    Пост-обработка на основе контекста предложения (русский язык)
    Переопределяет разбор морфологии там, где контекст явно указывает на топоним
    """
    result = words.copy()
    
    for i, word in enumerate(result):
        # 1. Предлог места + слово с большой буквы
        if (i > 0 and 
            result[i-1].get('word', '') in PLACE_PREPOSITIONS_RU and 
            word.get('is_uppercase', False)):
            
            # Проверяем падеж
            prep = result[i-1].get('word', '')
            expected_cases = PREPOSITION_CASES_RU.get(prep, [])
            word_case = word.get('case', '')
            
            if word_case in expected_cases:
                # Это топоним
                word['pos'] = 'существительное'
                word['pos_eng'] = 'NOUN'
                word['relevance_score'] = word.get('relevance_score', 0) + 0.5
            else:
                # Слово с большой буквы, но не в том падеже
                word['relevance_score'] = word.get('relevance_score', 0) - 0.2
        
        # 2. Слово с большой буквы и есть гео-маркер рядом
        if word.get('is_uppercase', False):
            # Ищем гео-маркеры в пределах 3 слов
            found_marker = False
            for j in range(max(0, i-3), min(len(result), i+4)):
                if j != i and result[j].get('is_geo_marker', False):
                    found_marker = True
                    break
            
            if found_marker and word.get('pos') in ['предлог', 'союз', 'частица']:
                word['pos'] = 'существительное'
                word['pos_eng'] = 'NOUN'
    
    return result