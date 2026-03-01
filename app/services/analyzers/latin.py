import spacy
from typing import Dict, Any, List, Optional
import time
from .base import BaseAnalyzer, AnalysisResult

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
    
    def analyze_word(self, word: str, context: Optional[List[str]] = None) -> AnalysisResult:
        """Анализ одного слова"""
        start_time = time.time()
        
        # Очищаем слово
        clean_word = word.strip('.,!?;:"()[]{}<>-—–…\'\"')
        
        # Определяем регистр
        is_upper = clean_word and clean_word[0].isupper()
        
        # Анализ с spaCy
        doc = self.nlp(clean_word)
        token = doc[0] if doc else None
        
        if token:
            pos = token.pos_
            pos_eng = token.tag_
            normal_form = token.lemma_
            
            # Извлекаем морфологические признаки
            morph = token.morph
            number = 'singular' if morph.get('Number') == ['Sing'] else 'plural'
            gender = morph.get('Gender', [''])[0] if morph.get('Gender') else ''
        else:
            pos = 'unknown'
            pos_eng = 'unknown'
            normal_form = clean_word.lower()
            number = ''
            gender = ''
        
        # Создаем результат
        result = AnalysisResult(
            word=clean_word,
            original=word,
            pos=pos,
            pos_eng=pos_eng,
            case='',  # В английском нет падежей
            number=number,
            gender=gender,
            normal_form=normal_form,
            score=1.0,
            is_geo_marker=False,  # TODO: добавить английские маркеры
            is_uppercase=is_upper,
            is_sentence_start=False,
        )
        
        elapsed = time.time() - start_time
        self._update_stats(1, elapsed)
        
        return result
    
    def analyze_batch(self, words: List[str]) -> List[AnalysisResult]:
        """Пакетный анализ с использованием spaCy pipeline"""
        start_time = time.time()
        
        # Объединяем слова в один текст для эффективности
        text = ' '.join(words)
        doc = self.nlp(text)
        
        results = []
        for token in doc:
            if not token.is_punct:
                result = AnalysisResult(
                    word=token.text,
                    original=token.text,
                    pos=token.pos_,
                    pos_eng=token.tag_,
                    case='',
                    number='singular' if token.morph.get('Number') == ['Sing'] else 'plural',
                    gender=token.morph.get('Gender', [''])[0] if token.morph.get('Gender') else '',
                    normal_form=token.lemma_,
                    score=1.0,
                    is_geo_marker=False,
                    is_uppercase=token.text[0].isupper() if token.text else False,
                    is_sentence_start=False,
                )
                results.append(result)
        
        elapsed = time.time() - start_time
        self._update_stats(len(words), elapsed)
        
        return results
    
    def get_supported_languages(self) -> List[str]:
        """Список поддерживаемых языков"""
        return [self.language]