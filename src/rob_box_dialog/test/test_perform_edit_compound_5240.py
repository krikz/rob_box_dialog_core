"""#5240: составное числительное (≥21) — одно число, не два слова.

``numerals`` режет «двадцать два» на (20, 2). При правке после сказанного {1..21} сегмент «Двадцать два шаг…»
считался повтором целиком, и ``drop_said`` начинал с «тридцать» — 22–29 выпадали. Склейка — в ``count_numbers``:
десятки 20..90 и единица того же падежа — одно число. ``numerals`` и ``counting_rest`` не меняются.
"""

from rob_box_dialog.plan.repeats import (
    count_numbers,
    drop_said,
    numerals,
    same_performance,
    said_numbers,
)


def test_count_numbers_glues_tens_and_units_of_the_same_case():
    """«Тридцать девять» = 39, «сорок» = 40, «двадцать» = 20, «двадцать один» = 21. Разный падеж не склеивается."""
    assert count_numbers("Тридцать девять. Сорок.") == (39, 40)
    assert count_numbers("сорок") == (40,)
    assert count_numbers("двадцать") == (20,)
    assert count_numbers("двадцать один") == (21,)
    assert count_numbers("21") == (21,)
    assert count_numbers("до сорока. Один") == (40, 1)  # «сорока» род., «один» им. — не 41 (#4320)
    assert count_numbers("двадцати двух") == (22,)
    assert numerals("двадцать два") == (20, 2)  # семантика numerals не меняется


def test_edit_after_twenty_one_keeps_twenty_two_not_thirty():
    """Сказано {1..21}, правка «Двадцать один шаг, двадцать два шаг, тридцать шаг» — остаток с «двадцать два»."""
    said = [str(n) for n in range(1, 22)]
    assert said_numbers(said) == frozenset(range(1, 22))
    rows = [("Двадцать один шаг, двадцать два шаг, тридцать шаг", "", "")]
    (kept, _, _) = drop_said(rows, said)[0]
    assert kept.lower().startswith("двадцать два")
    assert not kept.lower().startswith("тридцать")


def test_said_twenty_drops_the_bare_twenty_and_keeps_twenty_one():
    """Сказано {20}: «Двадцать шаг. Двадцать один шаг.» — остаток с «Двадцать один»."""
    rows = [("Двадцать шаг. Двадцать один шаг.", "", "")]
    (kept, _, _) = drop_said(rows, ["двадцать"])[0]
    assert kept.startswith("Двадцать один")


def test_partial_match_does_not_cut_the_unit_off_a_compound():
    """Сказано {20}: «двадцать два шаг» не превращается в «два шаг» — единица составного не отрезается."""
    rows = [("двадцать два шаг", "", "")]
    assert drop_said(rows, ["двадцать"]) == rows


def test_same_performance_matches_compound_words_to_digits_not_a_different_form():
    """«Двадцать один шаг.» и «21 шаг.» — то же выступление; без «шаг» — нет (#4342)."""
    assert same_performance(["Двадцать один шаг."], ["21 шаг."])
    assert not same_performance(["Двадцать один."], ["Двадцать один шаг."])


def test_bare_count_resplit_is_the_same_and_a_step_is_not():
    """#4320: голый счёт в разной нарезке — то же выступление; добавили «шаг» — не то же."""
    bare = ("Один, два, три.", "Двадцать один, двадцать два.")
    resplit = ("Один.", "Два, три, двадцать один.", "Двадцать два.")
    with_step = ("Один шаг, два шага, три шага, двадцать один шаг, двадцать два шага.",)
    assert same_performance(resplit, bare)
    assert same_performance(("21.", "22."), ("Двадцать один.", "Двадцать два."))
    assert not same_performance(with_step, bare)
