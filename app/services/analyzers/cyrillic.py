import pymorphy3
from typing import Dict, Any, List, Optional
import time
from .base import BaseAnalyzer, AnalysisResult

class CyrillicAnalyzer(BaseAnalyzer):
    """Анализатор для кириллических языков (русский, украинский и др.)"""
    
    # Маппинг тегов pymorphy3 на русские названия
    POS_MAP = {
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
    
    # Маппинг тегов на английские
    POS_MAP_ENG = {
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
    
    # Падежи
    CASE_MAP = {
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
    
    # Числа
    NUMBER_MAP = {
        'sing': 'единственное',
        'plur': 'множественное',
    }
    
    # Рода
    GENDER_MAP = {
        'masc': 'мужской',
        'femn': 'женский',
        'neut': 'средний',
        'ms-f': 'общий',
    }
    
    # Географические маркеры
    GEO_MARKERS = {
        'город', 'города', 'городу', 'городом', 'городе',
        'река', 'реки', 'реке', 'реку', 'рекой',
        'озеро', 'озера', 'озеру', 'озером', 'озере',
        'посёлок', 'посёлка', 'посёлку', 'посёлком', 'посёлке',
        'деревня', 'деревни', 'деревне', 'деревню', 'деревней',
        'село', 'села', 'селу', 'селом', 'селе',
        'гора', 'горы', 'горе', 'гору', 'горой',
        'край', 'края', 'краю', 'краем', 'крае',
        'область', 'области', 'областью',
        'район', 'района', 'району', 'районом', 'районе',
        'столица', 'столицы', 'столице', 'столицу',
        'страна', 'страны', 'стране', 'страну', 'страной',
    }
    
    def __init__(self, language: str = 'ru'):
        super().__init__(language)
        self.analyzer = pymorphy3.MorphAnalyzer(lang=language)
    
    def analyze_word(self, word: str, context: Optional[List[str]] = None) -> AnalysisResult:
        """Анализ одного слова"""
        start_time = time.time()
        
        # Очищаем слово от пунктуации
        clean_word = word.strip('.,!?;:"()[]{}<>-—–…\'\"')
        
        # Определяем регистр
        is_upper = clean_word and clean_word[0].isupper()
        
        # Определяем, является ли слово географическим маркером
        is_geo = clean_word.lower() in self.GEO_MARKERS
        
        # Морфологический анализ
        parsed = self.analyzer.parse(clean_word)[0]
        
        # Извлекаем теги
        pos_tag = parsed.tag.POS if parsed.tag.POS else 'UNKN'
        pos_ru = self.POS_MAP.get(pos_tag, 'неизвестно')
        pos_eng = self.POS_MAP_ENG.get(pos_tag, 'unknown')
        
        case_tag = parsed.tag.case if parsed.tag.case else ''
        case_ru = self.CASE_MAP.get(case_tag, '')
        
        number_tag = parsed.tag.number if parsed.tag.number else ''
        number_ru = self.NUMBER_MAP.get(number_tag, '')
        
        gender_tag = parsed.tag.gender if parsed.tag.gender else ''
        gender_ru = self.GENDER_MAP.get(gender_tag, '')
        
        # Нормальная форма
        normal_form = parsed.normal_form
        
        # Достоверность
        score = parsed.score
        
        # Создаем результат
        result = AnalysisResult(
            word=clean_word,
            original=word,
            pos=pos_ru,
            pos_eng=pos_eng,
            case=case_ru,
            number=number_ru,
            gender=gender_ru,
            normal_form=normal_form,
            score=score,
            is_geo_marker=is_geo,
            is_uppercase=is_upper,
            is_sentence_start=False,  # Будет установлено позже
        )
        
        # Обновляем статистику
        elapsed = time.time() - start_time
        self._update_stats(1, elapsed)
        
        return result
    
    def analyze_batch(self, words: List[str]) -> List[AnalysisResult]:
        """Пакетный анализ слов"""
        start_time = time.time()
        results = [self.analyze_word(w) for w in words]
        elapsed = time.time() - start_time
        
        self._update_stats(len(words), elapsed)
        return results