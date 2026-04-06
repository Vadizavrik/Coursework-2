# Класс Text для представления татарского текста и расчёта метрик сложности
import re
from tatar_morpheme_analyzer import TatarMorphemeAnalyzer


class Text:
    """Текст с набором метрик сложности"""

    def __init__(self, content: str = "", category: str = None, title: str = None) -> None:
        self.raw_text = content
        self.category = category
        self.title = title or 'Без названия'
        self.cleaned_text = ""
        self.sentences = []
        self.words = []
        self.metrics = {}
        self.morph_analyzer = TatarMorphemeAnalyzer()

    def preprocess(self) -> None:
        """Очистка и разбиение текста на предложения и слова"""
        text = self.raw_text.lower()
        
        # Защита точки в инициалах (И.И. → И_И_)
        text = re.sub(r'(\b[а-яәөүҗңһ])\.(\s*[а-яәөүҗңһ]\.)', r'\1_\2', text)
        text = re.sub(r'([а-яәөүҗңһ])\.', r'\1_', text)
        
        # Оставляет только татарские буквы + .!? + пробелы
        text = re.sub(r'[^а-яәөүҗңһ\s.!?_-]', ' ', text)
        text = re.sub(r'\d+', '', text)
        text = re.sub(r'\.{2,}', '.', text)
        text = re.sub(r'\s+', ' ', text)
        self.cleaned_text = text.strip()
        
        # Восстанавливает инициалы обратно
        text = re.sub(r'_', '.', text)
        
        # Разбиение на предложения (минимум 4 слова или 20+ символов)
        sentences = re.split(r'[.!?]+', text)
        self.sentences = [
            s.strip() for s in sentences 
            if s.strip() and (len(s.strip().split()) >= 4 or len(s.strip()) >= 20)
        ]
        
        # Извлечение слов
        self.words = re.findall(r'[а-яәөүҗңһ]+', text)

    def count_syllables(self, word: str) -> int:
        """Считает слоги по числу гласных"""
        vowels = 'аеёиоуэюяәөүыі'
        return sum(1 for char in word.lower() if char in vowels)

    # Синтаксические метрики

    def calculate_flesch_kincaid(self) -> float:
        """Адаптированный Флеш-Кинкайд для татарского"""
        if len(self.sentences) == 0 or len(self.words) == 0:
            return 1.0
        
        # Средняя длина предложения
        ASL = len(self.words) / len(self.sentences)
        
        # Доля длинных слов (≥8 букв)
        long_words = sum(1 for w in self.words if len(w) >= 8)
        long_word_ratio = long_words / len(self.words)
        
        # Формула
        complexity = 0.32 * ASL + 12.0 * long_word_ratio - 0.5
        
        return round(max(1.0, min(12.0, complexity)), 2)

    def calculate_lix(self) -> float:
        """Адаптированный LIX для татарского"""
        if len(self.sentences) == 0 or len(self.words) == 0:
            return 0.0
        
        # Средняя длина предложения
        ASL = len(self.words) / len(self.sentences)
        
        # Доля длинных слов (≥8 букв)
        long_words = sum(1 for w in self.words if len(w) >= 8)
        long_word_ratio = long_words / len(self.words)
        
        # Формула
        LIX_tatar = ASL + (long_word_ratio * 100)
        return round(LIX_tatar, 2)

    def calculate_coleman_liau(self) -> float:
        """Адаптированный Колман-Лиау"""
        if len(self.sentences) == 0 or len(self.words) == 0:
            return 1.0
        
        # Параметр S (предложения на 100 слов)
        S = (len(self.sentences) / len(self.words)) * 100
        
        # Параметр L (нормализован через отношение букв к морфемам)
        total_letters = sum(len(word) for word in self.words)
        total_morphemes = sum(
            self.morph_analyzer.count_morphemes(word) 
            for word in self.words
        )
        
        if total_morphemes > 0:
            L_norm = (total_letters / total_morphemes) * 100.0
        else:
            L_norm = 500.0
        
        # Формула с константой -9.5 (калибровка под татарский)
        cli = 0.0588 * L_norm - 0.296 * S - 9.5
        
        return round(max(1.0, min(12.0, cli)), 2)

    # Лексические метрики

    def calculate_ttr(self, window_size: int = 100) -> float:
        """Адаптированный TTR"""
        if not self.words:
            return 0.0
        
        # Извлечение корней через морфологический анализатор
        roots = []
        for word in self.words:
            morphemes = self.morph_analyzer._extract_morphemes(word)
            if morphemes:
                roots.append(morphemes[0])  # Первый элемент — корень
        
        if not roots:
            return 0.0
        
        # Если текст короче окна — считает по всему тексту
        if len(roots) < window_size:
            unique = len(set(roots))
            return round(unique / len(roots), 3)
        
        # Скользящее окно для устойчивости к длине текста
        ttr_values = []
        for i in range(len(roots) - window_size + 1):
            window = roots[i:i + window_size]
            unique_in_window = len(set(window))
            ttr_values.append(unique_in_window / window_size)
        
        return round(sum(ttr_values) / len(ttr_values), 3)

    def calculate_guiraud(self) -> float:
        """Адаптированный Жиро"""
        if not self.words:
            return 0.0
        
        N = len(self.words)
        
        # Извлекает корни (адаптация под агглютинацию)
        roots = []
        for word in self.words:
            morphemes = self.morph_analyzer._extract_morphemes(word)
            if morphemes:
                root = morphemes[0].lower()
                roots.append(root)
            else:
                roots.append(word.lower())  # Fallback, если корень не найден
        
        V_roots = len(set(roots))
        
        # Формула
        R_tatar = V_roots / (N ** 0.5)
        
        return round(R_tatar, 2)

    # Морфологические метрики

    def calculate_mmw(self) -> float:
        """Адаптированная MMW"""
        if not self.words or not self.sentences:
            return 0.0
        
        # Среднее число морфем на слово
        total_morphemes = sum(
            len(self.morph_analyzer._extract_morphemes(word))
            for word in self.words
        )
        mmw = total_morphemes / len(self.words)
        
        # Медиана длины предложений (устойчивее среднего к выбросам)
        sentence_lengths = [len(s.split()) for s in self.sentences if s.strip()]
        if not sentence_lengths:
            return 0.0
        
        sentence_lengths_sorted = sorted(sentence_lengths)
        n = len(sentence_lengths_sorted)
        if n % 2 == 1:
            median_length = sentence_lengths_sorted[n // 2]
        else:
            median_length = (sentence_lengths_sorted[n // 2 - 1] + sentence_lengths_sorted[n // 2]) / 2.0
        
        # Итоговая метрика (деление на 10 для удобного диапазона)
        mmw_adapted = (mmw * median_length) / 10.0
        
        return round(mmw_adapted, 2)

    # Общий метод расчёта

    def calculate_all_metrics(self) -> dict[str, float | int]:
        """Считает все метрики и возвращает словарь результатов"""
        # Если текст не обработан — запускает препроцессинг
        if not self.words:
            self.preprocess()
        
        # Базовая статистика
        word_count = len(self.words)
        sentence_count = len(self.sentences)
        unique_words = len(set(self.words))

        avg_word_len = round(sum(len(w) for w in self.words) / word_count, 2) if word_count else 0
        avg_sent_len = round(word_count / sentence_count, 2) if sentence_count else 0
        total_syllables = sum(self.count_syllables(w) for w in self.words) if self.words else 0

        # Словарь всех метрик
        self.metrics = {
            # Синтаксические
            'lix': self.calculate_lix(),
            'flesch_kincaid': self.calculate_flesch_kincaid(),
            'coleman_liau': self.calculate_coleman_liau(),

            # Лексические
            'ttr': self.calculate_ttr(),
            'guiraud': self.calculate_guiraud(),

            # Морфологические
            'mmw': self.calculate_mmw(),

            # Базовая статистика
            'word_count': word_count,
            'sentence_count': sentence_count,
            'unique_word_count': unique_words,
            'avg_word_length': avg_word_len,
            'long_word_count': len([w for w in self.words if len(w) >= 8]),
            'avg_sentence_length': avg_sent_len,
            'total_syllables': total_syllables,
        }

        return self.metrics
