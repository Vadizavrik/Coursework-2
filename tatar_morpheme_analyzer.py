# Морфемный анализатор для татарского языка
# Используется для расчёта морфологических метрик
# Основан на курсовой работе 1 курса

class TatarMorphemeAnalyzer:
    """Анализ морфемной структуры татарских слов"""

    def __init__(self):
        # Полный список аффиксов (сгруппировано по частям речи)
        self.all_affixes = [
            # Существительные
            "чы", "че", "лык", "лек", "сыз", "сез", "ла", "лә",
            "лар", "ләр", "нар", "нәр",
            "ым", "ем", "м", "ың", "ең", "ң", "ы", "е", "сы", "се",
            "быз", "без", "гыз", "гез", "лары", "ләре",
            "ның", "нең", "ны", "не", "га", "гә", "ка", "кә",
            "да", "дә", "та", "тә", "дан", "дән", "тан", "тән",
            # Глаголы
            "ыл", "ел", "тыр", "тер", "дыр", "дер", "ыш", "еш",
            "ма", "мә", "ымыз", "ыбыз", "емез", "ебез",  # 1л.мн.ч.
            "а", "ә", "ды", "де", "ты", "те", "ган", "гән", "кан", "кән", "ыр", "ер",
            "мын", "мен", "сың", "сең", "сыз", "сез",
            "у", "ү", "учы", "үче", "асы", "әсе", "ып", "еп",
            # Прилагательные
            "лы", "ле", "рак", "рәк",
            # Числительные
            "нчы", "нче", "ынчы", "енче"
        ]
        # Сортирует по длине (сначала длинные) — важно для корректного выделения
        self.sorted_affixes = sorted(set(self.all_affixes), key=len, reverse=True)

    def _extract_morphemes(self, word: str) -> list:
        """
        Извлекает морфемы из слова с учётом гармонии гласных, 
        последовательно отсекая аффиксы с конца слова
        """
        if not word or len(word) < 2:  # Минимум 2 буквы для корня
            return [word]

        max_affixes_per_word = 5  # Защита от бесконечного цикла
        remaining = word.lower()
        affixes_found = []

        # Ограничивает число аффиксов (защита от бесконечного цикла)
        for _ in range(max_affixes_per_word):
            found = False
            for affix in self.sorted_affixes:
                if (remaining.endswith(affix) 
                    and len(remaining) - len(affix) >= 2  # Мин. длина корня
                    and self._vowel_harmony_match(remaining[:-len(affix)], affix)):
                    
                    affixes_found.append(affix)
                    remaining = remaining[:-len(affix)]
                    found = True
                    break
            if not found:
                break

        # Возвращает: [корень, аффикс1, аффикс2, ...]
        return [remaining] + affixes_found[::-1]

    def _vowel_harmony_match(self, stem: str, affix: str) -> bool:
        """Проверяет гармонию гласных между корнем и аффиксом"""
        front_vowels = "әеөиүэ"
        back_vowels = "аыоу"
    
        # Находит последнюю гласную корня
        stem_vowels = [c for c in stem if c in front_vowels + back_vowels]
        if not stem_vowels:
            return True  # Нет гласных — пропускает проверку
    
        last_vowel = stem_vowels[-1]
        stem_is_front = last_vowel in front_vowels
    
        # Проверяет гласные в аффиксе
        affix_vowels = [c for c in affix if c in front_vowels + back_vowels]
        if not affix_vowels:
            return True  # Аффикс без гласных
    
        # Гласные должны быть одного ряда
        affix_has_front = any(v in front_vowels for v in affix_vowels)
    
        return affix_has_front == stem_is_front

    def count_morphemes(self, word: str) -> int:
        """Возвращает число морфем в слове (корень + аффиксы)"""
        morphemes = self._extract_morphemes(word)
        return len(morphemes)
