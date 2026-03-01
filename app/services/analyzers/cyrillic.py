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
    
    # Маппинг тегов на английские (ВЕРХНИЙ РЕГИСТР для тестов)
    POS_MAP_ENG = {
        'NOUN': 'NOUN',
        'ADJF': 'ADJ',
        'ADJS': 'ADJ',
        'COMP': 'COMP',
        'VERB': 'VERB',
        'INFN': 'VERB',
        'PRTF': 'PART',
        'PRTS': 'PART',
        'GRND': 'ADV',
        'NUMR': 'NUM',
        'ADVB': 'ADV',
        'NPRO': 'PRON',
        'PRED': 'PRED',
        'PREP': 'PREP',
        'CONJ': 'CONJ',
        'PRCL': 'PART',
        'INTJ': 'INTJ',
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
    
    def _analyze_single(self, word: str, context: Optional[List[str]] = None) -> AnalysisResult:
        """Внутренний метод анализа одного слова (без статистики)"""
        # Очищаем слово от пунктуации
        clean_word = word.strip('.,!?;:"()[]{}<>-—–…\'\"')
        
        if not clean_word:
            # Возвращаем пустой результат для пустого слова
            return AnalysisResult(
                word='',
                original=word,
                pos='unknown',
                pos_eng='UNKN',
                case='',
                number='',
                gender='',
                normal_form='',
                score=0.0,
                is_geo_marker=False,
                is_uppercase=False,
                is_sentence_start=False,
            )
        
        # Определяем регистр
        is_upper = clean_word[0].isupper()
        
        # Определяем, является ли слово географическим маркером
        is_geo = clean_word.lower() in self.GEO_MARKERS
        
        # Морфологический анализ
        parsed = self.analyzer.parse(clean_word)[0]
        
        # Извлекаем теги
        pos_tag = parsed.tag.POS if parsed.tag.POS else 'UNKN'
        pos_ru = self.POS_MAP.get(pos_tag, 'неизвестно')
        pos_eng = self.POS_MAP_ENG.get(pos_tag, 'UNKN')
        
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
        return AnalysisResult(
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
            is_sentence_start=False,
        )