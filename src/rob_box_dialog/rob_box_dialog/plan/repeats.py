"""Правка идущего выступления не повторяет уже сказанное (ADR-0148: решает код).

Марафоны 4-6, акт 8 (n807): «посчитай от одного до двадцати», посреди счёта «и после каждого числа добавляй слово шаг».
Модель присылала счёт С НАЧАЛА («Один шаг, два шага…»), а код ставил его на места ещё не сказанных сегментов - числа
9-19 звучали дважды. Вторая половина дефекта - в коде: правка ``edit_pending`` берёт у модели ВСЕ присланные
сегменты. Эта чистая функция снимает из правки то, что уже прозвучало, до того как оно встанет на места несказанных
сегментов (:meth:`~rob_box_dialog.plan.perform.SpeechSide.edit`); первая половина - данные в окне хода
(:func:`~rob_box_dialog.plan.perform.context_block`: ``last_said``, ``pending``).

Что считается повтором (только ведущая часть правки: модель переписывает с начала, а новое идёт за ней; припев в
середине правки законен и остаётся):

* сегмент слово в слово совпадает с уже сказанным (без знаков и регистра);
* счётный сегмент (не меньше двух числительных, и числительные - не меньше половины слов) целиком из чисел, которые уже
  прозвучали («Девять шагов, десять шагов…» после «Девять, десять…»); в сегменте-счёте, где есть и новые числа,
  ведущие числа-повторы отрезаются вместе со своей формой, в том числе внутри предложения через запятую - остаётся
  непрозвучавшее («Двадцать — шаг. Все дошли.» после «двадцать» → «Все дошли.»).

Разбор - по словам и таблицам, без регексов. Модуль чистый: без ROS и I/O.
"""

from __future__ import annotations

from typing import Dict, FrozenSet, List, Sequence, Tuple

#: Числа словами (именительный, рода): значение - канон, по нему сегменты сравниваются; цифры берутся как есть.
_NUMERAL_FORMS: Dict[int, Tuple[str, ...]] = {
    0: ("ноль", "нуль"), 1: ("один", "одна", "одно"), 2: ("два", "две"), 3: ("три",), 4: ("четыре",), 5: ("пять",),
    6: ("шесть",), 7: ("семь",), 8: ("восемь",), 9: ("девять",), 10: ("десять",), 11: ("одиннадцать",),
    12: ("двенадцать",), 13: ("тринадцать",), 14: ("четырнадцать",), 15: ("пятнадцать",), 16: ("шестнадцать",),
    17: ("семнадцать",), 18: ("восемнадцать",), 19: ("девятнадцать",), 20: ("двадцать",), 30: ("тридцать",),
    40: ("сорок",), 50: ("пятьдесят",), 60: ("шестьдесят",), 70: ("семьдесят",), 80: ("восемьдесят",),
    90: ("девяносто",), 100: ("сто",),
}
NUMERAL_WORDS: Dict[str, int] = {form: value for value, forms in _NUMERAL_FORMS.items() for form in forms}
#: Числительное словом для счёта кодом (``counting``): первая форма именительного.
NUMERAL_SAY: Dict[int, str] = {value: forms[0] for value, forms in _NUMERAL_FORMS.items()}
#: Родительный падеж («до сорока», «от одного», #4314); ё → е, как в :func:`words`.
NUMERAL_GENITIVE: Dict[str, int] = {
    "одного": 1, "одной": 1, "двух": 2, "трех": 3, "четырех": 4, "пяти": 5, "шести": 6, "семи": 7, "восьми": 8,
    "девяти": 9, "десяти": 10, "одиннадцати": 11, "двенадцати": 12, "тринадцати": 13, "четырнадцати": 14,
    "пятнадцати": 15, "шестнадцати": 16, "семнадцати": 17, "восемнадцати": 18, "девятнадцати": 19, "двадцати": 20,
    "тридцати": 30, "сорока": 40, "пятидесяти": 50, "шестидесяти": 60, "семидесяти": 70, "восьмидесяти": 80,
    "девяноста": 90, "ста": 100,
}
SENTENCE_END = ".!?…"
#: Слов, кроме чисел, в предложении счёта, которое всё ещё считается единицей счёта (когда счёт уже шёл): «и … шаг — пришли».
COUNT_FILLER_WORDS = 3


def words(text: str) -> Tuple[str, ...]:
    """Слова и числа текста: без знаков, в нижнем регистре, «ё» = «е». «Один — шаг, два!» → один, шаг, два."""
    out: List[str] = []
    current: List[str] = []
    for ch in text.lower().replace("ё", "е") + " ":
        if ch.isalnum():
            current.append(ch)
        elif current:
            out.append("".join(current))
            current = []
    return tuple(out)


def numerals(text: str) -> Tuple[int, ...]:
    """Числа текста по порядку: словами («девять», «одна») и цифрами («9»).

    Составное («двадцать два») здесь - два числа (20, 2), не одно: так считает :func:`is_counting` и тесты правки.
    Для сравнения сказанного и несказанного - :func:`count_numbers` (20+2 = 22)."""
    return tuple(int(w) if w.isdigit() else NUMERAL_WORDS[w] for w in words(text) if w.isdigit() or w in NUMERAL_WORDS)


def _compound_at(tokens: Sequence[str], i: int) -> Tuple[int, int]:
    """Число со слова ``i`` и сколько слов оно заняло. Десятки 20..90 (кратно 10) и единица 1..9 того же падежа -
    одно число («двадцать два» = 22, «двадцати двух» = 22); разные падежи не склеиваются («до сорока. Один» - 40, не 41,
    #4320). Цифра - одно слово, одно число. Не число - ``(0, 0)``. Сотни («сто пятьдесят») не склеиваются."""
    word = tokens[i]
    if word.isdigit():
        return int(word), 1
    value = NUMERAL_WORDS.get(word)
    genitive = word in NUMERAL_GENITIVE
    if value is None and genitive:
        value = NUMERAL_GENITIVE[word]
    if value is None:
        return 0, 0
    after = tokens[i + 1] if i + 1 < len(tokens) else ""
    same_case = genitive == (after in NUMERAL_GENITIVE)
    unit = (NUMERAL_GENITIVE if genitive else NUMERAL_WORDS).get(after) if same_case else None
    if 20 <= value <= 90 and value % 10 == 0 and unit is not None and 1 <= unit <= 9:
        return value + unit, 2
    return value, 1


def count_numbers(text: str) -> Tuple[int, ...]:
    """Числа текста для сравнения счёта: составное - одно число («Двадцать один.» = 21, «21» = 21, «сорок» = 40).

    Обход как у :func:`rob_box_dialog.counting._number_at`: склейка только внутри одного падежа. ``numerals`` не
    меняется - её зовут :func:`is_counting` и тесты, где «двадцать два» ещё два слова."""
    tokens = words(text)
    out: List[int] = []
    i = 0
    while i < len(tokens):
        value, used = _compound_at(tokens, i)
        if used:
            out.append(value)
        i += used or 1
    return tuple(out)


def is_counting(text: str) -> bool:
    """Счёт, а не рассказ с числом: не меньше двух чисел, и они - не меньше половины слов («Один шаг, два шага»)."""
    count = len(numerals(text))
    return count >= 2 and count * 2 >= len(words(text))


def said_numbers(said: Sequence[str]) -> FrozenSet[int]:
    """Какие числа уже прозвучали в сказанном. Составное - одно число: «двадцать один» даёт 21, не 20 и 1."""
    return frozenset(n for text in said for n in count_numbers(text))


def is_repeat(text: str, said: Sequence[str], said_nums: FrozenSet[int]) -> bool:
    """Правка этим сегментом повторила бы сказанное: те же слова или счёт целиком из уже названных чисел."""
    key = words(text)
    if not key:
        return False
    if any(words(done) == key for done in said):
        return True
    return is_counting(text) and all(n in said_nums for n in count_numbers(text))


def _sentences(text: str) -> List[str]:
    """Предложения по знакам конца (знак остаётся при предложении); хвост без знака - своё предложение."""
    out: List[str] = []
    start = 0
    for i, ch in enumerate(text):
        if ch in SENTENCE_END and (i + 1 == len(text) or text[i + 1].isspace()):
            out.append(text[start:i + 1].strip())
            start = i + 1
    if text[start:].strip():
        out.append(text[start:].strip())
    return out


def _count_unit(sentence: str, nums: Sequence[int], counting: bool) -> bool:
    """Предложение - единица счёта: числа - не меньше половины слов («Девятнадцать — шаг.»); счёт уже шёл в снятых
    ведущих сегментах (``counting``) - допустимы ещё до ``COUNT_FILLER_WORDS`` слов-приправ («и двадцать шаг — пришли.»
    после звучащего «И двадцать.»: М8 29.10, n807). Длиннее - рассказ с числом, он остаётся.

    Лишние слова считаются по словам (:func:`numerals`), не по склейке: «Двадцать два.» - два слова-числа, одно
    составное, и это всё ещё единица счёта."""
    spoken = numerals(sentence)
    extra = len(words(sentence)) - len(spoken)
    return len(spoken) * 2 >= len(words(sentence)) or (counting and extra <= COUNT_FILLER_WORDS)


def _unsaid_count_prefix(text: str, said_nums: FrozenSet[int]) -> str:
    """Счёт через запятую — с первого ещё не названного числа; пустая строка — ведущих повторов нет.

    Сказанное составное съедается целиком («двадцать один» после 21 — оба слова), срез — с первого слова несказанного
    составного, а не с его единицы («двадцать два» после 21 не режется до «два»)."""
    if not is_counting(text):
        return ""
    folded = text.lower().replace("ё", "е")
    spans = _word_spans(folded)
    seen_said = False
    i = 0
    while i < len(spans):
        value, used = _compound_at(tuple(word for _, _, word in spans), i)
        if used and value in said_nums:
            seen_said = True
            i += used
            continue
        if used and seen_said:
            return text[spans[i][0]:]
        i += used or 1
    return ""


def _word_spans(folded: str) -> List[Tuple[int, int, str]]:
    """Слова нижнего регистра: ``(начало, конец, слово)`` в ``folded`` (уже без «ё»)."""
    spans: List[Tuple[int, int, str]] = []
    start: int | None = None
    for i, ch in enumerate(folded + " "):
        if ch.isalnum():
            if start is None:
                start = i
            continue
        if start is not None:
            spans.append((start, i, folded[start:i]))
            start = None
    return spans


def _unsaid_part(text: str, said_nums: FrozenSet[int], counting: bool) -> str:
    """Счёт, где есть и новые числа: ведущие числа-повторы отрезаются по словам, а по предложениям убирается их форма
    («Двадцать — шаг. Все дошли.» после «двадцать» → «Все дошли.»); концовка счёт не отменяет. Счёт уже шёл в снятых
    ведущих сегментах (``counting``) - хватает одного числа в сегменте («Девятнадцать — шаг.»), иначе нужно два.
    Не счёт - как есть; всё предложения-повторы - ``""``."""
    part = _unsaid_count_prefix(text, said_nums)
    if part:
        return part
    if len(count_numbers(text)) < (1 if counting else 2):
        return text
    sentences = _sentences(text)
    skip = 0
    for sentence in sentences:
        nums = count_numbers(sentence)
        if not (nums and all(n in said_nums for n in nums) and _count_unit(sentence, nums, counting)):
            break
        skip += 1
    return " ".join(sentences[skip:]) if skip else text


def drop_said(rows: Sequence[Tuple[str, str, str]], said: Sequence[str]) -> List[Tuple[str, str, str]]:
    """Правка без ведущих повторов: ``rows`` - ``(текст, голос, эмоция)``, ``said`` - тексты, что уже прозвучали или
    отданы на звучание. Ведущие сегменты-повторы снимаются; первый не повтор остаётся (счёт - без уже названных
    чисел в начале) и всё за ним - как есть. Всё повтор - ``[]``."""
    nums = said_numbers(said)
    counting = False
    for i, (text, voice, emotion) in enumerate(rows):
        if is_repeat(text, said, nums):
            counting = counting or is_counting(text)
            continue
        part = _unsaid_part(text, nums, counting)
        if part:
            return [(part, voice, emotion), *rows[i + 1:]]
    return []


def counting_rest(text: str) -> Tuple[str, ...]:
    """Слова текста без чисел: форма счёта («шаг», «шага», «шагов»). Пустой кортеж — голый счёт, сравнивать нечего.

    Тот же разбор, что у :func:`words` и :func:`numerals`: без знаков и регистра, «ё» = «е». Склейка сегментов через
    пробел даёт ту же форму, что и по сегментам: нарезка на форму не влияет."""
    return tuple(word for word in words(text) if not (word.isdigit() or word in NUMERAL_WORDS))


def _counts_side(segments: Sequence[str]) -> bool:
    """Сторона выступления — счёт: каждый сегмент проходит :func:`is_counting`, либо склейка (:func:`count_numbers`)
    даёт составное (≥21 не из одного слова таблицы) и слова-числа — не меньше половины слов. Второе — только чтобы
    «21 шаг.» и «Двадцать один шаг.» сравнивались как счёт: по :func:`numerals` у цифры одно число, у слов — два, и
    порог :func:`is_counting` их разводит (#5240). Рассказ с одним числом сюда не попадает: склейки нет."""
    if segments and all(is_counting(text) for text in segments):
        return True
    whole = " ".join(segments)
    spoken = numerals(whole)
    glued = count_numbers(whole)
    compound = any(n >= 21 and n not in NUMERAL_SAY for n in glued)
    return compound and len(spoken) * 2 >= len(words(whole))


def same_performance(new: Sequence[str], old: Sequence[str]) -> bool:
    """Присланные сегменты ``new`` - то же выступление, что ``old``, целиком (#4320: та же просьба посреди идущего):
    счёт - те же числа по порядку (цифрами или словами, составное — одним числом, нарезка любая) и та же форма по словам
    («шаг» против голого счёта — другая просьба, #4342), остальное - те же слова (без знаков и регистра).
    Обе стороны считаются одной функцией (:func:`count_numbers`)."""
    if not new or not old:
        return False
    if _counts_side(new) and _counts_side(old):
        same_nums = count_numbers(" ".join(new)) == count_numbers(" ".join(old))
        same_form = counting_rest(" ".join(new)) == counting_rest(" ".join(old))
        return same_nums and same_form
    return words(" ".join(new)) == words(" ".join(old))


__all__ = ["NUMERAL_GENITIVE", "NUMERAL_SAY", "NUMERAL_WORDS", "count_numbers", "counting_rest", "drop_said",
           "is_counting", "is_repeat", "numerals", "said_numbers", "same_performance", "words"]
