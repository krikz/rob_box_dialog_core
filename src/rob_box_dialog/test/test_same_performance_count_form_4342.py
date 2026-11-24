"""#4342: счёт с формой («шаг») — не то же выступление, что голый счёт с теми же числами.

Акт 8, n807 (run 45474089269): звучал «Один, два, … семнадцать», модель прислала «Один шаг, два шага…».
``same_performance`` сравнивал только числа, оба счёта прошли ``is_counting``, и хост перезапустил выступление
вместо слияния — числа 1..17 прозвучали дважды. Голый счёт против голого счёта с теми же числами остаётся тем же
(#4320: та же просьба посреди идущего).
"""

from rob_box_dialog.plan.repeats import counting_rest, is_counting, same_performance

BARE = ("Один, два, три, четыре, пять.", "Шесть, семь, восемь, девять, десять.")
BARE_RESPLIT = ("Один, два.", "Три, четыре, пять, шесть, семь.", "Восемь, девять, десять.")
WITH_STEP = (
    "Один шаг, два шага, три шага.",
    "Четыре шага, пять шагов, шесть шагов, семь шагов, восемь шагов, девять шагов, десять шагов.",
)
WITH_STEP_RESPLIT = (
    "Один шаг, два шага.",
    "Три шага, четыре шага, пять шагов.",
    "Шесть шагов, семь шагов, восемь шагов, девять шагов, десять шагов.",
)


def test_count_with_step_is_not_the_same_as_the_bare_count():
    """«Один шаг…» и «Один…» — разные просьбы, даже если числа совпали и оба сегмента — счёт."""
    assert all(is_counting(text) for text in (*BARE, *WITH_STEP))
    assert not same_performance(WITH_STEP, BARE)
    assert not same_performance(BARE, WITH_STEP)


def test_bare_count_with_the_same_numbers_is_the_same_performance():
    """#4320: голый счёт против голого счёта, те же числа, другая нарезка, цифры или слова — то же выступление."""
    assert same_performance(BARE_RESPLIT, BARE)
    assert same_performance(("1, 2, 3, 4, 5.", "6, 7, 8, 9, 10."), BARE)
    loud = ("ОДИН, два!", "Три. Четыре, пять.")
    quiet = ("один", "два, три, четыре, пять.")
    assert same_performance(loud, quiet)
    assert counting_rest(" ".join(BARE)) == ()


def test_count_with_the_same_form_is_the_same_across_a_different_split():
    """Та же форма и те же числа — то же выступление, как бы сегменты ни нарезали."""
    assert same_performance(WITH_STEP_RESPLIT, WITH_STEP)
    assert same_performance(("Один ШАГ, два шага!",), ("один шаг. Два шага.",))


def test_a_different_form_is_not_the_same_count():
    assert not same_performance(("Один шаг, два шага.",), ("Один метр, два метра.",))
    assert not same_performance(("Один шаг, два шага.",), ("Один, два — шаг.",))


def test_form_in_only_some_segments_still_counts():
    """Форма в части сегментов не теряется на склейке: против голого счёта это не то же, против себя — то же."""
    partial = ("Один, два, три.", "Четыре шага, пять шагов.")
    bare = ("Один, два.", "Три, четыре, пять.")
    assert all(is_counting(text) for text in partial)
    assert not same_performance(partial, bare)
    assert same_performance(("Один, два.", "Три, четыре шага, пять шагов."), partial)


def test_empty_rest_and_empty_sides_stay_strict():
    assert counting_rest("Один, два, три.") == ()
    assert counting_rest("Один шаг, два шага.") == ("шаг", "шага")
    assert counting_rest("") == ()
    assert not same_performance((), BARE)
    assert not same_performance(BARE, ())
    assert not same_performance(("Один, два.",), ("Один, два, три.",))
