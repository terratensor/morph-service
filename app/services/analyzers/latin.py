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
        
        # Анализ с spaCy
        doc = self.nlp(clean_word)
        token = doc[0] if doc else None
        
        if token:
            pos = token.pos_
            pos_eng = token.tag_
            normal_form = token.lemma_
            
            # Извлекаем морфологические признаки
            number = 'singular' if token.morph.get('Number') == ['Sing'] else 'plural'
            gender = token.morph.get('Gender', [''])[0] if token.morph.get('Gender') else ''
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
            is_geo_marker=False,
            is_uppercase=is_upper,
            is_sentence_start=False,
        )
    
    def analyze_batch(self, words: List[str]) -> List[AnalysisResult]:
        """Переопределяем для оптимизации с spaCy pipeline"""
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
                    is_geo_marker=False,
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