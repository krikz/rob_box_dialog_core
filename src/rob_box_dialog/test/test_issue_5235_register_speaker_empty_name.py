"""#5235: фраза «Запомнил тебя, {name}» не строится из пустого имени.

Живой марафон 24.11 (акт 2c): модель позвала ``register_speaker`` с пустыми аргументами (``{}``),
тул и исполнитель отдали событие ``done`` с ``name=None`` — и код синтеза речи произнёс
«Запомнил тебя, None.» (``str.format(name=None)`` подставляет слово «None»). В монорепо это
чинит сам тул (``status=rejected``); здесь — вторая линия защиты: без записанного имени фразы
успеха нет вовсе, даже если старое событие пришло ``done``. Отказ (``identity.rejected``) слота
имени не имеет и звучит как раньше — его не трогаем.
"""

from rob_box_dialog import knowledge as kn
from rob_box_dialog.respond import ActionResult, phrase_from_result
from rob_box_dialog.turn import outcome_phrase


def _result(status, reason=None, **data):
    return ActionResult(
        "t/0",
        0,
        "personality",
        "register_speaker",
        kn.TOOL_CLASSES["register_speaker"],
        status,
        reason,
        data,
    )


def test_success_phrase_is_never_built_from_a_missing_name() -> None:
    """``None``, пусто, пробелы и литералы ``None``/``null`` в речь успеха не попадают."""
    for name in (None, "", "   ", "None", "null"):
        said = phrase_from_result(_result("done", name=name))
        text = "" if said is None else said.text
        assert "None" not in text and "null" not in text.lower()
        assert not text.startswith("Запомнил тебя")
        joined = outcome_phrase([_result("done", name=name)])
        assert joined is None or ("None" not in joined and not joined.startswith("Запомнил тебя"))


def test_recorded_name_still_says_remembered() -> None:
    """Записанное имя звучит как раньше: фраза кода из результата, не из догадки."""
    said = phrase_from_result(_result("done", name="Глеб"))
    assert said is not None and said.text == "Запомнил тебя, Глеб."
    assert outcome_phrase([_result("done", name="Глеб")]) == "Запомнил тебя, Глеб."


def test_refusal_still_speaks() -> None:
    """Отказ без слота имени не заглушён: «Не смог запомнить голос.» звучит (это не успех)."""
    said = phrase_from_result(_result("rejected", "name_required"))
    assert said is not None and said.text.strip()


def test_self_intro_name_is_not_silently_spoken_as_the_registered_name() -> None:
    """``self_intro_name`` в данных события не становится слотом успеха."""
    said = phrase_from_result(
        _result("rejected", "name_required", self_intro_name="Тамара", known_speaker_name="Нина")
    )
    text = "" if said is None else said.text
    assert "Тамара" not in text and "Запомнил тебя" not in text and "None" not in text
