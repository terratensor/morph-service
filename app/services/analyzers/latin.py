import spacy
from typing import Dict, Any, List, Optional
import time
from .base import BaseAnalyzer, AnalysisResult

# Временные заглушки для английских правил (позже заменим)
ENGLISH_GEO_MARKERS = {
    'city', 'cities', 'town', 'towns', 'village', 'villages',
    'river', 'rivers', 'lake', 'lakes', 'mountain', 'mountains',
    'country', 'countries', 'state', 'states', 'region', 'regions',
    'capital', 'capitals', 'ocean', 'sea', 'seas', 'bay', 'bays'
}

ENGLISH_PLACE_PREPOSITIONS = {
    'in', 'at', 'on', 'to', 'from', 'near', 'by', 'under', 'over', 'above', 'below'
}

def calculate_relevance_score_en(
    word_pos: str,
    is_uppercase: bool,
    is_sentence_start: bool,
    nearby_geo_markers: List[bool],
    prev_word: str = None
) -> float:
    """
    Временная заглушка для расчета релевантности английских топонимов
    Возвращает базовое значение 0.5 для всех слов
    Позже будет заменена на полноценную реализацию
    """
    # TODO: Реализовать полноценные правила для английского языка
    return 0.5

class LatinAnalyzer(BaseAnalyzer):
    """Анализатор для латинских языков (английский, немецкий и др.)"""
    
    def __init__(self, model: str = 'en_core_web_sm'):
        # Определяем язык по модели
        lang_map = {
            'en_core_web_sm': 'en',
            'de_core_news_sm': 'de',
            'fr_core_news_sm': 'fr',
            'es_core_news_sm': 'es',
        }
        language = lang_map.get(model, 'en')
        super().__init__(language)
        
        # Загружаем модель spaCy
        try:
            self.nlp = spacy.load(model)
        except OSError:
            import subprocess
            subprocess.run(['python', '-m', 'spacy', 'download', model])
            self.nlp = spacy.load(model)
        
        self.model = model
        # Временные правила для английского
        self.geo_markers = ENGLISH_GEO_MARKERS
        self.place_prepositions = ENGLISH_PLACE_PREPOSITIONS
    
    def _analyze_single(self, word: str, context: Optional[List[str]] = None) -> AnalysisResult:
        """Внутренний метод анализа одного слова"""
        # Очищаем слово
        clean_word = word.strip('.,!?;:"()[]{}<>-—–…\'\"')
        
        if not clean_word:
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
        is_geo = clean_word.lower() in self.geo_markers
        
        # Анализ с spaCy
        doc = self.nlp(clean_word)
        token = doc[0] if doc else None
        
        if token:
            pos = token.pos_
            pos_eng = token.tag_
            normal_form = token.lemma_
            
            morph = token.morph
            # Извлекаем морфологические признаки
            number = 'singular' if morph.get('Number') == ['Sing'] else 'plural'
            gender = morph.get('Gender', [''])[0] if morph.get('Gender') else ''
        else:
            pos = 'unknown'
            pos_eng = 'UNKN'
            normal_form = clean_word.lower()
            number = ''
            gender = ''
        
        return AnalysisResult(
            word=clean_word,
            original=word,
            pos=pos,
            pos_eng=pos_eng,
            case='',
            number=number,
            gender=gender,
            normal_form=normal_form,
            score=1.0,
            is_geo_marker=is_geo,
            is_uppercase=is_upper,
            is_sentence_start=False,
        )
    
    def calculate_relevance(self, word: AnalysisResult, words: List[AnalysisResult], idx: int) -> float:
        """
        Расчет релевантности для английского языка
        Пока возвращает заглушку, позже будет заменена
        """
        # Подготавливаем данные для функции
        nearby_geo_markers = []
        start = max(0, idx - 3)
        end = min(len(words), idx + 3)
        for j in range(start, end):
            if j != idx:
                nearby_geo_markers.append(words[j].is_geo_marker)
        
        prev_word = words[idx-1].word if idx > 0 else None
        
        return calculate_relevance_score_en(
            word_pos=word.pos,
            is_uppercase=word.is_uppercase,
            is_sentence_start=word.is_sentence_start,
            nearby_geo_markers=nearby_geo_markers,
            prev_word=prev_word
        )
    
    def post_process(self, words: List[AnalysisResult]) -> List[AnalysisResult]:
        """
        Пост-обработка для английского языка
        Пока ничего не делает, позже будет реализована
        """
        # TODO: Реализовать пост-обработку для английского
        return words

    def analyze_batch(self, words: List[str]) -> List[AnalysisResult]:
        """Пакетная обработка с spaCy pipeline"""
        start_time = time.time()
        
        # Фильтруем пустые слова
        valid_words = [w for w in words if w.strip()]
        if not valid_words:
            return []
        
        # Объединяем слова в один текст для эффективности
        text = ' '.join(valid_words)
        doc = self.nlp(text)
        
        results = []
        token_idx = 0
        for token in doc:
            if not token.is_punct:
                result = AnalysisResult(
                    word=token.text,
                    original=valid_words[token_idx] if token_idx < len(valid_words) else token.text,
                    pos=token.pos_,
                    pos_eng=token.tag_,
                    case='',
                    number='singular' if token.morph.get('Number') == ['Sing'] else 'plural',
                    gender=token.morph.get('Gender', [''])[0] if token.morph.get('Gender') else '',
                    normal_form=token.lemma_,
                    score=1.0,
                    is_geo_marker=token.text.lower() in self.geo_markers,
                    is_uppercase=token.text[0].isupper() if token.text else False,
                    is_sentence_start=False,
                )
                results.append(result)
                token_idx += 1
        
        elapsed = time.time() - start_time
        self.stats['words_processed'] += len(valid_words)
        self.stats['batches_processed'] += 1
        self.stats['total_time'] += elapsed
        
        return results
    
    def get_supported_languages(self) -> List[str]:
        """Список поддерживаемых языков"""
        return [self.language]